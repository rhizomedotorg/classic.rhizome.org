from django.db import models

# Create your models here.

class Block(models.Model):
    POLICY = 'policy'
    ABOUT = 'about'
    USER_MESSAGE = 'site message'
    SECTION_HEADER = 'section header'

    CATEGORY_CHOICES = (
        (POLICY, 'Policy'),
        (ABOUT, 'About'),
        (USER_MESSAGE, 'User Message'),
        (SECTION_HEADER, 'Section Header'),
    )

    ident = models.CharField(max_length=100, db_index=True, unique=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, blank=True, help_text='if applicable, only used for sorting in rza')
    text = models.TextField()

    def __unicode__(self):
        return self.ident

    class Meta:
        verbose_name_plural = 'content blocks'
        verbose_name = 'content block'

    @classmethod
    def get_text(cls, ident):
	    try:
	        return cls.objects.get(ident__iexact=ident).text
	    except cls.DoesNotExist:
	        return ''