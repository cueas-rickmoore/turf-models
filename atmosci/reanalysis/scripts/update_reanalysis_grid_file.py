#! /Volumes/Transport/venvs/atmosci/bin/python
#! /usr/bin/env python

import os, sys
import warnings

import datetime
UPDATE_START_TIME = datetime.datetime.now()

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime, lastDayOfMonth

from atmosci.reanalysis.factory import ReanalysisGribFileFactory, \
                                       ReanalysisGridFileFactory
from atmosci.reanalysis.smart_grib import SmartReanalysisGribReader


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def hourInTimezone(year, month, day, hour, tzinfo):
    # local_tzinfo must be an instance of pytz.tzinfo
    return tzinfo.localize(datetime.datetime(year, month, day, hour))

def timeString(time_obj): return time_obj.strftime('%Y-%m-%d:%H')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

usage = 'usage: %prog  analysis variable [options]'
usage += '\n   for data in current year:'
usage += '\n       %prog  analysis variable hour [options]'
usage += '\n       %prog  analysis variable day day [options]'
usage += '\n       %prog  analysis variable month day [options]'
usage += '\n       %prog  analysis variable month day hour [options]'
usage += '\n       %prog  analysis variable month day 1st_hour(UTC) last_hour(UTC) [options]'
usage += '\n       %prog  analysis variable month 1st_day hour(UTC) last_day hour(UTC) [options]'
usage += '\n       %prog  analysis variable 1st_month day hour(UTC) last_month day hour(UTC) [options]'
usage += '\n   for data in specific year:'
usage += '\n       %prog  analysis variable year month day [options]'
usage += '\n       %prog  analysis variable year month day hour(UTC) [options]'
usage += '\n       %prog  analysis variable year month day 1st_hour(UTC) last_hour(UTC) [options]'
usage += '\n       %prog  analysis variable year month 1st_day hour(UTC) last_day hour(UTC) [options]'
usage += '\n\nWhen no time args are passed, date is updated beginning one hour'
usage += '\nafter the last valid reanalysis date and ending at the current time.'

from optparse import OptionParser
parser = OptionParser(usage)

default = CONFIG.sources.reanalysis.grid.region
parser.add_option('-r', action='store', dest='grid_region', default=default,
       help='NWS region in grid file (default="%s")' % default)

default = CONFIG.sources.reanalysis.grid.source
parser.add_option('-s', action='store', dest='grid_source', default=default,
       help='NRCC grid format to use for datasets (default="%s")' % default)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-u', action='store_false', dest='utc_file', default=True,
       help='boolean: grid file uses UTC timezone (default=True)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

default = CONFIG.sources.reanalysis.grib.region
parser.add_option('--grib_region', action='store', dest='grib_region',
       help='NWS region in grib file (default="%s")' % default,
       default=default)

default = CONFIG.sources.reanalysis.grib.source
parser.add_option('--grib_source', action='store', dest='grib_source',
       help='NWS reanalysis product in grib file (default="%s")' % default,
       default=default)

default = CONFIG.sources.reanalysis.grib.timezone
parser.add_option('--gribtz', action='store', dest='grib_timezone',
       help='name of timezonae in grib file (default="%s")' % default,
       default=default)

default=CONFIG.project.local_timezone
text = 'name of local timezone used in date args (default="%s")'
parser.add_option('--localtz', action='store', dest='local_timezone',
       help=text % default, default=default)

del default, text

options, args = parser.parse_args()

num_time_args = len(args) - 2
if num_time_args not in (0,1,2,3,4,5,6,7):
    errmsg = '%d date arguments passed. 0 up to 7 time arguments'
    errmsg += ' are supported.\n%s'
    raise RuntimeError, errmsg % (num_time_args, usage)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
grib_region = options.grib_region
grib_source = options.grib_source
grib_timezone = options.grib_timezone
grid_region = options.grid_region
grid_source = options.grid_source
local_timezone = options.local_timezone
local_tzinfo = tzutils.asTzinfo(local_timezone)
utc_file = options.utc_file
verbose = options.verbose or debug

# complete analysis source key
analysis = args[0]
analysis_source = '.'.join((analysis,grib_source))

if utc_file: file_tzinfo = tzutils.asTzinfo('UTC')
else: file_tzinfo = local_tzinfo 

# need smart reader to retrieve the gribs and also to determine if passed grib variable is legit
grib_reader = SmartReanalysisGribReader(analysis_source, grid_source=grid_source, grid_region=grid_region)
if dev_mode: grib_reader.useDirpathsForMode('dev')

