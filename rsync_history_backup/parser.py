import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument("action",
#                     type=str,
#                     choices=["init", "backup", "dryrun", "versions", "diff"],
#                     help="action")
# parser.add_argument("path",
#                     type=str,
#                     nargs='?', default='.',
#                     help="location where the action should be executed.")
# parser.add_argument("--verbose", "-v",
#                     action="store_true",
#                     help="verbose flag.")
# parser.add_argument("--config", "-c",
#                     action="store",
#                     help="path to a config file.")
# parser.add_argument("--dst", "-d",
#                     action="store",
#                     help="path to the destionation directory.")
# parser.add_argument("--src", "-s",
#                     action="store",
#                     help="path to the source directory.")
# parser.add_argument("--log", "-l",
#                     action="store",
#                     help="path to log file.")

default_parser = argparse.ArgumentParser(add_help=False)
default_parser.add_argument("--verbose", "-v", action="store_true",
                            help="show debug output.")
default_parser.add_argument("--log", "-l", action="store", metavar="PATH",
                            help="path to log file.")

default_parser.add_argument("path", nargs='?', type=str, default='.',
                            help="location where the action " +
                                 "should be executed.")

parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(title='action',
                                   description='Choose between the actions: ' +
                                   '"init", "backup", "versions", "diff".',
                                   help='select the action you want to run.')


parser_init = subparsers.add_parser('init', help='initialize rhb environment.',
                                    parents=[default_parser])
parser_init.set_defaults(which='init')
# parser_init.add_argument("path", nargs='?', type=str, default='.',
#                         help="location where the action should be executed.")
parser_init.add_argument("--dst", "-d", action="store", metavar="FOLDER",
                         help="path to the destionation directory.")
parser_init.add_argument("--src", "-s", action="store", metavar="FOLDER",
                         help="path to the source directory.")

parser_bkup = subparsers.add_parser('backup', help='start a backup.',
                                    parents=[default_parser])
parser_bkup.set_defaults(which='backup')
# parser_bkup.add_argument("path", nargs='?', type=str, default='.',
#                         help="location where the action should be executed.")
parser_bkup.add_argument("--dst", "-d", action="store", metavar="FOLDER",
                         help="path to the destionation directory.")
parser_bkup.add_argument("--src", "-s", action="store", metavar="FOLDER",
                         help="path to the source directory.")
parser_bkup.add_argument("--config", "-c", action="store", metavar="FILE",
                         help="path to a config file.")
parser_bkup.add_argument("--dryrun", "-t", action="store_true",
                         help="Won't do the actual backup, only show changes.")

parser_vers = subparsers.add_parser('versions', help='show file versions.',
                                    parents=[default_parser])
parser_vers.set_defaults(which='versions')
parser_vers.add_argument("--config", "-c", action="store", metavar="FILE",
                         help="path to a config file.")
parser_vers.add_argument("--show", "-s", action="store_true",
                         help="show which version the local file is.")

parser__get = subparsers.add_parser('get', help='get file from backup folder',
                                    parents=[default_parser])
parser__get.set_defaults(which='get')

parser__get.add_argument("--generate-links", action="store_true",
                         help="generate symlinks (only linux).")
parser__get.add_argument("--delete-links", action="store_true",
                         help="delete symlinks (only linux).")
parser__get.add_argument("--version", action="store",
                         help="get specific file version.")

parser_drop = subparsers.add_parser('drop', help='delete given file.',
                                    parents=[default_parser])
parser_drop.set_defaults(which='drop')

parser_drop.add_argument("--all", action="store_true",
                         help="delete the file and it's history.")
parser_drop.add_argument("--history", action="store_true",
                         help="delete the complete file history.")
parser_drop.add_argument("--version", action="store",
                         help="delete the a specific file version.")
