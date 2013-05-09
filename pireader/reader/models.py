from django.db import models


class Feed(models.Model):

    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    last_checked = models.DateTimeField(blank=True, null=True, editable=False, default=None)
    last_updated = models.DateTimeField(blank=True, null=True, editable=False, default=None)

    def __unicode__(self):
        return self.url
