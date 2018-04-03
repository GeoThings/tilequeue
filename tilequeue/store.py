# define locations to store the rendered data

from boto import connect_s3
from boto.s3.bucket import Bucket
from builtins import range
from future.utils import raise_from
import md5
import os
from tilequeue.metatile import metatiles_are_equal
from tilequeue.format import zip_format
import random
import threading
from tilequeue.tile import reproject_lnglat_to_mercator, coord_to_mercator_bounds, calc_meters_per_pixel_dim
from tilequeue.transform import mercator_point_to_lnglat, transform_feature_layers_shape
from cStringIO import StringIO
import shapely
import json


def calc_hash(s):
    m = md5.new()
    m.update(s)
    md5_hash = m.hexdigest()
    return md5_hash[:5]


def s3_tile_key(date, path, layer, coord, extension):
    prefix = '/%s' % path if path else ''
    path_to_hash = '%(prefix)s/%(layer)s/%(z)d/%(x)d/%(y)d.%(ext)s' % dict(
        prefix=prefix,
        layer=layer,
        z=coord.zoom,
        x=coord.column,
        y=coord.row,
        ext=extension,
    )
    md5_hash = calc_hash(path_to_hash)
    s3_path = '/%(date)s/%(md5)s%(path_to_hash)s' % dict(
        date=date,
        md5=md5_hash,
        path_to_hash=path_to_hash,
    )
    return s3_path


class S3(object):

    def __init__(
            self, bucket, date_prefix, path, reduced_redundancy):
        self.bucket = bucket
        self.date_prefix = date_prefix
        self.path = path
        self.reduced_redundancy = reduced_redundancy

    def write_tile(self, tile_data, coord, format, layer):
        key_name = s3_tile_key(
            self.date_prefix, self.path, layer, coord, format.extension)
        key = self.bucket.new_key(key_name)
        key.set_contents_from_string(
            tile_data,
            headers={'Content-Type': format.mimetype},
            policy='public-read',
            reduced_redundancy=self.reduced_redundancy,
        )

    def read_tile(self, coord, format, layer):
        key_name = s3_tile_key(
            self.date_prefix, self.path, layer, coord, format.extension)
        key = self.bucket.get_key(key_name)
        if key is None:
            return None
        tile_data = key.get_contents_as_string()
        return tile_data

    def delete_tiles(self, coords, format, layer):
        key_names = [
            s3_tile_key(self.date_prefix, self.path, layer, coord, format.extension)
            for coord in coords
        ]
        del_result = self.bucket.delete_keys(key_names)
        return len(del_result.deleted)


def make_dir_path(base_path, coord, layer):
    path = os.path.join(
        base_path, layer, str(int(coord.zoom)), str(int(coord.column)))
    return path


def make_file_path(base_path, coord, layer, extension):
    basefile_path = os.path.join(
        base_path, layer,
        str(int(coord.zoom)), str(int(coord.column)), str(int(coord.row)))
    ext_str = '.%s' % extension
    full_path = basefile_path + ext_str
    return full_path


def os_replace(src, dst):
    '''
    Simple emulation of function `os.replace(..)` from modern version
    of Python. Implementation is not fully atomic, but enough for us.
    '''

    orig_os_replace_func = getattr(os, 'replace', None)

    if orig_os_replace_func is not None:
        # not need for emulation: we using modern version of Python.
        # fully atomic for this case

        orig_os_replace_func(src, dst)
        return

    if os.name == 'posix':
        # POSIX requirement: `os.rename(..)` works as `os.replace(..)`
        # fully atomic for this case

        os.rename(src, dst)
        return

    # simple emulation for `os.name == 'nt'` and other marginal
    # operation systems.  not fully atomic implementation for this
    # case

    try:
        # trying atomic `os.rename(..)` without `os.remove(..)` or
        # other operations

        os.rename(src, dst)
        error = None
    except OSError as e:
        error = e

    if error is None:
        return

    for i in range(5):
        # some number of tries may be failed
        # because we may be in concurrent environment with other
        # processes/threads

        try:
            os.remove(dst)
        except OSError:
            # destination was not exist
            # or concurrent process/thread is removing it in parallel with us
            pass

        try:
            os.rename(src, dst)
            error = None
        except OSError as e:
            error = e
            continue

        break

    if error is not None:
        raise_from(OSError('failed to replace'), error)