grid_variable = grib_reader.gridVariableName(args[1].upper())

now = datetime.datetime.now()
if num_time_args == 0: # get data for the current local hour 
    data_end_time = None
    data_start_time = None

elif num_time_args == 1:
    arg_2 = args[2]
    if 'b' in arg_2: # span multiple hours ending at current LOCAL time
        # arg 2 = number of hours before current time
        data_end_time = hourInTimezone(now.year, now.month, now.day, now.hour, local_tzinfo)
        if not tzutils.isSameTimezone(local_tzinfo, file_tzinfo):
            # convert local time to UTC time (file_tzinfo)
            data_end_time = tzutils.toTimeInZone(data_end_time, file_tzinfo)
        hours = int(args_2.replace('b',''))
        data_start_time = data_end_time - datetime.timedelta(hours=hours)
    else: # arg_2 == specific hour (UTC time) on current day
        data_start_time = data_end_time = \
            hourInTimezone(now.year, now.month, now.day, args_2, file_tzinfo)

elif num_time_args == 2:
    arg_2 = int(args[2])
    arg_3 = int(args[3].replace('h',''))
    if arg_3 == 99: # all hours for a month
        # args ... 2 = month, 3 is the trigger
        data_start_time = hourInTimezone(now.year, arg_2, 1, 0, file_tzinfo)
        last_day = lastDayOfMonth(now.year, arg_2)
        data_end_time = hourInTimezone(now.year, arg_2, last_day, 23, file_tzinfo)
    elif 'h' in args[3]:
        data_start_time = data_end_time = hourInTimezone(now.year, now.month, arg_2, arg_3, file_tzinfo)
    else: # all hours (UTC time) on multiple days in current month
        # args ... 2 = 1st day, 3 = last day
        data_start_time = hourInTimezone(now.year, now.month, arg_2, 0, file_tzinfo)
        data_end_time = hourInTimezone(now.year, now.month, arg_3, 23, file_tzinfo)

elif num_time_args == 3: # span multiple hours (UTC time) on a single day
    arg_2 = int(args[2])
    if arg_2 > 99:
        month = int(args[3])
        arg_4 = int(args[4])
        if arg_4 == 99: # all hours for a specific year/month
            # args ... 2 = year, 3 = month, 4 is the trigger
            data_start_time = hourInTimezone(arg_2, month, 1, 0, file_tzinfo)
            last_day = lastDayOfMonth(arg_2, month)
            data_end_time = hourInTimezone(arg_2, month, last_day, 23, file_tzinfo)
        else: # all hours for a specific year,month,day
            # args ... 2 = year, 3 = month, 4 = day
            data_start_time = hourInTimezone(arg_2, month, arg_4, 0, file_tzinfo)
            data_end_time = hourInTimezone(arg_2, month, arg_4, 23, file_tzinfo)
    else:
        if 'h' in args[4]:
            hour = int(args[4].replace('h',''))
            data_start_time = data_end_time = \
                hourInTimezone(now.year, arg_2, int(args[3]), hour, file_tzinfo)
        else:
            # specific hours for a specific day in current month
            # args ... 2 = day, 3 = 1st hour, 4 = last hour
            data_start_time = hourInTimezone(now.year, now.month, arg_2, int(args[3]), file_tzinfo)
            data_end_time = hourInTimezone(now.year, now.month, arg_2, int(args[4]), file_tzinfo)

elif num_time_args == 4:
    arg_2 = int(args[2])
    arg_3 = int(args[3])
    if arg_2 > 99: # times in specific year
        if 'h' in args[5]: # specific year/month/day/hour
            # args ... 2 = year, 3 = month, 4 = day, 5 = hour
            hour = int(args[5].replace('h','')) 
            update_start_time = hourInTimezone(arg_2, arg_3, int(args[4]), hour, file_tzinfo)
            update_end_time = update_start_time
        else: # all hours (UTC time) for multiple days in specific year/month
            # args ... 2 = year, 3 = month, 4 = 1st day, 5 = last day
            data_start_time = hourInTimezone(arg_2, arg_3, int(args[4]), 0, file_tzinfo)
            data_end_time = hourInTimezone(arg_2, arg_3, int(args[5]), 23, file_tzinfo)
    else: # specific hours (UTC time) for month/day in current year
        # args ... 2 = month, 3 = day, 4 = 1st hour, 5 = last hour
        data_start_time = hourInTimezone(now.year, arg_2, arg_3, int(args[4]), file_tzinfo)
        data_end_time = hourInTimezone(now.year, arg_2, arg_3, int(args[5]), file_tzinfo)

