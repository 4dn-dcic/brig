import datetime
import html
import io
import json
import requests

from dcicutils.misc_utils import (
    hms_now, as_datetime, in_datetime_interval, ignored, full_class_name, as_ref_datetime, as_seconds, remove_prefix,
)
from dcicutils.env_utils import (
    classify_server_url, FF_PROD_BUCKET_ENV, CGAP_PROD_BUCKET_ENV, get_bucket_env, is_cgap_env,
)


PRIORITY_RED = 'red'
PRIORITY_ORANGE = 'orange'
PRIORITY_YELLOW = 'yellow'
PRIORITY_GREEN = 'green'

DEFAULT_PRIORITY = PRIORITY_GREEN

ALL_PRIORITY_NAMES = [PRIORITY_GREEN, PRIORITY_YELLOW, PRIORITY_ORANGE, PRIORITY_RED]

PRIORITY_ORANGE_VALUE = ALL_PRIORITY_NAMES.index(PRIORITY_ORANGE)


def priority_value(priority):
    try:
        return ALL_PRIORITY_NAMES.index(priority)
    except Exception:
        return PRIORITY_ORANGE_VALUE


def merge_priorities(*priorities):
    priority = max(map(priority_value, priorities))
    return ALL_PRIORITY_NAMES[priority]


NULL_EVENT = {
    "name": "No Scheduled Events",
    "start_time": None,
    "end_time": None,
    "message": "No known problems. No disruptions planned.",
    "affects": {
        "name": "All Systems",
        "environments": None,
    }
}

DEFAULT_DATA_EVENTS = []

DEFAULT_DATA = {
    "calendar": DEFAULT_DATA_EVENTS,
}

CALENDAR_DATA_URL_PRD = "https://4dn-dcic-publicly-served.s3.amazonaws.com/4dn-status/calendar.json"
CALENDAR_DATA_URL_STG = "https://4dn-dcic-publicly-served.s3.amazonaws.com/4dn-status/calendar-staged.json"

PRD_ENDPOINT_PATH = '/4dn-status'
STG_ENDPOINT_PATH = '/4dn-status-staged'

CALENDAR_MISSING_MESSAGE = "Calendar data is unavailable."
CALENDAR_MISSING_PRIORITY = PRIORITY_RED


def get_calendar_data(staged=False):
    url = CALENDAR_DATA_URL_STG if staged else CALENDAR_DATA_URL_PRD

    try:
        r = requests.get(url)
        r.raise_for_status()
        result = r.json()
        return result or DEFAULT_DATA
    except Exception as e:
        data = {
            "priority": CALENDAR_MISSING_PRIORITY,
            "calendar": [],
            "message": CALENDAR_MISSING_MESSAGE,
            "problems": [{
                "message": "%s: %s" % (full_class_name(e), e)
            }],
        }
        return data


CGAP_LOGO_URL = "https://cgap.hms.harvard.edu/static/img/exported-logo.svg"
FF_LOGO_URL = "https://data.4dnucleome.org/static/img/4dn_logo.svg"


def convert_to_html(data, environment):
    if is_cgap_env(environment):
        logo_url = CGAP_LOGO_URL
        logo_url_alt = "CGAP helix logo"
        page_name = "CGAP Status"
    else:
        logo_url = FF_LOGO_URL
        logo_url_alt = "4DN sphere logo"
        page_name = "Fourfront Status"

    message = data.get("message")
    calendar_events = data.get('calendar')
    if not calendar_events and not message:
        # When there's no error message to shown, supply a default event if nothing else to show.
        calendar_events = [NULL_EVENT]
    priority = data.get('priority') or DEFAULT_PRIORITY
    event_str = io.StringIO()
    sections_used = []
    for i, event in enumerate(calendar_events, start=1):
        # print("calendar_event=", calendar_event, "i=", i)
        event_name = event.get('name') or "Event %s" % i
        affects = event.get('affects') or {}
        affects_name = affects.get('name') or ""
        # affects_envs = affects.get('environments') or []
        section = io.StringIO()
        section.write('<dt class="calendar-event">%s</dt>\n' % html.escape(event_name))
        section.write("<dd>\n")
        section.write('<p><span class="who">%s</span>' % html.escape(affects_name))
        section.write(' <span class="when">(%s to %s)</span></p>\n'
                      % (html.escape(event.get('start_time') or "now"),
                         html.escape(event.get('end_time') or "the foreseeable future")))
        section.write('<p class="what">%s</p>\n' % (html.escape(event.get("description") or "To Be Determined")))
        section.write("</dt>\n")
        event_str.write(section.getvalue())
        sections_used.append(i)
    event_body = event_str.getvalue()
    message = '<div class="message bgcolor_orange"><p>NOTE: ' + html.escape(message) + '</p></div>' if message else ''
    substitutions = {
        'PRIORITY': priority,
        'LOGO_URL': logo_url,
        'LOGO_URL_ALT': logo_url_alt,
        'PAGE_NAME': page_name,
        'EVENT_BODY': event_body,
        'MESSAGE': message,
    }
    body = '''
<!DOCTYPE html>
<html>
 <head>
  <title>4DN Status</title>
   <meta name="robots" content="noindex, nofollow" />
   <style><!--
   .bgcolor_red {background: #ffdddd}
   .bgcolor_orange {background: #ffeedd}
   .bgcolor_yellow {background: #ffffdd}
   .bgcolor_green {background: #ddffdd}
   .banner {padding-left: 30pt; padding-bottom: 10pt; padding-top: 10pt;}
   .page-name {padding-left: 10pt; font-size: 30pt;}
   .logo {height: 100%; vertical-align: middle; height: 36pt;}
   .calendar {padding-left: 30pt;}
   .calendar-event {font-size: 20pt;}
   .who {font-weight: bold; font-size: 16pt;}
   .when {font-weight: bold; font-size: 14pt;}
   .what {font-size: 12pt;}
   div.message {margin-top: 5pt; padding-left: 30pt; border: 1pt red solid; width: 500pt;}
   div.message p {font-weight: bold;}
  --></style>
 </head>
 <body>
  <div class="banner bgcolor_<<PRIORITY>>" id="banner">
   <table>
    <tr>
     <td valign="middle">
      <img src="<<LOGO_URL>>" class="logo" alt="<<LOGO_URL_ALT>>" />
     </td>
     <td class="page-name" valign="bottom"><<PAGE_NAME>></td>
    </tr>
   </table>
  </div>
  <<MESSAGE>>
  <dl class="calendar">
   <<EVENT_BODY>>
  </dl>
 </body>
</html>'''
    for name, val in substitutions.items():
        body = body.replace('<<' + name + '>>', val)
    return body


