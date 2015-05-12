#!/usr/bin/env python
# coding: utf-8
import os
import sys
import json
import subprocess
from multiprocessing.pool import ThreadPool

import click
from pip._vendor.distlib.compat import which

from brewchecker.formula import Library
from brewchecker.settings import settings
from brewchecker.utils import update_sources, echo, clean


class Loader(object):
    json = None
    result_dict = None

    def __init__(self):
        self.no_binaries = Loader.detect()
        update_sources()

    @staticmethod
    def detect():
        echo(u'Checking for VCS binaries:')
        no_binaries = []
        for cmd in [u'curl', u'git', u'hg', u'svn', u'cvs', u'bzr', u'fossil']:
            echo(u'  {}... '.format(cmd), nl=False)
            if which(cmd):
                msg = click.style(u'yes', 'green')
            else:
                no_binaries.append(cmd)
                msg = click.style(u'no', 'red')
            echo(u'{}.'.format(msg))

        if no_binaries:
            echo(click.style(
                u'Warning! Resources that uses {} will not be checked!'.format(u'/'.join(no_binaries)), 'yellow'
            ))
        return no_binaries

    def get_json(self):
        """
        Full command:
        $ brew irb -r ./inject.rb | sed 1,2d

        `sed` is used here to strip first two lines from Homebrew `irb`'s output, which ATM are:

        ==> Interactive Homebrew Shell
        Example commands available with: brew irb --examples

        We need to decide: strip them with sed, or just use python?
        Since Homebrew's `irb` command can change it's behavior in future, it's best for us to manually find
        start of JSON output.
        """
        echo(u"Getting library from Homebrew...", nl=False)
        inject_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inject.rb')
        brew_bin = settings.get('BREW_BIN')
        irb_proc = subprocess.Popen([brew_bin, 'irb', '-r', inject_file], stdout=subprocess.PIPE)
        self.json = subprocess.check_output(['sed', '1,2d'], stdin=irb_proc.stdout)
        echo(click.style(u"done!", "green"))
        return self

    def load(self):
        self.result_dict = json.loads(self.json)
        library = Library(self.result_dict)
        echo(u'Formulas found: ' + click.style(u'{}\n'.format(len(library)), 'green'))
        return library


@click.command()
@click.option(
    '-n', '--threads', type=click.INT, default=8, show_default=True, help=
    "Number of simultaneous downloads performed by brewchecker.\n"
    "Warning: increasing this number may cause errors and slow down your system."
)
@click.option('-q', '--quiet', is_flag=True, default=False, show_default=True, help="No log will be printed to STDOUT.")
@click.option(
    '-e', '--only-errors', is_flag=True, default=False, show_default=True, help=
    "Report will only contain formulas with errors."
)
@click.option('-l', '--log', type=click.File('a', encoding='utf-8', lazy=True), help="Path to log file.")
@click.option(
    '-o', '--output', type=click.File('w'), help=
    "Path to output file where JSON report will be saved.\n"
    "Warning: omitting this option will cause printing report after with its log, unless -q/--quiet is presented."
)
def main(**kwargs):
    settings.load(**kwargs)
    loader = Loader()
    loader.get_json()
    lib = loader.load()

    pool = ThreadPool(settings.get('THREADS'))
    pool.map(lambda x: x.run(), lib, 1)
    pool.close()
    pool.join()

    if settings.get('ONLY_ERRORS'):
        report = lib.report.errors
    else:
        report = lib.report.reports

    if settings.get('OUTPUT'):
        json.dump(report, settings.get('OUTPUT'))
    else:
        click.echo(json.dumps(report))
    clean()

if __name__ == '__main__':
    try:
        sys.exit(main())
    except:
        raise
    finally:
        clean()
