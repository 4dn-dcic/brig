==========
4dn-status
==========

If you have a function that is not part of an API, make a folder for it here.

General Information about brig functions
========================================

For more details, see `README.rst <../../README.rst>`_ in the ``brig`` repository root folder.

For information specifically about testing, see `TESTING.rst <../TESTING.rst>`_
in the same folder.

Staging and Deploying this interface
====================================

This interface is intended for upload to the 4dn-status lambda function.

There is also a 4dn-status-staged function you can use for testing.

4dn-status Data storage
=======================

Location of 4dn-status data
---------------------------

Storage for the ``/4dn-status`` endpoint is in S3 at:

   s3://4dn-dcic-publicly-served/4dn-status/calendar.json

Storage for the ``/4dn-status-staged`` endpoint is in S3 at:

   s3://4dn-dcic-publicly-served/4dn-status/calendar-staged.json

Format of a calendar.json file
------------------------------

The json data file for this endpoint contains a dictionary that can contain
data of the following kind. See the functionality description for information
on how this data is used.

* ``"calendar"`` (required)

  The calendar is a possibly empty list of
  ``<calendar-event>`` objects.

A ``<calendar-event>`` can have any of these fields:

* ``"name"`` (required)

  The name is a ``<string>`` that names the event.

* ``"description"``

  The description is a ``<string>`` that describes the event, usually in more detail
  than the name.

* ``"priority"`` (optional, default ``"green"``)

  A ``<priority-string>`` that specifies that the banner
  should have at least this priority if this event is displayed.

* ``"start_time"`` (optional, default ``null``)

  The start time is a ``<datetime-string>`` (or ``null``)
  specifying when the calendar event starts.
  If null or unspecified, it defaults to the beginning of time.

* ``"end_time"`` (optional, default ``null``)

  The end time is a ``<datetime-string>`` (or ``null``)
  specifying when the calendar event starts.
  If null or unspecified, it defaults to the end of time.

* ``"lead_time"`` (optional, default ``null``)

  The lead time is ``<relative-time-spec>`` that specifies an additional bit of
  time before a given event where the notice of the event should appear even though
  the event has not begun.

* ``"affects"`` (optional, default ``null``)

  A ``<affects-spec>`` describing the set of affected servers.
  If omitted, all environments are assumed affected.

The ``<affects-spec>`` has these elements:

* ``"name"``

  The name is a summary of affected systems for the situation where
  it's only certain systems. e.g., "CGAP Dev Systems"

* ``"environments"`` (optional, default a list of all valid environments)

  A list of the systems that this outage applies to.

  For Fourfront staging or production, ``fourfront-webprod`` is used in place
  of an ordinary name, since the blue/green distinction is problematic. It does
  not matter that we don't call it that name any more as an environment. (This
  is a formal token that is chosen using ``dcicutils.env_utils.get_bucket_env``.)

  For CGAP staging or production, ``fourfront-cgap`` is used for similar reasons.
  Of course, there is no CGAP staging right now, but there could be in the future.

Type Definitions
~~~~~~~~~~~~~~~~

* **<datetime-string>**

  A ``<datetime-string>`` is a ``<string>``
  of specialized form, specifically the
  format ``YYYY-mm-dd hh:mm:ss``
  and will be assumed to be relative to the reference time frame of the system,
  (which is ``US/Eastern`` for hms-based systems).

  It is also possible to specify
  a specific timezone, as in ``YYYY-mm-dd hh:mm:ss-nnnn`` or
  ``YYYY-mm-dd hh:mm:ss+nnnn`` where ``nnnn`` is an
  ``hhmm`` specification of a timezone offset to be added or subtracted to ``UTC``.
  This notation is *not* recommended because it will not respect daylight time.
  Using the reference time *will* use daylight time as appropriate.

* **<priority-string>**

  A ``<priority-string>`` is a ``<string>`` of specialized form.
  These are strings that represent CSS styles when using
  an HTML response.

  * ``"red"`` - Events that are outages.
  * ``"yellow"`` - Events that involve variable or risky behavior.
  * ``"green"`` - Events that are not disruptive or a notice about a lack of events.

  If multiple bgstyles are in play, the one with the
  highest priority will take precedence, using priority
  from lowest (``"green"``) to highest (``"red"``).

* **<relative-time-spec>**

  A ``<relative-time-spec>`` is either a number of seconds
  or else a dictionary with fields that specify the number of seconds in parts
  the way people talk about them. For example, 36 hours could be referred to as
  any of these:

  * ``{"days" 1, "hours": 12}``
  * ``{"days": 1.5}``
  * ``{"hours": 36}``
  * ``{"hours": 35, "minutes": 59, "seconds" 60}``

  Normally one would not use obscure breakdowns like the last one, of course.
  In general, the idea is to allow relative times to be referred to in a way
  intelligible to the human eye.

  Possible fields if the dictionary form is used are:

  * ``"days"``
  * ``"hours"``
  * ``"minutes"``
  * ``"seconds"``

* **<string>**

  A JSON string.


4dn-status Functionality
========================

