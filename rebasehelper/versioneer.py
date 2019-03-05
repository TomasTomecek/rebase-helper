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

from rebasehelper.plugins import Plugin


class BaseVersioneer(Plugin):
    """Base class for a versioneer"""

    # versioneer categories, see PACKAGE_CATEGORIES in constants for a complete list
    CATEGORIES = None

    @classmethod
    def run(cls, package_name):
        """
        Runs a versioneer.

        :param package_name: Name of a package
        :return: Latest upstream version of a package
        """
        raise NotImplementedError()
