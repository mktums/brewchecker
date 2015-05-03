# coding: utf-8
import os
import sys

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
        return color('38;05;9', u"\u2718") + ' ' + unicode(response_code)


def get_brew_repo():
    return Git(BREW_GIT_URL)


def get_brew_last_commit(repo):
    return repo.get_revision(BREW_CLONE_DIR)


def update_sources():
    s = get_brew_repo()
    if not os.path.exists(BREW_CLONE_DIR):
        sys.stdout.write("  Cloning Homebrew sources… ")
        s.obtain(BREW_CLONE_DIR)
        sys.stdout.write('Done!\n')
    else:
        sys.stdout.write("  Updating Homebrew sources… ")
        s.update(BREW_CLONE_DIR, ('master',))
        sys.stdout.write('Done!\n')

    print bold(u"\u2139 Last commit: {}".format(
        get_brew_last_commit(s)[:8]
    ))
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


def signal_handler(signal, frame):
    print '\rYou pressed Ctrl+C!'
    sys.exit(0)
