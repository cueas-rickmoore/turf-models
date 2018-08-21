#! /usr/bin/env python

import datetime
import warnings

import numpy as N

from atmosci.units import convertUnits
from atmosci.utils import tzutils

from turf.threats.factory import TurfThreatGridFileFactory
from turf.threats.smart_weather import SmartThreatWeatherReader


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import CONFIG, THREATS


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

default = CONFIG.project.region
parser.add_option('-r', action='store', dest='grid_region', default=default,
       help='NWS region in grid file (default="%s")' % default)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-f', action='store_true', dest='add_fcast', default=False,
       help='boolean: also update the forecast (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

text = 'name of local timezone used in date args (default=None).'
text += ' If None, the timezone in config.project.local_timezone will'
text += ' be used (currently "%s").' % CONFIG.project.local_timezone
parser.add_option('--localtz', action='store', dest='localtz',
       default=None, help=text)
del text

options, args = parser.parse_args()

num_args = len(args)
if num_args not in (0,1,2,3,4,5):
    errmsg = '%d date arguments passed. Up to 5 date arguments'
    errmsg += ' are supported.\nUsage: %s'
    raise RuntimeError, errmsg % (num_args, usage)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

add_fcast = options.add_fcast
debug = options.debug
dev_mode = options.dev_mode
local_timezone = options.localtz
region_key = options.grid_region
today = datetime.date.today()
verbose = options.verbose or debug


threat = args[0]
period_key = args[1]

start_date = None
num_date_args = len(args) - 2
if num_date_args == 0:
    end_date = today
elif num_date_args == 1:
    end_date = datetime.date(today.year, today.month, int(args[2]))
elif num_date_args == 2:
    end_date = datetime.date(today.year, int(args[2]), int(args[3]))
else:
    arg_2 = int(args[2])
    if num_date_args == 3:
        if arg_2 > 99:
            start_date = datetime.date(arg_2, int(args[3]), int(args[4]))
        else:
            year = today.year
            month = int(args[2])
            start_date = datetime.date(year, month, int(args[3]))
            end_date = datetime.date(year, month, int(args[4]))

    elif num_date_args == 4:
        if arg_2 > 99:
            month = int(args[3])
            start_date = datetime.date(arg_2, month, int(args[4]))
            end_date = datetime.date(arg_2, month, int(args[5]))
        else:
            year = today.year
            start_date = datetime.date(year, arg_2, int(args[3]))
            end_date = datetime.date(year, int(args[4]), int(args[5]))

    elif num_date_args == 5:
        start_date = datetime.date(arg_2, int(args[3]), int(args[4]))
        end_date = datetime.date(arg_2, int(args[5]), int(args[6]))
 
target_year = end_date.year

threat_factory = TurfThreatGridFileFactory()
region = threat_factory.regionConfig(region_key)
period = threat_factory.threatConfig(threat).periods[period_key]

weather_reader = SmartThreatWeatherReader(region)

if dev_mode:
    threat_factory.useDirpathsForMode('dev')
    weather_reader.useDirpathsForMode('dev')

if start_date is None:
    start_date = end_date
    end_date += datetime.timedelta(days=period.num_days)

print '\nrequested :'
print '      today =', today
print '      start =', start_date
print '        end =', end_date

start_date, end_end_date = threat_factory.fileTimespan(threat, start_date.year)
print '\nthreat file timespan :'
print '      start =', start_date
print '        end =', end_end_date

print '\nthreat risk dataset dates :'
dates = threat_factory.threatFileDates(threat, period_key, start_date.year, region)
for key, _time_ in dates.items():
    print '    %s = %s' % (key, _time_)

print '\nthreat risk date limits :'
dates = threat_factory.threatDateLimits(threat, period_key, start_date.year, region)
print '    first valid =', dates[0]
print '     last valid =', dates[1]

print '\nweather file times :'
times = weather_reader.weatherTimeAttributes('temps', end_date)
for key, _time_ in times.items():
    print '    %s = %s' % (key, _time_)

print '\nweather slices :'
slices = weather_reader.threatWeatherSlices(threat, 'temps', start_time, end_time)
for start, end in slices:
    print '    ', start, 'thru', end

