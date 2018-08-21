#! /usr/bin/env python

import datetime
ONE_HOUR = datetime.timedelta(hours=1)

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

from turf.weather.factory import TurfWeatherFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateReanalysis(factory, manager, variable, start_time, end_time, debug):
    # figure out the start time for reanalysis temperature
    if start_time is None:
        manager.open('r')
        prev_hour = manager.timeAttribute(variable, 'rtma_end_time', None) 
        if prev_hour is None:
            prev_hour = manager.timeAttribute(variable, 'fcast_start_time', None)
            if prev_hour is None:
                data_start_time = manager.timeAttribute(variable, 'start_time')
            else: data_start_time = prev_hour
        else: data_start_time = prev_hour + ONE_HOUR
        manager.close()
    else: data_start_time = start_time

    # get an forecast data reader for the variable
    reader = factory.gridFileReader(data_start_time, variable, region_key)

    # figure out the end time for reanalysis temperature
    anal_end_time = reader.timeAttribute(variable, 'last_valid_time')
    if end_time is None or end_time > anal_end_time:
        data_end_time = anal_end_time
        if data_end_time <= data_start_time:
            print 'Renalysis data for %s is already up to date' % variable
            return False
    else: data_end_time = end_time

    args = (variable, data_start_time.strftime('%Y-%m-%d:%H'),
            data_end_time.strftime('%Y-%m-%d:%H'))
    print 'Updating reanalysis data for %s from %s thru %s' % args

    # extract the relevant reanalysis data
    data = reader.timeSlice(variable, data_start_time, data_end_time, debug=debug)
    reader.close()
    del reader

    # update variable data in weather file
    manager.open('a')
    manager.updateReanalysis(variable, data_start_time, data)
    manager.close()
    if debug:
        manager.open('r')
        print '\n    rtma_end_time =',manager.timeAttribute(variable,'rtma_end_time')
        print ' last_valid_time =',manager.timeAttribute(variable,'last_valid_time')
        print 'fcast_start_time =',manager.timeAttribute(variable,'fcast_start_time')
        print '  fcast_end_time =',manager.timeAttribute(variable,'fcast_end_time')
        print '\n'
        manager.close()

    return True


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='grid_region', default='NE',
       help='NWS region in grid file (default="NE")')
                        
parser.add_option('-s', action='store', dest='grid_source', default='acis',
       help='NRCC grid format to use for datasets (default="acis")')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

parser.add_option('--localtz', action='store', dest='local_timezone',
                  default='US/Eastern')

options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
local_timezone = options.local_timezone
periods = ('daily','average')
region_key = options.grid_region
source_key = options.grid_source
verbose = options.verbose or debug

now = tzutils.asUtcHour(datetime.datetime.now(), local_timezone)

weather_key = 'temps'

# default to current year & month 
year = now.year
month = current_month = now.month

num_time_args = len(args)

if num_time_args == 0 :
    # no time args, discover them from times in the files
    start_time = None
    end_time = None

elif num_time_args == 1:
    month = int(args[0])
    start_time = tzutils.asUTCTime(datetime.datetime(year, month, 1, 0))
    last_day = lastDayOfMonth(year, month)
    end_time = tzutils.asUTCTime(datetime.datetime(year, month, last_day, 23))

elif num_time_args == 2:
    arg_0 = int(args[0])
    if arg_0 > 99:
        year = arg_0
        month = int(args[1])
        start = tzutils.asUTCTime(datetime.datetime(year, month, 1, 0))
        last_day = lastDayOfMonth(year, month)
        end_time = tzutils.asUTCTime(datetime.datetime(year, month, last_day, 23))
    elif 'h' in args[1]:
        hour = int(args[1].replace('h', ''))
        start_time = end_time = tzutils.asUTCTime(datetime.datetime(year, month, arg_0, hour))
    else:
        start_time = tzutils.asUTCTime(datetime.datetime(year, month, arg_0, 0))
        end_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[1]), 23))

elif num_time_args == 3:
    month = int(args[0])
    start_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[1]), 0))
    end_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[2]), 23))
    
elif num_time_args == 4:
    if 'm' in args[0]:
        month = int(args[0].replace('m', ''))
        day = int(args[1])
        start_time = tzutils.asUTCTime(datetime.datetime(year, month, day, int(args[2])))
        end_time = tzutils.asUTCTime(datetime.datetime(year, month, day, int(args[3])))
    else:
        arg_0 = int(args[0])
        if arg_0 > 99:
            year = arg_0
            month = int(args[1])
            start_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[2]), 0))
            end_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[3]), 23))
        else:
            start_time = tzutils.asUTCTime(datetime.datetime(year, month, arg_0, int(args[1])))
            end_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[2]), int(args[3])))

elif num_time_args == 5:
    month = int(args[0])
    start_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[1]), int(args[2])))
    end_time = tzutils.asUTCTime(datetime.datetime(year, month, int(args[3]), int(args[4])))


# create a factory for access to reanalysis files
turf_factory = TurfWeatherFileFactory()
if dev_mode: turf_factory.useDirpathsForMode('dev')
region = turf_factory.regionConfig(region_key)
source = turf_factory.sourceConfig(source_key)

# get a factory for access to forecast files
anal_factory = ReanalysisGridFileFactory()
if dev_mode: anal_factory.useDirpathsForMode('dev')

# get a data manager for the weather file components
manager = \
turf_factory.weatherFileManager(weather_key, year, month, region, mode='r')
manager.close()

completed = 0
# update reanalysis temperatures
success = updateReanalysis(anal_factory, manager, 'TMP', start_time, end_time, debug)
if success: completed += 1

# update reanalysis dew points
success = updateReanalysis(anal_factory, manager, 'DPT', start_time, end_time, debug)
if success: completed += 1

if completed > 0:
    print '\nCompleted reanalysis data updates in :\n', manager.filepath

