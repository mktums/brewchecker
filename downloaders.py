# coding: utf-8
import StringIO
import ftplib
import hashlib
import json
import os
import re
import shutil
from urlparse import urlparse

from pip.exceptions import InstallationError
from pip.vcs.bazaar import Bazaar
from requests import Timeout, codes, request
from requests.exceptions import ConnectionError
from requests.packages import urllib3

from settings import USER_AGENT, REPOS_DIR
from vcs import CustomGit, CustomHg, CustomSVN, CVS, Fossil

urllib3.disable_warnings()


class Downloader(object):
    STATUS = None

    def __init__(self, url_obj):
        self.url_obj = url_obj

    def run(self):
        raise NotImplemented


class HTTPDownloader(Downloader):
    """
    HTTP downloads comes with two ways of "downloading":
    1) First we try to use HTTP HEAD method;
    2) If HEAD falls with error - we use GET method.
    """

    HEADERS = {
        "User-Agent": USER_AGENT,
    }

    SSL_ERROR = None

    def fetch(self, skip_head=False):
        kwargs = dict(
            url=self.url_obj.get('url'), headers=self.HEADERS, allow_redirects=True, timeout=180, verify=False
        )

        if 'auth' in self.url_obj.keys():
            kwargs.update({'auth': self.url_obj.get('auth')})

        if skip_head:
            method = 'get'
        else:
            method = 'head'

        resp = request(method, **kwargs)
        return resp

    def run(self):
        try:
            resp = self.fetch()
            self.STATUS = resp.status_code
            if resp.status_code != codes.ok:
                resp = self.fetch(skip_head=True)
            self.STATUS = resp.status_code
        except (Timeout, ConnectionError):
            self.STATUS = 404
        return self


class ApacheDownloader(HTTPDownloader):
    """
    Downloader for apache.org website.
    """

    def fetch(self, skip_head=False):
        req = request('get', url=self.url_obj.get('url')+'&asjson=1', headers=self.HEADERS, verify=False).content
        resp = json.loads(req)
        url = resp.get('preferred') + resp.get('path_info')
        resp = request('get', url=url, headers=self.HEADERS)
        return resp


class FTPDownloader(Downloader):
    def fetch(self, ftp, directory, filename):
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


class GitDownloader(Downloader):
    """
    For optimization purposes we download bare repos.
    If tag/branch/commit presence is found - we check it.
    """
    def run(self):
        repo_url = self.url_obj.get('url')
        rev = self.url_obj.get('revision', False) or self.url_obj.get('branch', False) or self.url_obj.get('tag', False)
        repo_dir_suffix = repo_url.split('/')[-1]

        if not repo_dir_suffix:
            repo_dir_suffix = repo_url.split('/')[-2]
        repo_dir = REPOS_DIR + '/git/' + repo_dir_suffix

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        repo_url = 'git+' + self.url_obj.get('url')
        repo = CustomGit(repo_url)

        self.STATUS = 200

        try:
            repo.get_bare(repo_dir)
        except InstallationError:
            self.STATUS = 404

        if rev:
            try:
                repo.check_commit(rev, repo_dir)
            except InstallationError:
                self.STATUS = 404

        shutil.rmtree(repo_dir)
        return self


class MercurialDownloader(Downloader):
    def run(self):
        repo_url = self.url_obj.get('url')
        rev = self.url_obj.get('revision', False)
        branch = self.url_obj.get('branch', False)
        repo_dir_suffix = repo_url.split('/')[-1]

        if not repo_dir_suffix:
            repo_dir_suffix = repo_url.split('/')[-2]
        repo_dir = REPOS_DIR + '/hg/' + repo_dir_suffix

        repo_url = 'hg+' + self.url_obj.get('url')
        repo = CustomHg(repo_url)

        self.STATUS = 200

        try:
            repo.unpack(repo_dir)
        except InstallationError:
            self.STATUS = 404

        if rev:
            try:
                repo.check_commit(rev, repo_dir)
            except InstallationError:
                self.STATUS = 404

        if branch:
            try:
                repo.check_branch(branch, repo_dir)
            except InstallationError:
                self.STATUS = 404

        return self


class SubversionDownloader(Downloader):
    def run(self):
        repo_url = self.url_obj.get('url')
        rev = self.url_obj.get('revision', False)
        repo_dir_suffix = hashlib.md5(repo_url).hexdigest()
        repo_dir = REPOS_DIR + '/svn/' + repo_dir_suffix

        repo_url = 'svn+' + self.url_obj.get('url')

        repo = CustomSVN(repo_url)

        self.STATUS = 200

        try:
            repo.unpack(repo_dir)
        except InstallationError:
            self.STATUS = 404

        if rev:
            try:
                repo.info(rev, repo_dir)
            except InstallationError:
                self.STATUS = 404

        return self


class BazaarDownloader(Downloader):
    def run(self):
        repo_url = self.url_obj.get('url')
        repo_dir_suffix = hashlib.md5(repo_url).hexdigest()
        repo_dir = REPOS_DIR + '/bzr/' + repo_dir_suffix

        repo_url = 'bzr+' + self.url_obj.get('url')

        repo = Bazaar(repo_url)

        self.STATUS = 200

        try:
            repo.unpack(repo_dir)
        except InstallationError:
            self.STATUS = 404

        return self


class CVSDownloader(Downloader):
    def run(self):
        repo_url = self.url_obj.get('url')
        repo_dir_suffix = hashlib.md5(repo_url).hexdigest()
        repo_dir = REPOS_DIR + '/cvs_root/' + repo_dir_suffix
        repo = CVS(repo_url)

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.STATUS = 200

        try:
            repo.obtain(repo_dir)
        except Exception:
            self.STATUS = 404

        shutil.rmtree(repo_dir)

        return self


class FossilDownloader(Downloader):
    def run(self):
        repo_url = self.url_obj.get('url')
        repo_file_name = hashlib.md5(repo_url).hexdigest()
        repo_file = REPOS_DIR + '/fossil/' + repo_file_name
        repo = Fossil(repo_url)

        if os.path.exists(repo_file):
            os.remove(repo_file)

        self.STATUS = 200

        try:
            repo.obtain(repo_file)
        except Exception:
            self.STATUS = 404

        os.remove(repo_file)

        return self


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
