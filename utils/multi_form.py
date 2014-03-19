from django.utils.datastructures import SortedDict
from django.forms import Form
from django.forms.formsets import BaseFormSet
from utils.document_form import DocumentForm, DocumentFormSet
from utils.model_document import ModelDocument
from couchdb.client import Document

# from http://parand.com/say/index.php/2008/10/13/access-python-dictionary-keys-as-properties/
# This simple code snippet allows us to access dictionaries with object
# property syntax - David
class DictObj(object):
    def __init__(self, d):
        self.d = d

    def __getattr__(self, m):
        if hasattr(self.d, m) and callable(getattr(self.d, m)):
            return getattr(self.d, m)
        else:
            return self.d.get(m, None)


# Lifted from Alex Gaynor's nifty slides, http://www.slideshare.net/kingkilr/forms-getting-your-moneys-worth

class InstanceProxy(object):
    """
    When multiforms hold document and model forms, both instances need to be saved. This
    class makes that simpler.
    """
    def __init__(self, model=None, document=None):
        self.model = model
        self.document = document
        
    def save(self, **kwargs):
        self.model.save(**kwargs)
        self.document.save(**kwargs)
        

class MultipleFormBase(object):
    """
    Multiple form class. 
    """
    def __init__(self, data=None, files=None, **kwargs):
        instance = kwargs.get("instance")
        doc_instance = None
        # if we have a document instance get the model
        # if have a model instance get the document
        if instance and self.has_document_form:
            if not isinstance(instance, ModelDocument):
                raise Exception("Passed instance to MultipleForm that is not a ModelDocument when MutipleForm contains DocumentForms or Formset created with DocumentForms")
            else:
                doc_instance = instance
                self.doc_instance = doc_instance
                instance = doc_instance.model
        acc = []
        for prefix, form_class in self.form_classes.iteritems():
            kwargs_copy = kwargs.copy()
            # FIXME : WAAAAAAAY too much data type hard wiring going on here - David
            # FormSets/DocumentFormSets don't take standard model instances - David
            if not issubclass(form_class, DocumentFormSet) and issubclass(form_class, BaseFormSet) and instance:
                del kwargs_copy["instance"]
            elif instance:
                if issubclass(form_class, DocumentForm) or issubclass(form_class, DocumentFormSet):
                    kwargs_copy["instance"] = doc_instance
                else:
                    kwargs_copy["instance"] = instance
            acc.append((prefix, form_class(data=data, files=files, prefix=prefix, **kwargs_copy)))
        d = SortedDict(acc)
        self.forms = DictObj(d)
        if instance:
            self.instance = instance
        
    def as_table(self):
        return '\n'.join([form.as_table() for prefix, form in self.forms.iteritems()])

    def save(self, commit=True):
        for prefix, form in self.forms.iteritems():
            form.save(commit)
        if not self.has_document_form:
            return self.instance
        else:
            return InstanceProxy(model=self.instance,
                                 document=self.doc_instance)

    @property
    def errors(self):
        r = []
        for prefix, form in self.forms.iteritems():
            r.append(form.errors)
        return r

    def is_valid(self):
        return all(form.is_valid() for prefix, form in self.forms.iteritems())


def multiple_form_factory(form_classes, form_order=None):
    """
    The main factory function for combining different form classes together
    into one big form - i.e. Artwork Details Form.
    """
    hdf = has_document_form(form_classes)
    if form_order:
        form_classes = SortedDict([(prefix, form_classes[prefix])
                                   for prefix in form_order])
    else:
        form_classes = SortedDict(form_classes)
    return type('MultipleForm', (MultipleFormBase,), {
            'form_classes': form_classes,
            'has_document_form': hdf
            })

def has_document_form(form_classes):
    """
    Helper function to detect whether any document form classes have been passed to
    MultipleFormBase.
    """
    for prefix, form_class in form_classes.iteritems():
        if issubclass(form_class, DocumentForm):
            return True
        if issubclass(form_class, BaseFormSet) and issubclass(form_class.form, DocumentForm):
            return True
    return False
