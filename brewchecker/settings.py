# coding: utf-8
import os
import tempfile


class DefaultSettings(object):
    USER_AGENT = "Homebrew 0.9.5 (Ruby 2.0.0-481; Mac OS X 10.9.5)"
    BASE_DIR = tempfile.mkdtemp('brewchecker')
    BREW_GIT_URL = "git+https://github.com/Homebrew/homebrew.git"


class LazySettings(object):
    def _setup(self, name):
        setattr(self, name, getattr(DefaultSettings, name, None))

    def get(self, name):
        if not getattr(self, name, None):
            self._setup(name)
        return getattr(self, name)

    def load(self, **kwargs):
        for name, value in kwargs.iteritems():
            setattr(self, name.upper(), value)

    @property
    def BREW_CLONE_DIR(self):
        return os.path.join(self.get('BASE_DIR'), 'homebrew')

    @property
    def BREW_BIN(self):
        return os.path.join(self.get('BREW_CLONE_DIR'), 'bin/brew')

    @property
    def BREW_FORMULAS_DIR(self):
        return os.path.join(self.get('BREW_CLONE_DIR'), 'Library/Formula')

    @property
    def REPOS_DIR(self):
        return os.path.join(self.get('BASE_DIR'), 'repos')


settings = LazySettings()
