import requests
import subprocess
import os
import sys
import argparse
import re

parser = argparse.ArgumentParser(description='Backup (clone) github repos.')

parser.add_argument(
    'username', help='github username to backup repos for')
parser.add_argument(
    '-d', '--directory',
    default=os.getcwd(),
    help='directory to clone repos to (defaults to cwd)')
parser.add_argument(
    '-t', '--token',
    default=os.getenv('GITHUB_API_TOKEN'),
    help='api token for auth (defaults to env GITHUB_API_TOKEN) - if not available, auth disabled')
parser.add_argument('-S', '--starred',  action='store_true', help='backp user starred repos')
parser.add_argument('-U', '--user',  action='store_true', help='backup user repos (requires auth)')
parser.add_argument('-A', '--all',  action='store_true', help='backup all options')
parser.add_argument('-u', '--usergists',  action='store_true', help='backup user gists')
parser.add_argument('-s', '--starredgists',  action='store_true', help='backup user starred gists (requires auth)')
parser.add_argument('-n', '--userunauth',  action='store_true', help='backup user gists (without auth token)')
args = parser.parse_args()

user = args.username
auth = (user, args.token) if args.token else None

repos = {
        'repos': {},
        'starred-repos': {},
        'gists': {},
        'starred-gists': {}
        }


# function to get a list of data about repos, given api url, and optional params
# (assuming response is github's standard list of repositories in json format)
def get_repos(data):
    url = data.get('url')
    params = data.get('params', None)
    key = data.get('clone-key', 'clone_url')
    new_repos = []
    while True:
        res = None
        res_repos = None
        try:
            res = requests.get(url, params=params, auth=auth)
            res_repos = res.json()
        except:
            print("error getting repo information for url {}".format(url))
            sys.exit(1)
        for repo in res_repos:
            new_repos.append({'owner': repo['owner']['login'],
                          'clone_url': repo[key]})

        next_link = res.links.get('next', None)
        if next_link:
            url = next_link.get('url')
        else:
            break

    return new_repos

urls = []

# user repos, including those the user is a member of (includes private repos)
if args.all or args.user:
    if not args.token:
        print('token needed - user repos requires authentication')
        sys.exit(1)
    urls.append({
        'url': 'https://api.github.com/user/repos',
        'params': {'type': 'all'},
        'type': 'repos'
        })

# user repos, including those the user is a member of (un-auth version)
# only do this in certain cases
if (args.all and not args.token) or (args.userunauth and not args.user and not args.all):
    urls.append({
        'url': 'https://api.github.com/users/{}/repos'.format(user),
        'params': {'type': 'all'},
        'type': 'repos'
        })

# user starred repos
if args.all or args.starred:
    urls.append({
        'url': 'https://api.github.com/users/{}/starred'.format(user),
        'type': 'starred-repos'
        })

# user gists
if args.all or args.usergists:
    urls.append({
        'url': 'https://api.github.com/users/{}/gists'.format(user),
        'type': 'gists',
        'clone-key': 'git_pull_url'
        })

# starred gists
if args.all or args.starredgists:
    if not args.token:
        print('token needed - starred gists requires authentication')
        sys.exit(1)
    urls.append({
        'url': 'https://api.github.com/gists/starred',
        'type': 'starred-gists',
        'clone-key': 'git_pull_url'
        })


# build a list of repos to clone/update
for url in urls:
    r = get_repos(url)
    for repo in r:
        subdir = url.get('type')
        if repo['owner'] not in repos[subdir]:
            repos[subdir][repo['owner']] = []

        repos[subdir][repo['owner']].append(repo['clone_url'])


# go through the filesystem to build up list of commands to run (whether git
# clone or update existing) - also make any necessary dirs
root = os.path.realpath(args.directory)
to_run = []
NAME = re.compile(r'^.*/([^/]+)\.git$')

for subdir in repos:
    sub_root = os.path.join(root, subdir)
    for owner in repos[subdir]:
        os.makedirs(os.path.join(sub_root, owner), exist_ok=True)
        owner_root = os.path.join(sub_root, owner)
        for url in repos[subdir][owner]:
            name = NAME.match(url).group(1)
            path = os.path.join(owner_root, name)

            # check if exists
            if os.access(path, os.F_OK):
                # fetch, so shouldn't overwrite any local changes
                to_run.append({
                    'path': path,
                    'command': ['git', 'fetch', '--recurse-submodules=yes', '-t']})
            else:
                # this method doesn't clone a bare repo - rather the client-side
                # style we can work withh straight away
                to_run.append({
                    'path': owner_root,
                    'command': ['git', 'clone', '--recursive', url]})


# TODO: spawn multiple processes at once for parallel downloading
# actually run the git commands!
for command in to_run:
    print(command)
    subprocess.run(command['command'], cwd=command.get('path', None))
