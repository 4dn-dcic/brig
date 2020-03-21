The master copy of this data is in `4dn-dcic-publicly-served/4dn-status/ <https://s3.console.aws.amazon.com/s3/buckets/4dn-dcic-publicly-served/4dn-status/?region=us-east-1#>`_.

The events.json file should contain::

    {
        "page_name": "4DN Status",         # The name of the page
        "bgcolor": "#ffcccc",              # The color of the banner
        "events": [ 
            {...event description...}, ...
        ]
    }

where an event description looks like::

    {
        # The name of the event
        "name": "Fourfront System Upgrades",
        # When the event starts (optional, default now)
        "start_time": "2020-03-23 16:00:00-0400",
        # When the event stops (optional, default never)
        "end_time": "2020-03-24 20:00:00-0400",
        # A description of the event
        "message": "Upgrades to be performed.",
        "affects": {
            # A name for what's affected
            "name": "All Fourfront Systems",       
            # Specific environments affected
            "environments": [
                "fourfront-hotseat", ...
            ]
        }
    }

Note that the times don't have to be something that can be parsed.
