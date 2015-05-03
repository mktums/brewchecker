# coding: utf-8
import StringIO
import abc
import hashlib
import json
import os
import shutil
from urlparse import urlparse

import pycurl
from pip.exceptions import InstallationError
from pip.vcs.bazaar import Bazaar

from settings import USER_AGENT, REPOS_DIR
from vcs import CustomGit, CustomHg, CustomSVN, CVS, Fossil


class Downloader(object):
    __metaclass__ = abc.ABCMeta
    STATUS = None

    def __init__(self, url_obj):
        self.url_obj = url_obj

    @abc.abstractmethod
    def run(self):
        return


####
# N.B.: Here were HTTPDownloader and ApacheDownloader based on requests lib.
# You can access them by checkouting @6c652e87
####
class CurlDownloader(Downloader):
    def fetch(self, skip_head=False, url=None):
        c = pycurl.Curl()
        url = self.url_obj.url if not url else url

        blackhole = StringIO.StringIO()
        c.setopt(c.USERAGENT, USER_AGENT)
        c.setopt(c.URL, url)
        c.setopt(c.WRITEFUNCTION, blackhole.write)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.SSL_VERIFYPEER, 0)

        header = StringIO.StringIO()
        c.setopt(c.HEADERFUNCTION, header.write)

        if 'user' in self.url_obj.specs.keys():
            c.setopt(c.HTTPAUTH, c.HTTPAUTH_ANY)
            c.setopt(c.USERPWD, self.url_obj.specs.get('user'))

        if not skip_head:
            c.setopt(c.NOBODY, True)

        c.perform()
        self.STATUS = c.getinfo(c.HTTP_CODE)
        c.close()

        return self.STATUS, blackhole

    def run(self):
        try:
            # check for FTP
            if urlparse(self.url_obj.url).scheme == 'ftp':
                self.STATUS, _ = self.fetch(skip_head=True)
            else:
                self.STATUS, _ = self.fetch()
                if self.STATUS != 200:
                    self.STATUS, _ = self.fetch(skip_head=True)
        except Exception:
            self.STATUS = 404
        return self


class ApacheDownloader(CurlDownloader):
    """
    Downloader for apache.org website.
    """

    def get_mirror(self):
        _, body = self.fetch(url=self.url_obj.url+'&asjson=1', skip_head=True)
        resp = json.loads(body.getvalue())
        return resp.get('preferred') + resp.get('path_info')

    def run(self):
        # Saving original URL for logs
        old_url = self.url_obj.url
        self.url_obj.url = self.get_mirror()
        super(ApacheDownloader, self).run()
        # Restoring original URL
        self.url_obj.url = old_url
        return self


class AbstractVCSDownloader(Downloader):
    NAME = None
    VCS_CLASS = None

    REPO_URL = None
    REPO_DIR = None
    REVISION = None
    BRANCH = None
    TAG = None

    def __init__(self, url_obj):
        super(AbstractVCSDownloader, self).__init__(url_obj)
        self.REPO_URL = self.url_obj.url

        repo_dir_name = hashlib.md5(self.REPO_URL).hexdigest()
        self.REPO_DIR = '{0}/{1}/{2}'.format(REPOS_DIR, self.NAME, repo_dir_name)

        # Thanks to `json.loads()` some of this are ints or floats, instead of strings.
        revision = self.url_obj.specs.get('revision', None)
        if revision:
            self.REVISION = str(revision)

        branch = self.url_obj.specs.get('branch', None)
        if branch:
            self.BRANCH = str(branch)

        tag = self.url_obj.specs.get('tag', None)
        if tag:
            self.TAG = str(tag)

    def get_repo(self, repo):
        try:
            repo.obtain(self.REPO_DIR)
        except Exception:
            self.STATUS = 404

    def clean(self):
        if os.path.exists(self.REPO_DIR):
            try:
                shutil.rmtree(self.REPO_DIR)
            except OSError:
                pass

    def run_checks(self, repo):
        try:
            if self.REVISION:
                repo.check_commit(self.REVISION, self.REPO_DIR)

            if self.BRANCH:
                repo.check_branch(self.BRANCH, self.REPO_DIR)

            if self.TAG:
                repo.check_tag(self.TAG, self.REPO_DIR)

        except InstallationError:
            self.STATUS = 404

    def run(self):
        self.clean()
        repo = self.VCS_CLASS(self.REPO_URL)
        self.STATUS = 200
        self.get_repo(repo)

        if any([self.REVISION, self.BRANCH, self.TAG]):
            self.run_checks(repo)

        self.clean()

        return self


class GitDownloader(AbstractVCSDownloader):
    """
    For optimization purposes we download bare repos.
    """
    NAME = 'git'
    VCS_CLASS = CustomGit

    def __init__(self, url_obj):
        super(GitDownloader, self).__init__(url_obj)
        self.REPO_URL = 'git+{}'.format(self.REPO_URL)

    def get_repo(self, repo):
        try:
            repo.get_bare(self.REPO_DIR)
        except InstallationError:
            self.STATUS = 404


class MercurialDownloader(AbstractVCSDownloader):
    NAME = 'hg'
    VCS_CLASS = CustomHg

    def __init__(self, url_obj):
        super(MercurialDownloader, self).__init__(url_obj)
        self.REPO_URL = 'hg+{}'.format(self.REPO_URL)


class SubversionDownloader(AbstractVCSDownloader):
    NAME = 'svn'
    VCS_CLASS = CustomSVN

    def __init__(self, url_obj):
        super(SubversionDownloader, self).__init__(url_obj)
        self.REPO_URL = 'svn+{}'.format(self.REPO_URL)


class BazaarDownloader(AbstractVCSDownloader):
    NAME = 'bzr'
    VCS_CLASS = Bazaar

    def __init__(self, url_obj):
        super(BazaarDownloader, self).__init__(url_obj)
        self.REPO_URL = 'bzr+{}'.format(self.REPO_URL)


class CVSDownloader(AbstractVCSDownloader):
    NAME = 'cvs_root'
    VCS_CLASS = CVS


class FossilDownloader(AbstractVCSDownloader):
    NAME = 'fossil'
    VCS_CLASS = Fossil

    def clean(self):
        if os.path.exists(self.REPO_DIR):
            try:
                os.remove(self.REPO_DIR)
            except OSError:
                pass
