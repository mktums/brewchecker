# coding: utf-8

import requests
from requests import Request, Session, Timeout
from requests.exceptions import SSLError, ConnectionError
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
        del req.headers['Content-Length']
        return req

    def fetch(self, skip_head=False, verify_ssl=True):
        s = Session()

        req = self._prepare_request()

        if skip_head:
            req.method = 'GET'
        else:
            req.method = 'HEAD'
        resp = s.send(req, verify=verify_ssl, allow_redirects=True, timeout=20)
        return resp

    def run(self):
        try:
            resp = self.fetch()
            if resp.status_code != requests.codes.ok:
                resp = self.fetch(skip_head=True)
            self.STATUS = resp.status_code
        except requests.exceptions.SSLError as e:
            self.SSL_ERROR = e.message
            try:
                resp = self.fetch(skip_head=True, verify_ssl=False)
                self.STATUS = resp.status_code
            except SSLError as e:
                self.SSL_ERROR = e.message
                self.STATUS = 700
        except (ConnectionError, Timeout):
            self.STATUS = 503
        return self
