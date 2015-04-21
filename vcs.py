# coding: utf-8
import logging
import errno
from os import makedirs
from pip.exceptions import BadCommand
from pip.utils import call_subprocess
from pip.vcs.git import Git, os
from pip.vcs.mercurial import Mercurial
from pip.vcs.subversion import Subversion, get_rev_options
from utils import cd


class CustomGit(Git):
    def get_bare(self, dest):
        url, _ = self.get_url_rev()
        rev_options = ['origin/master']
        rev_display = ''
        if self.check_destination(dest, url, rev_options, rev_display):
            self.run_command(['clone', '-q', '--bare', url, dest], show_stdout=False)

    def check_commit(self, sha, location):
        return self.run_command(['rev-parse', '--verify', sha], show_stdout=False, cwd=location)


class CustomHg(Mercurial):
    def check_commit(self, sha, location):
        return self.run_command(['log', '-T', "'{node}\n'", '-r', sha], show_stdout=False, cwd=location)

    def check_branch(self, branch, location):
        return self.run_command(['log', '-T', "'{branch}\n'", '-r', "branch({})".format(branch), '-l', '1'],
                                show_stdout=False, cwd=location)


class CustomSVN(Subversion):
    def obtain(self, dest):
        url, rev = self.get_url_rev()
        rev_options = get_rev_options(url, rev)
        if rev:
            rev_display = ' (to revision %s)' % rev
        else:
            rev_display = ''
        if self.check_destination(dest, url, rev_options, rev_display):
            self.run_command(['checkout', '-q'] + rev_options + [url, dest], show_stdout=False)

    def info(self, rev, location):
        return self.run_command(['info', location, '-r', rev], show_stdout=False, extra_environ={'LANG': 'C'})


class CVS(object):
    name = 'cvs'

    def __init__(self, url=None):
        self.url = url
        super(CVS, self).__init__()

    def run_command(self, cmd, show_stdout=True,
                    filter_stdout=None, cwd=None,
                    raise_on_returncode=True,
                    command_level=logging.DEBUG, command_desc=None,
                    extra_environ=None):
        """
        Run a VCS subcommand
        This is simply a wrapper around call_subprocess that adds the VCS
        command name, and checks that the VCS is available
        """
        cmd = [self.name] + cmd
        try:
            return call_subprocess(cmd, show_stdout, filter_stdout, cwd,
                                   raise_on_returncode, command_level,
                                   command_desc, extra_environ)
        except OSError as e:
            # errno.ENOENT = no such file or directory
            # In other words, the VCS executable isn't available
            if e.errno == errno.ENOENT:
                raise BadCommand('Cannot find command %r' % self.name)
            else:
                raise  # re-raise exception if a different error occured

    def obtain(self, dest):
        if not os.path.exists(dest):
            makedirs(dest)

        with cd(dest):
            self.run_command([
                '-d{}'.format(self.url), 'checkout', self.url.split('/')[-1]
            ], show_stdout=False)

        return
