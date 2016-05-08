# -*- coding: utf-8 -*-

import sys
import os
import argparse
import logging
import json
from rsync_history_backup.basic import RsyncBackup
from rsync_history_backup.analyzer import BackupInfo
from rsync_history_backup.actions import init_action, dryrun_action, \
    backup_action, versions_action
from rsync_history_backup.parser import parser

# --------------------- FUNCTION DEFNITION -------------------- #


def create_log_file_handler(file_name=''):
    formatter = logging.Formatter('[ %(asctime)s - %(name)-30s ] ' +
                                  '%(levelname)-8s: %(message)s')
    fh = logging.FileHandler(file_name if file_name else 'rhb.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    return fh


def find_rhb_local_dir(cwd):
    """Search for the local settings dir, from current dir upwards"""
    current_dir = cwd
    while True:
        if os.path.isfile(os.path.join(current_dir, '.rhb', 'config.json')):
            return current_dir  # os.path.join(current_dir, '.rhb')
        if os.path.normpath(os.path.join(current_dir, '..')) is current_dir:
            return None
        current_dir = os.path.normpath(os.path.join(current_dir, '..'))


# -------------------------- PARSER -------------------------- #

# parser.add_argument("--history", "-h"
#                     action="store")

# -------------------------- LOGGER  -------------------------- #
logger = logging.getLogger('rhb')
logger.setLevel(logging.DEBUG)

# --------------------------  END   -------------------------- #


def run(sys_args):
    args = parser.parse_args(sys_args[1:])

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logger.addHandler(ch)

    if args.log:
        logger.addHandler(create_log_file_handler(args.log))

    if args.path:
        local_dir = find_rhb_local_dir(os.path.abspath(args.path))
    else:
        local_dir = find_rhb_local_dir(os.getcwd())
    logger.debug("Local settings found: {}".format(local_dir) if local_dir
                 else "No local settings found.")

    if args.which == 'init':
        if local_dir:
            logger.critical("RHB already initialized: '{}'.".format(local_dir))
            raise SystemExit("Exit.")
        elif args.path:
            logger.warning("Setting an extra path has no effect. "
                           "Use '--src' and '--dst' flag instead.")
        init_action(args.src, args.dst)

    elif args.which == 'backup':
        if not args.log:
            if local_dir and not args.dryrun:
                logger.addHandler(create_log_file_handler(
                    os.path.join(local_dir, ".rhb", "rhb.log")
                ))
        if args.path != '.' and (args.src or args.dst or args.config):
            logger.warning("Adding an additional path has no effect if "
                           "'--src' and '--dst' or '--config' are set.")

        if args.dryrun:
            dryrun_action(args.src, args.dst, args.config, local_dir)
        else:
            backup_action(args.src, args.dst, args.config, local_dir)

    elif args.which == 'versions':
        versions_action(args.config, local_dir, args.path, args.show)

    # elif args.which == 'get':
    #     get_action(local_dir, args.path, args.version)

    else:
        raise NotImplementedError("Sorry. Your requested action is apparently"
                                  "not implemented. :/")
