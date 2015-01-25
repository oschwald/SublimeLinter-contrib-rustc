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
from SublimeLinter.lint import Linter, util, persist


class Rust(Linter):

    """Provides an interface to Rust."""

    defaults = {
        'use-cargo': False,
        'use-crate-root': False,
        'crate-root': None,
    }
    cmd = ('rustc', '-Z no-trans')
    syntax = 'rust'
    tempfile_suffix = 'rs'

    regex = (
        r'^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s+\d+:\d+\s'
        r'(?:(?P<error>(error|fatal error))|(?P<warning>warning)):\s+'
        r'(?P<message>.+)'
    )

    use_cargo = False
    use_crate_root = False
    cargo_config = None
    crate_root = None

    def run(self, cmd, code):
        """
        Return a list with the command to execute.

        The command chosen is resolved as follows:

        If the `use-cargo` option is set, lint using a `cargo build`.
        If cargo is not used, and the `use-crate-root` option is set, lint
        the crate root. Finally, if the crate root cannot be determined, or the
        `use-crate-root` option is not set, lint the current file.

        Linting the crate (either through cargo or rustc) means that if
        errors are caught in other files, errors on the current file might
        not show up until these other errors are resolved.

        Linting a single file means that any imports from higher in the
        module hierarchy will probably cause an error and prevent proper
        linting in the rest of the file.
        """
        self.use_cargo = self.get_view_settings().get('use-cargo', False)
        self.use_crate_root = self.get_view_settings().get('use-crate-root', False)

        if self.use_cargo:
            current_dir = os.path.dirname(self.filename)
            self.cargo_config = util.find_file(current_dir, 'Cargo.toml')

            if self.cargo_config:
                self.tempfile_suffix = '-'

                return util.communicate(
                    ['cargo', 'build', '--manifest-path', self.cargo_config],
                    code=None,
                    output_stream=self.error_stream,
                    env=self.env)

        if self.use_crate_root:
            self.crate_root = self.locate_crate_root()

            if self.crate_root:
                cmd.append(self.crate_root)
                self.tempfile_suffix = '-'

                return util.communicate(
                    cmd,
                    code=None,
                    output_stream=self.error_stream,
                    env=self.env)

        self.tempfile_suffix = 'rs'
        return self.tmpfile(cmd, code)

    def split_match(self, match):
        """
        Return the components of the match.

        We override this because Cargo lints all referenced files,
        and we only want errors from the linted file. The same applies
        when linting from the crate root. Of course when linting a single
        file only, all the errors will be from that file because it is
        in a temporary directory.

        The matched file path is considered in the context of a working directory.
        If it is an absolute path, the working directory will be ignored. This
        working directory is not the same as the current Sublime Text process
        working directory -- it is the working directory of an external command.

        For Cargo, the working directory is the directory of Cargo.toml.
        When working with a crate root, the working directory is the directory of the
        crate root source file.
        """
        matched_file = match.group('file') if match else None

        if matched_file:
            if self.use_cargo:
                working_dir = os.path.dirname(self.cargo_config)

                if not self.is_current_file(working_dir, matched_file):
                    match = None

            elif self.use_crate_root:
                working_dir = os.path.dirname(self.crate_root)

                if not self.is_current_file(working_dir, matched_file):
                    match = None

        return super().split_match(match)

    def is_current_file(self, working_dir, matched_file):
        """
        Return true if `matched_file` is logically the same file as `self.filename`.

        Cargo example demonstrating how matching is done:

          - os.getcwd() = '/Applications/Sublime Text.app/Contents/MacOS'
          - `working_dir` = '/path/to/project'
          - `matched_file` = 'src/foo.rs'
          - `self.filename` = '/path/to/project/src/foo.rs'

        The current OS directory is not considered at all -- comparison is only done
        relative to where Cargo.toml was found.  `os.path.realpath` is used to
        normalize the filenames so that they can be directly compared after manipulation.
        """
        abs_matched_file = os.path.join(working_dir, matched_file)

        persist.debug('Sublime Text cwd: ', os.getcwd())
        persist.debug('Build cwd: ', working_dir)
        persist.debug('Current filename: ', self.filename)
        persist.debug('Matched filename: ', matched_file)
        persist.debug('Compared filename: ', abs_matched_file)

        return os.path.realpath(self.filename) == os.path.realpath(abs_matched_file)

    def locate_crate_root(self):
        """
        Return the filename of the crate root.

        The filename may be manually set in a configuration file (highest priority),
        or it is located by convention.

        When no configuration is set, main.rs will take preference over lib.rs.
        If neither main.rs or lib.rs are found, give up.
        """
        crate_root = self.get_view_settings().get('crate-root', None)

        if not crate_root:
            crate_root = util.find_file(os.path.dirname(self.filename), 'main.rs')

        if not crate_root:
            crate_root = util.find_file(os.path.dirname(self.filename), 'lib.rs')

        return crate_root
