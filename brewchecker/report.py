# coding: utf-8
from collections import OrderedDict


class FormulaReport(object):
    def __init__(self, formula):
        self.name = formula.name
        self.errors = {}

        self.summary = {
            'main': {
                'url': formula.main.url,
                'status': formula.main.status,
                'mirrors': [{'url': mirror.url, 'status': mirror.status} for mirror in formula.main.mirrors],
            },
            'patches': [],
            'resources': {},
        }

        for patch in formula.patches:
            patch_dict = {
                'url': patch.url,
                'status': patch.status,
                'mirrors': [{'url': mirror.url, 'status': mirror.status} for mirror in patch.mirrors]
            }
            self.summary['patches'] += [patch_dict, ]

        for name, resource in formula.resources.items():
            resource_dict = {
                name: {
                    'url': resource.url,
                    'status': resource.status,
                    'mirrors': [{'url': mirror.url, 'status': mirror.status} for mirror in resource.mirrors]
                }
            }
            self.summary['resources'].update(resource_dict)
        if formula.ERRORS:
            self.errors = self.summary


class LibraryReport(object):
    def __init__(self):
        self.reports = OrderedDict()
        self.errors = OrderedDict()

    def add(self, report):
        self.reports.update({report.name: report.summary})

    def add_errors(self, report):
        self.errors.update({report.name: report.errors})
