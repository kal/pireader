# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table(u'reader_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'reader', ['Category'])

        # Adding M2M table for field feeds on 'Category'
        db.create_table(u'reader_category_feeds', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('category', models.ForeignKey(orm[u'reader.category'], null=False)),
            ('feed', models.ForeignKey(orm[u'reader.feed'], null=False))
        ))
        db.create_unique(u'reader_category_feeds', ['category_id', 'feed_id'])

        # Adding field 'Feed.html_url'
        db.add_column(u'reader_feed', 'html_url',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Category'
        db.delete_table(u'reader_category')

        # Removing M2M table for field feeds on 'Category'
        db.delete_table('reader_category_feeds')

        # Deleting field 'Feed.html_url'
        db.delete_column(u'reader_feed', 'html_url')


    models = {
        u'reader.category': {
            'Meta': {'object_name': 'Category'},
            'feeds': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categories'", 'symmetrical': 'False', 'to': u"orm['reader.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'reader.feed': {
            'Meta': {'object_name': 'Feed'},
            'html_url': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['reader']