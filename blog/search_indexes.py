from haystack import indexes 

from blog.models import Post


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    byline = indexes.CharField(model_attr='byline', null=True)
    pub_date = indexes.DateTimeField(model_attr='modified', null=True)

    def get_updated_field(self):
    	return 'modified'

    def get_model(self):
    	return Post

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(status=2)
