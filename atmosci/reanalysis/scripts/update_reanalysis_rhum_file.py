#! /Volumes/Transport/venvs/atmosci/bin/python
#! /usr/bin/env python

import os, sys
import datetime
import warnings

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime, lastDayOfMonth
from atmosci.equations import rhumFromDpt
from atmosci.units import convertUnits

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def hourInTimezone(year, month, day, hour, tzinfo):
    # tzinfo must be an instance of pytz.tzinfo
    return tzinfo.localize(datetime.datetime(year, month, day, hour))

def compareTimes(tmp_times, dpt_times):
    keymsg = 'Time attribute "%s" in %s file but not in %s file'
    timerr = 'Time attribute "%s" = %s in %s file but = %s in %s file'

    errors = 0
    for key, hour in tmp_times.items():
        if key not in dpt_times:
            errors += 1
            print keymsg % (key, 'TMP', 'DPT')
        elif hour != dpt_times[key]:
            errors += 1
            print timerr % (key, repr(hour), 'TMP', dpt_times[key], 'DPT')

    return errors


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

usage = 'usage: %prog  [options]'
usage += '\n   for data in current year:'
usage += '\n       %prog  analysis hour(UTC) [options]'
usage += '\n       %prog  analysis day day [options]'
usage += '\n       %prog  analysis month day [options]'
usage += '\n       %prog  analysis month day hour(UTC) [options]'
usage += '\n       %prog  analysis month day 1st_hour(UTC) last_hour(UTC) [options]'
usage += '\n       %prog  analysis month 1st_day hour(UTC) last_day hour(UTC) [options]'
usage += '\n       %prog  analysis 1st_month day hour(UTC) last_month day hour(UTC) [options]'
usage += '\n   for data in specific year:'
usage += '\n       %prog  analysis year month day [options]'
usage += '\n       %prog  analysis year month day hour(UTC) [options]'
usage += '\n       %prog  analysis year month day 1st_hour(UTC) last_hour(UTC) [options]'
usage += '\n       %prog  analysis year month 1st_day hour(UTC) last_day hour(UTC) [options]'
usage += '\n       %prog  analysis year 1st_month day hour(UTC) last_month day hour(UTC) [options]'
usage += '\n\nWhen no time args are passed, date is updated beginning one hour'
usage += '\nafter the last valid reanalysis and ending at the current time.'

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

default = CONFIG.sources.reanalysis.grid.region
parser.add_option('-r', action='store', dest='grid_region', default=default,
       help='NWS region in grid file (default="%s")' % default)

