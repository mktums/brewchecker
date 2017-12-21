# coding: utf-8
import os
import time

import click
from pip.utils import rmtree
from pip.vcs.git import Git

from brewchecker.settings import settings


def echo(message=None, nl=True, err=False, _color=None):
    log = settings.get('LOG')
    msg = message if message else ''
    if nl:  # Nasty click.echo's bug =(
        msg += '\n'
    if log:
        click.echo(msg, log, nl=False, err=err, color=_color)
    if not settings.get('QUIET'):
        click.echo(msg, None, nl=False, err=err, color=_color)


def is_ok(response_code):
    if response_code in (200, 226):
        return True
    return False


def get_brew_repo():
    return Git(settings.get('BREW_GIT_URL'))


def get_brew_last_commit(repo):
    return repo.get_revision(settings.get('BREW_CLONE_DIR'))


def update_sources():
    s = get_brew_repo()
    echo("Cloning Homebrew sources... ", nl=False)
    s.obtain(settings.get('BREW_CLONE_DIR'))
    echo(click.style("done!", "green"))
    echo("Last commit: " + click.style("{}\n".format(get_brew_last_commit(s)[:8]), "green"))
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


def clean():
    echo('Cleaning up {}...'.format(settings.get('BASE_DIR')), nl=False)
    rmtree(settings.get('BASE_DIR'))
    echo(click.style('done!', 'green'))


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end = time.time()
        self.interval = self.end - self.start
