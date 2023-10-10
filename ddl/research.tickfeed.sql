-- SCHEMA: tickfeed 

-- DROP SCHEMA IF EXISTS tickfeed;

CREATE SCHEMA IF NOT EXISTS tickfeed
    AUTHORIZATION user;

GRANT ALL ON SCHEMA tickfeed TO user;

GRANT USAGE ON SCHEMA tickfeed TO tickfeedwriter;
