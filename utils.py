# coding: utf-8
import os
import git
import requests
import sys
import time
from settings import CLONE_DIR, HOMEBREW_GIT_URL


def color(this_color, string_):
    return "\033[" + this_color + "m" + string_ + "\033[0m"


def bold(string_):
    return color('1', string_)


def color_status(response_code):
    if response_code == requests.codes.ok:
        return color('38;05;10', u"\u2714")
    else:
        return color('38;05;9', u"\u2718") + ' ' + str(response_code)


def update_sources():
    if not os.path.exists(CLONE_DIR):
        sys.stdout.write("  Cloning Homebrew sources… ")
        repo = git.Repo.clone_from(HOMEBREW_GIT_URL, CLONE_DIR)
        sys.stdout.write('Done!\n')
    else:
        repo = git.Repo(CLONE_DIR)
        sys.stdout.write("  Updating Homebrew sources… ")
        repo.remotes.origin.pull()
        sys.stdout.write('Done!\n')

    print bold(u"\u2139 Last commit: {} ({})".format(
        repo.head.commit.hexsha[:10], time.strftime('%c', time.gmtime(repo.head.commit.committed_date))
    ))