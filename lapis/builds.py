# export module as lapis.builds

# set up the database
import postgresql
import json
import os
import time


#JSON schema for builds
schema = {
    'id': int,
    'name': str,
    'description': str,
    'source': str,
    'status': str,
    'started_at': str, #ISO 8601
    'finished_at': str, # ISO 8601
    'duration': int,
    'output': [
        {
            'name': str,
            'path': str,
            'size': int,
            'mtime': str, # ISO 8601
        }
    ]
}
# Postgresql schema setup
schema_sql = """
CREATE TABLE IF NOT EXISTS builds (
    id serial PRIMARY KEY,
    name varchar(255) NOT NULL,
    description varchar(255) NOT NULL,
    source varchar(255) NOT NULL,
    status varchar(255) NOT NULL,
    started_at timestamp NOT NULL,
    finished_at timestamp,
    duration int,
    output jsonb NOT NULL
);
"""

#export module as lapis.builds
