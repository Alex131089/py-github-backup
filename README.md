
# py-github-backup

Small script to clone all interesting repositories from Github

Copyright © 2016 Samuel Walladge

## About

This script is able to download your repos (including ones you are a collaborator on), starred repos, gists, and starred
gists from Github, into a structured directory for convenience. It currently does `git clone --recursive <url>` for
each repo, or `git fetch --recurse-submodules=yes -t` if the directory already exists in the backup dir. (So the
script can be run multiple times to incrementally backup repos over time.)

### Notes

- can work for other usernames too, but some features require api authentication (your private repos, starred gists,
  etc.)
- it has been roughly thrown together, with minimal testing - I've used it without problems, but YMMV. Use at own risk!
- beware of Github rate-limiting - probably shouldn't run it too often. ;)


## Installation

```shell
git clone <repo>
cd <repo>
pip install -r requirements.txt
python github-backup.py [args] username
```

## Usage

```
$ python github-backup.py --help
usage: github-backup.py [-h] [-d DIRECTORY] [-t TOKEN] [-S] [-U] [-A] [-u]
                        [-s] [-n]
                        username

Backup (clone) github repos.

positional arguments:
  username              github username to backup repos for

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        directory to clone repos to (defaults to cwd)
  -t TOKEN, --token TOKEN
                        api token for auth (defaults to env GITHUB_API_TOKEN)
                        - if not available, auth disabled
  -S, --starred         backp user starred repos
  -U, --user            backup user repos (requires auth)
  -A, --all             backup all options
  -u, --usergists       backup user gists
  -s, --starredgists    backup user starred gists (requires auth)
  -n, --userunauth      backup user gists (without auth token)
```

Example: `python github-backup.py -A -t secret-token myusername`

Running will create a directory tree with the following structure:

```
backup-dir
├── gists
│   └── myusername
│       └── gist1-id
├── repos
│   ├── username1
│   │   └── repo1
│   ├── organisation1
│   │   ├── repo1
│   │   ├── repo2
│   │   └── repo3
│   └── myusername
│       ├── repo1
│       ├── repo2
│       └── repo3
├── starred-gists
│   ├── username1
│   │   └── gist2-id
│   └── username2
│       └── gist1-id
└── starred-repos
    ├── username1
    │   └── repo42
    ├── username2
    │   └── repo1
    └── username3
        └── repo1
```

## License

```plaintext
py-github-backup - backup interesting Github repos
Copyright (C) 2016  Samuel Walladge

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
