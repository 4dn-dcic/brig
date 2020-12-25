# import datetime
import html
# import http
import io
import json
# import pytz
# import re
import requests

# from datetime import datetime as datetime_type
# from dateutil.parser import parse as dateutil_parse
from dcicutils.misc_utils import HMS_TZ, hms_now, as_datetime, in_datetime_interval, ignored
from dcicutils.env_utils import classify_server_url, FF_PROD_BUCKET_ENV, CGAP_PROD_BUCKET_ENV, get_bucket_env


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


CALENDAR_DATA_URL_PRD = "https://4dn-dcic-publicly-served.s3.amazonaws.com/4dn-status/events.json"
CALENDAR_DATA_URL_STG = "https://4dn-dcic-publicly-served.s3.amazonaws.com/4dn-status/events-staged.json"

PRD_ENDPOINT_PATH = '/4dn-status'
STG_ENDPOINT_PATH = '/4dn-status-staged'


def get_calendar_data(staged=False):
    url = CALENDAR_DATA_URL_STG if staged else CALENDAR_DATA_URL_PRD

    try:
        r = requests.get(url)
        result = r.json()
        return result or DEFAULT_DATA
    except Exception:
        return DEFAULT_DATA


def convert_to_html(data, environment):
    ignored(environment)  # TODO: Should this be ignored?
    events = data['events']
    bgcolor = data['bgcolor']
    event_str = io.StringIO()
    sections_used = []
    for i, event in enumerate(events, start=1):
        # print("event=", event, "i=", i)
        event_name = event.get('name') or "Event %s" % i
        affects = event.get('affects') or {}
        affects_name = affects.get('name') or "All Systems"
        # affects_envs = affects.get('environments') or []
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
     <td valign="middle">
      <img src="https://4dnucleome.org/Assets/images/4dn-logo_1.png" class="logo" alt="4D Nucleome" />
     </td>
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
    now = hms_now()
    for event in events:
        start_time = event.get('start_time', None)
        end_time = event.get('end_time', None)
        affected_envs = (event.get('affects') or {}).get('environments')
        if affected_envs is None or environment in map(canonicalize_environment, affected_envs):
            # TODO: It's possible the datetime will be ill-formed, in which case an error will be raised
            if in_datetime_interval(now, start=start_time, end=end_time):
                filtered.append(event)
    if not filtered:
        bgcolor = DEFAULT_COLOR
        filtered.append(DEFAULT_EVENT)
    return {
        "bgcolor": bgcolor,
        "events": filtered
    }


CORS_HEADERS = {
    # It may be that only GET is needed, but just in case. -kmp&akb 20-Mar-2020
    "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS",
    "Access-Control-Allow-Headers": ",".join([
        "Origin",
        "Accept",
        "X-Requested-With",
        "Content-Type",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cache-Control",
        "Authorization",
    ]),
    "Access-Control-Allow-Origin": "*",
}


def canonicalize_environment(environment):
    # We implement canonical naming of these environments by using the bucket environment.
    return get_bucket_env(environment)


def resolve_environment(referer, application, environment):
    """
    Given referer, application, and environment supplied with a request, figure out what environment to use.

    Note that if both multiple incompatible options are supplied, no error results.
    This function is intended to just pick the best value without complaining
    There is no value to an error message.

    :param referer: a string (referer URL) or None
    :param application: a string (either 'cgap' or 'fourfront') or None
    :param environment: an environment (e.g., 'fourfront-mastertest') or None
    :return: the environment to use
    """
    if environment:
        return canonicalize_environment(environment)
    if referer:
        classification = classify_server_url(referer, raise_error=False)
        if classification['kind'] in ('fourfront', 'cgap'):
            env = classification['environment']
            env = env.strip('-0123456789')
            return env
    if application == 'cgap':
        return CGAP_PROD_BUCKET_ENV
    else:
        return FF_PROD_BUCKET_ENV


def lambda_handler(event, context):
    ignored(context)  # This will be ignored unless the commented-out block below is uncommented.

    staged = event.get("rawPath", PRD_ENDPOINT_PATH) == STG_ENDPOINT_PATH

    data = get_calendar_data(staged=staged)
    params = event.get("queryStringParameters") or {}

    # It might be a security problem to leave this turned on in production, but it may be useful to enable
    # this during development to be able to see what's coming through. -kmp 7-Jul-2020
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    if params.get("echoevent"):
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Cache-Control": "public, max-age=120",
                # Note that this does not do Access-Control-Allow-Origin, etc.
                # as this is for debugging only. -kmp 19-Mar-2020
            },
            "body": json.dumps(event, indent=2),
            # Maybe also this, too ...
            # "context": json.dumps(context)  # or repr(context)
        }
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # The referer is available in a standard event packaging, in the headers,
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-data-mappings.html

    try:

        application = params.get("application")
        referer = event.get('headers', {}).get('referer')
        environment = params.get("environment")
        environment = resolve_environment(referer=referer, application=application, environment=environment)
        data = filter_data(data, environment)
        response_format = params.get("format") or "html"
        if response_format == 'json':
            result = {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Cache-Control": "public, max-age=120",
                },
                "body": json.dumps(data, indent=2),
            }
        else:
            result = {
                "statusCode": 200,
                "headers": {
                    "Content-Type": 'text/html',
                    "Cache-Control": "public, max-age=120",
                },
                "body": convert_to_html(data or [], environment)
            }
        result = dict(result, **CORS_HEADERS)
        return result

    except Exception as e:

        return {"message": "%s: %s" % (type(e), e)}


if __name__ == '__main__':

    raise RuntimeError("Tests have moved. Use the `brig-test` script.")
