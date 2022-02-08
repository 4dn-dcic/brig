====
brig
====

----------
Change Log
----------


0.5.1
=====

**PR 8: Cosmetic updates.**

* Adds a CHANGELOG.rst


0.5.0
=====

**PR 7: Python 3.7 and 3.8 upgrade**

* In service of C4-762, and in spite of the PR name,
  this change adds support for:

  * Python 3.7
  * Python 3.8
  * Python 3.9


0.4.0
=====

**PR 6: Changes to remove variable imports from env_utils (C4-700)**

* With this change, ``brig`` only imports functions from ``env_utils``, not variables.


0.3.0
=====

**PR 5: Dcument the 4dn-status protocol (C4-509)**

* Add documentation of the ``4dn-status`` protocol.

* Changed data format to be easier to document.

  * "bgcolor" is changed to "priority" and is a symbolic quality.

  * In calendar events, changed the field named ``"message"`` to ``"description"``.
  * Implemented ``"lead_time"`` so that notices can show up in advance of when they're active.
  * Fixed a bug where it only looked at referer and not host,
    so that now it can hopefully work on ``status.cgap.hms.harvard.edu``
    and ``status.data.4dnucleome.org``.

0.2.0
=====

**PR 3: Modify 4dn-status API to do the filtering work server-side (C4-363)**

* Add an ``application=`` query param that can be either ``cgap`` or ``fourfront``
  as a way of creating a backstop that is used if the referer is compromised.
  Ordinarily, an explicit environment has highest priority,
  but is no longer expected to be passed because it's hard to obtain in the client.
  Next the referer (in the headers, not query params) is preferred,
  but that's unreliable in some cases (especially localhost testing but maybe some clients.
  All calls should include ``application=cgap`` or ``application=fourfront``
  as a query param in case referer fails, since otherwise the default is information
  about fourfront-webprod because an arbitrary choice has to be made.

* Make timezone default to Eastern so that it doesn't have to be specified using
  the confusing ``-0400`` or ``-0500`` notation.
  Timezone can just be omitted and will default to HMS time.
  If supplied, it will be used as indicated unless the time simply doesn't parse,
  in which case it will be treated as if not supplied.

* Make environment passed get canonicalized in ``prod``,`` so basically any                                                                                                                                                                                                                               ,   green, or blue indicator is treated as a synonym.

* Add appropriate unit tests.

* Make some adjustments to file configurations and scripts to accommodate better debugging in PyCharm.
  There is now a ``pyproject.toml``                                                                                                                                                                         at repo toplevel that is only for debugging use
  but can be used to manage the venv you use for PyCharm.
  It should contain a set of requirements that's the union of all requirements
  in the repo (in any api or function), but that has to be manually maintained.
  Since it doesn't change often, that shouldn't be hard.

**PR 4: Additional API changes (C4-363)**

* Newly uses dcicutils 1.8.1 in lieu of removed file ``qa_utils_subset.py``,
  which had some duplicated functionality.

  To  use the interfaces from ``qa_utils``, some compatibility issues
  had to be addressed. For example:

  * in_date_range became in_date_interval

  * Uses new ``classify_server_url`` to figure out what kind of server
    the referer url is.

* Created a prd/stg distinction so this functionality is more easily tested.

  * ``CALENDAR_DATA_URL`` became ``CALENDAR_DATA_URL_PRD`` and ``CALENDAR_DATA_URL_STG.

  * The appropriate calendar data URL is chosen based on whether
    ``PRD_ENDPOINT_PATH`` (/4dn-status) or
    ``STG_ENDPOINT_PATH`` (/4dn-status-staged) is used,
    so that each of the production and staged repos has different data
    to allow for easy testing as a lambda function.

* Data files no longer have to contain timezones. They will be parsed
  as HMS-relative (US/Eastern) and so will get the appropriate daylight
  time best if a TZ is not given.
  It is OK (but error prone) to still use a `-0500` or `-0400` offset.
  Better to just omit it.

* Added a ``try`` around the main handler,
  yielding better error messaging if an error occurs.

Earlier than 0.2.0
==================

There was no poetry back then, so versioning was approximate.

**PR 1: Some initial file layout & documentation, and sources for 4dn-status function**

* Add some proposed structure. Check in some sources.

* Create a ``README.rst``.

**PR 2:Refactor 4dn-status testing**

* Refactor testing from ``4dn-status`` so that it happens in a separate file.

* Give some scripts different names so people can put them in their search path
  without them colliding with other things.

* Adjust documentation.

