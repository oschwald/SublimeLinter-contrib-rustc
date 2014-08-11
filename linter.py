#
# linter.py
# Linter for SublimeLinter3, a code checking framework for Sublime Text 3
#
# Written by Gregory Oschwald
# Copyright (c) 2014 Gregory Oschwald
#
# License: MIT
#

"""This module exports the Rustc plugin class."""

import os
from SublimeLinter.lint import Linter, util


class Rust(Linter):

    """Provides an interface to Rust."""

    defaults = {
        'use-cargo': False
    }
    executable = 'rustc'
    syntax = 'rust'
    tempfile_suffix = '-'

    regex = (
        r'^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s+\d+:\d+\s'
        r'(?:(?P<error>(error|fatal error))|(?P<warning>warning)):\s+'
        r'(?P<message>.+)'
    )

    def cmd(self):
        """Return a list with the command to execute."""
        use_cargo = self.get_view_settings().get('use-cargo', False)

        if use_cargo:
            config = util.find_file(
                os.path.dirname(self.filename), 'Cargo.toml')
            if config:
                return ['cargo', 'build', '--manifest-path', config]

        return ['rustc', '--no-trans']

    def split_match(self, match):
        """
        Return the components of the match.

        We override this because Cargo lints all referenced files,
        and we only want errors from the linted file.
        """
        if match:
            if os.path.basename(self.filename) != os.path.basename(match.group('file')):
                match = None

        return super().split_match(match)
