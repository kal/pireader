from django.db import models

class Feed(models.Model):

    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255, unique=True)
    html_url = models.CharField(max_length=255, blank=True, null=True, default=None)
    last_checked = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    last_updated = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    is_deleted = models.BooleanField(default=False)
    owner = models.ForeignKey('auth.User')
    unread_count = models.PositiveIntegerField(default=0)
    keep_count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        if self.is_deleted:
            return self.url
        else:
            return self.url + " **deleted**"

class Category(models.Model):
    """
    This model represents the categories that are used to group related feeds together.
    A feed can be placed in 0 or more categories
    """
    tag = models.CharField(max_length=255, unique=True)
    feeds = models.ManyToManyField(Feed, related_name='categories')
    owner = models.ForeignKey('auth.User')

    def natural_key(self):
        return self.tag