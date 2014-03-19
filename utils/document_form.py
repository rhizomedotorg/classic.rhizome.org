import re
import couchdb
import django.forms
from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.formsets import BaseFormSet, DELETION_FIELD_NAME
import operator
from couchdb.client import *
from couchdb.mapping import *

# ==============================================================================
# Utilities
# ==============================================================================

def pad(l, n):
    """
    Takes a list and pads it with n 'empty' values. This is used by
    update_in to fill empty lists with values that we can iterate
    over and replace.
    """
    empty = None
    if type(l) == couchdb.mapping.ListField.Proxy:
        empty = {}
    for i in range(n):
        l.append(empty)
    return l


# NOTE: Horrible hack - David

def update_in(x, ks, v):
    """
    Takes a dict, list, or object. Can deeply update any nested value
    as long as we're descending into only dicts, lists, and objects.
    """
    k = ks[0]

    if isinstance(x, list) or isinstance(x, dict):
        setter = operator.setitem
        getter = operator.getitem
    elif isinstance(x, object):
        setter = setattr
        getter = getattr
    else:
        raise Exception("Don't know how to update type %s" % type(x))

    # peek to see if we need to create a list
    if len(ks) > 1 and isinstance(ks[1], int) and not isinstance(getter(x, k), list):
        setter(x, k, [])
    elif isinstance(x, dict) and not x.has_key(k):
        x[k] = {}
    elif isinstance(x, list) and len(x) < (k+1):
        x = pad(x, (k+1)-len(x))
        x[k] = {}

    if len(ks) == 1:
        if isinstance(x, list) and len(x) < (k+1):
            x = pad(x, (k+1)-len(x))
        setter(x, k, v)
        return x
    else:
        update_in(getter(x, k), ks[1:], v)
        return x


def accessor(x, k):
    """
    Helper for get_in. Take a key and access x, which may be a dict, list or
    object.
    """
    if isinstance(x, dict) :
        if not x.has_key(k):
            return None
        else:
            return x[k]
    elif isinstance(x, list):
        if k+1 > len(x):
            return None
        else:
            return x[k]
    elif isinstance(x, type) or isinstance(x, object):
        return getattr(x, k)
    

def get_in(x, ks, default=None):
    """
    Takes a dict, list or object and list of keys. Will deeply access that key.
    If a key is not found, short circuits and returns None or the provided
    default value.
    """
    if x is None:
        return default
    for k in ks:
        x = accessor(x, k)
        if x is None:
            return default
    return x

# ==============================================================================
# DocumentForm
# ==============================================================================

# Map CouchDB Document field types to Django form field types - David
_doc_to_form_field = { couchdb.mapping.BooleanField : django.forms.BooleanField
                     , couchdb.mapping.TextField    : django.forms.CharField
                     , couchdb.mapping.IntegerField : django.forms.IntegerField
                     , couchdb.mapping.FloatField   : django.forms.DecimalField
                     , couchdb.mapping.DateField    : django.forms.DateTimeField }


def doc_to_form_field(instance):
    return _doc_to_form_field[instance.__class__](required=False)


def flatten_mapping(x, keys=[]):
    """
    Helper function that takes a couchdb.mapping instance and flattens it into
    a un-nested dictionary. This is critical for working with Django forms.
    """
    acc = {}
    if isinstance(x, couchdb.mapping.ListField):
        x = x.field.mapping
    if isinstance(x, couchdb.mapping.DictField):
        x = x.mapping
    if not hasattr(x, '_fields'):
        raise Exception("Cannot flatten this type.")
    fields = getattr(x, '_fields')
    for k, v in fields.items():
        nkeys = keys[:]
        nkeys.append(k)
        if isinstance(v, couchdb.mapping.DictField):
            r = flatten_mapping(v, nkeys)
            for m, n in r.items():
                acc[m] = n
        elif isinstance(v, couchdb.mapping.ListField):
            raise Exception("Nested ListFields not yet supported")
        elif isinstance(v, couchdb.mapping.Field):
            acc["__".join(nkeys)] = doc_to_form_field(v)
        else:
            raise Exception("Unknown field type %s" % type(v))
    return acc

LIST_KEY_MATCHER = re.compile("(\w+)-(\d+)")

# FIXME: Bug with Map List Map structures I think - David

def unflatten_fields(fields):
    """
    Takes a flat dictionary and re-nests the dictionary back into a proper
    structure containing lists and dictionary which can then be fed to a
    CouchDB mapping instance.
    """
    acc = {}
    for k, v in fields.items():
        ks = k.split("__")
        xs = []
        for k in ks:
            match = LIST_KEY_MATCHER.match(k)
            if match:
                k, n = match.groups()
                xs.extend([k, int(n)])
            else:
                xs.append(k)
        update_in(acc, xs, v)
    return acc


def flatten_fields(x, keys=[]):
    """
    Similar to flatten_mapping but only to be used with dicts or lists.
    """
    acc = {}
    if isinstance(x, dict):
        for k, v in x.items():
            nkeys = keys[:]
            nkeys.append(k)
            acc.update(flatten_fields(v, nkeys))
    elif isinstance(x, list):
        l = len(x)
        for i in range(l):
            nkeys = keys[:]
            nkeys[-1] = "%s-%s" % (nkeys[-1], i)
            acc.update(flatten_fields(x[i], nkeys))
    else:
        acc["__".join(keys)] = x
    return acc


def document_to_dict(document, fields=None, exclude=None):
    """
    Takes a document and converts it into a flattened dictionary. Drops the the _id
    and _rev fields.
    """
    if document is None:
        return {}
    # TODO : need to convert document data to flattened dict
    exclude = list(exclude or [])
    exclude.extend(["_id", "_rev"])
    data = {}
    for k, v in flatten_fields(dict(document._data)).items():
        if k in exclude:
           continue 
        data[k] = v
    return data


