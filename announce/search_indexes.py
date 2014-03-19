from haystack import indexes 

from announce.models import Opportunity, Event, Job


class OpportunityIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)
    
    def get_updated_field(self):
        return 'modified'

    def get_model(self):
        return Opportunity

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(status=True)
        
class JobIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
        return 'modified'

    def get_model(self):
        return Job 

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(status=True)
        
class EventIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
        return 'modified'

    def get_model(self):
        return Event 

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(status=True)
