import sys
import os
import glob
from datetime import datetime
import logging
from time import time
from rsync_history_backup.utils import Helper


class BackupInfo():

    def __init__(self, location, name):
        self.logger = logging.getLogger("rhb.BackupInfo")

        if not os.path.isdir(location):
            raise FileNotFoundError("The given location does not exist. " +
                                    "Make sure your device is mounted.")
        self.location = location
        self.name = name
        self.time_stamp = '%Y-%m-%d %H-%M-%S'
        self.save_history = (True if os.path.exists(self.history_dir) and
                             os.listdir(self.history_dir) else False)
        self.runs = None

    @property
    def size_human_readable(self):
        return Helper.size_human_readable(self.size)

    @property
    def log_dir(self):
        return os.path.join(self.location, 'log', self.name)

    @property
    def history_dir(self):
        return os.path.join(self.location, 'history', self.name)

    @property
    def current_dir(self):
        return os.path.join(self.location, 'current', self.name)

    def get_file_info(self, file_name, version=None):
        file_name = file_name.replace(self.current_dir + '/', '')
        if version and version not in ['current', 'None']:
            path = os.path.join(self.history_dir, version, file_name)
        else:
            path = os.path.join(self.current_dir, file_name)
        return {
            'name': os.path.basename(path),
            'mime_type': magic.from_file(path, mime=True).decode('utf-8'),
            'size': os.path.getsize(path),
            'size_human_readable':
                Helper.size_human_readable(os.path.getsize(path)),
            'versions': self.get_file_versions(file_name),
            'abs_path': path
        }

    def get_file_content(self, file_name, version=None):
        if version and version not in ['current', 'None']:
            path = os.path.join(self.history_dir, version, file_name)
        else:
            path = os.path.join(self.current_dir, file_name)
        if not os.path.isfile(path) or os.path.getsize(path) > (20 * 1024**2):
            return None

        f = open(path, 'r')
        content = f.read()
        f.close()

        return content

    def get_file_versions(self, file_path):
        """

            :file_path:
                ``string``;
                path to file relativ from the current/ root.
        """
        return self.get_files_versions([file_path])[file_path]

    def get_files_versions(self, file_paths):
        """

            :file_paths:
                ``tuple``;
                paths to file relativ from the current/ root.
        """
        res = {file_path: [] for file_path in file_paths}
        if not os.path.exists(self.history_dir):
            return res
        for dt in os.listdir(self.history_dir):
            dirname = os.path.join(self.history_dir, dt)
            for file_path in file_paths:
                if os.path.exists(os.path.join(dirname, file_path)):
                    res[file_path].append(dt)
        return res

    def serialize(self):
        param = vars(self)
        for key in param:
            if type(param[key]) is datetime:
                param[key] = param[key].strftime(self.time_stamp)
        return param