class TileDirectory(object):
    '''
    Writes tiles to individual files in a local directory.
    '''

    def __init__(self, base_path):
        if os.path.exists(base_path):
            if not os.path.isdir(base_path):
                raise IOError(
                    '`{}` exists and is not a directory!'.format(base_path))
        else:
            os.makedirs(base_path)

        self.base_path = base_path

    def write_tile(self, tile_data, coord, format, layer):
        dir_path = make_dir_path(self.base_path, coord, layer)
        try:
            os.makedirs(dir_path)
        except OSError:
            pass

        file_path = make_file_path(self.base_path, coord, layer,
                                   format.extension)
        swap_file_path = '%s.swp-%s-%s-%s' % (
            file_path,
            os.getpid(),
            threading.currentThread().ident,
            random.randint(1, 1000000)
        )

        try:
            with open(swap_file_path, 'w') as tile_fp:
                tile_fp.write(tile_data)

            # write file as atomic operation
            os_replace(swap_file_path, file_path)
        except Exception as e:
            try:
                os.remove(swap_file_path)
            except OSError:
                pass
            raise e

    def read_tile(self, coord, format, layer):
        file_path = make_file_path(self.base_path, coord, layer,
                                   format.extension)
        try:
            with open(file_path, 'r') as tile_fp:
                tile_data = tile_fp.read()
            return tile_data
        except IOError:
            return None

    def delete_tiles(self, coords, format, layer):
        delete_count = 0
        for coord in coords:
            file_path = make_file_path(self.base_path, coord, layer, format.extension)
            if os.path.isfile(file_path):
                os.remove(file_path)
                delete_count += 1

        return delete_count


def make_tile_file_store(base_path=None):
    if base_path is None:
        base_path = 'tiles'
    return TileDirectory(base_path)


class Memory(object):

    def __init__(self):
        self.data = None

    def write_tile(self, tile_data, coord, format, layer):
        self.data = tile_data, coord, format, layer

    def read_tile(self, coord, format, layer):
        if self.data is None:
            return None
        tile_data, coord, format, layer = self.data
        return tile_data


def make_s3_store(bucket_name,
                  aws_access_key_id=None, aws_secret_access_key=None,
                  path='osm', reduced_redundancy=False, date_prefix=''):
    conn = connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = Bucket(conn, bucket_name)
    s3_store = S3(bucket, date_prefix, path, reduced_redundancy)
    return s3_store


def tiles_are_equal(tile_data_1, tile_data_2, fmt):
    """
    Returns True if the tile data is equal in tile_data_1 and tile_data_2. For
    most formats, this is a simple byte-wise equality check. For zipped
    metatiles, we need to check the contents, as the zip format includes
    metadata such as timestamps and doesn't control file ordering.
    """

    if fmt and fmt == zip_format:
        return metatiles_are_equal(tile_data_1, tile_data_2)

    else:
        return tile_data_1 == tile_data_2


def write_tile_if_changed(store, tile_data, coord, format, layer):
    """
    Only write tile data if different from existing.

    Try to read the tile data from the store first. If the existing
    data matches, don't write. Returns whether the tile was written.
    """

    existing_data = store.read_tile(coord, format, layer)
    if not existing_data or \
       not tiles_are_equal(existing_data, tile_data, format):
        store.write_tile(tile_data, coord, format, layer)
        return True
    else:
        return False


def ensure_utf8_properties(props):
    new_props = {}
    for k, v in props.items():
        if isinstance(k, unicode):
            k = k.encode('utf-8')
        if isinstance(v, unicode):
            v = v.encode('utf-8')
        new_props[k] = v
    return new_props


def decode_json_tile_for_layers(tile_data, layer_data):
    layer_names_to_keep = set(ld['name'] for ld in layer_data)
    feature_layers = []
    json_data = json.loads(tile_data)
    for layer_name, json_layer_data in json_data.items():
        if layer_name not in layer_names_to_keep:
            continue
        features = []
        json_features = json_layer_data['features']
        for json_feature in json_features:
            json_geometry = json_feature['geometry']
            shape_lnglat = shapely.geometry.shape(json_geometry)
            shape_mercator = shapely.ops.transform(
                reproject_lnglat_to_mercator, shape_lnglat)
            properties = json_feature['properties']
            # Ensure that we have strings for all key values and not
            # unicode values. Some of the encoders except to be
            # working with strings directly
            properties = ensure_utf8_properties(properties)
            fid = None
            feature = shape_mercator, properties, fid
            features.append(feature)
        # a further transform asks for a layer_datum is_clipped
        # property where it applies clipping
        # but this data coming from json is already clipped
        feature_layer = dict(
            name=layer_name,
            features=features,
            layer_datum=dict(is_clipped=False),
        )
        feature_layers.append(feature_layer)
    return feature_layers


def reformat_selected_layers(
        json_tile_data, layer_data, coord, format, buffer_cfg):
    """
    Reformats the selected (subset of) layers from a JSON tile containing all
    layers. We store "tiles of record" containing all layers as JSON, and this
    function does most of the work of reading that, pruning the layers which
    aren't needed and reformatting it to the desired output format.
    """

    feature_layers = decode_json_tile_for_layers(json_tile_data, layer_data)
    bounds_merc = coord_to_mercator_bounds(coord)
    bounds_lnglat = (
        mercator_point_to_lnglat(bounds_merc[0], bounds_merc[1]) +
        mercator_point_to_lnglat(bounds_merc[2], bounds_merc[3]))

    meters_per_pixel_dim = calc_meters_per_pixel_dim(coord.zoom)

    scale = 4096
    feature_layers = transform_feature_layers_shape(
        feature_layers, format, scale, bounds_merc,
        meters_per_pixel_dim, buffer_cfg)

    tile_data_file = StringIO()
    format.format_tile(tile_data_file, feature_layers, coord.zoom,
                       bounds_merc, bounds_lnglat)
    tile_data = tile_data_file.getvalue()
    return tile_data