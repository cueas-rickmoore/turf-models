#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)
TODAY = datetime.date.today()
MAPS_START_TIME = datetime.datetime.now()

import PIL
import numpy as N

from atmosci.utils.timeutils import elapsedTime

from turf.threats.factory import TurfThreatGridFileFactory
from turf.maps.factory import TurfMapFileFactory
from turf.maps.visual import drawScatterMap, finishMap


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-f', action='store', type=int, dest='forecast', default=7)
parser.add_option('-r', action='store', dest='region', default='NE')

parser.add_option('-c', action='store_true', dest='contours', default=False)
parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

contours = options.contours
forecast = options.forecast
debug = options.debug
dev_mode = options.dev_mode
region_key = options.region
verbose = options.verbose or debug

threat_key = args[0]
period_key = args[1]

# assume forecast starts today
fcast_start = TODAY
# assume last obs was yesterday
previous_obs = TODAY - ONE_DAY

# factory for accessing threat data files
data_factory = TurfThreatGridFileFactory()
if dev_mode: data_factory.useDirpathsForMode('dev')
region = data_factory.regionConfig(region_key)
 

def findLastMap(map_factory, previous_obs, threat_key, period_key):
    map_factory.turfMapFilename(threat_key, None, region)


if start_date is None:
    reader = data_factory.threatFileReader(threat_key, period_key, TODAY.year)
else:
    reader = data_factory.threatFileReader(threat_key, period_key, start_date.year)
if verbose: print 'reading data from :\n', reader.filepath

if start_date is None:
    start_date = reader.dateAttribute('risk', 'last_obs_date',
                        reader.dateAttribute('risk', 'last_rtma_date',
                               reader.dateAttribute('risk', 'first_valid_date',
                                      reader.dateAttribute('risk', 'start_date'))))

if end_date is None:
    end_date = reader.dateAttribute('risk', 'last_valid_date', None)
    if end_date is None:
        print 'No valid %s data in file :\n%s' % reader.filepath
        print '\nExecution terminated.'
        reader.close()
        exit()

target_year = start_date.year
target_year_str = str(target_year)

# factory for building and accessing map files
map_factory = TurfMapFileFactory()
if dev_mode: map_factory.useDirpathsForMode('dev')
threat_fullname = map_factory.threatName(threat_key)
map_options = map_factory.mapOptions(threat_key).attrs

dirpath_template = map_factory.turfMapDirpath(threat_key, None, region) 
map_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)

mapfile_template = map_factory.turfMapFilename(threat_key, None, region)
map_title_template = map_options['title'] % {'threat':threat_fullname, 'date':'%(date)s'}

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

print 'Creating %s maps for %s thru %s' % (threat_fullname, 
                                           start_date.strftime('%Y-%m-%d'),
                                           end_date.strftime('%Y-%m-%d'))
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
        print '\ncreating %s risk map for %s' % (threat_fullname, map_date_str)
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
        if verbose: print '    ', map_filepath
        else: print '    ', map_filename

        thumb_filename = thumbfile_template.replace('||DATE||', file_date_str)
        thumb_filepath = os.path.join(thumb_dirpath, thumb_filename)
        image = PIL.Image.open(map_filepath)
        image.thumbnail(thumbnail_shape, PIL.Image.ANTIALIAS)
        image.save(thumb_filepath, 'PNG', quality=100, optimize=True)
        if debug: print '    ', thumb_filepath

    date += ONE_DAY
    days += 1

# turn annoying numpy warnings back on
warnings.resetwarnings()

info = (days, start_date, end_date)
print '\nProcessed maps for %d days : %s thru %s' % info
elapsed_time = elapsedTime(MAPS_START_TIME, True)
info = (threat_fullname, elapsed_time)
print 'Completed %s risk maps in %s' % info
