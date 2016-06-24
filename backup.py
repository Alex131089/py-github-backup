import requests
import subprocess
import os
import sys
import argparse

parser = argparse.ArgumentParser(description='Backup (clone) github repos.')

parser.add_argument(
    'username', help='github username to backup repos for')
parser.add_argument(
    '-d', '--directory',
    default=os.getcwd(),
    help='directory to clone repos to (defaults to cwd)')
args = parser.parse_args()

user = args.username

repos = {}
# FORMAT of repos dict:
# { 'user1':
#         {'myrepo1': 'http://clone.url/myrepo1.git',
#          'myrepo2': 'http://clone.url/myrepo2.git'},
#   'user2': etc...
# }


# function to get a list of data about repos, given api url, and optional params
# (assuming response is github's standard list of repositories in json format)
def get_repos(url, params=None):
    repos = []
    while True:
        res = None
        user_repos = None
        try:
            res = requests.get(url, params=params)
            user_repos = res.json()
        except:
            print("error getting repo information for url {}".format(url))
            sys.exit(1)
        for repo in user_repos:
            repos.append({'owner': repo['owner']['login'],
                          'name': repo['name'],
                          'clone_url': repo['clone_url']})

        next_link = res.links.get('next', None)
        if next_link:
            url = next_link.get('url')
        else:
            break

    return repos

# TODO: command line switches to choose what repos to download
urls = [

    # user repos, including those the user is a member of
    ('https://api.github.com/users/{}/repos'.format(user), {'type': 'all'}),

    # user starred repos
    ('https://api.github.com/users/{}/starred'.format(user), None)
]

# build a list of repos to clone/update
for url in urls:
    r = get_repos(url[0], url[1])
    for repo in r:
        owner, name, url = r['owner'], r['name'], r['clone_url']
        if owner not in repos:
            repos[owner] = {}
        repos[owner][name] = url


# go through the filesystem to build up list of commands to run (whether git
# clone or update existing) - also make any necessary dirs
root = args.d
to_run = []
for user in repos:
    # make all the user dirs
    os.mkdir(os.join(root, user))
    for repo in repos[user]:
        url = repos[user][repo]
        path = os.join(os.join(root, user), repo)
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
                'command': ['git', 'clone', '--recursive', url, path]})


# TODO: spawn multiple processes at once for parallel downloading
# actually run the git commands!
for command in to_run:
    print(command)
    subprocess.run(command['command'], cwd=command.get('path', None))
