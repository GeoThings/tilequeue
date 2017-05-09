import sys
import traceback
import re
from itertools import islice
from datetime import datetime
from tilequeue.tile import coord_marshall_int
from tilequeue.tile import create_coord

def format_stacktrace_one_line(exc_info=None):
    # exc_info is expected to be an exception tuple from sys.exc_info()
    if exc_info is None:
        exc_info = sys.exc_info()
    exc_type, exc_value, exc_traceback = exc_info
    exception_lines = traceback.format_exception(exc_type, exc_value,
                                                 exc_traceback)
    stacktrace = ' | '.join([x.replace('\n', '')
                             for x in exception_lines])
    return stacktrace


def grouper(iterable, n):
    """Yield n-length chunks of the iterable"""
    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, n))
        if not chunk:
            return
        yield chunk

def parse_log_file(log_file):
    ip_pattern = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    # didn't match againts explicit date pattern, in case it changes
    date_pattern = '\[([\d\w\s\/:]+)\]'
    tile_id_pattern = '\/([\w]+)\/([\d]+)\/([\d]+)\/([\d]+)\.([\d\w]*)'

    log_pattern = '%s - - %s "([\w]+) %s.*' % (ip_pattern, date_pattern, tile_id_pattern)

    iped_dated_coords = []
    for log_string in log_file:
        match = re.search(log_pattern, log_string)
        if match and len(match.groups()) == 8:
            iped_dated_coords.append((match.group(1), 
                                      datetime.strptime(match.group(2), '%d/%B/%Y %H:%M:%S'), 
                                      coord_marshall_int(create_coord(match.group(6), match.group(7), match.group(5)))))

    return iped_dated_coords

def mimic_prune_tiles_of_interest_sql_structure(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS tile_traffic_v4 (
            id bigserial primary key,
            date timestamp(6) not null,
            z integer not null,
            x integer not null,
            y integer not null,
            tilesize integer not null,
            service varchar(32),
            host inet not null
        )''')

def postgres_add_compat_date_utils(cursor):
    cursor.execute('''
        CREATE OR REPLACE FUNCTION DATEADD(interval_kind VARCHAR(20), interval_offset INTEGER, dt DATE)
        RETURNS TIMESTAMP AS $$
        BEGIN
            RETURN (SELECT dt + (interval_offset || ' ' || interval_kind)::INTERVAL);
        END;
        $$ language plpgsql
    ''')
    cursor.execute('''
        CREATE OR REPLACE FUNCTION GETDATE()
        RETURNS DATE AS $$
        BEGIN
            RETURN (SELECT current_date);
        END;
        $$ language plpgsql
    ''')
