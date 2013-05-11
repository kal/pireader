# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'Feed', fields ['url']
        db.create_unique(u'reader_feed', ['url'])

        # Adding unique constraint on 'Category', fields ['tag']
        db.create_unique(u'reader_category', ['tag'])


    def backwards(self, orm):
        # Removing unique constraint on 'Category', fields ['tag']
        db.delete_unique(u'reader_category', ['tag'])

        # Removing unique constraint on 'Feed', fields ['url']
        db.delete_unique(u'reader_feed', ['url'])


    models = {
        u'reader.category': {
            'Meta': {'object_name': 'Category'},
            'feeds': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categories'", 'symmetrical': 'False', 'to': u"orm['reader.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'reader.feed': {
            'Meta': {'object_name': 'Feed'},
            'html_url': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['reader']