#! /usr/bin/env python

import os, sys

import datetime
UPDATE_START_TIME = datetime.datetime.now()
ONE_DAY = datetime.timedelta(days=1)

import numpy as N
import pygrib

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime
from atmosci.utils.units import convertUnits

from atmosci.reanalysis.factory import ReanalysisGribFileFactory
from atmosci.reanalysis.urma.factory import URMAGribFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.urma.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def utcTimes(utc_datetime):
    return { 'utc_date':  utc_datetime.strftime('%Y%m%d'),
             'utc_hour':  utc_datetime.strftime('%H'),
             'utc_time':  utc_datetime.strftime('%Y%m%d%H') }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-g', action='store', dest='grib_source', default='ncep')
parser.add_option('-r', action='store', dest='region', default='conus')
parser.add_option('-s', action='store', dest='source', default='acis')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-f', action='store_true', dest='file_must_exist',
                        default=False)
parser.add_option('-u', action='store_true', dest='is_utc_time', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
file_must_exist = options.file_must_exist
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

print '\n\nworking with ReanalysisGribFileFactory'
factory = ReanalysisGribFileFactory('urma.%s' % grib_source, CONFIG)
if dev_mode:
    factory.useDirpathsForMode('dev')
    if debug:
        print 'dev mode filepaths requested :\n'
        print factory.config.dirpaths.attrs


# grib file path
print '\nLooking up grib filepath in ReanalysisGribFileFactory :'
filepath_1 = factory.gribFilepath(utc_hour, grib_var_name, region_key,
                                  file_must_exist=file_must_exist)
print filepath_1

# now read the same data using URMA factory
print '\n\nworking with URMAGribFileFactory'
factory = URMAGribFileFactory(grib_source, CONFIG)
if dev_mode:
    factory.useDirpathsForMode('dev')
    if debug:
        print 'dev mode filepaths requested :\n'
        print factory.config.dirpaths.attrs

# grib file path
print '\nLooking up grib filepath in ReanalysisGribFileFactory :'
filepath_2 = factory.urmaGribFilepath(utc_hour, grib_var_name, region_key,
                                      file_must_exist=file_must_exist)
print filepath_2
print '\nURMA filepath == Reanalysis filepath :', filepath_2 == filepath_1

