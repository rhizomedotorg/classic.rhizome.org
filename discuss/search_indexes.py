from haystack import indexes

from threadedcomments.models import ThreadedComment


class ThreadedCommentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='submit_date', null=True)

    def get_updated_field(self):
        return 'submit_date' 

    def get_model(self):
    	return ThreadedComment
    
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(is_public=True)
