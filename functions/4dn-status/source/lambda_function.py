import html
import http
import io
import json
import requests


SAMPLE_EVENTS = [
    {
        "name": "Fourfront System Upgrades",
        "start_time": "2020-03-23 16:00:00-0400",
        "end_time": "2020-03-24 20:00:00-0400",
        "message": ("Systems may be unavailable for writes"
                    " from 4pm EDT Monday, March 23, 2020"
                    " through 8pm EDT Tuesday, March 24, 2020."),
        "affects": {
            "name": "All Fourfront Systems",
            "environments": [
                "fourfront-hotseat",
                "fourfront-mastertest",
                "fourfront-webdev",
                "fourfront-webprod",
                "fourfront-webprod2",
                "fourfront-wolf",
            ],
        },
    },
]


SAMPLE_DATA = {
    "bgcolor": "#ffcccc",
    "events": SAMPLE_EVENTS
}
    

DEFAULT_COLOR = "#ccffcc"


DEFAULT_EVENT = {
    "name": "No Scheduled Events",
    "start_time": None,
    "end_time": None,
    "message": "No known problems. No disruptions planned.",
    "affects": {
        "name": "All Systems",
        "environments": None,
    }
}

   
DEFAULT_DATA = {
    "bgcolor": DEFAULT_COLOR,
    "events": [
        DEFAULT_EVENT,
    ],
}


def get_data():
    r = requests.get("https://4dn-dcic-publicly-served.s3.amazonaws.com/4dn-status/events.json")
    result = r.json()
    return result or DEFAULT_DATA


def convert_to_html(data, environment):
    events = data['events']
    bgcolor = data['bgcolor']
    event_str = io.StringIO()
    sections_used = []
    for i, event in enumerate(events, start=1):
        event_name = event.get('name') or "Event %s" % i
        affects = event.get('affects') or {}
        affects_name = affects.get('name') or "All Systems"
        affects_envs = affects.get('environments') or []
        section = io.StringIO()
        section.write('<dt class="event">%s</dt>\n' % html.escape(event_name))
        section.write("<dd>\n")
        section.write('<p><span class="who">%s</span>' % html.escape(affects_name))
        section.write(' <span class="when">(%s to %s)</span></p>\n' 
                      % (html.escape(event.get('start_time') or "now"),
                         html.escape(event.get('end_time') or "the foreseeable future")))
        section.write('<p class="what">%s</p>\n' % (html.escape(event.get('message') or "To Be Determined")))
        section.write("</dt>\n")
        event_str.write(section.getvalue())
        sections_used.append(i)
    event_body = event_str.getvalue()
    body = '''
<!DOCTYPE html>
<html>
 <head>
  <title>4DN Status</title>
   <meta name="robots" content="noindex, nofollow" />
   <style><!--
   .banner {padding-left: 30pt; background: <<BGCOLOR>>; padding-bottom: 10pt; padding-top: 10pt;}
   .page-name {padding-left: 10pt; font-size: 30pt;}
   .logo {height: 100%; vertical-align: middle;}
   .events {padding-left: 30pt;}
   .event {font-size: 20pt;}
   .who {font-weight: bold; font-size: 16pt;}
   .when {font-weight: bold; font-size: 14pt;}
   .what {font-weight: 12pt;}
  --></style>
 </head>
 <body>
  <div class="banner" id="banner">
   <table>
    <tr>
     <td valign="middle"><img src="https://4dnucleome.org/Assets/images/4dn-logo_1.png" class="logo" alt="4D Nucleome" /></td>
     <td class="page-name" valign="bottom">4DN Status</td>
    </tr>
   </table>
  </div>
  <dl class="events">
   <<EVENT_BODY>>
  </dl>
 </body>
</html>'''
    body = body.replace('<<BGCOLOR>>', bgcolor)
    body = body.replace('<<EVENT_BODY>>', event_body)
    return body
    

def filter_data(data, environment):
    events = data.get("events") or []
    bgcolor = data.get("bgcolor") or "#dddddd"
    filtered = []
    for event in events:
        affected_envs = (event.get('affects') or {}).get('environments')
        if affected_envs is None or environment in affected_envs:
            filtered.append(event)
    if not filtered:
        bgcolor = DEFAULT_COLOR
        filtered.append(DEFAULT_EVENT)
    return {
        "bgcolor": bgcolor,
        "events": filtered
    }


def lambda_handler(event, context, override_data=None):
    data = override_data or get_data()
    params = event.get("queryStringParameters") or {}
#    if params.get("echoevent"):
#        return {
#            "statusCode": 200,
#            "headers": {
#                "Content-Type": "application/json",
#                "Cache-Control": "public, max-age=120",
#                # Note that this does not do Access-Control-Allow-Origin
#                # as this is for debugging only. -kmp 19-Mar-2020
#            },
#            "body": json.dumps(event, indent=2),
#        }
    environment = params.get("environment") or "fourfront-webprod"
    data = filter_data(data, environment)
    format = params.get("format") or "html"
    if format == 'json':
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Cache-Control": "public, max-age=120",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(data, indent=2),
        }
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": 'text/html',
                "Cache-Control": "public, max-age=120",
                "Access-Control-Allow-Origin": "*",
           },
           "body": convert_to_html(data or [], environment)
        }


if __name__ == '__main__':

    def do_test_case(name, actual, expected):
        print("="*80)
        print("TEST:", name)
        print(" actual=", actual)
        print(" expected=", expected)
        assert actual['statusCode'] == 200
        assert json.loads(actual['body']) == expected
        print(">>> SUCCESS <<<")

    print(lambda_handler({}, None))

    print(lambda_handler({"queryStringParameters": None}, None))

    print(lambda_handler({"queryStringParameters": {}}, None))

    print(lambda_handler({"queryStringParameters": {"environment": "fourfront-cgapdev"}}, None))

    print(lambda_handler({"queryStringParameters": {"environment": "fourfront-cgapdev", "format": "json"}}, None))

    do_test_case("json for regular hosts",
                 lambda_handler({"queryStringParameters": {"format": "json"}},
                                None,
                                override_data=SAMPLE_DATA),
                 SAMPLE_DATA)

    do_test_case("json for cgapdev (not in sample set)",
                 lambda_handler({"queryStringParameters": {"environment": "fourfront-cgapdev", "format": "json"}},
                                None,
                                override_data=SAMPLE_DATA),
                 DEFAULT_DATA)

#    LAMBDA_EVENT_FOR_DEBUGGING = {"queryStringParameters": {"echoevent": "true"}}
#    do_test_case("request echoevent",
#                 lambda_handler(LAMBDA_EVENT_FOR_DEBUGGING, None),
#                 LAMBDA_EVENT_FOR_DEBUGGING)
