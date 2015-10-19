import os
# import magic
import sys
import numbers
import collections
import logging
if os.name == 'nt':       # Windows
    import ctypes


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def colorize(text, color=None):
        if color in bcolors.__dict__:
            return bcolors.__dict__[color] + text + bcolors.ENDC
        return text


class Helper:

    @staticmethod
    def size_human_readable(size, unit=None, ndigits=2):
        """Converts a given byte size to a human readable format."""
        units = ['byte(s)', 'KB', 'MB', 'GB', 'TB']
        if unit is not None and unit in units:
            return round(size / 1024**units.index(unit), ndigits)
        format_string = '%.' + str(ndigits) + 'f %s'
        for i in range(len(units)):
            if size / 1024**i < 100:
                return format_string % (float(size / (1024**i)), units[i])

    @staticmethod
    def get_size(obj):
        """Recursive function to dig out sizes of member objects."""
        def inner(obj, _seen_ids=set()):
            obj_id = id(obj)
            if obj_id in _seen_ids:
                return 0
            _seen_ids.add(obj_id)
            size = sys.getsizeof(obj)
            if isinstance(obj, (str, numbers.Number, range)):
                pass  # bypass remaining control flow and return
            elif isinstance(obj, (tuple, list, set, frozenset)):
                size += sum(inner(i) for i in obj)
            elif isinstance(obj, collections.Mapping) or hasattr(obj, 'items'):
                size += sum(inner(k) + inner(v) for k, v in obj.items())
            else:
                attr = getattr(obj, '__dict__', None)
                if attr is not None:
                    size += inner(attr)
            return size
        return inner(obj)

    @staticmethod
    def disk_usage(path):
        """Get the disk usage of the device the given path is on."""
        _ntuple_diskusage = collections.namedtuple('usage', 'total used free')
        if hasattr(os, 'statvfs'):  # POSIX
            st = os.statvfs(path)
            free = st.f_bavail * st.f_frsize
            total = st.f_blocks * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
            return _ntuple_diskusage(total, used, free)

        elif os.name == 'nt':       # Windows
            _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                ctypes.c_ulonglong()
            if sys.version_info >= (3,) or isinstance(path, unicode):
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
            else:
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
            ret = fun(path, ctypes.byref(_),
                      ctypes.byref(total),
                      ctypes.byref(free))
            if ret == 0:
                raise ctypes.WinError()
            used = total.value - free.value
            return _ntuple_diskusage(total.value, used, free.value)
        else:
            raise NotImplementedError("platform not supported")
