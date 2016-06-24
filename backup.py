import requests
import subprocess
import os

# TODO: allow specifying user from args
user = 'swalladge'

repos = {}

# FORMAT: 
# { 'user1':
#         {'myrepo1': 'http://clone.url/myrepo1.git',
#          'myrepo2': 'http://clone.url/myrepo2.git'},
#   'user2': etc...
# }


def get_repos(url):
    repos = []
    while True:
        res = requests.get(url)
        user_repos = res.json()
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
urls = ['https://api.github.com/users/{}/repos'.format(user),
        'https://api.github.com/users/{}/starred'.format(user)
        ]

for url in urls:
    r = get_repos(url)
    for repo in r:
        owner, name, url = r['owner'], r['name'], r['clone_url']
        if owner not in repos:
            repos[owner] = {}
        repos[owner][name] = url


print(repos)

root = os.getcwd()
# TODO: choose dir from args optional

# make all the user dirs
to_run = []
for user in repos:
    os.mkdir(os.join(root, user))
    for repo in repos[user]:
        url = repos[user][repo]
        path = os.join(os.join(root, user), repo)
        # check if exists
        if os.access(path, os.F_OK):
            to_run.append({'path': path, 'command': ['git', 'fetch', '--recurse-submodules=yes', '-t']})
        else:
            to_run.append({'command': ['git', 'clone', '--recursive', url, path]})

for command in to_run:
    # subprocess.run(command['command'], cwd=command.get('path', None))
    print(command)

