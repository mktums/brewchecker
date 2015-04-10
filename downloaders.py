# coding: utf-8
import json
import re

from requests import Request, Session, Timeout, get, codes
from requests.exceptions import ConnectionError
from requests.packages import urllib3

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
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) " \
                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"

    HEADERS = {
        "User-Agent": USER_AGENT,
    }

    SSL_ERROR = None

    def _prepare_request(self):
        req = Request(url=self.url_obj.get('url'), headers=self.HEADERS)
        if 'auth' in self.url_obj.keys():
            req.auth = self.url_obj.get('auth')
        req = req.prepare()
        if 'cr.yp.to' in req.url:
            del req.headers['Content-Length']
        return req

    def fetch(self, skip_head=False):
        s = Session()

        req = self._prepare_request()

        if skip_head:
            req.method = 'GET'
        else:
            req.method = 'HEAD'
        resp = s.send(req, allow_redirects=True, timeout=180, verify=False)
        return resp

    def run(self):
        try:
            resp = self.fetch()
            self.STATUS = resp.status_code
            if resp.status_code != codes.ok:
                resp = self.fetch(skip_head=True)
            self.STATUS = resp.status_code
        except (Timeout, ConnectionError):
            self.STATUS = 503
        return self


class ApacheDownloader(HTTPDownloader):
    """
    Downloader for apache.org website.
    """

    def _prepare_request(self):
        req = get(url=self.url_obj.get('url')+'&asjson=1', headers=self.HEADERS, verify=False).content
        resp = json.loads(req)
        url = resp.get('preferred') + resp.get('path_info')
        req = Request(url=url, headers=self.HEADERS).prepare()
        return req


RE_FTP = [
    re.compile(r'^ftp://'),
], 'ftp'

RE_GIT = [
    re.compile(r'^https?://.+\.git$'),
    re.compile(r'^git://'),
], 'git'

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
], 'svn'

RE_CVS = [
    re.compile(r'^cvs://'),
], 'cvs'

RE_HG = [
    re.compile(r'^https?://(.+?\.)?googlecode\.com/hg'),
    re.compile(r'^hg://'),
    re.compile(r'https?://(.+?\.)?sourceforge\.net/hgweb/'),
], 'hg'

RE_BZR = [
    re.compile(r'^bzr://'),
], 'bzr'

RE_FOSSIL = [
    re.compile(r'^fossil://'),
], 'fossil'

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
