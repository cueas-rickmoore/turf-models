#! /usr/bin/env python

import os

import datetime
ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(hours=24)

import numpy as N

from atmosci.utils import tzutils
from atmosci.reanalysis.smart_mapper import SmartReanalysisDataMapper


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='NE')
parser.add_option('-s', action='store', dest='summary', default=None)
parser.add_option('-t', action='store', type=int, dest='target_hour',
                        default=CONFIG.project.target_hour)
parser.add_option('-u', action='store_false', dest='units', default=None)
parser.add_option('-y', action='store', type=int, dest='target_year',
                        default=None)

parser.add_option('--tz', action='store', dest='local_timezone',
                          default=CONFIG.project.local_timezone)

parser.add_option('-c', action='store_true', dest='contours', default=False)
parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

contours = options.contours
debug = options.debug
dev_mode = options.dev_mode
local_timezone = options.local_timezone
region_key = options.region
summary = options.summary
target_hour = options.target_hour
target_year = options.target_year
units = options.units
verbose = options.verbose or debug

today = datetime.date.today()
if target_year is None: target_year = today.year

variable = args[0].upper()

if summary is None:
    if variable == 'PCPN': summary = 'total'
    else: summary = 'extremes'

if units is None:
    if variable == 'PCPN': units = 'in'
    elif variable == 'RHUM': units = '%'
    elif variable in ('DPT','TMP'): units = 'F'

num_date_args = len(args) - 1

if num_date_args == 0: # 1 day ending today at target_hour
    hour = datetime.datetime.combine(today, datetime.time(hour=target_hour))
    end_time = tzutils.asHourInTimezone(hour, local_timezone) + ONE_HOUR
    start_time = end_time - datetime.timedelta(hours=23)
else:
    hour = datetime.datetime(target_year,int(args[1]),int(args[2]),target_hour)
    if num_date_args == 2: # one day ending at month, day, target hour
        end_time = tzutils.asHourInTimezone(hour, local_timezone) + ONE_HOUR
        start_time = end_time - datetime.timedelta(hours=24)

    elif num_date_args == 3: # month, first day, last day
        start_time = tzutils.asHourInTimezone(hour, local_timezone) + ONE_HOUR
        hour = datetime.datetime(target_year,int(args[1]),int(args[3]),target_hour)
        end_time = tzutils.asHourInTimezone(hour, local_timezone) + ONE_HOUR

    elif num_date_args == 4: # month, day, month, day
        start_time = tzutils.asHourInTimezone(hour, local_timezone) + ONE_HOUR
        hour = datetime.datetime(target_year,int(args[3]),int(args[4]),target_hour)
        end_time = tzutils.asHourInTimezone(hour, local_timezone) + ONE_HOUR

    else:
        errmsg = '%d is an invalid number of date arguments.'
        raise RuntimeError, errmsg % num_date_args

if verbose:
    print 'requesting ...'
    print '          variable :', variable
    print '           summary :', summary
    print '          timezone :', repr(local_timezone)
    print '        start time :', repr(start_time)
    print '          end time :', repr(end_time)

# factory for accessing threat data files
mapper = SmartReanalysisDataMapper(region_key)
if dev_mode: mapper.useDirpathsForMode('dev')
print 'mapper timesonze', mapper.timezone, repr(mapper.tzinfo)

if summary == 'extremes':
    filepaths = mapper.mapDataExtremes(variable, start_time, end_time,
                                       region_key, debug, units=units)
    print 'created :', filepaths[0]
    print '         ', filepaths[1]

elif summary in ('sum', 'total'):
    filepath = mapper.mapDataTotals(variable, start_time, end_time, region_key,
                                    debug, units=units)
    print 'created :', filepath
elif summary in ('avg', 'mean'):
    filepath = mapper.dataMeans(variable, start_time, end_time, region_key,
                                debug, units=units)
    print 'created :', filepath


