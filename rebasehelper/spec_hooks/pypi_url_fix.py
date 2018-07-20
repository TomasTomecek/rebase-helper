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

import re

from rebasehelper.specfile import BaseSpecHook


class PyPIURLFixHook(BaseSpecHook):
    """SpecHook for transforming an old python package URL to a new URL
    (e.g. https://pypi.python.org/packages/* to
    https://files.pythonhosted.org/packages/* or https://pypi.python.org/pypi/*
    to https://pypi.org/project/*).

    """

    NAME = 'PyPI URL Fix'
    CATEGORIES = ['python']
    URL_TRANSFORMATIONS = [
        (r'https?://pypi\.python\.org/pypi/', 'https://pypi.org/project/'),
    ]
    SOURCES_URL_TRANSFORMATIONS = [
        (r'https?://pypi(\.python)?\.org/', 'https://files.pythonhosted.org/'),
    ]

    @classmethod
    def get_name(cls):
        return cls.NAME

    @classmethod
    def get_categories(cls):
        return cls.CATEGORIES

    @classmethod
    def run(cls, spec_file, rebase_spec_file, **kwargs):
        for index, line in enumerate(rebase_spec_file.spec_content.sections['%package']):
            if line.startswith("URL"):
                rebase_spec_file.spec_content.sections['%package'][index] = cls._transform_url(line)
            elif line.startswith("Source"):
                rebase_spec_file.spec_content.sections['%package'][index] = cls._transform_sources_url(line)
        rebase_spec_file.save()

    @classmethod
    def _transform_url(cls, line):
        for trans in cls.URL_TRANSFORMATIONS:
            line = re.sub(trans[0], trans[1], line)
        return line

    @classmethod
    def _transform_sources_url(cls, line):
        for trans in cls.SOURCES_URL_TRANSFORMATIONS:
            line = re.sub(trans[0], trans[1], line)
        return line
