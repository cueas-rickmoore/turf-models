#! /usr/bin/env python

import os
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.ndfd.factory import NdfdGridFileFactory

from turf.weather.factory import TurfWeatherFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getForecastData(factory, manager, variable, start_time, debug):
    if '.' in variable:
        grib_var, grid_var = variable.split('.')
    else: grib_var = grid_var = variable

    if start_time is None:
        manager.open('r')
        start_time = manager.timeAttribute(grid_var, 'rtma_end_time', None)
        if start_time is None:
            start_time = manager.timeAttribute(grid_var, 'start_time')
        else: start_time += ONE_HOUR
        manager.close()

    if os.path.exists(factory.ndfdGridFilepath(start_time, grib_var, 'NE')):
        # get a reader for the forecast file
        reader = factory.ndfdGridFileReader(start_time, grib_var, region_key)
        end_time = reader.timeAttribute(grid_var, 'last_valid_time', None)
        reader.close()

        if debug:
            times = (start_time.strftime('%m-%d:%H'), end_time.strftime('%m-%d:%H'))
            print '\nwill update forecast from %s thru %s' % times

        if end_time is None:
            del reader
            print '\nNO %s FORECAST AVAILABLE FOR %s/%s' % (variable,start_time.month,start_time.year)
            return start_time, end_time, None
        else:
            # extract the relevant forecast data
            reader.open()
            data = reader.timeSlice(grid_var, start_time, end_time)
            reader.close()
            del reader
            return start_time, end_time, data

    else: return start_time, None, None


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateForecast(manager, variable, fcast_start, data, debug):
    if len(data.shape) == 3:
        fcast_end = fcast_start + datetime.timedelta(hours=data.shape[0]-1)
        info = (variable, data.shape[0], fcast_start.strftime('%Y-%m-%d:%H'),
                fcast_end.strftime('%Y-%m-%d:%H'))
        print 'Updating %s forecast data for %s hours (%s thru %s)' % info 
    else:
        info = (variable, fcast_start.strftime('%Y-%m-%d:%H'))
        print 'Updating %s forecast data for 1 hour (%s)' % info 

    # update temperatures in weather file
    manager.open('a')
    manager.updateForecast(variable, fcast_start, data)
    fcast_end_time = manager.timeAttribute(variable,'fcast_end_time')
    manager.close()
    if debug:
        weather_manager.open('r')
        print '\n    rtma_end_time =',manager.timeAttribute(variable,'rtma_end_time')
        print 'fcast_start_time =',manager.timeAttribute(variable,'fcast_start_time')
        print '  fcast_end_time =',fcast_end_time
        print ' last_valid_time =',manager.timeAttribute(variable,'last_valid_time')
        print '\n'
        manager.close()

    return fcast_start, fcast_end_time


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updatePopPcpn(weather_manager, start_time, pop, pcpn,  debug):
    # need this to finagle to avoid NumPy's annoying runtime warnings
    pop_missing = N.where(N.isnan(pop))
    pop[pop_missing] = -999 # finagle for runtime warnings

    if pcpn is None:
        data = N.zeros(pop.shape, dtype=float)
        data.fill(0.01)
        data[N.where(pop < 50)] = 0
        data[pop_missing] = N.nan # undo runtime warning finagle
        updateForecast(weather_manager, 'PCPN', start_time, data, debug)
    else:
        if len(pop.shape) == 3 and pcpn.shape[0] < pop.shape[0]:
            data = N.zeros(pop.shape, dtype=float)
            data.fill(0.01)
            data[0:pcpn.shape[0],:,:] = pcpn
            data[N.where(pop < 50)] = 0
            data[pop_missing] = N.nan # undo runtime warning finagle
            updateForecast(weather_manager, 'PCPN', start_time, data, debug)
        else:
            pcpn[N.where(pop < 50)] = 0
            pcpn[pop_missing] = N.nan # undo runtime warning finagle
            updateForecast(weather_manager, 'PCPN', start_time, pcpn, debug)

    return updateForecast(weather_manager, 'POP', start_time, pop, debug)


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
region_key = options.grid_region
source_key = options.grid_source
verbose = options.verbose or debug

weather_key = 'wetness'

# only allow forecasts based on current date
now = datetime.datetime.now()
year = now.year
month = now.month
last_day_end = tzutils.asUtcTime(datetime.datetime(year, month, lastDayOfMonth(year, month), 23), 'UTC')

# create a factory for disease file access
turf_factory = TurfWeatherFileFactory()
if dev_mode: turf_factory.useDirpathsForMode('dev')
region = turf_factory.regionConfig(region_key)
source = turf_factory.sourceConfig(source_key)

# get a weather_manager for the weather files
weather_manager = turf_factory.weatherFileManager(weather_key, year, month, region, mode='r')
weather_manager.close()

# get a factory for forecast file ndfd_readers
ndfd_factory = NdfdGridFileFactory()
if dev_mode: ndfd_factory.useDirpathsForMode('dev')

# update humidity forecast
start_time, end_time, data = getForecastData(ndfd_factory, weather_manager, 'RHUM', None, debug)
if data is not None:
    updateForecast(weather_manager, 'RHUM', start_time, data, debug)
    # check for overlap with next month
    if end_time == last_day_end:
        next_start = last_day_end + ONE_HOUR
        # make sure file for next month exists before we try to put data into it
        filepath = turf_factory.weatherFilepath(weather_key, next_start.year, next_start.month, region)
        if not os.path.exists(filepath):
            turf_factory.buildWeatherFile(weather_key, next_start.year, next_start.month, region, source, 'UTC')
        next_manager = turf_factory.weatherFileManager(weather_key, next_start.year, next_start.month, region, mode='a')

        start, end, data = getForecastData(ndfd_factory, next_manager, 'RHUM', next_start, debug)
        if data is not None: updateForecast(next_manager, 'RHUM', start, data, debug)

# update precip probability forecast
pop_start, end_time, pop = getForecastData(ndfd_factory, weather_manager, 'POP12.POP', None, debug)
if pop is not None:
    # only update PCPN when there is POP
    start_time, end_time, pcpn = getForecastData(ndfd_factory, weather_manager, 'PCPN', pop_start, debug)

    if start_time != pop_start:
        print 'BAD NEWS : PCPN and POP start at different times :', start_time, pop_start
    else: 
        fcast_start, fcast_end = updatePopPcpn(weather_manager, pop_start, pop, pcpn,  debug)

    # check for overlap with next month
    if fcast_end == last_day_end:
        next_start = last_day_end + ONE_HOUR
        next_manager = turf_factory.weatherFileManager(weather_key, next_start.year, next_start.month, region, mode='a')

        pop_start, end_time, pop = getForecastData(ndfd_factory, next_manager, 'POP12.POP', next_start, debug)
        if pop is not None:
            # only update PCPN when there is POP
            pcpn_start, pcpn_end, pcpn = getForecastData(ndfd_factory, weather_manager, 'PCPN', pop_start, debug)

            if pcpn is not None and pcpn_start != pop_start:
                print 'BAD NEWS : PCPN and POP start at different times :', pcpn_start, pop_start
            else: updatePopPcpn(next_manager, pop_start, pop, pcpn,  debug)


print '\nCompleted forecast data updates in :\n', weather_manager.filepath

