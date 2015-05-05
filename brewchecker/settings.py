# coding: utf-8
import os
import tempfile

BASE_DIR = tempfile.mkdtemp()
BREW_GIT_URL = "git+https://github.com/Homebrew/homebrew.git"
BREW_CLONE_DIR = os.path.join(BASE_DIR, 'homebrew')
BREW_BIN = BREW_CLONE_DIR + '/bin/brew'
BREW_FORMULAS_DIR = BREW_CLONE_DIR + '/Library/Formula'
REPOS_DIR = os.path.join(BASE_DIR, 'repos')
USER_AGENT = "Homebrew 0.9.5 (Ruby 2.0.0-481; Mac OS X 10.9.5)"
THREADS = 10
