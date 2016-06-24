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

cwd = os.getcwd()

# 1. layout a file hierarchy to clone repos into (mkdir owner for owners)
# 2. use subprocess popen to call git clone --mirror for each
#    - can spawn multiple processes at once for parallel downloading
