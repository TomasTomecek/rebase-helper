# -*- coding: utf-8 -*-
#
# This tool helps you to rebase package to the latest version
# Copyright (C) 2013-2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Petr Hracek <phracek@redhat.com>
#          Tomas Hozza <thozza@redhat.com>

import os


from rebasehelper.plugins import Plugin
from rebasehelper.constants import RESULTS_DIR


class BaseChecker(Plugin):
    """Base class of package checkers.

    Attributes:
        DEFAULT(bool): If True, the checker is run by default.
        CATEGORY(str): Category which determines when the checker is run. Valid options: SRPM/RPM/SOURCE.
        results_dir(str): Path where the results are stored.
    """

    DEFAULT = False
    CATEGORY = None
    results_dir = None

    @classmethod
    def get_checker_output_dir_short(cls):
        """Return short version of checker output directory"""
        return os.path.join(RESULTS_DIR, 'checkers', cls.name)

    @classmethod
    def is_available(cls):
        raise NotImplementedError()

    @classmethod
    def run_check(cls, results_dir, **kwargs):
        """Perform the check itself and return results."""
        raise NotImplementedError()

    @classmethod
    def format(cls, data):
        """Formats checker output to a readable text form."""
        raise NotImplementedError()

    @classmethod
    def get_category(cls):
        return cls.CATEGORY

    @classmethod
    def get_underlined_title(cls, text, separator='='):
        return "\n{}\n{}".format(text, separator * len(text))

    @classmethod
    def get_important_changes(cls, checker_output):
        """
        Each checker has an opportunity to highlight some of its output.
        This function is optional, as not all checkers provide output with critical information.

        Args:
            checker_output (dict): Dictionary with output from the given checker.

        Returns:
            list: List of strings to be output to CLI as warning messages.
        """
