#!/usr/bin/env python
# coding: utf-8
import os
import glob

from settings import FORMULAS_DIR
from formula import Formula
from utils import bold, update_sources


def main():
    filelist = glob.glob(os.path.join(FORMULAS_DIR, '*.rb'))
    print bold(u"\u2139 {} formulas found.".format(len(filelist)))

    for filename in filelist:
        m = Formula(filename)
        m.clean_urls()
        m.process()
        m.report()


if __name__ == '__main__':
    print u"\U0001F37A  " + bold("Homebrew link checker")
    update_sources()
    main()
