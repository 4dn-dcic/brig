import html
import http
import io
import json
import requests

SAMPLE_DATA = {
    "bgcolor": "#ffcccc",
    "events":
        [
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
        ],
    }
    
DEFAULT_DATA = {
    "bgcolor": "#ccffcc",
    "events":
        [
            {
                "name": "No Scheduled Events",
                "start_time": "now",
                "end_time": "foreseeable future",
                "message": "There's nothing to report here.",
                "affects": {
                    "name": "All Systems",
                    "environments": None,
                },
            },
        ],
    }


ACTUAL_DATA = {
    "bgcolor": "#ffcccc",
    "events":
        [
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
        ],
    }


def get_data():
   r = requests.get("https://4dn-dcic-publicly-served.s3.amazonaws.com/4dn-status/events.json")
    result = r.json()
    # result = ACTUAL_DATA
    return result or DEFAULT_DATA

def get_data():
    result = ACTUAL_DATA
    return result or DEFAULT_DATA
    
PAGE_NAME = "4DN Status"

def lambda_handler(event, context):
    body = io.StringIO()
    data = get_data()
    events = data.get("events", [])
    bgcolor = data.get("bgcolor", "#dddddd")
    page_name = html.escape(PAGE_NAME)
    body.write("<!DOCTYPE html>")
    body.write("<html>\n<head>\n")
    body.write("<title>%s</title>" % page_name)
    body.write('<meta name="robots" content="noindex, nofollow" />')
    body.write("<style><!--\n")
    body.write('.banner {padding-left: 30pt; background: %s; padding-bottom: 10pt; padding-top: 10pt;}\n' % bgcolor)
    body.write('.page-name {padding-left: 10pt; font-size: 30pt;}\n')
    body.write('.logo {height: 100%; vertical-align: middle;}')
    body.write('.events {padding-left: 30pt;}\n')
    body.write('.event {font-size: 20pt;}\n')
    body.write('.who {font-weight: bold; font-size: 16pt;}\n')
    body.write('.when {font-weight: bold; font-size: 14pt;}\n')
    body.write('.what {font-weight: 12pt;}\n')
    body.write('--></style>\n')
    body.write('</head>\n<body>\n')
    body.write('<div class="banner">\n')
    body.write('<table><tr>\n')
    body.write('<td valign="middle"><img src="https://4dnucleome.org/Assets/images/4dn-logo_1.png" class="logo" alt="4D Nucleome" /></td>\n')
    body.write('<td class="page-name" valign="bottom">%s</td>\n' % page_name)
    body.write('</tr></table></div>\n')
    body.write('<dl class="events">\n')
    for i, item in enumerate(events):
        body.write('<dt class="event">%s</dt>\n' % html.escape(item.get('name', "Event %s" % i)))
        body.write("<dd>\n")
        body.write('<p><span class="who">%s</span>' % html.escape(item.get('affects', {}).get('name', "All Systems")))
        body.write(' <span class="when">(%s to %s)</span></p>\n' 
                   % (html.escape(item.get('start_time', 'now')),
                      html.escape(item.get('end_time', 'the foreseeable future'))))
        body.write('<p class="what">%s</p>\n' % html.escape(item.get('message', "To Be Determined")))
        body.write("</dt>\n")
    body.write("</dl>\n")
    # body.write("<pre>\n")
    # body.write(html.escape(json.dumps({"event": event}, indent=2)))
    # body.write("</pre>\n")
    body.write("</body></html>")
    body_text = body.getvalue()
    format = event.get("queryStringParameters", {}).get("format")
    if format == "json":
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            'body': json.dumps(data, indent=2),
        }
    else:
        return {
          'statusCode': 200,
          "headers": {
              'Content-Type': 'text/html',
           },
           'body': body_text
       }

if __name__ == '__main__':
    print(lambda_handler(None, None))
