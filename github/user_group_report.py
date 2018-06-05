from github import Github
import os
from jinja2 import Environment, FileSystemLoader

ACCESS_TOKEN = os.getenv("GIT_ACCESS_TOKEN")
PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(PATH),
    trim_blocks=False)

template_file_name = "report_template.jinja"


def render_template(template_filename, context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)





def create_report(type, data):
    """
    :param topic_list: list of topics
    :param topic_type: topic type (logs / events)
    :return: nothing, just creates files
    """
    fname = "report-{}.conf".format(type)
    context = {
        'type': type,
        'data': data,
    }
    #
    with open(fname, 'w') as f:
        report = render_template(template_file_name, context)
        f.write(report)








g = Github(ACCESS_TOKEN)



repo_list = []
team_list = []
team_summary = {}

all_teams =  g.get_organization('my_organization').get_teams()
# for team in all_teams:
#     team_list.append(team)

for team in all_teams:
    team_summary[team.name] = {}
    team_summary[team.name]['members'] = []
    team_summary[team.name]['repositories'] = []
    team_members = team.get_members()
    for member in team_members:
        if member.name is None:
            team_summary[team.name]['members'].append(member.login)
        else:
            team_summary[team.name]['members'].append("{} ({})".format(member.login, member.name.encode('utf-8')))
    for repository in team.get_repos():
        team_summary[team.name]['repositories'].append(repository.name)

for team, members in team_summary.items():
    print("Team : {}".format(team))

    for member in members:
        print("| {}".format(member))

    print("Repositories : {}".format(team_summary[team]['repositories']))

