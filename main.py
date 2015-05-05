#!/usr/bin/env python
# coding: utf-8
import json
import subprocess
import signal
from multiprocessing.pool import ThreadPool

from formula import Library
from settings import BREW_BIN, THREADS
from utils import bold, update_sources, signal_handler


signal.signal(signal.SIGINT, signal_handler)


class Loader(object):
    json = None
    result_dict = None

    def get_json(self, brew_bin=BREW_BIN):
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
        irb_proc = subprocess.Popen([brew_bin, 'irb', '-r', './inject.rb'], stdout=subprocess.PIPE)
        self.json = subprocess.check_output(['sed', '1,2d'], stdin=irb_proc.stdout)
        return self

    def load(self):
        self.result_dict = json.loads(self.json)
        library = Library(self.result_dict)
        # print bold(u"\u2139 {} formulas found.".format(len(library)))
        return library


def main():
    loader = Loader().get_json()
    lib = loader.load()
    pool = ThreadPool(THREADS)
    pool.map(lambda x: x.run(), lib, 1)
    pool.close()
    pool.join()
    print lib.report.full_report()

if __name__ == '__main__':
    # print u"\U0001F37A  " + bold("Homebrew link checker")
    update_sources()
    main()
