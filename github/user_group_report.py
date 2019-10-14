import os
import datetime

from github import Github
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def render_template(template_filename, context):
    """
    :param template_filename: Name of the template file in the current directory
    :param context: vars for rendering the template (github data, date, organization)
    :return: rendered template from context data
    """
    PATH = os.path.dirname(os.path.abspath(__file__))
    template_environment = Environment(
        autoescape=False,
        loader=FileSystemLoader(PATH),
        trim_blocks=False)

    return template_environment.get_template(template_filename).render(context)


def create_report(type, data, org):
    """
    :param topic_list: list of topics
    :param topic_type: topic type (logs / events)
    :return: nothing, just creates files
    """

    template_name = "report_users.jinja"
    output_report = "report.html"
    output_pdf = "report.pdf"

    context = {
        'type': type,
        'data': data,
        'date': get_date(),
        'org': org
    }
    with open(output_report, 'w') as f:
        report = render_template(template_name, context)
        f.write(report)
    HTML(filename=output_report).write_pdf(output_pdf)


def get_date():
    return str(datetime.datetime.now().strftime('%H_%M_%d_%m_%Y'))


def test_env_var(variable):
    if os.environ.get(variable) is not None:
        return os.getenv(variable)
    else:
        print("Environment variable '{}' is not set".format(variable))
        exit(1)


def main():
    team_summary = {}

    # scripts required environment variables
    access_token = test_env_var("GIT_ACCESS_TOKEN")
    organization = test_env_var("ORGANIZATION")

    g = Github(access_token)

    all_teams = g.get_organization(organization).get_teams()
    total_number_of_repos = g.get_organization(organization).owned_private_repos + g.get_organization(
        organization).public_repos

    print("Getting github data for organization {}".format(organization))
    for team in all_teams:
        team_summary[team.name] = {}
        team_summary[team.name]['members'] = []
        team_summary[team.name]['repositories'] = []
        team_summary[team.name]['count'] = ""
        team_members = team.get_members()
        for member in team_members:
            if member.name is None:
                team_summary[team.name]['members'].append(member.login)
            else:
                team_summary[team.name]['members'].append("{} ({})".format(member.login, str(member.name)))
        for repository in team.get_repos():
            team_summary[team.name]['repositories'].append(repository.name)
        team_summary[team.name]['repositories'].sort()

    for team in team_summary:
        count = (len(team_summary[team]['repositories']))
        result = "{} / {}".format(count, total_number_of_repos)
        if len(team_summary[team]['repositories']) == total_number_of_repos:
            team_summary[team]['repositories'] = ["All"]
        team_summary[team]['count'] = result
    print("Creating report")
    create_report('users', team_summary, organization)
    print("Report generated")


if __name__ == "__main__":
    main()