elif num_time_args == 5:
    arg_2 = int(args[2])
    if arg_2 > 99: # specific hours (UTC time) for specific year/month/day
        # args ... 2 = year, 3 = month, 4 = day, 5 = 1st hour, 6 = last hour
        month = int(args[3])
        day = int(args[4]) 
        data_start_time = hourInTimezone(arg_2, month, day, int(args[5]), file_tzinfo)
        data_end_time = hourInTimezone(arg_2, month, day, int(args[6]), file_tzinfo)
    else: # mutiple days/hours in specific month of current year
        # args ... 2 = month, 3 = 1st day, 4 = 1st hour, 5 = last day, 6 = last hour
        data_start_time = hourInTimezone(now.year, arg_2, int(args[3]), int(args[4]), file_tzinfo)
        data_end_time = hourInTimezone(now.year, arg_2, int(args[5]), int(args[6]), file_tzinfo)

elif num_time_args == 6:
    arg_2 = int(args[2])
    if arg_2 > 99: # specific days/hours (UTC time) in specific year/month
        arg_7 = int(args[7])
        if arg_7 == 99: # all hours (UTC time) in specific year/month/day span
            # args ... 2 = year, 3 = 1st month, 4 = 1st day, 5 = last month, 6 = last day
            update_start_time = hourInTimezone(arg_2, int(args[3]), int(args[4]), 0, file_tzinfo)
            update_end_time = hourInTimezone(arg_2, int(args[5]), int(args[6]), 23, file_tzinfo)
        else: # specific days/hours (UTC time) in specific year/month
            month = int(args[3])
            # args ... 2 = year, 3 = month, 4 = 1st day, 5 = 1st hour, 6 = last day, 7 = last hour
            data_start_time = hourInTimezone(arg_2, month, int(args[4]), int(args[5]), file_tzinfo)
            data_end_time = hourInTimezone(arg_2, month, int(args[6]), arg_7, file_tzinfo)
    else: # specific months/days/hours (UTC time) in current year
        data_start_time = hourInTimezone(now.year, arg_2, int(args[3]), int(args[4]), file_tzinfo)
        data_end_time = hourInTimezone(now.year, int(args[5]), int(args[6]), int(args[7]), file_tzinfo)

elif num_time_args == 7: # multiple days in different month of the same year
    # args ... 2 = year, 3 = first month, 4 = 1st day, 5 = 1st hour,
    #                    6 = last month 7 = last day, 8 = last hour
    year = int(args[2])
    update_start_time = hourInTimezone(year, int(args[3]), int(args[4]), int(args[5]), file_tzinfo)
    update_end_time = hourInTimezone(year, int(args[6]), int(args[7]), int(args[8]), file_tzinfo)

# create a factory for access to grid files
grid_factory = ReanalysisGridFileFactory()
if dev_mode: grid_factory.useDirpathsForMode('dev')

# get all available data since last reanalysis update
if data_start_time is None:
    time_attr_key = '%s_end_time' % analysis.lower()

    filepath = grid_factory.analysisGridFilepath(now, grid_variable, grid_region)
    if not os.path.exists(filepath):
        # look in previous month to make sure it was completed
        if now.month >=2:
            prev_month = now.month - 1
            last_day = lastDayOfMonth(now.year, prev_month)
            btimeSliceefore = datetime.datetime(now.year, prev_month, last_day, 23)
        else: before = datetime.datetime(now.year-1, 12, 31, 23)

        prevpath = grid_factory.analysisGridFilepath(before, grid_variable, grid_region)
        if os.path.exists(prevpath):
            reader = grid_factory.gridFileReader(before, grid_variable, grid_region)
            last_time = reader.timeAttribute(grid_variable, time_attr_key)
            if last_time.day < last_day: data_start_time = last_time
            elif last_time.hour < 23: data_start_time = last_time
            reader.close()
        del reader

        grid_factory.buildReanalysisGridFile(now, grid_variable, grid_region, 'UTC')

    # start time is in current month
    if data_start_time is None:
        reader = grid_factory.gridFileReader(now, grid_variable, grid_region)
        last_anal_time = reader.timeAttribute(grid_variable, time_attr_key, None)
        if last_anal_time is None: # file never updated before
            data_start_time = reader.timeAttribute(grid_variable, 'start_time')
        else: # starting 1 hour after last valid time in file
            data_start_time = last_anal_time + datetime.timedelta(hours=1)
        reader.close()
        del reader

    data_end_time = grib_reader.lastAvailableGribHour(grid_variable, data_start_time)
    if data_start_time >= data_end_time:
        why = (grid_variable, data_end_time.strftime('%Y-%m-%d:%H'))
        print '%s grid file is already at latest available analysis time : %s' % why
        exit()

