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
import six

from rebasehelper.plugins import Plugin
from rebasehelper.logger import logger_output
from rebasehelper.results_store import results_store
from rebasehelper.constants import RESULTS_DIR, REPORT


class BaseOutputTool(Plugin):
    """
    Base class for OutputTools.
    print_cli_summary must be overridden in order to produce different CLI output
    """

    DEFAULT = False
    EXTENSION = ''

    @classmethod
    def get_report_path(cls, app):
        return os.path.join(app.results_dir, REPORT + '.' + cls.EXTENSION)

    @classmethod
    def prepend_results_dir_name(cls, *path_members):
        return os.path.join(RESULTS_DIR, *path_members)

    @classmethod
    def print_cli_summary(cls, app):
        """
        Print report of the rebase

        :param app: Application instance
        """
        cls.app = app
        cls.print_patches_cli()
        result = results_store.get_result_message()

        cls.print_important_checkers_output()

        logger_output.heading('\nAvailable logs:')
        logger_output.info('%s:\n%s', 'Debug log', cls.prepend_results_dir_name(app.debug_log_file))
        if results_store.get_old_build() is not None:
            logger_output.info('%s:\n%s', 'Old build logs and (S)RPMs', cls.prepend_results_dir_name('old-build'))
        if results_store.get_new_build() is not None:
            logger_output.info('%s:\n%s', 'New build logs and (S)RPMs', cls.prepend_results_dir_name('new-build'))
        logger_output.info('')

        logger_output.heading('%s:', 'Rebased sources')
        logger_output.info("%s", cls.prepend_results_dir_name(os.path.relpath(app.rebased_sources_dir,
                                                                              app.results_dir)))

        patch = results_store.get_changes_patch()
        if 'changes_patch' in patch:
            logger_output.heading('%s:', 'Generated patch')
            logger_output.info("%s\n", cls.prepend_results_dir_name(os.path.basename(patch['changes_patch'])))

        cls.print_report_file_path()

        if not app.conf.patch_only:
            if 'success' in result:
                logger_output.success('\n%s' % result['success'])
            # Error is printed out through exception caught in CliHelper.run()
        else:
            if results_store.get_patches()['success']:
                logger_output.success("\nPatching successful")
            elif results_store.get_patches()['success']:
                logger_output.error("\nPatching failed")

    @classmethod
    def print_important_checkers_output(cls):
        """Iterates over all checkers output to highlight important checkers warning"""
        checkers_results = results_store.get_checkers()
        for check_tool in six.itervalues(cls.runner.checkers):
            for check, data in sorted(six.iteritems(checkers_results)):
                if check == check_tool.name:
                    out = check_tool.get_important_changes(data)
                    if out:
                        logger_output.warning('\n'.join(out))

    @classmethod
    def print_report_file_path(cls):
        """Print path to the report file"""
        logger_output.heading('%s report:' % cls.name)
        logger_output.info('%s', cls.prepend_results_dir_name('report.' + cls.EXTENSION))

    @classmethod
    def print_patches_cli(cls):
        """Print info about patches"""
        patch_dict = {
            'inapplicable': logger_output.error,
            'modified': logger_output.success,
            'deleted': logger_output.success,
        }

        for patch_type, logger_method in six.iteritems(patch_dict):
            cls.print_patches_section_cli(logger_method, patch_type)

    @classmethod
    def print_patches_section_cli(cls, logger_method, patch_type):
        """
        Print info about one of the patches key section

        :param logger_method: method to be used for logging
        :param patch_type: string containing key for the patch_dict
        """
        patches = results_store.get_patches()
        if not patches:
            return

        if patch_type in patches:
            logger_output.info('\n%s patches:', patch_type)
            for patch in sorted(patches[patch_type]):
                logger_method(patch)

    @classmethod
    def run(cls, logs, app):  # pylint: disable=unused-argument
        raise NotImplementedError()
