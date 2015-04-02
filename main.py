#!/usr/bin/env python
# coding: utf-8
import os
import sys
import glob
import time

import git
import requests
from downloaders import DownloadStrategyDetector


HOMEBREW_GIT_URL = "https://github.com/Homebrew/homebrew.git"
CLONE_DIR = 'homebrew'
FORMULAS_DIR = CLONE_DIR + '/Library/Formula'
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"


def color(this_color, string_):
    return "\033[" + this_color + "m" + string_ + "\033[0m"


def bold(string_):
    return color('1', string_)


print u"\U0001F37A  " + bold("Homebrew link checker")


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

filelist = glob.glob(os.path.join(FORMULAS_DIR, '*.rb'))
print bold(u"\u2139 {} formulas found.".format(len(filelist)))


def color_status(response_code):
    if response_code == requests.codes.ok:
        return color('38;05;10', u"\u2714")
    else:
        return color('38;05;9', u"\u2718") + ' ' + str(response_code)

for filename in filelist:
    # Module
    module_name = os.path.splitext(os.path.basename(filename))[0]
    print color('38;05;3', u"\U0001F4E6"), ' ', module_name

    with open(filename) as formula:
        # Module code
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
                    ### Parsing Ruby output
                    # import subprocess
                    # value = 'echo "PP.pp(\'{}\'.f.stable)" | ./homebrew/bin/brew irb -r pp -f '.format(module_name)
                    # output = subprocess.check_output(
                    #     value,
                    #     shell=True,
                    # )
                    # data = output.splitlines()[4:-2]
                    # print data
                    # needed_strings = "@url", "@mirrors", "@patches"
                    # for n in data:
                    #     for y in needed_strings:
                    #         if n.strip().startswith(y):
                    #             print n

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
                    url_obj.update({'auth': (user, passwd), })

                strategy = DownloadStrategyDetector(url_obj).detect()

                if not isinstance(strategy, str):

                    downloader = strategy(url_obj)
                    resp = downloader.run()
                    if resp.STATUS != requests.codes.ok:
                        print '  ', color_status(resp.STATUS), url_obj['url']
                        if resp.SSL_ERROR:
                            print '  ', color('38;05;3', u"    \u26A0  {}".format(resp.SSL_ERROR))