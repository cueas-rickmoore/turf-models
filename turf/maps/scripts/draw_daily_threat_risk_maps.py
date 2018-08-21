#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

import PIL
import numpy as N

from nrcc_viz.maps import drawFilledContours, finishMap

from turf.threats.factory import TurfThreatGridFileFactory
from turftool.maps.factory import TurfMapFileFactory
from turftool.maps.visual import drawScatterMap


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

threat_key = args[0]
num_date_args = len(args) - 1

# get the start & end dates
if num_date_args == 1:
    start_date = end_date = datetime.date.today()
elif num_date_args in (3,4,5):
    year = int(args[1])
    month = int(args[2])
    start_date = datetime.date(year,month,int(args[3]))
    if num_date_args == 3: # single day
        end_date = start_date
    elif num_date_args == 4: # end on different day
        end_date = datetime.date(year,month,int(args[4]))
    elif num_date_args == 5: # end at different month and day
        end_date = datetime.date(year,int(args[4]),int(args[5]))
else:
    errmsg = 'Invalid number of date arguments (%d).' % num_date_args
    raise ValueError, errmsg

target_year = start_date.year

# factory for accessing threat data files
grid_factory = TurfThreatGridFileFactory()
if dev_mode: grid_factory.useDirpathsForMode('dev')
region = grid_factory.regionConfig(region_key)

reader = grid_factory.gridFileReader(threat_key, 'daily', target_year, region)
if verbose: print 'reading data from :\n', reader.filepath
date_attrs = reader.dateAttributes('risk')
last_valid_date = date_attrs['last_valid_date']
data_start_date = date_attrs['start_date']

# factory for building and accessing map files
map_factory = TurfMapFileFactory()
if dev_mode: map_factory.useDirpathsForMode('dev')
map_options = map_factory.mapOptions(threat_key, region).attrs
threat = map_factory.configForThreat(threat_key)

dirpath_template = map_factory.turfMapDirpath(threat_key, None, region) 
map_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)

mapfile_template = map_factory.turfMapFilename(threat_key, None, region)
map_title_template = map_options['title'] % {'threat':threat.fullname, 'date':'%(date)s'}

dirpath_template = map_factory.turfThumbnailDirpath(threat_key, None, region) 
thumb_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
if not os.path.exists(thumb_dirpath): os.makedirs(thumb_dirpath)

thumbfile_template = \
    map_factory.turfThumbnailFilename(threat_key, None, region)

no_data_config = map_factory.maps.no_threat
thumbnail_shape = map_factory.maps.thumbnail_shape

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

print 'creating %s maps for %s thru %s' % (threat_key.upper(), 
                                           start_date.strftime('%Y-%m-%d'),
                                           end_date.strftime('%Y-%m-%d'))

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
        print '\ncreating %s risk map for %s' % (threat_key.upper(), map_date_str)
    map_options['finish'] = False

    # risk data the date
    risk = reader.dataForDate('risk', date)
    risk_count = len(N.where(risk >= 0)[0])
    if risk_count > 0:
        if contours:
            options, _map_, fig, axes, fig1, xy_extremes = \
                drawFilledContours(risk, lats, lons, **map_options)
        else:
            options, _map_, fig, axes, fig1, xy_extremes = \
                drawScatterMap(risk, lats, lons, **map_options)
        mapped = True
    else:
        index = reader._dateToIndex('risk', date)
        print 'No data for %s (index=%d)' % (date.strftime('%Y-%m-%d'), index)
        mapped = False

    if mapped:
        finishMap(fig, axes, fig1, **options)
        print 'created', map_filepath

        thumb_filename = thumbfile_template.replace('||DATE||', file_date_str)
        thumb_filepath = os.path.join(thumb_dirpath, thumb_filename)
        image = PIL.Image.open(map_filepath)
        image.thumbnail(thumbnail_shape, PIL.Image.ANTIALIAS)
        print '   thumbnail', thumb_filepath
        image.save(thumb_filepath, 'PNG', quality=100, optimize=True)

    date += ONE_DAY

# turn annoying numpy warnings back on
warnings.resetwarnings()

