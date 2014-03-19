from couchdb.mapping import Document, DocumentMeta


class ModelDocumentManager():
    """
    Manage for dealing with ModelDocuments. This helps provide a similar interface as django.models.Model:

    Example: Artwork.objects.get(pk=XXXX)

    This will return a couchdb.client.Document instance.
    """
    def __init__(self, doc_class):
        self.doc_class = doc_class
    
    def get(self, **kwargs):
        pk = kwargs.get("pk")
        if pk:
            return self.doc_class.load(self.doc_class.db, str(pk))
        return None

    def all(self, **kwargs):
        return self.doc_class.db

class ModelDocumentMeta(DocumentMeta):
    """
    Metaclass for ModelDocuments. Allows specifying an internal Meta class
    similar to django.model.Model:

    class Artwork(ModelDocument):
        class Meta:
            model = ArtworkStub
    """
    def __new__(mcs, name, bases, dct):
        mc = dct.get("Meta")
        model = None
        db = None
        
        try:
            model = getattr(mc, "model")
        except:
            pass

        if model:
            dct["_model"] = model

        try:
            db = getattr(mc, "db")
        except:
            pass

        if db:
            dct["db"] = db

        new_class = super(ModelDocumentMeta, mcs).__new__(mcs, name, bases, dct)
        new_class.objects = ModelDocumentManager(new_class)
        
        return new_class


class ModelDocument(Document):
    """
    ModelDocument class. ModelDocument are models that store data in both
    CouchDB and a normal Django backend (MySQL, PostgreSQL, sqlite3).
    Just extends couchdb.clientDocument with the added feature that accessing
    the model property will return the Django model associated with document.
    """
    __metaclass__ = ModelDocumentMeta

    def __getattr__(self, m):
        if m == 'model':
            return self._model.objects.get(pk=self.id)
