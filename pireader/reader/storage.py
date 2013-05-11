import os
from time import gmtime, mktime, strftime
import cPickle
import itertools
from django.conf import settings
import sys

class FeedStore:

    KEEP_CHARACTERS = [' ', '.', '_']

    def __init__(self):
        self._baseDirectory = settings.READER['data_path']
        self._feedsDirectory = os.path.join(self._baseDirectory, 'feeds')
        self.__ensure_directory(self._feedsDirectory)

    def ensure_feed_directory(self, feed_id):
        feed_dir = self.__get_feed_directory(feed_id)
        self.__ensure_directory(feed_dir)
        self.__ensure_directory(os.path.join(feed_dir, 'read'))

    def add_entry(self, feed_id, entry):
        fn = self.__make_entry_filename(entry)
        entry_filename = os.path.join(self.__get_feed_directory(feed_id), fn)
        if not os.path.exists(entry_filename):
            self.__write_entry(entry, entry_filename)

    def mark_read(self, feed_id, entry_name):
        try:
            feed_dir = self.__get_feed_directory(feed_id)
            os.rename(os.path.join(feed_dir, entry_name), os.path.join(feed_dir, 'read', entry_name))
        except:
            # If the entry is gone, just continue
            pass

    def get_feed_counts(self):
        feed_counts = {}
        for feed_dir in os.listdir(self._feedsDirectory):
            feed_counts[feed_dir] = len([n for n in os.listdir(os.path.join(self._feedsDirectory, feed_dir)) if os.path.isfile(os.path.join(self._feedsDirectory, feed_dir, n))])
        return feed_counts

    def get_entries(self, feed_id, skip=0, take=None):
        feed_dir = self.__get_feed_directory(feed_id)
        entry_files = os.listdir(feed_dir)
        entry_files.sort()
        entries_iter = [os.path.join(feed_dir, f) for f in entry_files if os.path.isfile(os.path.join(feed_dir, f))]
        return list(map(self.__read_entry, itertools.islice(entries_iter, skip, take)))

    def __write_entry(self, entry, path):
        with open(path, 'w') as entry_file:
            cPickle.dump(entry, entry_file)

    def __read_entry(self, path):
        with open(path, 'r') as entry_file:
            entry = cPickle.load(entry_file)
            entry['ref'] = os.path.basename(path)
            return entry

    def __make_entry_filename(self, entry):
        z = gmtime(mktime(entry['published_parsed']))
        ts =  strftime('%Y%m%dT%H%M%SZ', z)
        entry_id = self.__normalize_id(entry['guid'])
        return ts + '_' + entry_id

    def __normalize_id(self, to_normalize):
        return ''.join([c for c in to_normalize if c.isalnum() or c in self.KEEP_CHARACTERS]).rstrip()

    def __get_feed_directory(self, feed_id):
        return os.path.join(self._feedsDirectory, str(feed_id))

    def __ensure_directory(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)