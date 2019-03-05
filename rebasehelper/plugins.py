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

import six

import pkg_resources

from rebasehelper.logger import logger
from rebasehelper.results_store import results_store


class Plugin(object):
    name = None
    runner = None


class PluginLoader(object):
    @classmethod
    def load(cls, entrypoint, runner):
        """Loads an entrypoint from setup.py.

        Args:
            entrypoint (str): Entrypoint to be loaded.
            runner (PluginRunner): PluginRunner instance to be set
                as an attribute of Plugin instance.

        Returns:
            dict: Loaded entrypoints.

        """
        result = {}
        for ep in pkg_resources.iter_entry_points(entrypoint):
            result[ep.name] = None
            try:
                plugin = ep.load()
            except ImportError:
                # skip broken plugin
                continue
            try:
                if not issubclass(plugin, Plugin):
                    raise TypeError
            except TypeError:
                # skip broken plugin
                continue
            else:
                plugin.name = ep.name
                # Some plugins require access to other plugins. Avoid cyclic
                # imports by setting runner as an attribute.
                plugin.runner = runner
            result[ep.name] = plugin
        return result


class PluginRunner(object):
    PLUGIN_ENTRYPOINTS = {
        'build_tools': 'rebasehelper.build_tools',
        'srpm_build_tools': 'rebasehelper.srpm_build_tools',
        'checkers': 'rebasehelper.checkers',
        'spec_hooks': 'rebasehelper.spec_hooks',
        'build_log_hooks': 'rebasehelper.build_log_hooks',
        'versioneers': 'rebasehelper.versioneers',
        'output_tools': 'rebasehelper.output_tools',
    }

    def __init__(self):
        self.plugins = {}
        for entrypoint_name, entrypoint in six.iteritems(self.PLUGIN_ENTRYPOINTS):
            self.plugins[entrypoint_name] = PluginLoader.load(entrypoint, self)

    def __getattr__(self, plugin_type):
        return self.plugins.get(plugin_type)

    def get_all_tools(self, plugin_type):
        return list(self.plugins[plugin_type])

    def get_supported_tools(self, plugin_type):
        return [k for k, v in six.iteritems(self.plugins[plugin_type]) if v]

    def get_default_tools(self, plugin_type, return_one=False):
        default = [k for k, v in six.iteritems(self.plugins[plugin_type]) if v and getattr(v, 'DEFAULT', False)]
        return default if not return_one else default[0] if default else None

    def get_build_tool(self, tool):
        try:
            return self.plugins['build_tools'][tool]
        except KeyError:
            raise NotImplementedError("Unsupported RPM build tool")

    def get_srpm_build_tool(self, tool):
        try:
            return self.plugins['srpm_build_tools'][tool]
        except KeyError:
            raise NotImplementedError("Unsupported SRPM build tool")

    def run_checker(self, results_dir, checker_name, **kwargs):
        """Runs a particular checker and returns the results.

        Args:
            results_dir (str): Path to a directory in which the checker
                should store the results.
            checker_name (str): Name of the checker to run.

        Raises:
            NotImplementedError: If a checker with the given name doesn't
                exist.

        Returns:
            Results of the checker.

        """
        try:
            checker = self.plugins['checkers'][checker_name]
        except KeyError:
            return None
        if checker.CATEGORY != kwargs.get('category'):
            return None

        logger.info("Running checks on packages using '%s'", checker_name)
        return checker.run_check(results_dir, **kwargs)

    def run_spec_hooks(self, spec_file, rebase_spec_file, **kwargs):
        """Runs all non-blacklisted spec hooks.

        Args:
            spec_file (rebasehelper.specfile.SpecFile): Original SpecFile object.
            rebase_spec_file (rebasehelper.specfile.SpecFile): Rebased SpecFile object.
            **kwargs: Keyword arguments from Application instance.

        """
        blacklist = kwargs.get("spec_hook_blacklist", [])

        for name, spec_hook in six.iteritems(self.spec_hooks):
            if not spec_hook or name in blacklist:
                continue
            categories = spec_hook.CATEGORIES
            if not categories or spec_file.category in categories:
                logger.info("Running '%s' spec hook", name)
                spec_hook.run(spec_file, rebase_spec_file, **kwargs)

    def run_build_log_hooks(self, spec_file, rebase_spec_file, non_interactive, force_build_log_hooks, **kwargs):
        """Runs all non-blacklisted build log hooks.

        Args:
            spec_file (rebasehelper.specfile.SpecFile): Original SpecFile object.
            rebase_spec_file (rebasehelper.specfile.SpecFile): Rebased SpecFile object.
            non_interactive (bool): Whether rebase-helper is in non-interactive mode.
            force_build_log_hooks (bool): Whether to run the hooks even in
                non-interactive mode.
            kwargs (dict): Keyword arguments from instance of Application.

        Returns:
            bool: Whether build log hooks made some changes to the SPEC file.

        """
        changes_made = False
        if not non_interactive or force_build_log_hooks:
            blacklist = kwargs.get('build_log_hook_blacklist', [])
            for name, build_log_hook in six.iteritems(self.build_log_hooks):
                if not build_log_hook or name in blacklist:
                    continue
                categories = build_log_hook.CATEGORIES
                if not categories or spec_file.category in categories:
                    logger.info('Running %s build log hook.', name)
                    result, rerun = build_log_hook.run(spec_file, rebase_spec_file, **kwargs)
                    result = build_log_hook.merge_two_results(results_store.get_build_log_hooks().get(name, {}), result)
                    results_store.set_build_log_hooks_result(name, result)
                    if rerun:
                        changes_made = True
        return changes_made

    def run_versioneer(self, versioneer, package_name, category, versioneer_blacklist=None):
        """Runs specified versionner or all versioneers subsequently until
        one of them succeeds.

        Args:
            versioneer (str): Name of a versioneer.
            package_name (str): Name of a package.
            category (str): Package category.
            versioneer_blacklist (list): List of versioneers that will be skipped.

        Returns:
            str: Latest upstream version of a package.

        """
        if versioneer_blacklist is None:
            versioneer_blacklist = []

        if versioneer:
            logger.info("Running '%s' versioneer", versioneer)
            return self.versioneers[versioneer].run(package_name)
        # run all versioneers, except those disabled in config, categorized first
        allowed_versioneers = [v for k, v in six.iteritems(self.versioneers) if v and k not in versioneer_blacklist]
        for versioneer in sorted(allowed_versioneers, key=lambda v: not v.CATEGORIES):
            categories = versioneer.CATEGORIES
            if not categories or category in categories:
                logger.info("Running '%s' versioneer", versioneer.name)
                result = versioneer.run(package_name)
                if result:
                    return result
        return None

    def run_output_tool(self, tool, logs=None, app=None):
        """Runs the specified output tool.

        Args:
            tool (str): Tool to run.
            logs (list): Build logs containing information about the failed rebase.
            app (rebasehelper.application.Application): Application class instance.

        """
        output_tool = self.output_tools[tool]
        logger.info("Running '%s' output tool.", tool)
        output_tool.run(logs, app=app)
        output_tool.print_cli_summary(app)


# Global instance of PluginRunner. It is enough to load it once per application run.
plugin_runner = PluginRunner()
