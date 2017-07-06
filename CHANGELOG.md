CHANGELOG
=========

v1.8.0
------
* Move TOI from redis to s3.
* Support reading immortal tiles from s3.
* Split up process_coord into process and format.
* Create a TOI set on seed if file toi-set doesn’t exist.
* Add fix when metatiles are disabled.
* Support single file for intersect command.
* Add only valid zoom levels to TOI.

v1.7.0
------
* **New features:**
    * Add new command that 'gardens' the tiles of interest set to add and remove tiles based on various rules. See [#176](https://github.com/tilezen/tilequeue/pull/176), [#178](https://github.com/tilezen/tilequeue/pull/178), [#179](https://github.com/tilezen/tilequeue/pull/179), [#180](https://github.com/tilezen/tilequeue/pull/180), [#182](https://github.com/tilezen/tilequeue/pull/182), [#183](https://github.com/tilezen/tilequeue/pull/183), [#184](https://github.com/tilezen/tilequeue/pull/184), and [#189](https://github.com/tilezen/tilequeue/pull/189).
* **Enhancements:**
    * When enqueueing tiles of interest for seed rendering, enqueue at zoom level 15 instead of 16. See [#181](https://github.com/tilezen/tilequeue/pull/181).
    * Add optional support for `statsd` in command.py. See [#185](https://github.com/tilezen/tilequeue/pull/185).

v1.6.0
------
* **New features:**
    * Add support for 2x2 metatiles (and 512px tiles). See [#163](https://github.com/tilezen/tilequeue/pull/163), [#166](https://github.com/tilezen/tilequeue/pull/166), and [#169](https://github.com/tilezen/tilequeue/pull/169).
    * Cut child 256px tiles from 512px parent in the 2x2 metatile, rather than re-requesting that 256px bbox from database. See [#158](https://github.com/tilezen/tilequeue/pull/158).
    * Pass nominal zoom instead of coordinates. See [#161](https://github.com/tilezen/tilequeue/pull/161).
* **Enhancements:**
    * Drop parts of MultiPolygons which lie outside the clip boundary of the tile (primarily affects buildings and water layers). See [#171](https://github.com/tilezen/tilequeue/pull/171).
    * Make queue sizes configurable, and default to smaller queue size to accomodate larger 2x2 metatiles. See [#172](https://github.com/tilezen/tilequeue/pull/172).
    * Move existing tiles of interest (TOI) instead of copying it to avoid AWS Redis failover. See [#122](https://github.com/tilezen/tilequeue/pull/122).
    * Load new TOI from file 'toi.txt', just as the TOI dump process saves to 'toi.txt'. See [#122](https://github.com/tilezen/tilequeue/pull/122).
* **Bug fixes:**
    * Delete rejected jobs from SQS queue. See [#173](https://github.com/tilezen/tilequeue/pull/173).
    * Trap MemoryError and let ops recover process. See [#174](https://github.com/tilezen/tilequeue/pull/174).
    * Fix LinearRing error. See [#175](https://github.com/tilezen/tilequeue/pull/175).

v1.5.0
------
* Emit additional metrics during intersection

v1.4.0
------
* When checking to see if a tile has changed, compare ZIP file contents only. (See [#152](https://github.com/tilezen/tilequeue/issues/152))
* On WOF neighbourhood update, return a better error message for invalid dates. (See [#154](https://github.com/tilezen/tilequeue/pull/154))
* Remove "layers to format" functionality. (See [#155](https://github.com/tilezen/tilequeue/pull/155))

v1.3.0
------
* Roll back the use of psycopg2 connection pools. (See [#149](https://github.com/tilezen/tilequeue/pull/149))

v1.2.1
------
* Fix connection leak: Track connections before trying to use them. (See [#150](https://github.com/tilezen/tilequeue/pull/150))
* Fix issue processing WOF data with z coordinates: Ignore extra coordinates, e.g: z, in reprojection. (See [#148](https://github.com/tilezen/tilequeue/pull/148))

v1.2.0
------
* Improve performance of GeoJSON and TopoJSON format generation by using ujson (See [#139](https://github.com/tilezen/tilequeue/issues/139))
* Improve performance of MVT format generation by using builtin round function (See [#144](https://github.com/tilezen/tilequeue/pull/144))
* Reduce database pressure by use psycopg2 connection pools (See [#141](https://github.com/tilezen/tilequeue/issues/141))
* Reduce database requests by registering hstore/json (See [#142](https://github.com/tilezen/tilequeue/issues/142))
* Reduce memory usage during tile seeding (See [#126](https://github.com/tilezen/tilequeue/issues/126))
* Expose unique option for seeding tile generator (See [#127](https://github.com/tilezen/tilequeue/issues/127))
* Support long zooms (See [#130](https://github.com/tilezen/tilequeue/pull/130))

v1.1.1
------
* Use queue name from message to acknowledge message. See [#134](https://github.com/tilezen/tilequeue/issues/134).

v1.1.0
------
* Add command to dump the tiles of interest list to a text file
* Add support for generating metatiles (see also: tapalcatl)
* Add priority queues implementation
* Increase topojson scale from 1024 -> 4096

v1.0.1
------
* Add bbox filter to test for partial overlapping, rather than intersecting, the bbox.

v1.0.0
------
* Update wof projection to 3857.
* Update srid throughout from 900913 -> 3857.
* Add basic size logging for the objects returned from queries.
* Support multiple geometries in queries.
* Add filter to intersect with padded bounds.
* Conditionally store tile data. Print total storage counts for each tile.
* Correct the buffered mvt format definition.
* Convert wof min/max zooms to floats.
* Update sample cfg to reflect latest choices.
* Add pyclipper dependency to requirements.

v0.10.0
-------
* Improve json encoding
* Add boroughs to wof processing
* Add support for configurable area thresholds
* Add l10n names to wof processing
* Port used TileStache fork code to eliminate dependency
* Add configurable bounds buffer support
* Remove simplification, now a vector-datasource transform step
* Ensure json properties are utf-8 encoded
* Add support to generate s3 urls with no path
* Handle empty strings when edtf parsing wof dates

v0.9.0
------
* Delegate quantization to mapbox-vector-tile. See [#82](https://github.com/mapzen/tilequeue/issues/82).
* Expand mz_properties in features. See [#81](https://github.com/mapzen/tilequeue/pull/81).
* Exclude null values from yaml output. See [#84](https://github.com/mapzen/tilequeue/pull/84).
* Remove outdated tests exercising a transform that is no longer used. See [6de8f00](https://github.com/mapzen/tilequeue/commit/6de8f00579840794bdb7febd4e113a5cd976421a).

v0.8.0
------
* Use an empty list if the 'transforms' parameter is missing, rather than raise KeyError.
* Metatile at z16
* Support storing individual formatted layers
* Pass context object to post-process functions.
* Add resource abstraction to manage transforms with io requirements
* Don't filter out small features at z16, which may be needed for subsequent zooms

v0.7.1
------
* Eliminate extra slash in S3 filename. [Issue](https://github.com/mapzen/tilequeue/pull/65).
* Update `make_queue` signature to support sending items to the queue for rendering when a request for a tile which hasn't been rendered before is received. [Issue](https://github.com/mapzen/tilequeue/pull/66) as part of [larger issue](https://github.com/mapzen/tile-tasks/issues/39).

v0.7.0
------
* WOF neighbourhoods with inception and cessation dates are now respected, with those features being hidden from tiles. [Issue](https://github.com/mapzen/tilequeue/issues/59).
* The WOF update process is now robust to intermittent HTTP errors. This could help if you've been experiencing occasional WOF update failures. [Issue](https://github.com/mapzen/vector-datasource/tilequeue/60).

v0.6.1
------
* Made the WOF processor robust to missing `lbl:longitude` and `lbl:latitude` properties by falling back to the geometry's position. This isn't as good as the label position, but better than erroring.

v0.6.0
------
* Added a date prefix to be used to distinguish between different versions of the tiles in the store. This means it's not necessary to create a new bucket for each release.
* Added a hash prefix for files stored in an S3 bucket. This is recommended practice for distributing load for a bucket across an S3 cluster.

v0.5.1
------
* Move reproject_lnglat_to_mercator function for outside usage

v0.5.0
------
* Configure better defaults in sample config
* Add WOF neighbourhood processing
  - add command to load initial neighbourhoods to database
  - add command to track updates
* Create abstraction to factor out threaded enqueueing

v0.4.1
------
* Add bbox_intersection filter for Jinja, which allows clipping to the query bounding box.

v0.4.0
------
* Convert post process config into a list, to support generating dynamic `label_placement`s for more than one input layer.

v0.3.0
------
* Add read_tile to store interface

0.2.0
-----
* Stable
