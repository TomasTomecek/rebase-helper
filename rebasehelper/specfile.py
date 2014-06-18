try:
    from functools import reduce
except ImportError:
    pass # we're on Python 2 => ok
import os
try:
    import rpm
except ImportError:
    pass
import shutil
import mimetypes
from rebasehelper.utils import ProcessHelper
from rebasehelper.logger import logger
from rebasehelper import settings
from rebasehelper.utils import get_content_file,  write_to_file
from rebasehelper.utils import get_temporary_name, remove_temporary_name


def get_source_name(name):
    new_name = name.split('/')[-1]
    return new_name


def get_rebase_name(name):
    """
    Function returns a name in results directory
    :param name:
    :return: full path to results dir with name
    """
    dir_name = os.path.dirname(name)
    file_name = os.path.basename(name)
    return os.path.join(dir_name, settings.REBASE_RESULTS_DIR, file_name)


class SpecFile(object):
    """
    Class who manipulates with SPEC file
    """
    values = []

    def __init__(self, specfile, new_sources, download=True):
        self.spec_file = specfile
        self.download = download
        self.rebased_spec = get_rebase_name(specfile)
        if os.path.exists(self.rebased_spec):
            os.unlink(self.rebased_spec)
        shutil.copy(self.spec_file, self.rebased_spec)
        self.old_spc = rpm.spec(self.spec_file)
        self.new_spc = rpm.spec(self.rebased_spec)
        self.new_sources = new_sources

    def get_patch_option(self, line):
        """
        Function returns a patch options
        :param line:
        :return: patch options like -p1
        """
        spl = line.strip().split()
        if len(spl) == 1:
            return spl[0], " "
        elif len(spl) == 2:
            return spl[0], spl[1]
        else:
            return spl[0], spl[1]

    def get_rebased_spec(self):
        """
        Function returns rebase.spec file
        """
        return self.rebased_spec

    def get_patch_number(self, line):
        """
        Function returns patch number
        :param line:
        :return: patch_num
        """
        fields = line.strip().split()
        patch_num = fields[0].replace('Patch', '')[:-1]
        return patch_num

    def get_content_rebase(self):
        """
        Function reads a content rebase.spec file
        """
        lines = get_content_file(self.get_rebased_spec(), "r", method=True)
        return lines

    def get_patches_flags(self):
        """
        For all patches: get flags passed to %patch macro and index of application
        """
        patch_flags = {}
        lines = self.get_content_rebase()
        lines = [x for x in lines if x.startswith(settings.PATCH_PREFIX)]
        for index, line in enumerate(lines):
            num, option = self.get_patch_option(line)
            num = num.replace(settings.PATCH_PREFIX, '')
            patch_flags[int(num)] = (option, index)
        # {num: (flags, index of application)}
        return patch_flags

    def _get_version_from_spec(self, spec_file):
        hdr = spec_file.sourceHeader
        version = hdr[rpm.RPMTAG_VERSION]
        if not version:
            return None
        return version

    def get_spec_versions(self):
        """
        Function return an old and a new versions
        :return:
        """
        old_version = self._get_version_from_spec(self.old_spc)
        new_version = self._get_version_from_spec(self.new_spc)
        return [old_version, new_version]

    def get_package_name(self):
        hdr = self.new_spc.sourceHeader
        return hdr[rpm.RPMTAG_NAME]

    def is_patch_git_generated(self, full_patch_name):
        """
        Return:
          True if patch is generated by git ('git diff' or 'git format-patch')
          False means patch is generated by gendiff or somehow else.
        """
        with open(full_patch_name) as f:
            for line in f:
                if line.startswith("diff "):
                    if line.startswith("diff --git"):
                        return True
                    else:
                        return False
        return False

    def get_patches(self):
        """
        Function returns a list of patches from a spec file
        """
        patches = {}
        patch_flags = self.get_patches_flags()
        cwd = os.getcwd()
        sources = [x for x in self.new_spc.sources if x[2] == 2]
        for source in sources:
            filename, num, patch_type = source
            full_patch_name = os.path.join(cwd, filename)
            if not os.path.exists(full_patch_name):
                logger.error('Patch {0} does not exist'.format(filename))
                continue
            if num in patch_flags:
                patches[num] = [full_patch_name, patch_flags[num][0], \
                                patch_flags[num][1], self.is_patch_git_generated(full_patch_name)]
        # list of [name, flags, index, git_generated]
        return patches

    def get_sources(self):
        """
        Function returns a all sources
        """
        sources = [x for x in self.new_spc.sources if x[2] == 0 or x[2] == 1]
        return sources

    def _download_source(self, source_name, download_name):
        """
        Function downloads a source name defined in SPEC file
        """
        if not self.download:
            return
        if not os.path.exists(download_name):
            ret_code = ProcessHelper.run_subprocess_cwd('wget {0}'.format(source_name), shell=True)

    def get_all_sources(self):
        """
        Function returns all sources mentioned in specfile
        """
        cwd = os.getcwd()
        sources = self.get_sources()
        remote_files = ['http:', 'https:', 'ftp:']
        for index, src in enumerate(sources):
            new_name = get_source_name(src[0])
            if int(src[1]) == 0:
                sources[index] = os.path.join(cwd, new_name)
            else:
                remote = [x for x in remote_files if src[0].startswith(x)]
                if remote:
                    self._download_source(src[0], new_name)
                sources[index] = os.path.join(cwd, new_name)
        return sources

    def get_old_tarball(self):
        """
        Function returns a old sources from specfile
        """
        sources = self.get_sources()
        old_source_name = [x for x in sources if x[1] == 0]
        old_source_name = old_source_name[0][0]
        source_name = get_source_name(old_source_name)
        self._download_source(old_source_name, source_name)
        return source_name

    def get_new_tarball(self):
        """
        Function gets a new tarball if it does not exist.
        """
        sources = self.get_sources()
        new_source_name = [x for x in sources if x[1] == 0]
        new_source_name = new_source_name[0][0]
        url_path = new_source_name.split('/')[:-1]
        url_path.append(self.new_sources)
        if not os.path.exists(self.new_sources):
            self._download_source('/'.join(url_path), self.new_sources)

    def check_empty_patches(self, patch_name):
        """
        Function checks whether patch is empty or not
        """
        cmd = []
        cmd.append("/usr/bin/lsdiff")
        cmd.append(patch_name)
        temp_name = get_temporary_name()
        ret_code = ProcessHelper.run_subprocess(cmd, temp_name)
        if ret_code != 0:
            return False
        lines = get_content_file(temp_name)
        remove_temporary_name(temp_name)
        if not lines:
            return True
        else:
            return False

    def remove_empty_patches(self, lines, patch_num):
        """
        Remove ampty patches from SPEC file
        """
        for num in patch_num:
            for index, line in enumerate(lines):
                if not line.startswith('%patch{0}'.format(num)):
                    continue
                lines[index] = '#' + line

    def write_updated_patches(self, **kwargs):
        """
        Function writes a patches to -rebase.spec file
        """
        if 'new' not in kwargs:
            return None
        new_files = kwargs.get('new', None)
        if 'patches' not in new_files:
            return None
        patches = new_files.get('patches', None)

        logger.debug('Patches:{0}'.format(patches))
        lines = self.get_content_rebase()
        removed_patches = []
        for index, line in enumerate(lines):
            # We take care about patches.
            if not line.startswith('Patch'):
                continue
            fields = line.strip().split()
            patch_num = self.get_patch_number(line)
            patch_name = patches[int(patch_num)][0]
            comment = ""
            if self.check_empty_patches(patch_name):
                comment = '#'
                removed_patches.append(patch_num)
                del patches[int(patch_num)]
            lines[index] = comment + ' '.join(fields[:-1]) + ' ' + os.path.basename(patch_name) +'\n'
        self.remove_empty_patches(lines, removed_patches)

        write_to_file(self.get_rebased_spec(), "w", lines)