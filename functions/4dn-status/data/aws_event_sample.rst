The result of this operation::

   curl --referer http://foo.com \
        https://505darvwgc.execute-api.us-east-1.amazonaws.com/4dn-status?echoevent=true

Yields this::

   {
     "version": "2.0",
     "routeKey": "ANY /4dn-status",
     "rawPath": "/4dn-status",
     "rawQueryString": "echoevent=true",
     "headers": {
       "accept": "*/*",
       "content-length": "0",
       "host": "505darvwgc.execute-api.us-east-1.amazonaws.com",
       "referer": "http://foo.com",
       "user-agent": "curl/7.64.1",
       "x-amzn-trace-id": "...some-id...",
       "x-forwarded-for": "1.2.3.4",
       "x-forwarded-port": "443",
       "x-forwarded-proto": "https"
     },
     "queryStringParameters": {
       "echoevent": "true"
     },
     "requestContext": {
       "accountId": "123456789012",
       "apiId": "505darvwgc",
       "domainName": "505darvwgc.execute-api.us-east-1.amazonaws.com",
       "domainPrefix": "505darvwgc",
       "http": {
         "method": "GET",
         "path": "/4dn-status",
         "protocol": "HTTP/1.1",
         "sourceIp": "1.2.3.4",
         "userAgent": "curl/7.64.1"
       },
       "requestId": "...another-id...",
       "routeKey": "ANY /4dn-status",
       "stage": "$default",
       "time": "30/Oct/2020:06:33:44 +0000",
       "timeEpoch": 1604039624859
     },
     "isBase64Encoded": false
   }

Without the ``--referer`` argument to ``curl``, this line will be absent in ``"headers"``::

       "referer": "http://foo.com",


