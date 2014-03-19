from haystack import indexes

from artbase.models import ArtworkStub, MemberExhibition


class ArtworkStubIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    byline = indexes.CharField(model_attr='byline', null=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
        return 'modified'

    def get_model(self):
        return ArtworkStub
    
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.exclude(status='unsubmitted').exclude(status='deleted')
        
class MemberExhibitionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
        return 'modified'

    def get_model(self):
        return MemberExhibition
    
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(live=True)
