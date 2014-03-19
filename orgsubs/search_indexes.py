from haystack import indexes

from orgsubs.models import Organization


class OrganizationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
        return 'modified'

    def get_model(self):
    	return Organization

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all().order_by('name')
