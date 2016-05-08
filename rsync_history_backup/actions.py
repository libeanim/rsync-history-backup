import sys
import os
import logging
import json
from rsync_history_backup.basic import RsyncBackup
from rsync_history_backup.analyzer import BackupInfo
from rsync_history_backup.utils import bcolors


def init_action(src, dst):
    """
    """
    logger = logging.getLogger('rhb.init_action()')

    def get_dir(name):
        while True:
            d = input("{} directory: ".format(name.capitalize()))
            if not os.path.isdir(d):
                print("Directory does not exist.", "Try again.")
            else:
                # Return abspath here?
                return os.path.abspath(d)

    if not src:
        src = get_dir('source')
    if not dst:
        dst = get_dir('destination')
    name = input("Name: ")
    logger.info("Initializing {}:\nSRC: {}\nDST:{}".format(name, src, dst))
    os.mkdir(os.path.join(src, '.rhb'))
    logger.debug("Made '.rhb' dir.")

    default_config = {
        "destination": dst,
        "sync_options": ["--recursive", "--update", "--delete", "--owner",
                         "--group", "--times", "--links", "--safe-links",
                         "--super", "--one-file-system", "--devices"],
        "hist_options": ["--update", "--owner", "--group", "--times",
                         "--links", "--super"],
        "source": src,
        "name": name,
        "save_history": True
    }
    with open(os.path.join(src, 'rsync-ignore.txt'), 'w+') as rsi:
        rsi.write('.rhb/\n')
        rsi.flush()
    logger.debug("Created default 'rsync-ignore.txt'.")
    with open(os.path.join(src, '.rhb', 'config.json'), 'w+') as cfg:
        json.dump(default_config, cfg)
    logger.debug("Created 'config.json'.")
    logger.info(" -> finished.")
    print("HINT:", "Use http://gitignore.io to generate a rsync-ignore.txt.")


def _init_rhb(src, dst, cfg, local_dir):
    logger = logging.getLogger('rhb._init_rhb()')
    logger.debug("Initializing rhb object.")
    if cfg:
        logger.debug("Config path found: {}".format(cfg))
        if local_dir:
            logger.warning("Local configuration found, but using " +
                           "given config file.")
        rhb = RsyncBackup.load_config_file(open(config, 'r'))
    elif src and dst:
        logger.debug("Source and destination set:\n{}; {}".format(src, dst))
        if local_dir:
            logger.warning("Local configuration found, but using " +
                           "given source and destination path.")
        rhb = RsyncBackup(src, dst)
    elif local_dir:
        logger.debug("Local settings found: {}".format(local_dir))
        rhb = RsyncBackup.load_config_file(
            open(os.path.join(local_dir, '.rhb', 'config.json'), 'r')
        )
    else:
        logger.critical("You have to set either a config file, " +
                        "the '--src' and '-dst' flag or " +
                        "be in a directory with a rhb local directory.")
        sys.exit(1)
    logger.debug("rhb: src={}; dst={}".format(rhb.source, rhb.destination))
    return rhb


def _get_service_info(local_dir):
    file_name = os.path.join(local_dir, '.rhb', 'service.json')
    if os.path.isfile(file_name):
        return json.load(open(file_name, 'r'))
    return None


def backup_action(src, dst, cfg, local_dir):
    rhb = _init_rhb(src, dst, cfg, local_dir)
    service_info = _get_service_info(local_dir)
    if service_info:
        map(rhb.add_exclude_path, service_info['dropped'])
    return rhb.run_backup()


def dryrun_action(src, dst, cfg, local_dir):
    logger = logging.getLogger('rhb.dryrun_action')
    rhb = _init_rhb(src, dst, cfg, local_dir)
    try:
        out = rhb.dry_run()
    except FileNotFoundError as e:
        logger.critical("{}: {}".format(rhb.source, e))
        sys.exit(1)

    if not out:
        return True

    for t in out:
        if not out[t]:
            continue
        print('\n' + t.upper() + ':', "({} changes)".format(len(out[t])))
        if len(out[t]) > 100:
            continue
        for f in out[t]:
            print(" - " + f.replace(rhb.source + '/', ''))

    return True


def versions_action(config, local_dir, path, show=False):
    logger = logging.getLogger("rhb.versions_action()")
    if not path:
        logger.critical("You have to set a file you want to analyze.")
        sys.exit(1)
    if config:
        cfg = json.load(open(config, 'r'))
        backup_info = BackupInfo(cfg['destination'], cfg['name'])
        file_name = os.path.abspath(path).replace(cfg['source'], '')
    elif local_dir:
        cfg = json.load(open(os.path.join(
            local_dir, '.rhb', 'config.json'),
            'r'
        ))
        backup_info = BackupInfo(cfg['destination'], cfg['name'])
        file_name = os.path.abspath(path).replace(local_dir, '')
    else:
        logger.critical("You have either to set a config file or" +
                        "be in a directory with a rhb local directory.")
        sys.exit(1)
    if not backup_info.save_history:
        logger.warning("This backup has no history stored.")
        return False

    if file_name:
        file_name = file_name[1:] if file_name[0] == '/' else file_name

    def print_versions(file_name):
        vers = []
        if os.path.isfile(os.path.join(backup_info.current_dir, file_name)):
            vers.append("current")
        vers += backup_info.get_file_versions(file_name)
        if len(vers) > 0:
            print(bcolors.colorize(file_name, 'BOLD'))
            print(len(vers), "version(s) found:")
            print(' - ' + '\n - '.join(vers))
        else:
            print("No versions found.\n",
                  "Either this file is on the ignore list or " +
                  "was created after the last backup.\n",
                  "Run 'rhb backup' or 'rhb dryrun' to be sure.")

    if os.path.isdir(path):
        for fi in os.listdir(path):
            tmp = os.path.join(path, fi)
            if os.path.isfile(tmp):
                print_versions(os.path.join(file_name, fi))
                print("")
    elif os.path.isfile(os.path.join(backup_info.current_dir, file_name)):
        print_versions(file_name)
    # print('Destination:', backup_info.location)

    return True


def get_action(local_dir, path, version=None):
    if local_dir:
        logger.debug("Local settings found: {}".format(local_dir))
        rhb = RsyncBackup.load_config_file(
            open(os.path.join(local_dir, '.rhb', 'config.json'), 'r')
        )
    else:
        logger.critical("You have to be in a directory with " +
                        "a rhb local directory.")
        sys.exit(1)
