# coding: utf-8
import click

from brewchecker.downloaders import (
    CurlDownloader, GitDownloader, ApacheDownloader, SubversionDownloader, MercurialDownloader,
    CVSDownloader, BazaarDownloader, FossilDownloader
)
from brewchecker.lib import SlicableDict
from brewchecker.report import FormulaReport, LibraryReport
from brewchecker.utils import echo, is_ok, Timer


class Resource(object):
    def __init__(self, specs):
        self.url = specs.get('url')
        self.specs = specs.get('specs')
        self.status = None
        self.strategy = specs.get('strategy')

        # N.B.:
        # Homebrew's documentation is unclear about setting options for mirrors (like :using, :revision, etc),
        # so at this moment we can only assume that mirror MUST be a curlable[1] file.
        #
        # We must investigate this sourcecode for more details:
        # https://github.com/Homebrew/homebrew/blob/d12b17e99b3071fba88fb5a6cbcefcbe136f7733/Library/Homebrew/download_strategy.rb#L260-L324
        #
        # For now it seems that mirrors exists only in CurlDownloadStrategy,
        # and they shares `meta` (or `specs`) with parent resource.
        #
        # @MistyDeMeo's clarification on this (taken from IRC conversation with her permission):
        #
        # 00:58:30 mistym: It's an attribute on SoftwareSpec, so technically it could be used by any
        #                  download strategy, but in practice CurlDownloadStrategy and its subclasses are the only
        #                  download strategies that *use* mirrors. You could define them for other download strategies
        #                  but they'd be ignored.
        # 00:59:04 mistym: Unlike `url`, `mirrors` don't include their own download strategies; they're intended
        #                  to be used by the download strategy defined by the `url`
        #
        # [1] See https://indiewebcamp.com/curlable
        mirrors = specs.get('mirrors', [])
        self.mirrors = [Resource({'url': url, 'strategy': self.strategy, 'specs': self.specs}) for url in mirrors]

        try:
            self.downloader = self.get_downloader_class()
        except KeyError:
            self.downloader = None

    def get_downloader_class(self):
        downloaders = {
            'CurlDownloadStrategy': CurlDownloader,
            'NoUnzipCurlDownloadStrategy': CurlDownloader,
            'GitDownloadStrategy': GitDownloader,
            'CurlApacheMirrorDownloadStrategy': ApacheDownloader,
            'SubversionDownloadStrategy': SubversionDownloader,
            'MercurialDownloadStrategy': MercurialDownloader,

            # Following strategies are user-contributed, and basically just CurlDownloadStrategy
            # with some after-download actions.
            'Formulary::Formulae::FreeimageHttpDownloadStrategy': CurlDownloader,
            'Formulary::Formulae::RpmDownloadStrategy': CurlDownloader,
            'Formulary::Formulae::MatDownloadStrategy': CurlDownloader,

            # Strategies below currently aren't used in formulas' "stable" section
            # but we still have to have support them.
            'CVSDownloadStrategy': CVSDownloader,
            'BazaarDownloadStrategy': BazaarDownloader,
            'FossilDownloadStrategy': FossilDownloader,
        }

        try:
            downloader = downloaders.get(self.strategy)
        except KeyError as e:
            raise RuntimeWarning(u"No downloader found for {}".format(e.args))
        return downloader

    def get_downloader(self):
        if not self.downloader:
            return None
        return self.downloader(self)


class Formula(object):
    def __init__(self, library, module):
        self.library = library
        self.report = None
        self.ERRORS = False
        name, specs = module
        self.name = name
        self.main = Resource(specs.get('main'))
        self.patches = [Resource(patch) for patch in specs.get('patches', None)]
        self.resources = {name: Resource(spec) for name, spec in specs.get('resources', None).items()}

    def run_mirrors(self, resource):
        for mirror in resource.mirrors:
            downloader = mirror.get_downloader()
            mirror.status = is_ok(downloader.run().STATUS)
            if not mirror.status:
                self.ERRORS = True

    def _run(self, resource):
        downloader = resource.get_downloader()
        if downloader:
            resource.status = is_ok(downloader.run().STATUS)
            if not resource.status:
                self.ERRORS = True
            self.run_mirrors(resource)

    def run_main(self):
        self._run(self.main)

    def run_patches(self):
        for patch in self.patches:
            self._run(patch)

    def run_resources(self):
        for name, resource in self.resources.iteritems():
            self._run(resource)

    def run(self):
        with Timer() as t:
            # echo(u"Start checking {} formula...".format(click.style(self.name, bold=True)))
            self.run_main()
            self.run_patches()
            self.run_resources()
        self.report = FormulaReport(self)
        self.library.report.add(self.report)
        if self.ERRORS:
            self.library.report.add_errors(self.report)
        status = click.style(u"\u2714", "green") if not self.ERRORS else click.style(u"\u2718", "red")
        status_text = u'okay' if not self.ERRORS else u'not okay'
        output = u"{} {} formula is {}.".format(
            status, click.style(self.name, bold=True), status_text, t.interval
        )
        output += u" Done in %.03f sec." % t.interval
        echo(output)


class Library(object):
    def __init__(self, dictionary=None):
        if dictionary:
            self._collection = SlicableDict(sorted(
                {f.name: f for f in [Formula(self, module) for module in dictionary.iteritems()]}.iteritems()
            ))
        self.report = LibraryReport()

    def __getitem__(self, key):
        if isinstance(key, slice):
            lib = Library()
            lib._collection = self._collection.__getitem__(key)
            for formula in lib:
                formula.library = lib
            return lib
        return self._collection.__getitem__(key)

    def __getattr__(self, item):
        return self._collection.__getitem__(item)

    def __iter__(self):
        return self._collection.itervalues()

    def __len__(self):
        return len(self._collection)