parser.add_option('-u', action='store_false', dest='utc_file', default=True,
       help='boolean: grid file uses UTC timezone (default=True)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

default=CONFIG.project.local_timezone
text = 'name of local timezone used in date args (default="%s")'
parser.add_option('--localtz', action='store', dest='local_timezone',
       help=text % default, default=default)
del default

options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
grid_region = options.grid_region
local_timezone = options.local_timezone
local_tzinfo = tzutils.asTzinfo(local_timezone)
now = datetime.datetime.now()
utc_file = options.utc_file
verbose = options.verbose or debug

if utc_file: file_tzinfo = tzutils.asTzinfo('UTC')
else: file_tzinfo = local_tzinfo 

now = datetime.datetime.now()
num_time_args = len(args)
if num_time_args == 0: # get data for the current local hour
    update_end_time = None
    update_start_time = None

elif num_time_args == 1:
    arg_0 = args[0]
    if 'b' in arg_0: # span multiple hours ending at current LOCAL time
        update_end_time = hourInTimezone(now.year, now.month, now.day, now.hour, local_tzinfo)
        if not tzutils.isSameTimezone(local_tzinfo, file_tzinfo):
            # convert local time to UTC time (file_tzinfo)
            update_end_time = tzutils.toTimeInZone(update_end_time, file_tzinfo)
        hours = int(args_1.replace('b',''))
        update_start_time = update_end_time - datetime.timedelta(hours=hours)
    else: # arg_0 == specific hour (UTC time) on current day
        update_start_time = update_end_time = \
            hourInTimezone(now.year, now.month, now.day, int(args_1), file_tzinfo)

elif num_time_args == 2:
    arg_0 = int(args[0])
    arg_1 = int(args[1])
    if arg_1 == 99: # all hours for a month
        # args ... 1 = month, 2 is the trigger
        update_start_time = hourInTimezone(now.year, arg_0, 1, 0, file_tzinfo)
        last_day = lastDayOfMonth(now.year, arg_0)
        update_end_time = hourInTimezone(now.year, arg_0, last_day, 23, file_tzinfo)
    else: # all hours (UTC time) on multiple days in current month
        # args ... 1 = 1st day, 2 = last day
        update_start_time = hourInTimezone(now.year, now.month, arg_0, 0, file_tzinfo)
        update_end_time = hourInTimezone(now.year, now.month, arg_1, 23, file_tzinfo)

elif num_time_args == 3: # span multiple hours (UTC time) on a single day
    arg_0 = int(args[0])
    if arg_0 > 99:
        month = int(args[1])
        arg_2 = int(args[2])
        if arg_2 == 99: # all hours for a year/month
            # args ... 1 = year, 2 = month, 3 is the trigger
            update_start_time = hourInTimezone(arg_0, month, 1, 0, file_tzinfo)
            last_day = lastDayOfMonth(arg_0, month)
            update_end_time = hourInTimezone(arg_0, month, last_day, 23, file_tzinfo)
        else: # all hours for a specific year,month,day
            # args ... 1 = year, 2 = month, 3 = day
            update_start_time = hourInTimezone(arg_0, month, arg_2, 0, file_tzinfo)
            update_end_time = hourInTimezone(arg_0, month, arg_2, 23, file_tzinfo)
    elif 'h' in args[1]:
        first_hour = int(args[1].replace('h',''))
        # specific hours for a specific day in current month
        # args ... 0 = day, 1 = 1st hour, 2 = last hour
        update_start_time = hourInTimezone(now.year, now.month, arg_0, first_hour, file_tzinfo)
        update_end_time = hourInTimezone(now.year, now.month, arg_0, int(args[2]), file_tzinfo)
    else:
        # all hours for a specific days in same month
        # args ... 0 = month, 1 = 1st day, 2 = last day
        update_start_time = hourInTimezone(now.year, arg_0, int(args[1]), 0, file_tzinfo)
        update_end_time = hourInTimezone(now.year, arg_0, int(args[2]), 23, file_tzinfo)

elif num_time_args == 4:
    arg_0 = int(args[0])
    arg_1 = int(args[1])
    if arg_0 > 99: # times in specific year
        arg_3 = args[3]
        if 'h' in arg_3: # specific year/month/day/hour
            # args ... 1 = year, 2 = month, 3 = day, 4 = hour
            hour = int(arg_3.replace('h','')) 
            update_start_time = hourInTimezone(arg_0, arg_1, int(args[2]), hour, file_tzinfo)
            update_end_time = update_start_time
        else: # all hours (UTC time) for a multiple days in specific year/month
            # args ... 1 = year, 2 = month, 3 = 1st day, 4 = last day
            update_start_time = hourInTimezone(arg_0, arg_1, int(args[2]), 0, file_tzinfo)
            update_end_time = hourInTimezone(arg_0, arg_1, int(args[3]), 23, file_tzinfo)
    else: # # specific hours (UTC time) for month/day in current year
        # args ... 1 = month, 2 = day, 3 = 1st hour, 4 = last hour
        update_start_time = hourInTimezone(now.year, arg_0, arg_1, int(args[2]), file_tzinfo)
        update_end_time = hourInTimezone(now.year, arg_0, arg_1, int(args[3]), file_tzinfo)

elif num_time_args == 5:
    arg_0 = int(args[0])
    if arg_0 > 99: # specific hours (UTC time) for specific year/month/day
        # args ... 1 = year, 2 = month, 3 = day, 4 = 1st hour, 5 = last hour
        month = int(args[1])
        day = int(args[2]) 
        update_start_time = hourInTimezone(arg_0, month, day, int(args[3]), file_tzinfo)
        update_end_time = hourInTimezone(arg_0, month, day, int(args[4]), file_tzinfo)
    else: # mutiple days/hours in specific month of current year
        # args ... 1 = month, 2 = 1st day, 3 = 1st hour, 4 = last day, 5 = last hour
        update_start_time = hourInTimezone(now.year, arg_0, int(args[1]), int(args[2]), file_tzinfo)
        update_end_time = hourInTimezone(now.year, arg_0, int(args[3]), int(args[4]), file_tzinfo)

elif num_time_args == 6:
    arg_0 = int(args[0])
    if arg_0 > 99: # times in specific year
        arg_5 = int(args[5])
        if arg_5 == 99: # all hours (UTC time) in specific year/month/day span
            # args ... 1 = year, 2 = 1st month, 3 = 1st day, 4 = last month, 5 = last day
            update_start_time = hourInTimezone(arg_0, int(args[1]), int(args[2]), 0, file_tzinfo)
            update_end_time = hourInTimezone(arg_0, int(args[3]), int(args[4]), 23, file_tzinfo)
        else: # specific days/hours (UTC time) in specific year/month
            # args ... 1 = year, 2 = month, 3 = 1st day, 4 = 1st hour, 5 = last day, 5 = last hour
            month = int(args[1])
            update_start_time = hourInTimezone(arg_0, month, int(args[2]), int(args[3]), file_tzinfo)
            update_end_time = hourInTimezone(arg_0, month, int(args[4]), int(args[5]), file_tzinfo)
    else: # specific months/days/hours (UTC time) in current year
        update_start_time = hourInTimezone(now.year, arg_0, int(args[1]), int(args[2]), file_tzinfo)
        update_end_time = hourInTimezone(now.year, int(args[3]), int(args[4]), int(args[5]), file_tzinfo)

elif num_time_args == 7: # multiple days in different month of the same year
    # args ... 1 = year, 2 = first month, 3 = 1st day, 4 = 1st hour,
    #                    5 = last month 6 = last day, 7 = last hour
    year = int(args[0])
    update_start_time = hourInTimezone(year, int(args[1]), int(args[2]), int(args[3]), file_tzinfo)
    update_end_time = hourInTimezone(year, int(args[4]), int(args[5]), int(args[6]), file_tzinfo)


# create a factory for access to grid files
grid_factory = ReanalysisGridFileFactory()
if dev_mode: grid_factory.useDirpathsForMode('dev')

if update_start_time is None:
    filepath = grid_factory.analysisGridFilepath(now, 'RHUM', grid_region)
    if not os.path.exists(filepath):
        grid_factory.buildReanalysisGridFile(now, 'RHUM', grid_region, 'UTC')

    reader = grid_factory.gridFileManager(now, 'RHUM', grid_region)
    time_attr_key = '%s_end_time' % analysis.lower()
    last_anal_time = reader.timeAttribute('RHUM', time_attr_key, None)
    if last_anal_time is None: # file never updated before
        update_start_time = reader.timeAttribute('RHUM', 'start_time')
    else: # starting 1 hour after last valid time in file
        update_start_time = last_anal_time + datetime.timedelta(hours=1)

    # now find the end time in the TMP file
    reader = grid_factory.gridFileManager(update_start_time, 'TMP', grid_region) 
    time_attr_key = '%s_end_time' % analysis.lower()
    update_end_time = reader.timeAttribute('TMP', time_attr_key, None)

    # check hether we can (or should) do the update
    if update_end_time is None: # temperature never updated
        monthyear = update_start_time.strftime('%M, %Y')
        print 'WARNING: NO TEMPERATURE DATA AVAIALBLE FOR %s' % monthyear
        exit()

    elif update_start_time >= update_end_time:
        last_time = update_end_time.strftime('%Y-%m-%d:%H')
        print 'RHUM is already at max available analysis time for TMP : %s' % last_time
        exit()

if update_end_time.month > update_start_time.month:
    periods = [ ]
    start = update_start_time
    month = update_start_time.month
    while True: 
        last_day = lastDayOfMonth(start.year, start.month)
        end = hourInTimezone(start.year, start.month, last_day, 23, file_tzinfo)
        if end < update_end_time:
            periods.append((start, end))
            month += 1
            if month <= 12:
                start = hourInTimezone(start.year, month, 1, 0, file_tzinfo)
            else:
                year = start.year + 1
                month = 1
                start = hourInTimezone(year, month, 1, 0, file_tzinfo)
        else: 
            periods.append((start, update_end_time))
            break;
else:
    periods = [(update_start_time,update_end_time),]

if verbose:
    print 'requesting data for ...'
    print ' update start time :', repr(update_start_time)
    print '   update end time :', repr(update_end_time)
    print '          timezone :', repr(local_timezone)
    print 'periods :'
    for period in periods:
        print 'start :', period[0], '   end :', period[1]

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

for slice_start, slice_end in periods:
    # make sure that a grid file exists for the requested time period
    filepath = grid_factory.analysisGridFilepath(slice_start, 'RHUM', grid_region)
    if not os.path.exists(filepath):
        grid_factory.buildReanalysisGridFile(slice_start, 'RHUM', grid_region, 'UTC')

    if debug:
        print '\ntmp/dpt data timespan : start =', repr(slice_start), ': data end =', repr(slice_end)
    # get manager for the slice time span
    manager = grid_factory.gridFileManager(slice_start, 'RHUM', grid_region)
    manager.close()

    filepath = grid_factory.analysisGridFilepath(slice_start, 'TMP', grid_region)
    if not os.path.exists(filepath):
        monthyear = slice_start.strftime('%M, %Y')
        print 'WARNING: NO TEMPERATURE DATA AVAIALBLE FOR %s' % monthyear
        exit()

    tmp_reader = grid_factory.gridFileManager(slice_start, 'TMP', grid_region)
    if debug: print 'temperature file path :\n    ', tmp_reader.filepath
    tmpfile_times = tmp_reader.timeAttributes('TMP')
    tmp_reader.close()

    filepath = grid_factory.analysisGridFilepath(slice_start, 'DPT', grid_region)
    if not os.path.exists(filepath):
        monthyear = slice_start.strftime('%M, %Y')
        print 'WARNING: NO DEW POINT DATA AVAIALBLE FOR %s' % monthyear
        exit()

    dpt_reader = grid_factory.gridFileManager(slice_start, 'DPT', grid_region)
    if debug: print 'dew point file path :\n', dpt_reader.filepath
    dptfile_times = dpt_reader.timeAttributes('DPT')
    dpt_reader.close()

    errors = compareTimes(tmpfile_times, dptfile_times)
    if errors > 0:
        print 'ERROR : time in TMP file and DPT file are out of sync for'
        interval = (slice_start.strftime('%Y-%m-%d:%H'),
                    slice_end.strftime('%Y-%m-%d:%H'))
        print '        interval %s to %s' % interval
        print 'EXITING : further processing is not possible..'
        exit()

    tmp_reader.open()
    tmp = tmp_reader.timeSlice('TMP', slice_start, slice_end)
    tmp_units = tmp_reader.datasetAttribute('TMP','units')
    tmp_reader.close()

    dpt_reader.open()
    dpt = dpt_reader.timeSlice('DPT', slice_start, slice_end)
    dpt_units = dpt_reader.datasetAttribute('DPT','units')
    dpt_reader.close()
    if dpt_units != tmp_units: dpt = convertUnits(dpt, dpt_units, tmp_units)
 
    rhum = N.around(rhumFromDpt(tmp, dpt, tmp_units), 2)
    num_hours = rhum.shape[0]

    if verbose:
        msg = 'Adding RHUM for %d hours beginning %s :'
        print msg % (num_hours, tzutils.tzaString(slice_start))
    manager.open('a')
    manager.updateReanalysisData('rtma', 'RHUM', slice_start, rhum)
    manager.close()

    if verbose:
        skip = ('end_time', 'start_time', 'timezone', 'tzinfo')
        print '\nUpdated time attributes for RHUM dataset :'
        manager.open('r')
        for time_key, hour in manager.timeAttributes('RHUM').items():
            if not time_key in skip:
                print '    %s = %s' % (time_key, hour.strftime('%Y-%m-%d:%H'))
        manager.close()
        print ' '

# turn annoying numpy warnings back on
warnings.resetwarnings()

msg = 'Added RHUM for %d hours beginning %s :'
print msg % (num_hours, tzutils.tzaString(slice_start))

