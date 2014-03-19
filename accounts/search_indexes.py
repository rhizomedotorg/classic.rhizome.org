from haystack import indexes

from accounts.models import RhizomeUser


class RhizomeUserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
        return 'modified'

    def get_model(self):
    	return RhizomeUser
    
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(visible=True, is_active=True)
