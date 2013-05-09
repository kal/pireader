__author__ = 'kal'

from django_cron import CronJobBase, Schedule
from models import Feed
import sys
import feedparser
from django.utils import timezone
from storage import FeedStore
from time import strftime, mktime, gmtime
import os.path

class FeedProcessorJob(CronJobBase):
    RUN_EVERY_MINS = 0

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code='pireader.reader.feedprocessor'

    def __init__(self, feed_store=None):
        """

        :param feed_store: storage.FeedStore
        """
        self.__store = feed_store or FeedStore(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data'))

    def do(self):
        try:
            for f in Feed.objects.all():
                self.process_feed(f)
        except:
            print "Unexpected exception: ", sys.exec_info()[0]

    def process_feed(self, f):
        try:
            self.__store.ensure_feed_directory()
            d = feedparser.parse(f.url)
            if self.should_process(f, d):
                print "Entry count: {0}".format(len(d.entries))
                for e in d.entries:
                    self.process_entry(f, e)
            f.last_checked = timezone.now()
            f.save()
        except:
            print "Failed to process feed {0}. Cause {1}".format(f.url, sys.exc_info()[0])

    def should_process(self, feed, feed_content):
        """Return True if the feed content indicates that there may be one or more new items to add for the feed"""
        return True

    def process_entry(self, feed, entry):
        try:
            self.__store.add_entry(str(feed.id), entry)
        except:
            print "Failed to process entry {0}. Cause {1}".format(entry, sys.exc_info()[0   ])


