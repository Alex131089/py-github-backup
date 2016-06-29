import requests
import subprocess
import os
import argparse

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
parser.add_argument('-S', '--starred',  action='store_true', help='backup user starred repos')
parser.add_argument('-R', '--repos',  action='store_true', help='backup user repos (requires auth for private repos)')
parser.add_argument('-A', '--all',  action='store_true', help='backup all options')
parser.add_argument('-g', '--gists',  action='store_true', help='backup user gists')
parser.add_argument('-s', '--starredgists',  action='store_true', help='backup user starred gists (requires auth)')
parser.add_argument('-z', '--ssh',  action='store_true', help='use ssh urls instead of https')
args = parser.parse_args()

user = args.username
auth = (user, args.token) if args.token else None

repos = []


class Repo():
    def __init__(self):
        self.url = None
        self.name = None
        self.owner = None
        self.subdir = None


# function to get json data from server
def get_json(url, params=None, auth=None):
    data = []
    while True:
        res = None
        js = None
        try:
            res = requests.get(url, params=params, auth=auth)
            js = res.json()
        except:
            print("error getting data for url {}".format(url))
        for j in js:
            data.append(j)

        next_link = res.links.get('next', None)
        if next_link:
            url = next_link.get('url')
        else:
            break

    return data


# user repos
if args.all or args.repos:
    params = {'type': 'all'}

    if args.token:
        data = get_json('https://api.github.com/user/repos', params=params, auth=auth)
    else:
        print('no auth - private repos not going to be fetched')
        data = get_json('https://api.github.com/users/{}/repos'.format(user), params=params, auth=auth)

    for repo in data:
        r = Repo()
        r.owner = repo['owner']['login']
        r.name = repo['name']
        if args.ssh:
            r.url = repo['ssh_url']
        else:
            r.url = repo['clone_url']

        r.subdir = 'repos'
        repos.append(r)

# user starred repos
if args.all or args.starred:
    data = get_json('https://api.github.com/users/{}/starred'.format(user), auth=auth)
    for repo in data:
        r = Repo()
        r.owner = repo['owner']['login']
        r.name = repo['name']
        if args.ssh:
            r.url = repo['ssh_url']
        else:
            r.url = repo['clone_url']

        r.subdir = 'starred-repos'
        repos.append(r)

# user gists
if args.all or args.gists:
    data = get_json('https://api.github.com/users/{}/gists'.format(user), auth=auth)
    for repo in data:
        r = Repo()
        r.owner = repo['owner']['login']
        r.name = repo['id']
        if args.ssh:
            r.url = 'git@gist.github.com:{}.git'.format(repo['id'])
        else:
            r.url = repo['git_pull_url']

        r.subdir = 'gists'
        repos.append(r)

# starred gists
if args.all or args.starredgists:
    if args.token:
        data = get_json('https://api.github.com/gists/starred', auth=auth)
        for repo in data:
            r = Repo()
            r.owner = repo['owner']['login']
            r.name = repo['id']
            if args.ssh:
                r.url = 'git@gist.github.com:{}.git'.format(repo['id'])
            else:
                r.url = repo['git_pull_url']
            r.subdir = 'starred-gists'

            repos.append(r)

    else:
        print('skipping starred gists - auth required')


# go through the filesystem to build up list of commands to run (whether git
# clone or update existing) - also make any necessary dirs
root = os.path.realpath(args.directory)
to_run = []
for repo in repos:
    sub_root = os.path.join(root, repo.subdir)
    os.makedirs(os.path.join(sub_root, repo.owner), exist_ok=True)
    owner_root = os.path.join(sub_root, repo.owner)
    path = os.path.join(owner_root, repo.name)

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
            'command': ['git', 'clone', '--recursive', repo.url]})


# TODO: spawn multiple processes at once for parallel downloading

# actually run the git commands!
for command in to_run:
    print(command)
    subprocess.run(command['command'], cwd=command.get('path', None))
