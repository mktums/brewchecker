# coding: utf-8
import os
import requests
import sys

from pip.vcs import git

from settings import CLONE_DIR, HOMEBREW_GIT_URL


def color(this_color, string_):
    return "\033[" + this_color + "m" + string_ + "\033[0m"


def bold(string_):
    return color('1', string_)


def color_status(response_code):
    if response_code == requests.codes.ok:
        return color('38;05;10', u"\u2714")
    else:
        return color('38;05;9', u"\u2718") + ' ' + unicode(response_code)


def update_sources():
    s = git.Git(HOMEBREW_GIT_URL)
    if not os.path.exists(CLONE_DIR):
        sys.stdout.write("  Cloning Homebrew sources… ")
        s.obtain(CLONE_DIR)
        sys.stdout.write('Done!\n')
    else:

        sys.stdout.write("  Updating Homebrew sources… ")
        s.update(CLONE_DIR, ('master',))
        sys.stdout.write('Done!\n')

    print bold(u"\u2139 Last commit: {}".format(
        s.get_revision(CLONE_DIR)[:8]
    ))


class CustomGit(git.Git):
    def get_bare(self, dest):
        url, _ = self.get_url_rev()
        rev_options = ['origin/master']
        rev_display = ''
        if self.check_destination(dest, url, rev_options, rev_display):
            self.run_command(['clone', '-q', '--bare', url, dest], show_stdout=False)

    def check_commit(self, sha, location):
        return self.run_command(['rev-parse', '--verify', sha], show_stdout=False, cwd=location)
