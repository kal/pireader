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
from django.contrib.auth.models import User

TEST_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data_"+ strftime("%Y%m%d%H%M%S", gmtime()))
TESTDATA_PATH = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../testdata"))
TEST_READER_SETTINGS = {'data_path' : TEST_PATH}

class StoreTestCase(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.default_user = User.objects.create_user('fred', 'fred@example.org', 'testing')
        self.default_user.save()
        self.other_user = User.objects.create_user('bert', 'bert@example.org', 'testing')
        self.other_user.save()

    def tearDown(self):
        self.__clean_data()
        TestCase.tearDown(self)

    def default_login(self, enforce_csrf_checks = False):
        client = Client(enforce_csrf_checks=enforce_csrf_checks)
        client.login(username='fred', password='testing')
        return client

    def other_login(self):
        client = Client()
        client.login(username='bert', password='testing')
        return client

    def __clean_data(self):
        if os.path.exists(TEST_PATH):
            shutil.rmtree(TEST_PATH)

    def create_feed(self, title, url, days_since_checked=0, days_since_updated=0, owner=None):
        now = timezone.now()
        feed = Feed(url=url, title=title,
                                   last_checked=now + datetime.timedelta(days=days_since_checked),
                                   last_updated=now + datetime.timedelta(days=days_since_checked + days_since_updated),
                                   owner = owner or self.default_user)
        feed.save()
        return feed

    def populate_feed(self, store, feed_id, entry_count):
        store.ensure_feed_directory(feed_id)
        for i in range(1, entry_count + 1):
            entry = {
                'title': 'Test Entry',
                'published_parsed': timezone.now().utctimetuple(),
                'guid' : 'http://example.org/feed/?p={0}'.format(i)
            }
            store.add_entry(feed_id, entry)

    def import_opml(self, opml_file_name, user = None):
        if not user:
            user = self.default_user
        with open(os.path.join(TESTDATA_PATH, opml_file_name)) as f:
            feedprocessor.import_opml(f.read(), user)



@override_settings(READER=TEST_READER_SETTINGS)
class FeedStoreTests(StoreTestCase):

    def test_feedstore_creates_base_directory(self):
        FeedStore()
        self.assertTrue(os.path.exists(TEST_PATH))

    def test_add_entry(self):
        fs = FeedStore()
        f = self.create_feed("Feed 1", "http://example.org/feed1/rss", 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        counts_before = fs.get_feed_counts()
        self.assertTrue(counts_before.has_key(feed_id))
        self.assertEqual(0, counts_before[feed_id])
        fs.add_entry(feed_id, {
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
        f = self.   create_feed("MyFeed", "http://example.org/feed", 1)
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
        f = self.create_feed('Feed 2', 'http://example.org/feed2/rss', 1)
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
        remaining_item_count = fs.mark_read(feed_id, entry['ref'])
        self.assertEqual(0, remaining_item_count)
        counts_after = fs.get_feed_counts()
        self.assertEqual(0, counts_after[feed_id])
        self.assertTrue(os.path.exists(os.path.join(TEST_PATH, "feeds", feed_id, 'read', entry['ref'])))

    def test_keep_unread(self):
        fs = FeedStore()
        f = self.create_feed('Feed 3', 'http://example.org/feed3/rss', 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        self.populate_feed(fs, feed_id, 2)
        entries = fs.get_entries(feed_id)
        self.assertEqual(2, len(entries))
        fs.keep(feed_id, entries[0]['ref'])
        fs.mark_read(feed_id, entries[0]['ref']) # should have no effect
        fs.mark_read(feed_id, entries[1]['ref']) # should delete entry not in kept directory
        entries = fs.get_entries(feed_id) # should return the 1 kept item
        self.assertEqual(1, len(entries))
        fs.unkeep(feed_id, entries[0]['ref']) # will restore item back to feed directory
        entries = fs.get_entries(feed_id) # should return 1 item from the feed directory
        self.assertEqual(1, len(entries))
        fs.mark_read(feed_id, entries[0]['ref']) # should delete entry
        entries = fs.get_entries(feed_id)
        self.assertEqual(0, len(entries))

    def test_read_all_and_restore(self):
        fs = FeedStore()
        f = self.create_feed('Feed 4', 'http://example.org/feed4/rss', 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        self.populate_feed(fs, feed_id, 10)
        entries = fs.get_entries(feed_id)
        self.assertEqual(10, len(entries))
        # Restore when no items unread should make no difference
        fs.restore_all_items(feed_id)
        entries = fs.get_entries(feed_id)
        self.assertEqual(10, len(entries))
        # Read one item then restore them all
        fs.mark_read(feed_id, entries[0]['ref'])
        self.assertEqual(9, len(fs.get_entries(feed_id)))
        fs.restore_all_items(feed_id)
        entries = fs.get_entries(feed_id)
        self.assertEqual(10, len(entries))
        # Read all items
        fs.mark_all_read(feed_id)
        entries = fs.get_entries(feed_id)
        self.assertEqual(0, len(entries))
        # Restore all items
        fs.restore_all_items(feed_id)
        entries = fs.get_entries(feed_id)
        self.assertEqual(10, len(entries))

    def test_read_many(self):
        fs = FeedStore()
        f = self.create_feed('Feed 5', 'http://example.org/feed4/rss', 1)
        feed_id = str(f.id)
        fs.ensure_feed_directory(feed_id)
        self.populate_feed(fs, feed_id, 10)
        entries = fs.get_entries(feed_id)
        self.assertEqual(10, len(entries))
        remaining_count = fs.mark_read(feed_id, (e['ref'] for e in entries[0:3]))
        self.assertEqual(7, remaining_count)


@override_settings(READER=TEST_READER_SETTINGS)
class OpmlTests(StoreTestCase):

    def test_simple_opml_import(self):
        self.import_opml('simple.opml')
        self.assertEqual(6, Feed.objects.count())
        lrb_blog = Feed.objects.get(title='LRB blog')
        self.assertIsNotNone(lrb_blog)
        self.assertEqual('http://www.lrb.co.uk/blog/feed/', lrb_blog.url)
        self.assertEqual('http://www.lrb.co.uk/blog', lrb_blog.html_url)
        sparql = Feed.objects.get(title='newest questions tagged sparql - Stack Overflow')
        self.assertIsNotNone(sparql)
        self.assertEqual('http://stackoverflow.com/feeds/tag?tagnames=sparql&sort=newest', sparql.url)

    def test_google_opml_import(self):
        self.import_opml('google.opml')


@override_settings(READER=TEST_READER_SETTINGS)
class SubscriptionsResourceTests(StoreTestCase):

    def test_simple_resource_list(self):
        self.import_opml('simple.opml')
        client = self.default_login()
        response = client.get('/reader/subscriptions', HTTP_X_REQUESTED_WITH='XMLHttpRequest', Accept='application/json')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(0, len(data['categories']))
        self.assertEqual(6, len(data['uncategorized']))

    def test_login_required_to_list(self):
        self.import_opml('simple.opml')
        client = Client()
        response = client.get('/reader/subscriptions', HTTP_X_REQUESTED_WITH='XMLHttpRequest', Accept='application/json')
        self.assertEqual(302, response.status_code)

    def test_correct_login_required_to_list(self):
        self.import_opml('simple.opml')
        client = self.other_login()
        response = client.get('/reader/subscriptions', HTTP_X_REQUESTED_WITH='XMLHttpRequest', Accept='application/json')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(0, len(data['categories']))
        self.assertEqual(0, len(data['uncategorized']))

    def test_simple_resource_add(self):
        self.import_opml('simple.opml')
        client = self.default_login()
        home = client.get('/reader/')
        csrf_token = unicode(home.context['csrf_token'])
        response = client.post('/reader/subscriptions',
                    data={'url' : 'http://techquila.com/tech/feed/' },
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                    X_CSRFToken=csrf_token,
                    Accept='application/json')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(1, len(data))
        self.assertEqual('http://techquila.com/tech/feed/', data[0]['fields']['url'])
        self.assertEqual('Techquila Tech', data[0]['fields']['title'])
        self.assertEqual('http://techquila.com/tech', data[0]['fields']['html_url'])

    def test_login_required_to_add(self):
        self.import_opml('simple.opml')
        client = Client()
        response = client.post('/reader/subscriptions',
                    data={'url' : 'http://techquila.com/tech/feed/' },
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                    Accept='application/json')
        self.assertEqual(302, response.status_code) # Expect redirect to login page

    def test_csrf_required_to_add(self):
        self.import_opml('simple.opml')
        client = self.default_login(True)
        response = client.post('/reader/subscriptions',
                    data={'url' : 'http://techquila.com/tech/feed/' },
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                    Accept='application/json')
        self.assertEqual(403, response.status_code)

@override_settings(READER=TEST_READER_SETTINGS)
class FeedResourceTests(StoreTestCase):

    def setUp(self):
        StoreTestCase.setUp(self)
        self.store = FeedStore()
        self.import_opml('simple.opml')
        for f in Feed.objects.all():
            self.store.ensure_feed_directory(str(f.id))

    def test_get_one(self):
         # setup
        self.populate_feed(self.store, "1", 1)
        client = self.default_login()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(1, len(data))
        self.assertEqual('Test Entry', data[0]['title'])

    def test_login_required(self):
        self.populate_feed(self.store, "1", 1)
        client = Client()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(302, response.status_code)

    def test_correct_login_required(self):
        self.populate_feed(self.store, "1", 1)
        client = self.other_login()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(401, response.status_code)

    def test_get_many(self):
        self.populate_feed(self.store, "1", 10)
        client = self.default_login()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(10, len(data))

    def test_read_one(self):
        self.populate_feed(self.store, "1", 10)
        client = self.default_login()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        entries = json.loads(response.content)
        self.assertEqual(10, len(entries))
        update = {'read': [entries[0]['ref']]}
        response = client.post('/reader/subscriptions/1', json.dumps(update), 'application/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        entries = json.loads(response.content)
        self.assertEqual(9, len(entries))

    def test_correct_login_required_to_update(self):
        self.populate_feed(self.store, "1", 10)
        client = self.other_login()
        update = {'read': '12345'}
        response = client.post('/reader/subscriptions/1', json.dumps(update), 'application/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(401, response.status_code)

    def test_read_many(self):
        self.populate_feed(self.store, "1", 10)
        client = self.default_login()
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        entries = json.loads(response.content)
        self.assertEqual(10, len(entries))
        update = {'read': []}
        for e in entries:
            update['read'].append(e['ref'])
        response = client.post('/reader/subscriptions/1', json.dumps(update), 'application/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        responseData = json.loads(response.content)
        self.assertEqual(0, responseData['unread_count'])
        self.assertEqual(200, response.status_code)
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        entries = json.loads(response.content)
        self.assertEqual(0, len(entries))

    def test_read_all(self):
        self.populate_feed(self.store, "1", 10)
        client = self.default_login()
        update = {'read_all' : -1}
        response = client.post('/reader/subscriptions/1', json.dumps(update), 'application/json',
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        response = client.get('/reader/subscriptions/1')
        self.assertEqual(200, response.status_code)
        entries = json.loads(response.content)
        self.assertEqual(0, len(entries))

    def test_restore_all(self):
        self.populate_feed(self.store, "1", 10)
        self.store.mark_all_read("1")
        client = self.default_login()
        entries = self.__get_entries(client, "1")
        self.assertEqual(0, len(entries))
        update = {'restore_all': 1}
        response = client.post('/reader/subscriptions/1', json.dumps(update), 'application/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        entries = json.loads(response.content)
        self.assertEqual(10, len(entries))

    def __get_entries(self, client, feed_id = "1"):
        response = client.get('/reader/subscriptions/' + feed_id)
        self.assertEqual(200, response.status_code)
        return json.loads(response.content)

def clean_data():
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)

