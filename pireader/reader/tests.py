from django.test import TestCase
from models import Feed
from django.utils import timezone
import datetime
import os
from storage import FeedStore
from time import gmtime, strftime
import shutil


TEST_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data_"+ strftime("%Y%m%d%H%M%S", gmtime()))


class FeedStoreTests(TestCase):

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

    def test_feedstore_creates_base_directory(self):
        self.__clean_data()
        FeedStore(TEST_PATH)
        self.assertTrue(os.path.exists(TEST_PATH))

    def test_add_entry(self):
        self.__clean_data()
        fs = FeedStore(TEST_PATH)
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
        self.__clean_data()
        fs = FeedStore(TEST_PATH)
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

    def test_remove_entry(self):
        self.__clean_data()
        fs = FeedStore(TEST_PATH)
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
        fs.delete_entry(feed_id, entry['ref'])
        counts_after = fs.get_feed_counts()
        self.assertEqual(0, counts_after[feed_id])

