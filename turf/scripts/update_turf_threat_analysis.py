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
usage += '\n\nno date args passed : update all days since perevious analysis.'

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-r', action='store', dest='grid_region', default='NE',
       help='NWS region in grid file (default="NE")')

parser.add_option('-s', action='store', dest='grid_source', default='acis',
       help='Grid source type (default="acis")')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-p', action='store_true', dest='prev_day', default=False,
       help='boolean: only update the previous day (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

options, args = parser.parse_args()

num_date_args = len(args) - 2
if num_date_args not in (0,1,2,3,4,5):
    errmsg = '%d date arguments passed. Up to 5 date arguments'
    errmsg += ' are supported.\nUsage: %s'
    raise RuntimeError, errmsg % (num_args, usage)

debug = options.debug
dev_mode = options.dev_mode
prev_day = options.prev_day
region_key = options.grid_region
source_key = options.grid_source
verbose = options.verbose or debug

threat_key = args[0]
period_key = args[1]

num_days = None
if num_date_args == 0:
    if prev_day: start_date = end_date = TODAY - ONE_DAY
    else: start_date = end_date = None

elif num_date_args == 1:
    if 'n' in args[2]:
        num_days = int(args[2].replace('n',''))
        start_date = None
    else:
        start_date = end_date = \
            datetime.date(TODAY.year, TODAY.month, int(args[2]))

elif num_date_args == 2:
    if 'n' in args[3]:
        start_date = datetime.date(TODAY.year, TODAY.month, int(args[2]))
        num_days = int(args[3].replace('n',''))
        end_date = None
    elif 'd' in args[2] or 'd' in args[3]:
        start_date = datetime.date(TODAY.year, TODAY.month, int(args[2].replace('d','')))
        end_date = datetime.date(TODAY.year, TODAY.month, int(args[3].replace('d','')))
    else:
        start_date = end_date = datetime.date(TODAY.year, int(args[2]), int(args[3]))

elif num_date_args == 3:
    arg_2 = int(args[2])
    if arg_2 > 99:
        start_date = end_date = \
            datetime.date(arg_2, int(args[3]), int(args[4]))
    else:
        year = TODAY.year
        start_date = datetime.date(year, arg_2, int(args[3]))
        end_date = datetime.date(year, arg_2, int(args[4]))

else:
    arg_2 = int(args[2])
    if num_date_args == 4:
        if arg_2 > 99:
            month = int(args[3])
            start_date = datetime.date(arg_2, month, int(args[4]))
            end_date = datetime.date(arg_2, month, int(args[5]))
        else:
            year = TODAY.year
            start_date = datetime.date(year, arg_2, int(args[3]))
            end_date = datetime.date(year, int(args[4]), int(args[5]))

    elif num_date_args == 5:
        start_date = datetime.date(arg_2, int(args[3]), int(args[4]))
        end_date = datetime.date(arg_2, int(args[5]), int(args[6]))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# create a factory for access to the threat file
factory = SmartThreatModelFactory()
if dev_mode: factory.useDirpathsForMode('dev')
threat_fullname = factory.threatName(threat_key)

if start_date is None: # everything since previous reanalysis data
    if debug:
        print '\nBEFORE DISCOVERY :'
        print '    start_date :', start_date
        print '      end_date :', end_date
    if not factory.threatFileExists(threat_key, period_key, TODAY.year):
        factory.buildThreatGridFile(threat_key, period_key, TODAY, source_key)

    start_or_error = factory.discoverObsStartDate(threat_key, period_key)
    if isinstance(start_or_error, basestring): # check for error
        print '\n%s\nExecution terminated.' % start_or_error
        exit()
    start_date = start_or_error

    if num_days is None:
        end_date = factory.discoverMaxEndDate(threat_key, period_key, start_date)
    else:
        end_date = factory.endInDays(threat_key, period_key, start_date, num_days)

    if debug:
        print '\nAFTER DISCOVERY :'
        print '    start_date :', start_date
        print '      end_date :', end_date

    # reanalysis data is NEVER available on or oafter the current day !!
    if start_date >= TODAY: start_date = TODAY - ONE_DAY
    if end_date >= TODAY: end_date = TODAY - ONE_DAY

else:
    if end_date is None:
        if num_days is None:
            end_date = factory.discoverMaxEndDate(threat_key, period_key, start_date)
        else:
            end_date = factory.endInDays(threat_key, period_key, start_date, num_days)

        if debug:
            print '\nAFTER DISCOVERY :'
            print '    start_date :', start_date
            print '      end_date :', end_date

    # reanalysis data is NEVER available on or oafter the current day !!
    if start_date >= TODAY: start_date = TODAY - ONE_DAY
    if end_date >= TODAY: end_date = TODAY - ONE_DAY

    # make sure file exists for dates specified in script date date or args
    if not factory.threatFileExists(threat_key, period_key, start_date.year):
        factory.buildThreatGridFile(threat_key, period_key, start_date, source_key)
    result = factory.validateTimespan(threat_key, period_key, start_date, end_date)
    valid, dates, message = result
    if message is not None: print '\n%s' % message
    if valid:
        start_date, end_date = dates
    else:
        print 'Execution terminated.'
        exit()

