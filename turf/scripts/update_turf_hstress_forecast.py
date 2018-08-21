#! /usr/bin/env python

import datetime
ONE_DAY = datetime.timedelta(days=1)
TODAY = datetime.date.today()
UPDATE_START_TIME = datetime.datetime.now()

import warnings

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime

from turf.threats.smart_models import SmartThreatModelFactory
from turf.weather.smart_grid import SmartWeatherDataReader

def timeString(time_obj): return time_obj.strftime('%Y-%m-%d:%H')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

usage = '%prog [date] [options]'
usage += '\n    When passing dates without year :'
usage += '\n       %prog [day_in_current_month] [options]'
usage += '\n       %prog [month day] [options]'
usage += '\n       %prog [month 1st_day last_day] [options]'
usage += '\n       %prog [1st_month day last_month day] [options]'
usage += '\n    When passing dates with year :'
usage += '\n       %prog [year month day] [options]'
usage += '\n       %prog [year month 1st_day last_day] [options]'
usage += '\n       %prog [year 1st_month day last_month day] [options]'
usage += '\n\nno date args passed : update all days since perevious forecast.'

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-r', action='store', dest='grid_region', default='NE',
       help='NWS region in grid file (default="NE")')

parser.add_option('-s', action='store', dest='grid_source', default='acis',
       help='Grid source type (default="acis")')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

options, args = parser.parse_args()

num_args = len(args)
if num_args not in (0,1,2,3,4,5):
    errmsg = '%d date arguments passed. Up to 5 date arguments'
    errmsg += ' are supported.\nUsage: %s'
    raise RuntimeError, errmsg % (num_args, usage)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
region_key = options.grid_region
source_key = options.grid_source
verbose = options.verbose or debug

threat_key = 'hstress'
period_key = 'daily'

num_date_args = len(args)
if num_date_args == 0:
    start_date = None
    end_date = None

else:
    arg_0 = int(args[0])
    if num_date_args == 1:
        start_date = end_date = datetime.date(TODAY.year, TODAY.month, arg_0)

    elif num_date_args == 2:
        start_date = end_date = datetime.date(TODAY.year, arg_0, int(args[1]))

    elif num_date_args == 3:
        if arg_0 > 99:
            start_date = end_date = datetime.date(arg_0, int(args[1]), int(args[2]))
        else:
            year = TODAY.year
            start_date = datetime.date(year, arg_0, int(args[1]))
            end_date = datetime.date(year, arg_0, int(args[2]))

    elif num_date_args == 4:
        if arg_0 > 99:
            month = int(args[1])
            start_date = datetime.date(arg_0, month, int(args[2]))
            end_date = datetime.date(arg_0, month, int(args[3]))
        else:
            year = TODAY.year
            start_date = datetime.date(year, arg_0, int(args[1]))
            end_date = datetime.date(year, int(args[2]), int(args[3]))

    elif num_date_args == 5:
        start_date = datetime.date(arg_0, int(args[1]), int(args[2]))
        end_date = datetime.date(arg_0, int(args[3]), int(args[4]))


# create a factory for access to the threat file
factory = SmartThreatModelFactory()
if dev_mode: factory.useDirpathsForMode('dev')
threat_fullname = factory.threatName(threat_key)

if debug:
    print '\nBEFORE DISCOVERY :'
    print '    start_date :', start_date
    print '      end_date :', end_date


if start_date is None: # everything since previous forecast data
    # make sure file exists for dates specified in script date date or args
    if not factory.threatFileExists(threat_key, period_key, TODAY.year):
        factory.buildThreatGridFile(threat_key, period_key, TODAY, source_key)

    start_or_error = factory.discoverFcastStartDate(threat_key, period_key)
    if isinstance(start_or_error, basestring): # check for error
        print '\n%s\nExecution terminated.' % start_or_error
        exit()
    start_date = start_or_error

else:
    # make sure file exists for dates specified in script date date or args
    if not factory.threatFileExists(threat_key, period_key, start_date.year):
        factory.buildThreatGridFile(threat_key, period_key, start_date, source_key)

if end_date is None:
    num_days = factory.project.fcast_days
    end_date = factory.endInDays(threat_key, period_key, start_date, num_days)

if debug:
    print '\nAFTER DISCOVERY :'
    print '    start_date :', start_date
    print '      end_date :', end_date

result = factory.validateTimespan(threat_key, period_key, start_date, end_date)
valid, dates, message = result
if message is not None: print '\n%s' % message
if valid:
    start_date, end_date = dates
else:
    print '\nExecution terminated.'
    exit()

if debug:
    print '\nAFTER VALIDATION :'
    print '    start_date :', start_date
    print '      end_date :', end_date


