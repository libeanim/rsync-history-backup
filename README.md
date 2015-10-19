# Rsync History Backup

Easily backup your data with rsync and an automatically generated version history.

**Attention** This project is in alpha stage and is only tested on linux!

The major goal of this project is it to make an easy and transparent backup tool
with the power of rsync.
Your backup folder contains three subfolders: `current`, `history` and `log`.

* In the **`current` directory** you can access your up-to-date backup.

* In the **`history` directory** there are all file versions stored in an easy
  understandable way and you can access them directly.

* Lastly, you can look into the **`log` directory** if you want to know which
  files were created or deleted during any backup.

There is no need for any additional software just a file browser and a text
editor are required to access all your data.

And on top of that it is easy to create a front end application, making the
handling even easier.

## Why do we need another backup tool?

* **Your project appears to be similar to `rsnapshot`?**

  That's true. Unfortunately `rsnapshot` uses hardlinks to provide its features
  which are not supported by every file system, especially not on (older) samba
  network file shares.

* **Why not using `rdiff`, it has delta compression!**

  `rdiff` is a great tool, but it can't follow symlinks (although `rsync` can)
  and has some problems with samba shares too. The last major release was almost
  3 years ago and they recommend to mount samba shares with `smbfs` (which is
  deprecated) rather than `CIFS`.

* **Why not using `git` or `git annex`?**

  `git` respectively `git annex` for larger files are really good programs for
  backups of your local files.

  `git annex` is unbeatable when you want to backup your files
  to many different devices and always want to know which device contains what
  data. But it's not that easy for newcomers and the `lock` and `unlock`
  command which is needed to make proper git commits sometimes disturbs your
  workflow. you can use it in `direct mode`, but then you lose some features.
  Additionally, it's not that easy to access your data on the backup repo and
  some processes might be confusing if you don't know `git` inside out.
  I just wanted to create a backup system which is really easy to maintain and
  use.

  But don't get me wrong! I could definitely recommend to use `git annex`. I used
  it for more than a year and was perfectly happy with it.

* **But there is program `xyz` which is much more tested and developed than this one!**

  If you have a backup program which completely matches your needs, just use it.

  I decided to write a program which matches my needs and makes it easy to
  access your data locally or in your backup folder at any time with nothing
  more than a file browser.

## Requirements

* rsync
* python3

## Installation

This is the easiest installation for testing:

1. Make sure you fulfil the requirements.

2. Clone the repository:

        git clone "https://github.com/libeanim/rsync-history-backup.git"


3. Create a bash alias in your `~/.bashrc` or `~/.bash_aliases` file (**recommended**)

        alias rhb='path/to/repo/rhb.py'

  **or**

  create a symlink from the rhb.py file to your local library path, e.g.:

      sudo ln -s /path/to/repo/rhb.py /usr/local/bin/rhb

If you want to uninstall "Rsync History Backup" just delete the repository and
make sure to remove the symlink in your library path or the bash alias, if
created.


# Quickstart

## Run `rhb` from the command line

`rhb` has multiple 'actions': `init`, `backup`, `versions`, `get` and `drop`.

To call these actions just run:

    rhb {action}

each action has multiple flags or options, run

    rhb {action} --help

for further information.

## Run a backup without intialization

Just run following command:

    rhb backup --src /path/to/local/folder --dst /path/to/backup/folder

If you want to have more options, you can create a settings file (e.g. `config.json`):

    {
      "destination": "/path/to/destination",
      "sync_options": ["--recursive", "--update", "--delete", "--owner",
                       "--group", "--times", "--links", "--safe-links",
                       "--super", "--one-file-system", "--devices"],
      "hist_options": ["--update", "--owner", "--group", "--times",
                       "--links", "--super"],
      "source": "/path/to/source",
      "name": "backup_name",
      "save_history": true
    }

and then run:

    rhb backup --config path/to/config.json


## Initializing a backup

1. To initialize a backup run:

        rhb init --source /path/to/local/folder --dest /path/to/backup/folder

  this will create a .rhb folder in your source directory containing the
  information required for the backup.
  All the configuration is stored in a `config.json` file within this directory.
  There you can edit the `sync_options` to customize the synchronization behavior
  of rsync.

      {
        "rsync_backup":{
          "destination": "/path/to/destination",
          "sync_options": ["--recursive", "--update", "--delete", "--owner",
                           "--group", "--times", "--links", "--safe-links",
                           "--super", "--one-file-system", "--devices"],
          "hist_options": ["--update", "--owner", "--group", "--times",
                           "--links", "--super"],
          "source": "/path/to/source",
          "name": "my_name",
          "save_history": true
        },
      ...
      }

2. If you are now in your source folder or any subfolder, you can run the

        rhb backup

  command.


# Roadmap

*In arbitrary order.*

* Show current file version in `versions` action.
* Implement `get` and `drop` to get file history or drop it.
* Enhance `get` and `drop` option to get something similar like `git annex get` and `drop`.
* Implement some auto backup feature.
* Allow multiple backup locations for one source.