# enforce end date .... reanalysis can never be TODAY or later
yesterday = TODAY - ONE_DAY
if end_date > yesterday:
    print '\nLatest possible reanalysis data is for yesterday (%s).' % repr(yesterday)
    if start_date > yesterday:
        print '   date span %s thru %s is invalid.' % (repr(start_date), repr(end_date))
        print 'Execution terminated.'
        exit()
    end_date = yesterday
    print '   end date adjusted to %s' % repr(start_date)


# discover timespan for update
new_start_date, start_time, end_time = \
    factory.threatWeatherTimespan(threat_key, start_date, end_date, period_key)
num_days = (end_date - start_date).days + 1

if debug:
    print '\n%s data timspan :' % threat_fullname
    print 'start date =', start_date
    print '  end date =', end_date
    print '  num_days =', num_days
    print '     hours =', num_days * 24
    print '\nWeather data timspan :'
    print 'start time =', start_time
    print '  end time =', end_time
    print '      diff =', end_time - start_time
    print '     hours =', (end_time - start_time).days * 24
if verbose:
    details = (threat_fullname, period_key.title())
    print '\nEstimated time period required to update %s %s reanalysis :' % details
    print 'weather data start =', start_time
    print 'weather   data end =', end_time
    print 'time diff in hours =', tzutils.hoursInTimespan(start_time, end_time)


# make sure all estimated times are available
success, analysis_start, analysis_end = \
    factory.availableReanalysisTimes('temps', start_time, end_time)

if success < 0:
    print '\nNo reanalysis data available for required time period.'
    print '    %s thru %s' % (timeString(start_time),
                              timeString(end_time))
    print '\nExecution terminated'
    exit()

if analysis_end < start_time:
    print '\nReanalysis data ends before requested time period begins.'
    print '  requested date start ', timeString(start_time)
    print '  analysis data ends @ ', timeString(analysis_end)
    print '\nExecution terminated'
    exit()

if analysis_end < end_time:
    print '\nReanalysis data ends before requested time period.'
    print '  requested data thru ', timeString(end_time)
    print ' analysis data ends @ ', timeString(analysis_end)
    print '\nExecution terminated'
    exit()

if success == 0:
    print '\nTimespan was adjusted to limits of available reanalysis data.'
    print '    %s thru %s\n' % (timeString(analysis_start),
                              timeString(analysis_end))

if verbose:
    print '\n Updating %s %s risk :' % (threat_fullname, period_key.title())
    print ' analysis start date :', new_start_date
    print '  weather data start :', start_time
    print '  weather   data end :', end_time
    print 'number of data hours =', tzutils.hoursInTimespan(start_time, end_time)
if debug:
    print '\nfactory.availableReanalysisTimes returned :'
    print 'analysis_start :', analysis_start
    print '  analysis_end :', analysis_end 
    num_hours = tzutils.hoursInTimespan(analysis_end, analysis_start)
    print '      num days :', num_hours / 24


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
threat_index = model.threatIndex(*model_data)
if debug:
    print 'threat_index grid shape :', threat_index.shape
    print '\nThreat index summary :'
    risk_thresholds = list(factory.riskThresholds(threat_key, period_key))
    risk_thresholds.reverse()
    prev_threshold = risk_thresholds[0]
    prev_count = len(N.where(threat_index > prev_threshold)[0])
    print '    %6d nodes with index > %.1f' % (prev_count, prev_threshold)

    for threshold in risk_thresholds[1:]:
        count = len(N.where(threat_index > threshold)[0]) - prev_count
        print '    %6d nodes with %.1f <= index > %.1f' % (count, prev_threshold, threshold)
        prev_count = count
        prev_threshold = threshold

    count = len(N.where(threat_index < 0.)[0])
    print '    %6d nodes with index < 0.' % count


# update the threat index dataset 
manager = factory.threatFileManager(threat_key, period_key, start_date.year)
index_end_date = manager.updateReanalysis('threat', start_date, threat_index)
manager.close()

# run the model's risk calculator
risk_level = model.riskLevel(threat_index)

if debug:
    print '\nRisk level summary :'
    risk_thresholds = list(factory.riskThresholds(threat_key, period_key))
    for level in range(len(risk_thresholds)):
        count = len(N.where(risk_level == level)[0])
        print '    %6d nodes with risk level == %d' % (count, level)

# update the threat risk dateset
manager.open('a')
risk_end_date = manager.updateReanalysis('risk', start_date, risk_level)
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
print '\nCompleted %s reanalysis update in %s' % (threat_fullname, elapsed_time)