# discover timespan for update
new_start_date, start_time, end_time = \
    factory.threatWeatherTimespan(threat_key, start_date, end_date, period_key)
num_days = end_date - start_date

if debug:
    print '  num_days =', num_days
    print '     hours =', num_days.days * 24
    print 'start time =', start_time
    print '  end time =', end_time
    print '      diff =', end_time - start_time
    print '     hours =', (end_time - start_time).days * 24
if verbose:
    details = (threat_fullname, period_key.title())
    print '\nEstimated time period required to update %s %s forecast :' % details
    print 'weather start date =', new_start_date
    print 'weather data start =', start_time
    print 'weather   data end =', end_time
    print 'time diff in hours =', tzutils.hoursInTimespan(start_time, end_time)


# make sure all estimated times are available
forecast_start, forecast_end = \
    factory.availableForecastTimes('temps', start_time, end_time)

if forecast_start is None:
    print '\nNo forecast data available for required time period.'
    print '    %s thru %s' % (timeString(start_time), timeString(end_time))
    print '\nExecution terminated'
    exit()

if forecast_start > end_time:
    print '\nForecast begins after requested time period.'
    print '       requested : %s thru %s' % (timeString(start_time), timeString(end_time))
    print ' first available :', timeString(forecast_start) 
    print '\nExecution terminated'
    exit()

if forecast_start != start_time or forecast_end != end_time:
    print '\nTimespan was adjusted to limits of available forecast data.'
    print '    processing %s thru %s\n' % (timeString(forecast_start), timeString(forecast_end))

if verbose:
    print '\n Updating %s %s risk :' % (threat_fullname, period_key.title())
    print ' forecast start date :', new_start_date
    print '  weather data start :', start_time
    print '  weather   data end :', end_time
    print 'number of data hours =', tzutils.hoursInTimespan(start_time, end_time)
if debug:
    print '\nfactory.availableForecastTimes returned :'
    print 'forecast_start :', forecast_start
    print '  forecast_end :', forecast_end 
    print '      num days :', forecast_end - forecast_start


# get all data for model
model_data = factory.getModelWeatherData(threat_key, start_time, end_time)


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


# get the appropriate threat model
model = factory.riskModel(threat_key, start_time, period_key, debug)

# run the model's threat index calculator
stress_hours = model.stressHours(*model_data)
if debug:
    print 'stress_hours grid shape :', stress_hours.shape
    print '\nThreat index summary :'
    risk_thresholds = list(factory.riskThresholds(threat_key, period_key))
    risk_thresholds.reverse()
    prev_threshold = risk_thresholds[0]
    prev_count = len(N.where(stress_hours > prev_threshold)[0])
    print '    %6d nodes with index > %.1f' % (prev_count, prev_threshold)

    for threshold in risk_thresholds[1:]:
        count = len(N.where(stress_hours > threshold)[0]) - prev_count
        print '    %6d nodes with %.1f <= index > %.1f' % (count, prev_threshold, threshold)
        prev_count = count
        prev_threshold = threshold

    count = len(N.where(stress_hours < 0.)[0])
    print '    %6d nodes with index < 0.' % count

# update the threat index dataset 
manager = factory.threatFileManager(threat_key, period_key, start_date.year)
index_end_date = manager.updateForecast('stress', start_date, stress_hours)
manager.close()

# run the model's risk calculator
risk_level = model.riskLevel(stress_hours)

if debug:
    print '\nRisk level summary :'
    risk_thresholds = list(factory.riskThresholds(threat_key, period_key))
    for level in range(len(risk_thresholds)):
        count = len(N.where(risk_level == level)[0])
        print '    %6d nodes with risk level == %d' % (count, level)

# update the threat risk dateset
manager.open('a')
risk_end_date = manager.updateForecast('risk', start_date, risk_level)
manager.close()


# turn annoying numpy warnings back on
warnings.resetwarnings()


print '\nCompleted update of %s risk.' % threat_fullname
dates = (start_date.strftime('%Y-%m-%d'), index_end_date.strftime('%Y-%m-%d'))
print 'Threat index dataset time span : %s thru %s' % dates
dates = (start_date.strftime('%Y-%m-%d'), risk_end_date.strftime('%Y-%m-%d'))
print 'Risk dataset time span : %s thru %s' % dates
times = (tzutils.hoursInTimespan(end_time, start_time),
         start_time.strftime('%Y-%m-%d:%H'), end_time.strftime('%Y-%m-%d:%H'))
print 'Processed %d raw data hours: %s thru %s' % times
elapsed_time = elapsedTime(UPDATE_START_TIME, True)
print '\nCompleted %s forecast update in %s' % (threat_fullname, elapsed_time)