The endpoint ``/4dn-status`` (and ``/4dn-status-staging``) returns status information
for a particular affected environment.

Query Parameters
----------------

* **application**

  The application specified should be one of ``fourfront`` or ``cgap``.
  Using this bypasses any heuristics related to the name of a referring URL.

* **environment**

  The environment can be something like ``fourfront-mastertest`` or another so-called "ffenv"
  name, to include the name of a CGAP env such as ``fourfront-cgapdev``. This is more specific
  than using ``application`` so takes priority. There is no need to supply both. However, the
  UI might not be aware of the exact environment name.  If supplying this explicitly, use
  ``fourfront-webprod`` for either staging (``staging.4dnucleome.org``)
  or production (``data.4dnucleome.org``). Use ``fourfront-cgap`` for production CGAP
  (``cgap.hms.harvard.edu``).

Debugging parameters **not to be used in production**:

* **debug**

  Causes the response to contain debugging information (when ``format=json`` is also used).

* **format**

  When used with ``format=json`` the result is JSON rather than HTML.

* **now**

  Can be used to specify a reference time, rather than the current time, for interactive testing.
  The time should be in the format of a ``<datetime-string>``.

Format of endpoint call result
------------------------------

The call will return data that is similar to what's in the calendar.json file, but
filtered to contain only relevant entries matching:

* The time at which the call is made.

  For debugging only, the time can be overridden with ``now=``
  as a query parameter.

* The ``environment=`` parameter given. (See the ``affects`` specification in the
  calendar.json file.

  If no ``environment=`` is given, then if ``application=`` is given, the environment
  ``fourfront-webprod`` is used for ``fourfront`` and ``fourfront-cgap`` is given for
  ``cgap``.


  If neither ``environment=`` or ``application=`` is given, then if the referer is
  a CGAP url, ``application=cgap`` will be assumed, and otherwise ``application=fourfront``
  will be assumed.

The following additional fields may appear and have the following meaning:

* ``"message"``

  If a ``"message"`` is present, it is an error message to be used instead of the
  calendar data.

* ``"problems"``

  If ``"problems"`` is given, it is a list of detailed information about errors that
  happened. It is for debugging only and is not intended to be presented to users.

* ``"priority"``

  If a ``"priority"`` appears, it will be a ``<priority-string>``.
  This token may be useful in picking a display color for the data.

  Individual calendar entries will have possibly-differing priorities, but
  if the overall calendar priority is ``"green"``, it may be useful to just omit
  display of the calendar entirely, as this indicates normal system operation
  and not a piece of priority information.

CGAP vs Fourfront
-----------------

It is recommended that any call from the CGAP application use the query argument
``application=cgap`` and any call from Fourfront use the query argument ``application=fourfront``.
This will avoid any confusion if the ``referer`` header is missing or mal-formed.

By default, the host is the primary server host, so that the production application
doesn't have to say. That is, ``/4dn-status`` for CGAP any CGAP environment
will look at the ``referer`` header, see that it is a cgap host,
and will return information about ``cgap.hms.harvard.edu`` as if
``/4dn-status?environment=fourfront-cgap`` had been supplied, and similarly for
any non-CGAP host will return information as if
``/4dn-status?environment=fourfront-webprod`` had been supplied.

.. note::

   See explanation of ``<affects-spec>`` above for more information about this choice
   of environment name.

Examples
========

Given a calendar file like::

   {
     "calendar: []
   }

Browsing to::

    /4dn-status?application=cgap

Will might show an HTML page with this essential content::

    ===== [CGAP helix logo] CGAP Status ===== <- green banner
    No Scheduled Events
    All Systems (now to the foreseeable future)
    No known problems. No disruptions planned.

Given::

    /4dn-status?application=cgap&format=json

the result will be::

   {
     "priority": "green",
     "calendar": []
   }

This same result might happen if the calendar contains events in the past or
in the too-far future::

   {
     "calendar: [{
       "start_time": "2050-01-01 00:00:00",
       "end_time": "2050-01-02 00:00:00",
       "lead_time": {"weeks": 1},
       "name": "CGAP Long-term Maintenance",
       "description": "Background testing that CGAP's part have not rusted out from old age.",
       "priority": "yellow",
       "affects": {"environments": ["fourfront-cgap"], "name": "CGAP"}
     }]
   }

A week before the specified start time, however, the result will start to be::

   {
     "priority": "yellow",
     "calendar: [{
       "start_time": "2050-01-01 00:00:00",
       "end_time": "2050-01-02 00:00:00",
       "lead_time": {"weeks": 1},
       "name": "CGAP Long-term Maintenance",
       "description": "Background testing that CGAP's part have not rusted out from old age.",
       "priority": "yellow",
       "affects": {"environments": ["fourfront-cgap"], "name": "CGAP"}
     }]
   }

with corresponding HTML that displays as something like::

   ===== [4DN sphere logo] CGAP Status ===== <- yellow banner
   CGAP Long-Term Maintenance
   CGAP (2050-01-01 00:00:00 to 2050-01-02 00:00:00)
   Background testing that CGAP's part have not rusted out from old age.

