# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import logging
import json
import re
from datetime import datetime
from tempfile import mkstemp

if sys.version_info < (3, 0):
    raise RuntimeError("Must use python 3.0 or greater.")


class RsyncBackup:

    def __init__(self, source, destination,
                 name=None, rsync_exe='rsync', exclude_file='',
                 save_history=True, local_history=False,
                 sync_options=["--recursive", "--update", "--delete",
                               "--owner", "--group", "--times", "--links",
                               "--safe-links", "--super", "--one-file-system",
                               "--devices"],
                 hist_options=["--update", "--owner", "--group", "--times",
                               "--links", "--super"]):
        self.time_format = r'%Y-%m-%d %H-%M-%S'
        self.logger = logging.getLogger("rhb.RsyncBackup")
        self.source = os.path.abspath(source) + '/'
        # if not os.path.exists(destination):
        #     raise FileNotFoundError(
        #         "the backup location does not exist." +
        #         " Please check if your device is mounted"
        #     )
        self.destination = os.path.abspath(destination)
        self.name = name if name else os.path.basename(source)
        self.rsync_exe = rsync_exe
        self.save_history = save_history
        self.local_history = local_history
        if self.local_history:
            self.exclude_option = ['--include=/.rhb/history/',
                                   '--include=/.rhb/log/', '--exclude=/.rhb/*']
        else:
            self.exclude_option = ['--exclude=/.rhb/']
        if exclude_file and os.path.isfile(exclude_file):
            self.logger.debug("Using user exclude file.")
            self.exclude_option += ['--exclude-from={}'.format(exclude_file)]
        elif os.path.isfile(os.path.join(self.source, 'rsync-ignore.txt')):
            self.logger.debug("Default exclude file found.")
            self.exclude_option += ['--exclude-from={}'.format(
                os.path.join(self.source, 'rsync-ignore.txt'))]
        else:
            self.logger.debug("No exclude file found.")
        self.sync_options = sync_options + self.exclude_option
        self.hist_options = hist_options
        self.time_stamp = None
        self.dryrun = None
        self.change_log = None

    @staticmethod
    def load_config_file(file_object):
        """
        """
        logger = logging.getLogger('rhb.RsyncBackup.load_config_file()')
        logger.debug(' - [load_config_file() called.]')
        cfg = json.load(file_object)
        if not 'destination' not in cfg and \
                ('source' not in cfg and 'sources' not in cfg):
            raise Exception("Config file is invalid.")
        if 'source' in cfg:
            logger.debug('Single source found.')
            return RsyncBackup(**cfg)
        elif 'sources' in cfg:
            logger.debug('Multiple sources found.')
            res = []
            for src in cfg['sources']:
                tmp = cfg.copy()
                tmp.pop('sources', None)
                res.append(RsyncBackup(**dict(set(tmp) & set(src))))
            return res
        return None

    @property
    def current_dir(self):
        """Returns the path to the backups current directory."""
        # return os.path.join(self.destination, 'current', self.name)
        return os.path.join(self.destination, self.name)

    @property
    def history_dir(self):
        """Returns the path to the backups history directory."""
        # return os.path.join(self.destination, 'history', self.name)
        if self.local_history:
            return os.path.join(self.source, '.rhb', 'history')
        return os.path.join(self.destination, self.name, '.rhb', 'history')

    @property
    def log_dir(self):
        """Returns the path to the backups log directory."""
        # return os.path.join(self.destination, 'log', self.name)
        if self.local_history:
            return os.path.join(self.source, '.rhb', 'log')
        return os.path.join(self.destination, self.name, '.rhb', 'log')

    @property
    def local_settings_dir(self):
        """Returns the path to the local settings directory in the source
        folder."""
        return os.path.join(self.source, '.rhb')

    @property
    def history_time_stamp_dir(self):
        """Returns the history directory with the current time stamp as
        subfolder."""
        if not self.time_stamp:
            raise ValueError('Variable time_stamp has not been initialized! ' +
                             'This is a bug and should happen automatically.')
        return os.path.join(self.history_dir, self.time_stamp)

    def _run_rsync(self, source, destination, options=[], check_output=True):
        """Run rsync.

        * Parameters:

            :source:
                ``string``;
                path to the source folder.

            :destination:

                ``string``;
                path to the destination folder.

            :options:
                ``list``;
                list of all rsync options which should be set.

            :check_output:
                ``bool``;
                if ``True`` the rsync process will be started as a subprocess
                and it's console output will be piped and then returned.
                If ``False`` the rsync console output is piped to
                ``std::out``

        * Return:

            If ``check_output`` is ``True`` the rsync console output else
            it will return ``True`` when process is finished.
        """

        self.logger.debug(' - [_run_rsync() called.]')
        # print(self.rsync_exe, ' '.join(options + [source, destination]))

        if not check_output:
            os.system(' '.join([self.rsync_exe] + options +
                      [source, destination]))
            return True

        return subprocess.check_output(
            [self.rsync_exe] + options +
            [source, destination]
        )

    def _get_changes(self):
        self.logger.debug(' - [_get_changes() called.]')
        self.logger.info("Looking for changes.")
        if not os.path.exists(self.current_dir):
            os.makedirs(self.current_dir)
        options = ['--dry-run', '--itemize-changes', '--out-format="%i|%n|"'] \
            + self.sync_options

        self.time_stamp = datetime.now().strftime(self.time_format)
        dryrun = self._run_rsync(self.source, self.current_dir, options)
        dryrun = dryrun.decode("utf-8") \
            .replace('"', '') \
            .replace('.d..t......|./|\n', '')

        self.dryrun = dryrun
        if not dryrun:
            self.logger.info(" -> no changes found.")
            return False
        self.change_log = self.__get_change_log(dryrun)
        self.logger.info(
            " -> {} change(s) found.".format(len(dryrun.split('\n')) - 1)
        )
        return self.change_log

    def __get_change_log(self, dryrun_text):
        self.logger.debug(' - [__get_change_log() called.]')
        regs = {
            'created': '[\>fcd]{2}[\.\+]{9}\|(.*)\|',
            'deleted': '\*deleting  \|(.*)\|',
            'changed': '[\>f\.st]{11}\|(.*)\|'
        }
        res = {}
        for reg_name in regs.keys():
            reg = re.compile(regs[reg_name])
            res[reg_name] = [el for el in reg.findall(dryrun_text) if el]

        return res

    def _save_file_logs(self, change_log):
        self.logger.debug(' - [_save_file_logs() called.]')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        file_name = "{}.json".format(self.time_stamp)
        json.dump(change_log,
                  open(os.path.join(self.log_dir, file_name), 'w'))

        # if self.save_dryrun and self.dryrun:
        #     file_name = '{}.{}'.format(self.time_stamp, 'dryrun')
        #     fl = open(os.path.join(self.log_dir, file_name), 'w+')
        #     fl.write(self.dryrun)
        #     fl.flush()
        #     fl.close()
        # else:
        #     self.logger.warning(
        #         "Not saving the 'dryrun' file might cause problems.")
        #
        # for k in change_log.keys():
        #     if not change_log[k]:
        #         continue
        #
        #     file_name = '{}.{}'.format(self.time_stamp, k)
        #     fl = open(os.path.join(self.log_dir, file_name), 'w+')
        #     fl.write('\n'.join(change_log[k]))
        #     fl.flush()
        #     fl.close()
        self.logger.debug("Log file saved.")
        return True

    def _move_to_history(self, change_log):
        self.logger.debug(' - [_move_to_history() called.]')
        if not self.save_history:
            return False
        if not len(change_log['deleted'] + change_log['changed']) > 0:
            self.logger.debug("No files need to be moved to the history.")
            return True

        self.logger.info("Move deleted or changed files to history.")

        if not os.path.isdir(self.history_dir):
            os.mkdir(self.history_dir)

        if not os.path.isdir(self.history_time_stamp_dir):
            os.mkdir(self.history_time_stamp_dir)

        tmp_list = '\n'.join(sorted(
            change_log['deleted'] + change_log['changed']
        ))
        fd, file_name = mkstemp()
        tmp_file = open(file_name, 'w')
        tmp_file.write(tmp_list)
        tmp_file.flush()
        tmp_file.close()
        self.logger.debug(" -> tempfile written: {}".format(file_name))

        options = self.hist_options + ['--files-from={}'.format(file_name)]

        out = self._run_rsync(self.current_dir, self.history_time_stamp_dir,
                              options)
        self.logger.debug(" -> files moved.")
        os.close(fd)
        os.remove(file_name)
        self.logger.debug(" -> tempfile deleted.")
        return out

    def _new_backup(self):
        self.logger.info("Starting backup:")
        options = self.sync_options + ['--info=progress2']
        out = self._run_rsync(self.source, self.current_dir, options, False)
        self.logger.info(" -> backup finished.")
        return out

    def run_backup(self):
        """Run an entire backup with the given configuration"""

        self.logger.debug("Starting backup of '{}'.".format(self.source))

        self.dry_run()
        if not self.change_log:
            return True

        self._save_file_logs(self.change_log)
        self._move_to_history(self.change_log)
        self._new_backup()
        # self.logger.debug('Backup finished.')
        return True

    def dry_run(self):
        """Start a dry run which only shows the changes since the last backup.

        * Return:

            ``dict``;
            This returns a dictionary with the keys: 'created', 'changed' and
            'deleted'. Their values are a ``list`` containing all corresponding
            files.
        """
        self.logger.debug("Starting dry run for {}...".format(self.source))
        if not os.path.exists(self.destination):
            raise FileNotFoundError(
                "The backup location does not exist. " +
                "Please check if your device is mounted."
            )

        if not os.path.exists(self.current_dir):
            os.makedirs(self.current_dir)

        out = self._get_changes()
        self.logger.debug(' -> dry run done.')
        return out