class DocumentFormMeta(DeclarativeFieldsMetaclass):
    """
    Metaclass for DocumentForm classes. Similar in concept to the
    django.forms.models.ModelFormMetaclass  except this one is designed to work with
    Document - the CouchDB model.
    """
    def __new__(mcs, name, bases, dct):
        document = None
        path = None
        mc = dct.get("Meta")

        if mc:
            mcdt = mc
            accsr = getattr
        else:
            mcdt = dct
            accsr = operator.getitem
        
        try:
            document = accsr(mcdt, "document")
        except:
            pass
        if document:
            dct["_document"] = document
        
        try:
            path = accsr(mcdt, "path")
        except:
            pass

        if path:
            if not document:
                raise Exception("Defined a document path without a document")
            dct.update(flatten_mapping(get_in(document, path)))
            dct["_path"] = path
            
        return super(DocumentFormMeta, mcs).__new__(mcs, name, bases, dct)


class DocumentForm(django.forms.Form):
    """
    DocumentForm class. Based on django.form.BaseModelForm.
    """
    __metaclass__ = DocumentFormMeta

    def __init__(self, data=None, **kwargs):
        self._index = None
        initial = kwargs.get("initial")
        instance = kwargs.get("instance")
        index = kwargs.get("index")
        if index is not None:
            self._index = index
            del kwargs["index"]
        if instance is None:
            object_data = {}
        else:
            self.instance = instance
            object_data = document_to_dict(get_in(instance, self.get_path()))
        if initial is not None:
            object_data.update(initial)
        if kwargs.has_key("instance"):
            del kwargs["instance"]
        super(DocumentForm, self).__init__(data, initial=object_data, **kwargs)

    def get_path(self):
        """
        DocumentForms generally point to only a specify part of CouchDB document. Documents
        are really like many django Models lumped into one. get_path returns the keys
        needed to get to this form's portion of it's document, even down to it's numerical
        index (required to support DocumentFormSet"
        """
        path = list(self._path)
        if self._index is not None:
            path.append(self._index)
        return tuple(path)

    def save(self, commit=True, index=None):
        if index is not None:
            self._index = index
        # TODO : check if we're empty - David
        if not self.instance:
            raise Exception("Attempt to save Document form w/o instance")
        if not hasattr(self, "cleaned_data"):
            is_valid = self.is_valid()
            if not is_valid:
                raise Exception("Attempt to save invalid DocumentForm")
        d = unflatten_fields(self.cleaned_data)
        # TODO : convert date time information to Couch format - David
        update_in(self.instance, self.get_path(), unflatten_fields(self.cleaned_data))
        if commit:
            self.instance.save()
        else:
            return self.instance


class DocumentFormSet(BaseFormSet):
    """
    ListFields can specify mappings. DocumentFormSet are so that multiple instances of
    values can be created at ListField mapped property. For example, from
    artbase.models.Artwork:

    creators = ListField(DictField(Mapping.build(
                   name    = DictField(Mapping.build(
                                 name_authority    = TextField(),
                                 name_authority_id = IntegerField(),
                                 display_string    = TextField()
                                 )),
                   user_id = IntegerField(),
                   roles   = TextField(),
                   attrs   = TextField(),
                   xts     = TextField(),
                   )))

    DocumentFormSets can manage ListField properties like this.
    """
    def __init__(self, **kwargs):
        self.instance = kwargs.get("instance")
        if self.instance:
            del kwargs["instance"]
        super(DocumentFormSet, self).__init__(**kwargs)

    def _document_path(self):
        return self.__class__.form._path

    def _document_field(self):
        return get_in(self.instance, self._document_path(), [])

    def initial_form_count(self):
        """
        Actual initial form count, not counting extra forms.
        """
        if not(self.data or self.files):
            return max(len(self._document_field()), 1)
        return super(DocumentFormSet, self).initial_form_count()

    def _construct_form(self, i, **kwargs):
        kwargs['instance'] = self.instance
        kwargs['index'] = i
        return super(DocumentFormSet, self)._construct_form(i, **kwargs)

    def save_new_objects(self, commit=True):
        self.new_objects = []
        for form in self.extra_forms:
            if not form.has_changed():
                continue
            self.new_objects.append(form.save(commit=commit))
        return self.new_objects

    def save_existing_objects(self, commit=True):
        """
        If the forms have changed update all the forms simply skipping deleted
        ones and don't increment the index. At the end pop off as many items as
        were delete.

        Because we don't have real ids into and we want some level of atomicity
        and efficiency, we must track when we we're looking at a new *unchanged*
        form. We don't want to add these to the DB, thus we use count and orig_count
        to detect if we're looking at a *new* form.
        """
        self.existing_objects = []
        index = 0
        count = 0
        orig_count = len(self._document_field())
        has_deleted_objects = False
        deleted_objects = 0
        # always update everything except for deleted objects
        for form in self.initial_forms:
            count = count+1
            # skip empty *new* forms
            if count > orig_count and not form.has_changed():
                continue
            if self.can_delete:
                raw_delete_value = form._raw_value(DELETION_FIELD_NAME)
                should_delete = form.fields[DELETION_FIELD_NAME].clean(raw_delete_value)
                # just skip deleted objects
                if should_delete:
                    deleted_objects = deleted_objects+1
                    continue
            self.existing_objects.append(form.save(commit=commit, index=index))
            index = index+1
        for n in range(deleted_objects):
            self._document_field().pop()
        return self.existing_objects

    # TODO: add errors

    def save(self, commit=True):
        # NOTE: this is modeled after how ModelFormSet works - David
        return self.save_existing_objects(commit=commit) + self.save_new_objects(commit=commit)