def filter_data(data, environment, *, debug=False, now=None):
    calendar_events = data.get("calendar") or []
    priority = DEFAULT_PRIORITY
    # "message" and "problems" are not intended to be used in ordinary calendar.json file.
    # Instead they're used for error handling if the calendar is not available
    # and must be propagated so the end user will understand why data was unavailable.
    message = data.get("message")
    problems = data.get("problems", [])
    filtered_calendar_events = []
    filter_now = as_datetime(now, raise_error=False) or ref_now()
    seen = []
    removed = []
    for event in calendar_events:
        try:
            seen.append(event)
            start_time = event.get('start_time', None)
            end_time = event.get('end_time', None)
            affected_envs = (event.get('affects') or {}).get('environments')
            if affected_envs is None or environment in map(canonicalize_environment, affected_envs):
                if start_time:
                    start_time = as_ref_datetime(start_time)
                    lead_time = event.get('lead_time') or {}
                    if lead_time:
                        if isinstance(lead_time, dict):
                            # "lead_time": {"hours": 1, "minutes": 30}
                            lead_seconds = as_seconds(**lead_time)
                        else:
                            # "lead_time": 5400
                            lead_seconds = lead_time
                        # This operation affects only the filtering, but not the display.
                        start_time -= datetime.timedelta(seconds=lead_seconds)
                if in_datetime_interval(filter_now, start=start_time, end=end_time):
                    filtered_calendar_events.append(event)
                    priority = merge_priorities(priority, event.get("priority"))
                else:
                    removed.append(event)
        except Exception as e:
            problems.append({
                "event": event,
                "message": "%s: %s" % (full_class_name(e), e),
            })
    result = {}
    if debug:
        result["now"] = now
        result["filter_now"] = str(filter_now)
        result["seen"] = seen
        result["defaulted"] = False
        result["removed"] = removed
    result["priority"] = priority
    if message:
        result["message"] = message
    result["calendar"] = filtered_calendar_events
    if problems:
        result["problems"] = problems
    return result


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


def resolve_environment(host, referer, application, environment):
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
    if host and host.startswith("status."):
        host_url = 'https://' + remove_prefix("status.", host)
        classification = classify_server_url(host_url, raise_error=False)
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
    # if params.get("echoevent"):
    #     return {
    #         "statusCode": 200,
    #         "headers": {
    #             "Content-Type": "application/json",
    #             "Cache-Control": "public, max-age=120",
    #             # Note that this does not do Access-Control-Allow-Origin, etc.
    #             # as this is for debugging only. -kmp 19-Mar-2020
    #         },
    #         "body": json.dumps(event, indent=2),
    #         # Maybe also this, too ...
    #         # "context": json.dumps(context)  # or repr(context)
    #     }
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # The referer is available in a standard event packaging, in the headers,
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-data-mappings.html

    try:

        now = params.get("now", None)
        debug = params.get("debug", "FALSE").upper() == "TRUE"
        application = params.get("application")
        host = event.get('headers', {}).get('host')
        referer = event.get('headers', {}).get('referer')
        environment = params.get("environment")
        environment = resolve_environment(host=host, referer=referer, application=application, environment=environment)
        data = filter_data(data, environment, debug=debug, now=now)
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

        return {"message": "%s: %s" % (full_class_name(e), e)}


if __name__ == '__main__':

    raise RuntimeError("Tests have moved. Use the `brig-test` script.")
