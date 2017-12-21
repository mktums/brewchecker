#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from concurrent import futures
from subprocess import DEVNULL

import click
from brewchecker.formula import Library
from brewchecker.settings import settings
from brewchecker.utils import update_sources, echo, clean
from pip._vendor.distlib.compat import which


class Loader(object):
    json = None
    result_dict = None

    def __init__(self):
        self.no_binaries = Loader.detect()
        update_sources()

    @staticmethod
    def detect():
        echo('Checking for VCS binaries:')
        no_binaries = []
        for cmd in ['curl', 'git', 'hg', 'svn', 'cvs', 'bzr', 'fossil']:
            echo(f'  {cmd}... ', nl=False)
            if which(cmd):
                msg = click.style('yes', 'green')
            else:
                no_binaries.append(cmd)
                msg = click.style('no', 'red')
            echo(f'{msg}.')

        if no_binaries:
            echo(click.style(
                f"Warning! Resources that uses {'/'.join(no_binaries)} will not be checked!", 'yellow'
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
        inject_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inject.rb')

        # Without updaing Homebrew there will be no `irb` command. It's in 'homebrew-core' tap.
        brew_bin = settings.get('BREW_BIN')
        echo("Updating Homebrew...", nl=False)
        brew_upd = subprocess.Popen(
            [brew_bin, 'update', '-q'], stdout=DEVNULL, stderr=subprocess.STDOUT, close_fds=True)
        brew_upd.wait()
        echo(click.style("done!", "green"))

        echo("Getting library from Homebrew...", nl=False)
        irb_proc = subprocess.Popen([brew_bin, 'irb', '-r', inject_file], stdout=subprocess.PIPE)
        self.json = subprocess.check_output(['sed', '1,2d'], stdin=irb_proc.stdout)
        echo(click.style("done!", "green"))
        return self

    def load(self):
        self.result_dict = json.loads(self.json)
        library = Library(self.result_dict)
        echo('Formulas found: ' + click.style(f'{len(library)}\n', 'green'))
        return library


@click.command()
@click.option(
    '-n', '--threads', type=click.INT, default=8, show_default=True, help="""
    Number of simultaneous downloads performed by brewchecker
    Warning: increasing this number may cause errors and slow down your system.
    """
)
@click.option('-q', '--quiet', is_flag=True, default=False, show_default=True, help="No log will be printed to STDOUT.")
@click.option(
    '-e', '--only-errors', is_flag=True, default=False, show_default=True,
    help="Report will only contain formulas with errors.",
)
@click.option('-l', '--log', type=click.File('a', encoding='utf-8', lazy=True), help="Path to log file.")
@click.option(
    '-o', '--output', type=click.File('w'), help="""
    Path to output file where JSON report will be saved
    Warning: omitting this option will cause printing report after with its log, unless -q/--quiet is presented."""
)
def main(**kwargs):
    settings.load(**kwargs)
    loader = Loader()
    loader.get_json()
    lib = loader.load()

    with futures.ThreadPoolExecutor(max_workers=settings.get('THREADS')) as executor:
        executor.map(lambda x: x.run(), lib, chunksize=1)

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
    except BaseException:
        raise
    finally:
        clean()