if data_end_time == data_start_time:
    periods = ((data_start_time, data_end_time),)
else:
    periods = grib_reader.slices(data_start_time, data_end_time) 

if verbose:
    print 'requesting ...'
    print '          analysis :', analysis
    print '     grid variable :', grid_variable
    print ' update start time :', repr(data_start_time)
    print '   update end time :', repr(data_end_time)
    print '\nperiods :'
    for period in periods:
        print '    %s to %s' % (repr(period[0]),repr(period[1]))

kwargs = { 'debug':debug, 'verbose':verbose }
missing_times = [ ]
total_hours = 0

missing_msg = '\nAdding %%d of %%d requested hours of %s beginning %%s' % grid_variable
success_msg = '\nAdding data for %%d hours of %s beginning %%s' % grid_variable
timespan_warning = '\nWARNING: No %s data found for timespan %%s thru %%s' % grid_variable
hour_warning = '\nWARNING: No %s data found for %%s' % grid_variable


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


for slice_start, slice_end in periods:
    # make sure that a file exists for the requeste time period
    filepath = grid_factory.analysisGridFilepath(slice_start, grid_variable, grid_region)
    if not os.path.exists(filepath):
        grid_factory.buildReanalysisGridFile(slice_start, grid_variable, grid_region, 'UTC')

    manager = grid_factory.gridFileManager(slice_start, grid_variable, grid_region)
    var_times = manager.timeAttributes(grid_variable, True)
    manager.close()
    grid_start_time = var_times['start_time']
    grid_end_time = var_times['end_time']
    grid_tzinfo = manager.tzinfo

    if debug:
        print '\ngrid file time attrs :'
        print '    grid start time :', grid_start_time
        print '      grid end time :', grid_end_time
        print '      grid timezone :', repr(grid_tzinfo)
    if verbose:
        print '\ngrib request time attrs :'
        print '    grib start time :', slice_start
        print '      grib end time :', slice_end
        hours_in_slice = tzutils.hoursInTimespan(slice_start, slice_end)
        print '     hours in slice :', hours_in_slice

    grib_units, grib_data, failed = \
        grib_reader.timeSlice(grid_variable, slice_start, slice_end, **kwargs)
    num_fails = len(failed)
    if num_fails > 0: missing_times.extend(failed)
    
    if slice_end > slice_start:
        hours_in_slice = grib_data.shape[0]
    else: hours_in_slice = 1 # 2D slice is one hour

    if num_fails < hours_in_slice:
        valid_hours = hours_in_slice - num_fails
        total_hours += valid_hours
        if valid_hours < hours_in_slice:
            print missing_msg % (valid_hours, hours_in_slice, tzutils.tzaString(slice_start))
        else:
            print success_msg % (valid_hours, tzutils.tzaString(slice_start))

        manager.open('a')
        manager.updateReanalysisData(analysis, grid_variable, slice_start,
                                     grib_data, units=grib_units)
        manager.close()

        if verbose:
            skip = ('end_time', 'start_time', 'timezone', 'tzinfo')
            print '\nUpdated time attributes for %s dataset :' % grid_variable
            manager.open('r')
            for time_key, hour in manager.timeAttributes(grid_variable).items():
                if not time_key in skip:
                    print '    %s = %s' % (time_key, hour.strftime('%Y-%m-%d:%H'))
            manager.close()
            print ' '

    else:
        if slice_end > slice_start:
            print timespan_warning % (slice_start.strftime('%Y-%m-%d:%H'),
                                      slice_end.strftime('%Y-%m-%d:%H') )
        else: print hour_warning % slice_start.strftime('%Y-%m-%d:%H')


# turn annoying numpy warnings back on
warnings.resetwarnings()

if len(missing_times) > 0:
    for missing in missing_times:
        reason, hour, filepath = missing
        info = (timeString(hour), reason, filepath.split('conus/')[1])
        print '\nDate missing for %s : %s\n    %s' % info
        success, message = \
            grid_factory.repairMissingReanalysis(hour, grid_variable, grid_region)
        print '    %s' % message
        if success: total_hours += 1

elapsed_time = elapsedTime(UPDATE_START_TIME, True)
msg = '\ncompleted update of %d hours of "%s" data in %s'
print msg % (total_hours, grid_variable, elapsed_time)

