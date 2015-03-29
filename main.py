#!/usr/bin/env python
# coding: utf-8
import os
import sys
import glob
import time
from urlparse import urlparse
from collections import Counter

import git
import requests
import ftputil


# http://stackoverflow.com/a/29202163
from requests.packages.urllib3.contrib import pyopenssl
pyopenssl.inject_into_urllib3()

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


def determine_download_strategy(_url_obj):
    o = urlparse(_url_obj['url'])

    # Git
    if o.path.endswith('.git') or o.scheme == 'git':
        return 'git'

    # Apache website
    if 'www.apache.org/dyn/closer.cgi' in o.geturl():
        return 'apache'

    # SVN
    if 'googlecode.com/svn' in o.geturl() or 'sourceforge.net/svnroot/' in o.geturl() or o.netloc.startswith(
            'svn.') or 'http://svn\.apache\.org/repos/' in o.geturl() or 'svn+http' in o.scheme:
        return 'svn'

    # Mercurial
    if 'googlecode.com/hg' in o.geturl() or 'sourceforge.net/hgweb/' in o.geturl():
        return 'hg'

    if 'using' in _url_obj.keys():
        if _url_obj['using'] in (
            'MatDownloadStrategy',
            'FreeimageHttpDownloadStrategy',
            'RpmDownloadStrategy',
            'HgBundleDownloadStrategy'
        ):
            return o.scheme
        if _url_obj['using'] == 'nounzip':
            return o.scheme
        return _url_obj['using']

    else:
        return o.scheme


def color_status(response_code):
    if response_code == requests.codes.ok:
        return color('38;05;10', u"\u2714")
    else:
        return color('38;05;9', u"\u2718") + ' ' + str(response_code)


schemes = Counter()
responses = Counter()
errors = {}

for filename in glob.glob(os.path.join(FORMULAS_DIR, '*.rb')):
    # Module
    module_name = os.path.splitext(os.path.basename(filename))[0]
    # print color('38;05;3', u"\U0001F4E6"), ' ', module_name
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

                # Since I don't know how to execute Ruby code inside Python
                # I'll just ignore those urls who must be eval'd.
                if "#{" in clean_line:
                    print filename

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

                strategy = determine_download_strategy(url_obj)
                if not strategy:
                    print filename, url_obj, clean_line
                schemes.update([strategy, ])

                # if determine_download_strategy(url_obj) in ('http', 'https'):
                #     kwargs = {
                #         'headers': {
                #             "User-Agent": USER_AGENT,
                #         },
                #         'allow_redirects': True,
                #         'timeout': 20,
                #     }
                #     if 'user' in url_obj.keys():
                #         user, passwd = url_obj['user'].split(':')
                #         kwargs.update({'auth': (user, passwd), })
                #     try:
                #         resp = requests.head(url_obj['url'], **kwargs)
                #         if resp.status_code != requests.codes.ok:
                #             resp = requests.get(url_obj['url'], **kwargs)
                #     except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                #         resp.status_code = 700
                #     responses.update([resp.status_code, ])
                #     print '  ', color_status(resp.status_code), url_obj['url']
                #     if len(clean_line) > 1:
                #         print url_obj
                #     resp.close()
                #
                # if resp.status_code != requests.codes.ok:
                #     errors.update({module_name: {url_obj['url']: resp.status_code}})

                    # FTP ##
                    # elif o.scheme == "ftp":
                    #     try:
                    #         host = ftputil.FTPHost(o.netloc, 'anonymous')
                    #         host.getcwd()
                    #         resp = host.path.getsize(o.path)
                    #     except Exception as e:
                    #         print line, url, e.message
                    #     finally:
                    #         host.close()
                    # /FTP ##
                    #
                    # else:
                    #     print o
                    # except Exception as e:
                    #     print "[!!!]", url, e.message, line

print schemes
# print responses
# print errors