from github import Github
import os

ACCESS_TOKEN = os.getenv("GIT_ACCESS_TOKEN")

g = Github(ACCESS_TOKEN)
#
# for repo in g.get_user().get_repos():
#     print(repo.name)

repo_list = []
team_list = []
for team in g.get_organization('my_organization').get_teams():
    team_list.append(team)

for repo in g.get_organization('my_organization').get_repos():
    repo_list.append(repo)

for team in team_list:
    for repo in repo_list:
        print("Updating {} / {}".format(team.name, repo.name))
        if repo.name == 'my_organization_special_repo':
            print("Skipping {}".format(repo.name))
        else:
            if team.name == "Aministration":
                team.add_to_repos(repo)
                team.set_repo_permission(repo, 'admin')
            else:
                team.add_to_repos(repo)
                team.set_repo_permission(repo, 'write')