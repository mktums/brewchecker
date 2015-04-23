# coding: utf-8
import os
import sys

from downloaders import DownloadStrategyDetector, Downloader
from utils import color_status, color


class Formula(object):
    def __init__(self, filepath):
        with open(filepath) as text:
            self.content = text.readlines()
        self.name = os.path.splitext(os.path.basename(filepath))[0]
        self.URLS = list()
        self.ERRORS = dict()

    def clean_urls(self):
        formula = iter(self.content)
        for line in formula:
            clean_line = line.strip()

            # Get all urls from module
            if clean_line.startswith(('url', 'mirror ')):

                # Clean url
                def try_next(_line):
                    if _line.strip().endswith(','):
                        next_line = next(formula)
                        if next_line.strip().startswith('#'):
                            return try_next(next_line)
                        else:
                            return next_line + try_next(next_line)
                    else:
                        return ''

                clean_line += try_next(line)

                if "#{" in clean_line:
                    continue

                clean_line = [x.strip() for x in clean_line.split(',') if x]
                url_obj = {
                    'url': clean_line[0].split(' ')[1].strip('\'\" ')
                }

                if len(clean_line) > 1:
                    for x in clean_line[1:]:
                        z, y = x.split("=>")
                        if 'user' in z:
                            url_obj[z.strip().replace(":", "")] = y.strip(' \"\'')
                        else:
                            url_obj[z.strip().replace(":", "")] = y.strip(' \"\'').replace(":", "")
                if 'user' in url_obj.keys():
                    user, passwd = url_obj.pop('user').split(':')
                    url_obj.update(dict(auth=(user, passwd)))

                self.URLS.append(url_obj)

    def process(self):
        for url_obj in self.URLS:
            strategy = DownloadStrategyDetector(url_obj).detect()
            if issubclass(strategy, Downloader):
                downloader = strategy(url_obj)
                resp = downloader.run()
                if resp.STATUS != 200:
                    self.ERRORS[url_obj['url']] = resp.STATUS

    def report(self):
        if self.ERRORS:
            sys.stdout.write(color('38;05;3', u"\U0001F4E6") + u'  ' + self.name + u'\n')
            for url, errno in self.ERRORS.items():
                sys.stdout.write('  ' + color_status(errno) + u' ' + url + u'\n')
            sys.stdout.flush()
