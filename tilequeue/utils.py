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

    tile_log_records = []
    for log_string in log_file:
        match = re.search(log_pattern, log_string)
        if match and len(match.groups()) == 8:
            tile_log_records.append((match.group(1), 
                                      datetime.strptime(match.group(2), '%d/%b/%Y %H:%M:%S'), 
                                      coord_marshall_int(create_coord(match.group(6), match.group(7), match.group(5)))))

    return tile_log_records


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


class LayerConfig(object):

    def __init__(self, all_layer_names, layer_data):
        self.all_layer_names = sorted(all_layer_names)
        self.layer_data = layer_data
        self.layer_data_by_name = dict(
            (layer_datum['name'], layer_datum) for layer_datum in layer_data)
        self.all_layers = [self.layer_data_by_name[x]
                           for x in self.all_layer_names]


def parse_layer_spec(layer_spec, layer_config):
    """convert a layer spec into layer_data

    returns None is any specs in the optionally comma separated list
    are unknown layers"""
    if layer_spec == 'all':
        return layer_config.all_layers
    individual_layer_names = layer_spec.split(',')
    unique_layer_names = set()
    for layer_name in individual_layer_names:
        if layer_name == 'all':
            if 'all' not in unique_layer_names:
                for all_layer_datum in layer_config.all_layers:
                    unique_layer_names.add(all_layer_datum['name'])
        unique_layer_names.add(layer_name)
    sorted_layer_names = sorted(unique_layer_names)
    layer_data = []
    for layer_name in sorted_layer_names:
        if layer_name == 'all':
            continue
        layer_datum = layer_config.layer_data_by_name.get(layer_name)
        if layer_datum is None:
            return None
        layer_data.append(layer_datum)
    return layer_data
