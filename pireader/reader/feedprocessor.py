__author__ = 'kal'

from django_cron import CronJobBase, Schedule
from django_cron.models import CronJobLog
from models import Feed, Category
import sys
import feedparser
from django.utils import timezone
from storage import FeedStore
import os.path
import opml

class FeedProcessorJob(CronJobBase):
    RUN_EVERY_MINS = 0

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code='pireader.reader.feedprocessor'

    def __init__(self, feed_store=None):
        """

        :param feed_store: storage.FeedStore
        """
        self.__store = feed_store or FeedStore()

    def do(self):
        try:
            for f in Feed.objects.all():
                try:
                    self.process_feed(f)
                except:
                    log = CronJobLog(message="Failed to process feed {0}. Cause: {1}".format(f, sys.exc_info()))
                    log.save()
        except:
            print "Unexpected exception: ", sys.exec_info()[0]

    def process_feed(self, f):
        feed_id = str(f.id)
        self.__store.ensure_feed_directory(feed_id)
        d = feedparser.parse(f.url)
        if self.should_process(f, d):
            for e in d.entries:
                self.process_entry(feed_id, e)
        f.last_checked = timezone.now()
        if (not f.title) and (d['feed'].has_key('title')):
            f.title = d['feed']['title']
        if (not f.html_url) and (d['feed'].has_key('link')):
            f.html_url = d['feed']['link']
        f.save()

    def should_process(self, feed, feed_content):
        """Return True if the feed content indicates that there may be one or more new items to add for the feed"""
        return True

    def process_entry(self, feed_id, entry):
        try:
            self.__store.add_entry(feed_id, entry)
        except:
            print "Failed to process entry {0}. Cause {1}".format(entry, sys.exc_info()[0])


class NoFeedsFound(Exception):
    pass

def import_opml(url_or_string):
    outline = opml.from_string(url_or_string)
    if len(outline) == 0:
        raise NoFeedsFound()
    for outline_element in outline:
        process_outline(outline_element)


def process_outline(outline_element, tag=None):
    if getattr(outline_element, 'type', '') == 'rss':
        add_feed(outline_element, tag)
    else:
        tag = getattr(outline_element, 'title', None)
        for child_element in outline_element:
            process_outline(child_element, tag)


def add_feed(outline_element, tag=None):
    feed_url = outline_element.xmlUrl
    try:
        return Feed.objects.get(url=feed_url)
    except Feed.DoesNotExist:
        category = assert_category(tag)
        feed = Feed.objects.create(
            url=feed_url,
            title=getattr(outline_element, 'title', feed_url),
            html_url=getattr(outline_element, 'htmlUrl', None))
        feed.save()
        if not category is None:
            category.feeds.add(feed)
            category.save()


def assert_category(category_tag):
    if category_tag is None:
        return None
    try:
        return Category.objects.get(tag=category_tag)
    except Category.DoesNotExist:
        category = Category.objects.create(tag=category_tag)
        category.save()
        return category


def initialize(feed):
    processor = FeedProcessorJob()
    processor.process_feed(feed)