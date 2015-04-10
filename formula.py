# coding: utf-8
import os
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
            if clean_line.startswith('url '):

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
                    'url': clean_line[0].replace("url ", "").strip('\'\" ')
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

    def report(self):
        if self.ERRORS:
            print color('38;05;3', u"\U0001F4E6"), ' ', self.name
            for errno, url in self.ERRORS.items():
                print '  ', color_status(errno), url
