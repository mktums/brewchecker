#!/usr/bin/env python
# coding: utf-8
import os
import glob

import requests

from settings import FORMULAS_DIR
from downloaders import DownloadStrategyDetector
from formula import Formula
from utils import bold


def main():

    print u"\U0001F37A  " + bold("Homebrew link checker")

    filelist = glob.glob(os.path.join(FORMULAS_DIR, '*.rb'))

    print bold(u"\u2139 {} formulas found.".format(len(filelist)))

    for filename in filelist:
        m = Formula(filename)
        try:
            m.clean_urls()
        except Exception as e:
            print m.name, m.content, e
            break

        for url_obj in m.URLS:
            strategy = DownloadStrategyDetector(url_obj).detect()
            if not isinstance(strategy, str):
                downloader = strategy(url_obj)
                resp = downloader.run()
                if resp.STATUS != requests.codes.ok:
                    m.ERRORS[url_obj['url']] = resp.STATUS
        m.report()

if __name__ == '__main__':
    main()
