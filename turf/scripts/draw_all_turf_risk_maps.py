#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)
TODAY = datetime.date.today()
SCRIPT_START_TIME = datetime.datetime.now()

import PIL
import numpy as N

from atmosci.utils.timeutils import elapsedTime

from turf.threats.factory import TurfThreatGridFileFactory
from turf.maps.factory import TurfMapFileFactory
from turf.maps.visual import drawScatterMap, finishMap


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='NE')

parser.add_option('-c', action='store_true', dest='contours', default=False)
parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

contours = options.contours
debug = options.debug
dev_mode = options.dev_mode
region_key = options.region
verbose = options.verbose or debug

period_key = args[0]
period_name = period_key.title()

# default : build last obs date and forecast
target_year = TODAY.year
target_year_str = str(target_year)

# factory for accessing threat data files
data_factory = TurfThreatGridFileFactory()
if dev_mode: data_factory.useDirpathsForMode('dev')
region = data_factory.regionConfig(region_key)

# factory for building and accessing map files
map_factory = TurfMapFileFactory()
if dev_mode: map_factory.useDirpathsForMode('dev')
no_data_config = map_factory.maps.no_threat
thumbnail_shape = map_factory.maps.thumbnail_shape

total_maps = 0

# loop over all threats
for threat_key in ('anthrac','bpatch','dspot','hstress','pblight'):
    threat_fullname = map_factory.threatName(threat_key)

    MAPS_START_TIME = datetime.datetime.now()

    reader = data_factory.threatFileReader(threat_key, period_key, target_year)
    start_date = reader.dateAttribute('risk', 'last_obs_date',
                        reader.dateAttribute('risk', 'last_rtma_date',
                               reader.dateAttribute('risk', 'first_valid_date',
                                      reader.dateAttribute('risk', 'start_date'))))
    end_date = reader.dateAttribute('risk', 'last_valid_date', None)

    dirpath_template = map_factory.turfMapDirpath(threat_key, None, region) 
    map_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
    if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)
    mapfile_template = map_factory.turfMapFilename(threat_key, None, region)

    dirpath_template = map_factory.turfThumbnailDirpath(threat_key, None, region) 
    thumb_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
    if not os.path.exists(thumb_dirpath): os.makedirs(thumb_dirpath)
    thumbfile_template = map_factory.turfThumbnailFilename(threat_key, None, region)

    # filter annoying numpy warnings
    warnings.filterwarnings('ignore',"All-NaN axis encountered")
    warnings.filterwarnings('ignore',"All-NaN slice encountered")
    warnings.filterwarnings('ignore',"invalid value encountered in greater")
    warnings.filterwarnings('ignore',"invalid value encountered in less")
    warnings.filterwarnings('ignore',"Mean of empty slice")
    # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

    # use the same coordintes for all dates
    lats = reader.lats
    lons = reader.lons

    print 'Drawing %s %s Risk maps:' % (threat_fullname, period_name)
    
    map_options = map_factory.mapOptions(threat_key).attrs
    map_title_template = map_options['title'] % {'threat':threat_fullname, 'date':'%(date)s'}

    days = 0
    date = start_date
    while date <= end_date:
        # get filepath for this date
        file_date_str = date.strftime('%Y%m%d')
        map_filename = mapfile_template.replace('||DATE||', file_date_str)
        map_filepath = os.path.join(map_dirpath, map_filename)
        map_options['outputfile'] = map_filepath

        # date-specific map options
        map_date_str = date.strftime('%Y-%m-%d')
        map_options['date'] = map_date_str
        map_options['title'] = map_title_template % {'date':map_date_str,}
        if debug:
            print '\ndrawing %s risk map for %s' % (threat_fullname, map_date_str)
        map_options['finish'] = False

        # risk data the date
        reader.open()
        risk = reader.dataForDate('risk', date)
        reader.close()
        risk_count = len(N.where(risk >= 0)[0])
        if risk_count > 0:
            options, _map_, fig, axes, fig1, xy_extremes = \
                     drawScatterMap(risk, lats, lons, **map_options)
            mapped = True
        else:
            index = reader._dateToIndex('risk', date)
            print 'No data for %s (index=%d)' % (date.strftime('%Y-%m-%d'), index)
            mapped = False

        if mapped:
            finishMap(fig, axes, fig1, **options)
            if debug: print '   ', map_filepath
            elif verbose: print '   ', map_filename

            thumb_filename = thumbfile_template.replace('||DATE||', file_date_str)
            thumb_filepath = os.path.join(thumb_dirpath, thumb_filename)
            image = PIL.Image.open(map_filepath)
            image.thumbnail(thumbnail_shape, PIL.Image.ANTIALIAS)
            image.save(thumb_filepath, 'PNG', quality=100, optimize=True)
            if debug: print '   ', thumb_filepath

        date += ONE_DAY
        days += 1

    # turn annoying numpy warnings back on
    warnings.resetwarnings()

    elapsed_time = elapsedTime(MAPS_START_TIME, True)
    info = (days, threat_fullname, period_name, elapsed_time)
    print '    Completed %d %s %s Risk maps in %s\n' % info
    total_maps += days

elapsed_time = elapsedTime(SCRIPT_START_TIME, True)
info = (total_maps, elapsed_time)
print 'Generated %d risk maps in %s' % info

