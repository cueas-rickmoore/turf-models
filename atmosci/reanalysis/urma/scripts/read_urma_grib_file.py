#! /usr/bin/env python

import os, sys
import warnings

import datetime
UPDATE_START_TIME = datetime.datetime.now()
ONE_DAY = datetime.timedelta(days=1)

import numpy as N
import pygrib

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime
from atmosci.utils.units import convertUnits

from atmosci.reanalysis.urma.factory import URMAGribFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def utcTimes(utc_datetime):
    return { 'utc_date':  utc_datetime.strftime('%Y%m%d'),
             'utc_hour':  utc_datetime.strftime('%H'),
             'utc_time':  utc_datetime.strftime('%Y%m%d%H') }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-q', action='store', dest='grib_source', default='ncep')
parser.add_option('-r', action='store', dest='region', default='conus')
parser.add_option('-s', action='store', dest='source', default='acis')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-u', action='store_true', dest='is_utc_time', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
grib_source = options.grib_source
is_utc_time = options.is_utc_time
region_key = options.region
source_key = options.source
verbose = options.verbose or debug

grib_var_name = args[0].upper()

num_args = len(args)
if len(args) == 1:
    local_hour = tzutils.asLocalHour(datetime.datetime.now(),'US/Eastern')
    utc_hour = tzutils.asUtcHour(target_hour)
elif num_args > 1:
    if num_args >= 5:
        time_tuple = tuple([int(t) for t in args[1:5]])
        utc_hour = tzutils.asHourInTimezone(time_tuple, 'UTC')
        local_hour = tzutils.asLocalHour(utc_hour, 'US/Eastern')
    else:
        errmsg = 'At least 5 arguments are required when requesting a '
        errmsg += 'specific time. (variable year month day hour)'
        raise RuntimeError, errmsg
else:
    errmsg = 'No arguments passed to script. You must at least specify'
    raise RuntimeError, '%s the grib variable name.' % errmsg

if debug:
    print 'requesting ...'
    print '    variable :', grib_var_name
    print '    local hour :', local_hour
    print '    UTC hour :', utc_hour

factory = URMAGribFileFactory('ncep', CONFIG)
if dev_mode:
    factory.useDirpathsForMode('dev')
    if debug:
        print 'dev mode filepaths requested :\n'
        print factory.config.dirpaths.attrs

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# need indexes from static file for source
source_shape, source_indexes = \
       factory.gribIndexesForRegion(region_key, source_key)
# read the grib file
reader = factory.urmaGribFileReader(utc_hour, grib_var_name, region_key,
                                    file_must_exist=True,
                                    shared_grib_dir=True)
message = reader.messageFor(grib_var_name)
if debug:
    print 'message retrieved :\n    ', message
    print 'valid date :', message.validDate
    print 'data units :', message.units

data = message.values[source_indexes]
if debug:
    print 'retrieved shape :', data.shape
    print data

data = data.reshape(source_shape)
if debug: print 'grid shape :', data.shape

data[N.where(data == 9999)] = N.nan
if debug: 
    print data
    print 'data extremes :', N.nanmin(data), N.nanmax(data)
reader.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()

#elapsed_time = elapsedTime(UPDATE_START_TIME, True)
#msg = '\ncompleted NDFD forecast update for %s thru %s in %s'
#print msg % (fcast_start.strftime('%m-%d'), fcast_end.strftime('%m-%d, %Y'),
#             elapsed_time)

