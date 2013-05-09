# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Feed.last_updated'
        db.alter_column(u'reader_feed', 'last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True))

        # Changing field 'Feed.last_checked'
        db.alter_column(u'reader_feed', 'last_checked', self.gf('django.db.models.fields.DateTimeField')(null=True))

    def backwards(self, orm):

        # Changing field 'Feed.last_updated'
        db.alter_column(u'reader_feed', 'last_updated', self.gf('django.db.models.fields.DateTimeField')(default=None))

        # Changing field 'Feed.last_checked'
        db.alter_column(u'reader_feed', 'last_checked', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 5, 8, 0, 0)))

    models = {
        u'reader.feed': {
            'Meta': {'object_name': 'Feed'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['reader']