# coding: utf-8
import StringIO
import ftplib
import hashlib
import json
import os
import re
import shutil
from urlparse import urlparse

import pycurl
from pip.exceptions import InstallationError
from pip.vcs.bazaar import Bazaar

from settings import USER_AGENT, REPOS_DIR
from vcs import CustomGit, CustomHg, CustomSVN, CVS, Fossil


class Downloader(object):
    STATUS = None

    def __init__(self, url_obj):
        self.url_obj = url_obj

    def run(self):
        raise NotImplemented


####
# N.B.: Here were HTTPDownloader and ApacheDownloader based on requests lib.
# You can access them by checkouting @6c652e87
####
class HTTPDownloader(Downloader):
    def fetch(self, skip_head=False, url=None):
        c = pycurl.Curl()
        url = self.url_obj.get('url') if not url else url
        blackhole = StringIO.StringIO()
        c.setopt(c.USERAGENT, USER_AGENT)
        c.setopt(c.URL, url)
        c.setopt(c.WRITEFUNCTION, blackhole.write)
        c.setopt(c.FOLLOWLOCATION, True)
        header = StringIO.StringIO()
        c.setopt(c.HEADERFUNCTION, header.write)
        c.setopt(c.SSL_VERIFYPEER, 0)

        if 'auth' in self.url_obj.keys():
            c.setopt(c.HTTPAUTH, c.HTTPAUTH_ANY)
            c.setopt(c.USERPWD, ":".join(self.url_obj.get('auth')))

        if not skip_head:
            c.setopt(c.NOBODY, True)

        c.perform()
        self.STATUS = c.getinfo(c.HTTP_CODE)
        c.close()

        return self.STATUS, blackhole

    def run(self):
        try:
            self.STATUS, _ = self.fetch()
            if self.STATUS != 200:
                self.STATUS, _ = self.fetch(skip_head=True)
        except Exception:
            self.STATUS = 404
        return self


class ApacheDownloader(HTTPDownloader):
    """
    Downloader for apache.org website.
    """

    def get_mirror(self):
        _, body = self.fetch(url=self.url_obj.get('url')+'&asjson=1', skip_head=True)
        resp = json.loads(body.getvalue())
        return resp.get('preferred') + resp.get('path_info')

    def run(self):
        self.url_obj['url'] = self.get_mirror()
        super(ApacheDownloader, self).run()
        return self


class FTPDownloader(Downloader):
    @staticmethod
    def fetch(ftp, directory, filename):
        ftp.cwd(directory)
        f = StringIO.StringIO()
        ftp.retrbinary("RETR " + filename, f.write)
        f.close()
        del f

    def run(self):
        parsed = urlparse(self.url_obj.get('url'))
        directory, filename = os.path.split(parsed.path)
        self.STATUS = 200
        try:
            ftp = ftplib.FTP(parsed.netloc)
            ftp.login()
            self.fetch(ftp, directory, filename)
        except Exception:
            self.STATUS = 404
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
        self.REPO_URL = self.url_obj.get('url')

        repo_dir_name = hashlib.md5(self.REPO_URL).hexdigest()
        self.REPO_DIR = '{}/{}/{}'.format(REPOS_DIR, self.NAME, repo_dir_name)

        self.REVISION = self.url_obj.get('revision', None)
        self.BRANCH = self.url_obj.get('branch', None)
        self.TAG = self.url_obj.get('tag', None)

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


RE_FTP = [
    re.compile(r'^ftp://'),
], FTPDownloader

RE_GIT = [
    re.compile(r'^https?://.+\.git$'),
    re.compile(r'^git://'),
], GitDownloader

RE_APACHE = [
    re.compile(r'https?://www\.apache\.org/dyn/closer\.cgi'),
], ApacheDownloader

RE_SVN = [
    re.compile(r'^https?://(.+?\.)?googlecode\.com/svn]'),
    re.compile(r'^https?://svn\.'),
    re.compile(r'^svn://'),
    re.compile(r'https?://(.+?\.)?sourceforge\.net/svnroot/'),
    re.compile(r'^http://svn\.apache\.org/repos/'),
    re.compile(r'^svn\+http://'),
], SubversionDownloader

RE_CVS = [
    re.compile(r'^cvs://'),
], CVSDownloader

RE_HG = [
    re.compile(r'^https?://(.+?\.)?googlecode\.com/hg'),
    re.compile(r'^hg://'),
    re.compile(r'https?://(.+?\.)?sourceforge\.net/hgweb/'),
], MercurialDownloader

RE_BZR = [
    re.compile(r'^bzr://'),
], 'bzr'

RE_FOSSIL = [
    re.compile(r'^fossil://'),
], FossilDownloader

RE_PATTERNS = (
    RE_FTP, RE_GIT, RE_APACHE, RE_SVN, RE_CVS, RE_HG, RE_BZR, RE_FOSSIL
)


def test_patterns(text, patterns):
    for pattern in patterns:
        if re.findall(pattern, text):
            return True
    return False


class DownloadStrategyDetector():
    def __init__(self, _url_obj):
        url_obj = _url_obj.copy()
        self.url = url_obj.pop('url')
        self.params = url_obj

    def from_url(self):
        for re_group, downloader in RE_PATTERNS:
            if test_patterns(self.url, re_group):
                return downloader

        return HTTPDownloader

    def from_params(self):
        using = self.params.get('using', False)
        if using == 'hg':
            return RE_HG[1]
        elif using == 'ftp':
            return RE_FTP[1]
        elif using == 'git':
            return RE_GIT[1]
        elif using == 'bzr':
            return RE_BZR[1]
        elif using == 'cvs':
            return RE_CVS[1]
        elif using == 'fossil':
            return RE_FOSSIL[1]
        else:
            return False

    def detect(self):
        _strategy = self.from_params() or self.from_url()
        return _strategy
