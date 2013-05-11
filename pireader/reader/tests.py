from django.core import serializers
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import Client
from models import Feed
from django.utils import timezone
import datetime
import os
import json
from storage import FeedStore
import feedprocessor
from time import gmtime, strftime
import shutil


TEST_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data_"+ strftime("%Y%m%d%H%M%S", gmtime()))
TESTDATA_PATH = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../testdata"))
TEST_READER_SETTINGS = {'data_path' : TEST_PATH}

class StoreTestCase(TestCase):

    def tearDown(self):
        self.__clean_data()

    def __clean_data(self):
        if os.path.exists(TEST_PATH):
            shutil.rmtree(TEST_PATH)

    def __create_feed(self, title, url, days_since_checked=0, days_since_updated=0):
        now = timezone.now()
        feed = Feed(url=url, title=title,
                                   last_checked=now + datetime.timedelta(days=days_since_checked),
                                   last_updated=now + datetime.timedelta(days=days_since_checked + days_since_updated))
        feed.save()
        return feed


@override_settings(READER=TEST_READER_SETTINGS)
class FeedStoreTests(StoreTestCase):

    def test_feedstore_creates_base_directory(self):
        FeedStore()
        self.assertTrue(os.path.exists(TEST_PATH))

    def test_add_entry(self):
        fs = FeedStore()
        f = self.__create_feed("Feed 1", "http://example.org/feed1/rss", 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        counts_before = fs.get_feed_counts()
        self.assertTrue(counts_before.has_key(feed_id))
        self.assertEqual(0, counts_before[feed_id])
        fs.add_entry(f.id, {
            'title': 'Test Entry',
            'published_parsed': f.last_updated.utctimetuple(),
            'guid': 'http://example.org/feed1/?p=1'
        })
        counts_after = fs.get_feed_counts()
        self.assertTrue(counts_after.has_key(feed_id))
        self.assertEqual(1, counts_after[feed_id])
        entries = fs.get_entries(feed_id)
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual('http://example.org/feed1/?p=1', entry['guid'])
        self.assertEqual('Test Entry', entry['title'])
        self.assertTrue(entry.has_key('ref'))

    def test_cannot_add_entry_twice(self):
        fs = FeedStore()
        f = self.__create_feed("MyFeed", "http://example.org/feed", 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        entry = {
            'title': "Test Entry",
            'published_parsed' : f.last_updated.utctimetuple(),
            'guid' : 'http://example.org/feed1/?p=1'
        }
        fs.add_entry(feed_id, entry)
        feed_counts = fs.get_feed_counts()
        self.assertEqual(1, feed_counts[feed_id])
        fs.add_entry(feed_id, entry)
        feed_counts = fs.get_feed_counts()
        self.assertEqual(1, feed_counts[feed_id])

    def test_read_entry(self):
        fs = FeedStore()
        f = self.__create_feed('Feed 2', 'http://example.org/feed2/rss', 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        entry = {
            'title': 'Test Entry',
            'published_parsed': f.last_updated.utctimetuple(),
            'guid' : 'http://example.org/feed2/?p=2'
        }
        fs.add_entry(feed_id, entry)
        counts_before = fs.get_feed_counts()
        self.assertEqual(1, counts_before[feed_id])
        entry = fs.get_entries(feed_id)[0]
        fs.mark_read(feed_id, entry['ref'])
        counts_after = fs.get_feed_counts()
        self.assertEqual(0, counts_after[feed_id])
        self.assertTrue(os.path.exists(os.path.join(TEST_PATH, "feeds", feed_id, 'read', entry['ref'])))


def import_opml(opml_file_name):
    with open(os.path.join(TESTDATA_PATH, opml_file_name)) as f:
        feedprocessor.import_opml(f.read())

@override_settings(READER=TEST_READER_SETTINGS)
class OpmlTests(TestCase):

    def test_simple_opml_import(self):
        import_opml('simple.opml')
        self.assertEqual(6, Feed.objects.count())
        lrb_blog = Feed.objects.get(title='LRB blog')
        self.assertIsNotNone(lrb_blog)
        self.assertEqual('http://www.lrb.co.uk/blog/feed/', lrb_blog.url)
        self.assertEqual('http://www.lrb.co.uk/blog', lrb_blog.html_url)
        sparql = Feed.objects.get(title='newest questions tagged sparql - Stack Overflow')
        self.assertIsNotNone(sparql)
        self.assertEqual('http://stackoverflow.com/feeds/tag?tagnames=sparql&sort=newest', sparql.url)

    def test_google_opml_import(self):
        import_opml('google.opml')


@override_settings(READER=TEST_READER_SETTINGS)
class SubscriptionsResourceTests(TestCase):

    def test_simple_resource_list(self):
        import_opml('simple.opml')
        client = Client()
        response = client.get('/reader/subscriptions', HTTP_X_REQUESTED_WITH='XMLHttpRequest', Accept='application/json')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(0, len(data['categories']))
        self.assertEqual(6, len(data['uncategorized']))

    def test_simple_resource_add(self):
        import_opml('simple.opml')
        client = Client()
        response = client.post('/reader/subscriptions',
                    data='{"url":"http://techquila.com/tech/feed/"}',
                    content_type="application/json",
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                    Accept='application/json')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(1, len(data))
        self.assertEqual('http://techquila.com/tech/feed/', data[0]['fields']['url'])
        self.assertEqual('Techquila Tech', data[0]['fields']['title'])
        self.assertEqual('http://techquila.com/tech', data[0]['fields']['html_url'])


@override_settings(READER=TEST_READER_SETTINGS)
class FeedResourceTests(StoreTestCase):

    def setUp(self):
        self.store = FeedStore()
        import_opml('simple.opml')
        for f in Feed.objects.all():
            self.store.ensure_feed_directory(str(f.id))

    def __populate_feed(self, feed_id, entry_count):
        self.store.ensure_feed_directory(feed_id)
        for i in range(1, entry_count + 1):
            entry = {
                'title': 'Test Entry',
                'published_parsed': timezone.now().utctimetuple(),
                'guid' : 'http://example.org/feed/?p={0}'.format(i)
            }
            self.store.add_entry(feed_id, entry)

    def test_get_one(self):
         # setup
        self.__populate_feed("1", 1)
        client = Client()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(1, len(data))
        self.assertEqual('Test Entry', data[0]['title'])

    def test_get_many(self):
        self.__populate_feed("1", 10)
        client = Client()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(10, len(data))

def clean_data():
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)

