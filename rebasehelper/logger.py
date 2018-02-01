# -*- coding: utf-8 -*-
#
# This tool helps you to rebase package to the latest version
# Copyright (C) 2013-2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation; either version 2 of the License, or
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

import logging


class LoggerHelper(object):
    """
    Helper class for setting up a logger
    """

    @staticmethod
    def get_basic_logger(logger_name, level=logging.DEBUG):
        """
        Sets-up a basic logger without any handler

        :param logger_name: Logger name
        :param level: severity level
        :return: created logger
        """
        basic_logger = logging.getLogger(logger_name)
        basic_logger.setLevel(level)
        return basic_logger

    @staticmethod
    def add_stream_handler(logger_object, level=None):
        """
        Adds console handler with given severity.

        :param logger_object: logger object to add the handler to
        :param level: severity level
        :return: created handler object
        """
        console_handler = logging.StreamHandler()
        if level:
            console_handler.setLevel(level)
        logger_object.addHandler(console_handler)
        return console_handler

    @staticmethod
    def add_file_handler(logger_object, path, formatter_object=None, level=None):
        """
        Adds FileHandler to a given logger

        :param logger_object: Logger object to which the file handler will be added
        :param path: Path to file where the debug log will be written
        :return: None
        """
        file_handler = logging.FileHandler(path, 'w')
        if level:
            file_handler.setLevel(level)
        if formatter_object:
            file_handler.setFormatter(formatter_object)
        logger_object.addHandler(file_handler)


#  the main rebase-helper logger
logger = LoggerHelper.get_basic_logger('rebase-helper')
#  logger for output tool
logger_output = LoggerHelper.get_basic_logger('output-tool', logging.INFO)
logger_report = LoggerHelper.get_basic_logger('rebase-helper-report', logging.INFO)
logger_upstream = LoggerHelper.get_basic_logger('rebase-helper-upstream')
LoggerHelper.add_stream_handler(logger_output)
formatter = logging.Formatter("%(asctime)s %(levelname)s\t: %(message)s")
