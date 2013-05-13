import os
from time import gmtime, mktime, strftime
import cPickle
import itertools
import shutil
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
        self.__ensure_directory(os.path.join(feed_dir, 'keep'))

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
        keep_dir = self.__get_keep_directory(feed_id)
        self.__ensure_directory(keep_dir)
        keep_files = os.listdir(keep_dir)
        keep_files.sort()
        keeps = [os.path.join(keep_dir, f) for f in keep_files if os.path.isfile(os.path.join(keep_dir, f))]
        entries = [os.path.join(feed_dir, f) for f in entry_files if os.path.isfile(os.path.join(feed_dir, f))]
        return list(map(self.__read_entry, itertools.islice(itertools.chain(keeps,  entries), skip, take)))

    def __write_entry(self, entry, path):
        with open(path, 'w') as entry_file:
            cPickle.dump(entry, entry_file)

    def __read_entry(self, path):
        with open(path, 'r') as entry_file:
            entry = cPickle.load(entry_file)
            entry['ref'] = os.path.basename(path)
            return entry

    def keep(self, feed_id, entry_name):
        feed_dir = self.__get_feed_directory(feed_id)
        keep_dir = self.__get_keep_directory(feed_id)
        entry_path = os.path.join(feed_dir, entry_name)
        keep_path = os.path.join(keep_dir, entry_name)
        entry = None
        if os.path.exists(entry_path):
            entry = self.__read_entry(entry_path)
        else:
            entry_path = os.path.join(feed_dir, 'read', entry_name)
            if os.path.exists(entry_path):
                entry = self.__read_entry(entry_path)
        if not entry:
            raise EntryDoesNotExist(feed_id, entry_name)
        entry['keep_unread'] = True
        self.__write_entry(entry, keep_path)

    def unkeep(self, feed_id, entry_name):
        keep_dir = self.__get_keep_directory(feed_id)
        keep_path = os.path.join(keep_dir, entry_name)
        if not os.path.exists(keep_path):
            raise EntryDoesNotExist(feed_id, entry_name)
        entry_path = os.path.join(self.__get_feed_directory(feed_id), entry_name)
        entry = self.__read_entry(keep_path)
        entry['keep_unread'] = False
        self.__write_entry(entry, entry_path)
        os.unlink(keep_path)

    def __make_entry_filename(self, entry):
        z = gmtime(mktime(entry['published_parsed']))
        ts =  strftime('%Y%m%dT%H%M%SZ', z)
        entry_id = self.__normalize_id(entry['guid'])
        return ts + '_' + entry_id

    def __normalize_id(self, to_normalize):
        return ''.join([c for c in to_normalize if c.isalnum() or c in self.KEEP_CHARACTERS]).rstrip()

    def __get_feed_directory(self, feed_id):
        return os.path.join(self._feedsDirectory, feed_id)

    def __get_keep_directory(self, feed_id):
        return os.path.join(self.__get_feed_directory(feed_id), "keep")

    def __ensure_directory(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

class StorageError(Exception):
    """Base class for storage errors"""

class EntryDoesNotExist(StorageError):
    """Raised when an operation is attempted on an entry that cannot be found in the store"""
    def __init__(self, feed_id, entry_name):
        self.feed_id = feed_id
        self.entry_name = entry_name
    def __unicode__(self):
        return "EntryDoesNotExist: {0} in feed {1}".format(self.entry_name, self.feed_id)