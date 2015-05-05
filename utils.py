# coding: utf-8
import os
import sys

from pip._vendor.distlib.compat import OrderedDict
from pip.vcs.git import Git

from settings import BREW_CLONE_DIR, BREW_GIT_URL


def color(this_color, string_):
    return "\033[" + this_color + "m" + string_ + "\033[0m"


def bold(string_):
    return color('1', string_)


def color_status(response_code):
    if response_code in (200, 226):
        return color('38;05;10', u"\u2714")
    else:
        return color('38;05;9', u"\u2718")  # + ' ' + unicode(response_code)


def get_brew_repo():
    return Git(BREW_GIT_URL)


def get_brew_last_commit(repo):
    return repo.get_revision(BREW_CLONE_DIR)


def update_sources():
    s = get_brew_repo()
    if not os.path.exists(BREW_CLONE_DIR):
        # sys.stdout.write("  Cloning Homebrew sources… ")
        s.obtain(BREW_CLONE_DIR)
        # sys.stdout.write('Done!\n')
    else:
        # sys.stdout.write("  Updating Homebrew sources… ")
        s.update(BREW_CLONE_DIR, ('master',))
        # sys.stdout.write('Done!\n')

    # print bold(u"\u2139 Last commit: {}".format(get_brew_last_commit(s)[:8]))
    return s


class CD:
    """Context manager for changing the current working directory"""
    def __init__(self, new_path):
        self.newPath = os.path.expanduser(new_path)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


# http://stackoverflow.com/questions/27912308/how-can-you-slice-with-string-keys-instead-of-integers-on-a-python-ordereddict
def _key_slice_to_index_slice(items, key_slice):
    try:
        if key_slice.start is None:
            start = None
        else:
            start = next(idx for idx, (key, value) in enumerate(items)
                         if key == key_slice.start)
        if key_slice.stop is None:
            stop = None
        else:
            stop = next(idx for idx, (key, value) in enumerate(items)
                        if key == key_slice.stop)
    except StopIteration:
        raise KeyError
    return slice(start, stop, key_slice.step)


class SlicableDict(OrderedDict):
    def __getitem__(self, key):
        if isinstance(key, slice):
            items = self.items()
            index_slice = _key_slice_to_index_slice(items, key)
            return SlicableDict(items[index_slice])
        return super(SlicableDict, self).__getitem__(key)

    def __setitem__(self, key, value, *args, **kwargs):
        if isinstance(key, slice):
            items = self.items()
            index_slice = _key_slice_to_index_slice(items, key)
            items[index_slice] = value.items()
            self.clear()
            self.update(items)
            return
        return super(SlicableDict, self).__setitem__(key, value, *args, **kwargs)

    def __delitem__(self, key, *args, **kwargs):
        if isinstance(key, slice):
            items = self.items()
            index_slice = _key_slice_to_index_slice(items, key)
            del items[index_slice]
            self.clear()
            self.update(items)
            return
        return super(SlicableDict, self).__delitem__(key, *args, **kwargs)


def signal_handler(signal, frame):
    print '\rYou pressed Ctrl+C!'
    sys.exit(0)
