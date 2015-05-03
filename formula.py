# coding: utf-8
from downloaders import (
    CurlDownloader, GitDownloader, ApacheDownloader, SubversionDownloader, MercurialDownloader,
    CVSDownloader, BazaarDownloader, FossilDownloader
)
from utils import color_status, color, SlicableDict


class Resource(object):
    def __init__(self, specs):
        self.url = specs.get('url')
        self.specs = specs.get('specs')
        mirrors = specs.get('mirrors', [])
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
        # [1] See https://indiewebcamp.com/curlable
        self.mirrors = [Resource({'url': url, 'strategy': 'CurlDownloadStrategy', 'specs': self.specs}) for url in mirrors]
        self.strategy = specs.get('strategy')

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
            raise RuntimeWarning("No downloader found for {}".format(e.args))
        return downloader

    def get_downloader(self):
        return self.downloader(self)


class Formula(object):
    def __init__(self, module):
        name, specs = module
        self.name = name
        self.main = Resource(specs.get('main'))
        self.patches = [Resource(patch) for patch in specs.get('patches', None)]
        self.resources = {name: Resource(spec) for name, spec in specs.get('resources', None).items()}

    def run_mirrors(self, resources):
        for resource in resources.mirrors:
            downloader = resource.get_downloader()
            resource.status = downloader.run().STATUS
            print color_status(resource.status) + '    Mirror: {}'.format(resource.url)

    def run_main(self):
        downloader = self.main.get_downloader()
        self.main.status = downloader.run().STATUS
        print color_status(self.main.status) + '  Main URL: {}'.format(self.main.url)
        self.run_mirrors(self.main)

    def run_patches(self):
        for patch in self.patches:
            downloader = patch.get_downloader()
            patch.status = downloader.run().STATUS
            print color_status(patch.status) + '  Patch: {}'.format(patch.url)
            self.run_mirrors(patch)

    def run_resources(self):
        for name, resource in self.resources.iteritems():
            downloader = resource.get_downloader()
            resource.status = downloader.run().STATUS
            print color_status(resource.status) + '  Resource "{}": {}'.format(name, resource.url)
            self.run_mirrors(resource)

    def run(self):
        print color('38;05;3', u"\U0001F4E6") + u'  ' + self.name
        self.run_main()
        self.run_patches()
        self.run_resources()


class Library(object):
    def __init__(self, dictionary):
        self._collection = SlicableDict(sorted(
            {f.name: f for f in [Formula(module) for module in dictionary.iteritems()]}.iteritems()
        ))

    def __getitem__(self, key):
        return self._collection.__getitem__(key)

    def __getattr__(self, item):
        return self._collection.__getitem__(item)

    def __iter__(self):
        return self._collection.itervalues()

    def __len__(self):
        return len(self._collection)
