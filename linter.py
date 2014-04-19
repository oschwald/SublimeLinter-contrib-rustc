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

from SublimeLinter.lint import Linter


class Rust(Linter):

    """Provides an interface to Rust."""

    syntax = 'rust'
    cmd = 'rustc'
    tempfile_suffix = 'rs'

    regex = (
        r'^.+?:(?P<line>\d+):(?P<col>\d+):\s+\d+:\d+\s'
        r'(?:(?P<error>(error|fatal error))|(?P<warning>warning)):\s+'
        r'(?P<message>.+)'
    )
