import json
import re
import pprint

from slackbot.bot import respond_to, listen_to
from gocd import Server

config = {
    'server': 'server-url',
    'user': 'user',
    'password': 'password',
}

pp = pprint.PrettyPrinter(indent=2)

srv = Server(config['server'], config['user'], config['password'])

AUTHORIZED_USER_IDS = [
    "xxx",
    "yyy",
    "zzz"
]


def check_authorized(msg):
    if msg._get_user_id() in AUTHORIZED_USER_IDS:
        return True
    return False


@respond_to('regex_run (.*) (.*)')
def run_regex_pipeline(message, regex, confirm):
    if not check_authorized(message):
        message.reply('Unauthorized')
        return

    pattern = re.compile(regex)
    pipeline_groups = srv.pipeline_groups()
    pipelines_match = []
    fields = []
    triggered = "Nope"
    for pipeline in pipeline_groups.pipelines:
        if bool(pattern.match(pipeline)):
            pipelines_match.append(pipeline)
    attachments = [
        {
            'fallback': 'Scheduling pipelines',
            'title': 'Scheduling pipelines',
            'title_link': '{}/go/'.format(config['server']),
            'color': '#59afe1',
        }]
    message.send_webapi('', attachments)

    for p in pipelines_match:
        fields.append({"title": p,
                       "value": "> <{}/go/tab/pipeline/history/{}|link>".format(config['server'], p),
                       "short": bool(True)})

        if confirm == "yes":
            triggered = "Yep, run incoming"
            srv.pipeline(p).schedule()

    summary = [
        {
            'fallback': 'Pipeline execution summary',
            'title': 'Triggered ? {}'.format(triggered),
            'title_link': '{}/go/',
            'fields': fields,
            'color': '#59afe1',
        }]
    message.send_webapi('', summary)
    if confirm.lower() != "yes":
        rerun = [{
            'fallback': 'To run the pipelines above, add argument : yes',
            'title': 'To run the pipelines above, add argument : yes',
            'title_link': '{}/go/',
            'color': '#FFA500',
        }]
        message.send_webapi('', rerun)


@respond_to('regex_pipeline_status (.*)')
def regex_pipeline_status(message, regex):
    if not check_authorized(message):
        message.reply('Unauthorized')
        return
    fields = []
    pattern = re.compile(regex)
    pipeline_groups = srv.pipeline_groups()
    pipelines_match = []
    for pipeline in pipeline_groups.pipelines:
        if bool(pattern.match(pipeline)):
            pipelines_match.append(pipeline)

    for p in pipelines_match:
        p_status = srv.pipeline(p).history()
        res = json.loads(p_status._content)['pipelines'][0]['stages'][0]['result']

        fields.append({"title": " > {}".format(str(p)),
                       "value": "{}".format(res),
                       "short": bool(True)})

    failed_pipelines = [failed_field for failed_field in fields if failed_field['value'] == "Failed"]
    failed = [{
        "fields": failed_pipelines,
        "color": "#ff9900",
    }]
    success_pipelines = [success_field for success_field in fields if success_field['value'] == "Passed"]
    success = [{
        "fields": success_pipelines,
        "color": "#33cc33",
    }]
    message.send_webapi('', failed)

    message.send_webapi('', success)


@respond_to('regex_pipeline_pause (.*) (.*)')
def regex_pipeline_pause(message, regex, pause_message):
    if not check_authorized(message):
        message.reply('Unauthorized')
        return
    fields = []
    print(pause_message)
    pattern = re.compile(regex)
    pipeline_groups = srv.pipeline_groups()
    pipelines_match = []
    for pipeline in pipeline_groups.pipelines:
        if bool(pattern.match(pipeline)):
            pipelines_match.append(pipeline)
    if len(pipelines_match) == 0:
        print("no match")

    for p in pipelines_match:
        p_status = srv.pipeline(p).pause(pause_message)
        if p_status.status_code == 200:
            paused_bool = True
        else:
            paused_bool = False
        fields.append({"title": " > {}".format(str(p)),
                       "value": " Paused : {} / {}".format(paused_bool, pause_message),
                       "short": bool(True)})

    paused = [{
        "fields": fields,
        "color": "#33cc33",
    }]
    message.send_webapi('', paused)


@respond_to('regex_pipeline_unpause (.*)')
def regex_pipeline_unpause(message, regex):
    if not check_authorized(message):
        message.reply('Unauthorized')
        return
    fields = []
    pattern = re.compile(regex)
    pipeline_groups = srv.pipeline_groups()
    pipelines_match = []
    for pipeline in pipeline_groups.pipelines:
        if bool(pattern.match(pipeline)):
            pipelines_match.append(pipeline)

    for p in pipelines_match:
        p_status = srv.pipeline(p).unpause()
        if p_status.status_code == 200:
            try:
                print(p_status.body())
            except Exception as e:
                print(e)
                pass
            unpaused_bool = True
        else:
            unpaused_bool = False

        fields.append({"title": " > {}".format(str(p)),
                       "value": " Unpaused : {}".format(unpaused_bool),
                       "short": bool(True)})

    unpaused = [{
        "fields": fields,
        "color": "#33cc33",
    }]
    message.send_webapi('', unpaused)
