#! /usr/bin/env python

import os
import datetime
ONE_HOUR = datetime.timedelta(hours=1)
UPDATE_START_TIME = datetime.datetime.now()

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth, elapsedTime

from atmosci.ndfd.factory import NdfdGridFileFactory
from atmosci.reanalysis.factory import ReanalysisGridFileFactory

from turf.weather.factory import TurfWeatherFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TODAY = datetime.date.today()
THIS_YEAR = TODAY.year
THIS_MONTH = TODAY.month
LAST_DAY_OF_MONTH = datetime.date(THIS_YEAR, THIS_MONTH, lastDayOfMonth(THIS_YEAR, THIS_MONTH))
if THIS_MONTH < 12: 
    NEXT_YEAR = THIS_YEAR
    NEXT_MONTH = THIS_MONTH + 1
else:
    NEXT_YEAR = THIS_YEAR + 1
    NEXT_MONTH = 1


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

options, args = parser.parse_args()

debug = options.debug
dev_mode = options.dev_mode
verbose = options.verbose or debug


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def nextMonth(year, month):
    if month < 12: return year, month+1
    else: year+1, 1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def printSuccessMsg(variable, source, start_time, end_time):
    if start_time == end_time:
        info = (variable, source, start_time.strftime('%m/%d:%H'))
        print '%s %s was updated for %s' % info
    else:
        info = (variable, source, start_time.strftime('%m/%d:%H'),
                                  end_time.strftime('%m/%d:%H'))    
        print '%s %s was updated for %s thru %s' % info

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def timeString(time_obj, with_year=False):
    if with_year: return time_obj.strftime('%Y-%m-%d:%H')
    return time_obj.strftime('%m-%d:%H')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def getForecastData(ndfd_factory, variable, start_time, debug):
    if '.' in variable: grid_var, grib_var = variable.split('.')
    else: grid_var = grib_var = variable

    # get a reader for the forecast file
    reader = ndfd_factory.ndfdGridFileReader(start_time, grib_var, 'NE')
    if debug:
        print 'getForecastData :', start_time
        print reader.filepath
    end_time = reader.timeAttribute(grib_var, 'last_valid_time', None)
    if debug: print 'last_valid_time :', end_time
    reader.close()

    if end_time is None:
        del reader
        if variable != 'PCPN':
            print '\nNO %s FORECAST AVAILABLE FOR %s/%s' % (grib_var, start_time.month, start_time.year)
        return start_time, end_time, None
    else:
        # extract the relevant forecast data
        reader.open()
        data = reader.timeSlice(grib_var, start_time, end_time)
        reader.close()
        del reader
        return start_time, end_time, data

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def getReanalysisData(anal_factory, manager, variable, year, month, debug):
    manager.open('r')
    rtma_end_time = manager.timeAttribute(variable, 'rtma_end_time', None) 
    if rtma_end_time is None:
        data_start_time = manager.timeAttribute(variable, 'fcast_start_time',
                                  manager.timeAttribute(variable, 'start_time'))
    else: data_start_time = rtma_end_time + ONE_HOUR
    manager.close()

    # get a renalysis data reader for the variable
    reader = anal_factory.gridFileReader(data_start_time, variable, 'NE')
    # figure out the end time of reanalysis data for this variable
    data_end_time = reader.timeAttribute(variable, 'last_valid_time')
    if data_end_time > data_start_time:
        # extract the relevant reanalysis data
        data = reader.timeSlice(variable, data_start_time, data_end_time)
    else:
        data = None
        print 'Renalysis data for %s is already up to date' % variable

    # delete the reader
    reader.close()
    del reader

    return data_start_time, data_end_time, data

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateForecast(manager, variable, fcast_start, data, debug):
    # update temperatures in weather file
    manager.open('a')
    manager.updateForecast(variable, fcast_start, data)
    manager.close()

    if len(data.shape) == 3:
        fcast_end = fcast_start + datetime.timedelta(hours=data.shape[0]-1)
    else: fcast_end = fcast_start
    printSuccessMsg(variable, 'forecast', fcast_start, fcast_end)

    if debug:
        print '\nforecast variable', variable
        print ' update_start_time =', fcast_start
        print '   update_end_time =', fcast_end
        manager.open('r')
        print '     rtma_end_time =', manager.timeAttribute(variable,'rtma_end_time')
        print '  fcast_start_time =', manager.timeAttribute(variable,'fcast_start_time')
        print '    fcast_end_time =', manager.timeAttribute(variable,'fcast_end_time')
        print '   last_valid_time =', manager.timeAttribute(variable,'last_valid_time')
        manager.close()

    return fcast_start, fcast_end

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateFcastPcpn(wetness_manager, start_time, pop, pcpn, debug):
    # need this to finagle to avoid NumPy's annoying runtime warnings
    pop_missing = N.where(N.isnan(pop))
    pop[pop_missing] = -999 # finagle for runtime warnings

    if pcpn is None:
        data = N.zeros(pop.shape, dtype=float)
        data.fill(0.01)
        data[N.where(pop < 50)] = 0
        data[pop_missing] = N.nan # undo runtime warning finagle
        fcast_start, fcast_end = updateForecast(wetness_manager, 'PCPN', start_time, data, debug)
        info = (timeString(fcast_start), timeString(fcast_end))
        print 'PCPN forecast was estimated using POP for %s thru %s' % info

    elif pcpn.shape[0] < pop.shape[0]:
        data = N.zeros(pop.shape, dtype=float)
        data.fill(0.01)
        data[0:pcpn.shape[0],:,:] = pcpn
        data[N.where(pop < 50)] = 0
        data[pop_missing] = N.nan # undo runtime warning finagle
        fcast_start, fcast_end = updateForecast(wetness_manager, 'PCPN', start_time, data, debug)
        printSuccessMsg('PCPN', 'forecast', fcast_start, fcast_end)
        since = start_time + datetime.timedelta(hours=pcpn.shape[0])
        print 'PCPN forecast beginning %s was estimated using POP' % timeString(since)

    else:
        pcpn[N.where(pop < 50)] = 0
        pcpn[pop_missing] = N.nan # undo runtime warning finagle
        fcast_start, fcast_end = updateForecast(wetness_manager, 'PCPN', start_time, pcpn, debug)

    return fcast_start, fcast_end

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateReanalysis(manager, variable, start_time, data, debug):
    # update variable data in weather file
    manager.open('a')
    manager.updateReanalysis(variable, start_time, data)
    manager.close()

    if len(data.shape) == 3:
        end_time = start_time + datetime.timedelta(hours=data.shape[0]-1)
    else:
        end_time = start_time
    printSuccessMsg(variable, 'reanalysis', start_time, end_time)

    if debug:
        print '\nreanalysis variable :', variable
        print ' update_start_time =', start_time
        print '   update_end_time =', end_time
        manager.open('r')
        print '     rtma_end_time =', manager.timeAttribute(variable,'rtma_end_time')
        print '   last_valid_time =', manager.timeAttribute(variable,'last_valid_time')
        print '  fcast_start_time =', manager.timeAttribute(variable,'fcast_start_time')
        print '    fcast_end_time =', manager.timeAttribute(variable,'fcast_end_time')
        manager.close()

    return start_time, end_time

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateTempsFileForecast(ndfd_factory, turf_factory, fcast_start_time, debug):
    # get a data manager for the temps weather file components
    year = fcast_start_time.year
    month = fcast_start_time.month
    # make sure the weather file exists
    weather_filepath = turf_factory.weatherFilepath('TMP', year, month)
    if not os.path.exists(weather_filepath):
        turf_factory.buildWeatherFile('TMP', year, month)
    manager = turf_factory.weatherFileManager('TMP', year, month)
    manager.close()

    # update temperature forecast
    start_time, end_time, data = getForecastData(ndfd_factory, 'TMP.TEMP', fcast_start_time, debug)
    if data is None:
        tmp_end_time = fcast_start_time 
    else:
        fcast_start, tmp_end_time = updateForecast(manager, 'TMP', start_time, data, debug)

    # update dew point forecast
    start_time, end_time, data = getForecastData(ndfd_factory, 'DPT', fcast_start_time, debug)
    if data is None:
        dpt_end_time = fcast_start_time 
    else: 
        fcast_start, dpt_end_time = updateForecast(manager, 'DPT', start_time, data, debug)

    manager.close()
    del manager

    return max(tmp_end_time, dpt_end_time)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateTempsFileReanalysis(anal_factory, turf_factory, year, month, debug):
    # get a data manager for the temps weather file components
    # make sure the weather file exists
    weather_filepath = turf_factory.weatherFilepath('TMP', year, month)
    if not os.path.exists(weather_filepath):
        turf_factory.buildWeatherFile('TMP', year, month)
    manager = turf_factory.weatherFileManager('TMP', year, month)
    manager.close()

    # update reanalysis temperature
    start_time, tmp_end_time, data = getReanalysisData(anal_factory, manager, 'TMP', year, month, debug)
    if data is None:
        manager.open('r')
        tmp_end_time = manager.timeAttribute('TMP', 'rtma_end_time',
                               manager.timeAttribute('TMP', 'start_time') - ONE_HOUR)
        manager.close()
    else:
        anal_start, tmp_end_time = updateReanalysis(manager, 'TMP', start_time, data, debug)

    # update reanalysis dew point
    start_time, dpt_end_time, data = getReanalysisData(anal_factory, manager, 'DPT', year, month, debug)
    if data is None:
        manager.open('r')
        dpt_end_time = manager.timeAttribute('DPT', 'rtma_end_time',
                               manager.timeAttribute('DPT', 'start_time') - ONE_HOUR)
        manager.close()
    else:
        anal_start, dpt_end_time = updateReanalysis(manager, 'DPT', start_time, data, debug)

    manager.close()
    del manager

    # return max end time in case TMP or DPT forecast spills over into next month
    return max(tmp_end_time, dpt_end_time)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateWetnessFileForecast(ndfd_factory, turf_factory, fcast_start_time, debug):
    # get a data manager for the temps weather file components
    year = fcast_start_time.year
    month = fcast_start_time.month
    # make sure the weather file exists
    weather_filepath = turf_factory.weatherFilepath('RHUM', year, month)
    if not os.path.exists(weather_filepath):
        turf_factory.buildWeatherFile('RHUM', year, month)
    manager = turf_factory.weatherFileManager('RHUM', year, month)
    manager.close()

    # update humidity forecast
    start_time, end_time, data = getForecastData(ndfd_factory, 'RHUM', fcast_start_time, debug)

    if data is None:
        rhum_end_time = fcast_start_time - ONE_HOUR
    else:
        fcast_start, rhum_end_time = updateForecast(manager, 'RHUM', start_time, data, debug)

    # update precip probability forecast
    pop_start, pop_end_time, pop = getForecastData(ndfd_factory, 'POP', fcast_start_time, debug)
    if data is None:
        pop_end_time = fcast_start_time - ONE_HOUR
    else:
        pop_start, pop_end_time = updateForecast(manager, 'POP', pop_start, pop, debug)

        # only update PCPN when there is POP
        start_time, end_time, pcpn = getForecastData(ndfd_factory, 'PCPN', pop_start, debug)
        fcast_start, pcpn_end_time = updateFcastPcpn(manager, start_time, pop, pcpn, debug)

    manager.close()
    del manager

    # return max end time in case RHUM or POP/PCPN spills over into next month
    return max(rhum_end_time, pop_end_time)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateWetnessFileReanalysis(anal_factory, turf_factory,  year, month, debug):
    # get a data manager for the temps weather file components
    # make sure the weather file exists
    weather_filepath = turf_factory.weatherFilepath('RHUM', year, month)
    if not os.path.exists(weather_filepath):
        turf_factory.buildWeatherFile('RHUM', year, month)
    manager = turf_factory.weatherFileManager('RHUM', year, month)
    manager.close()

    # get reanalysis humidity
    start_time, rhum_end_time, data = getReanalysisData(anal_factory, manager, 'RHUM', year, month, debug)
    # update reanalysis humidity
    if data is None:
        manager.open('r')
        rhum_end_time = manager.timeAttribute('RHUM', 'rtma_end_time',
                               manager.timeAttribute('RHUM', 'start_time') - ONE_HOUR)
        manager.close()
    else:
        anal_time, rhum_end_time = updateReanalysis(manager, 'RHUM', start_time, data, debug)

    # update reanalysis precip
    start_time, pcpn_end_time, data = getReanalysisData(anal_factory, manager, 'PCPN', year, month, debug)
    if data is None:
        manager.open('r')
        pcpn_end_time = manager.timeAttribute('PCPN', 'rtma_end_time',
                               manager.timeAttribute('PCPN', 'start_time') - ONE_HOUR)
        manager.close()
    else:
        update_start, pcpn_end_time = updateReanalysis(manager, 'PCPN', start_time, data, debug)

        # fudge the POP from PCPN values : any PCPN > 0.01 is 100% else 0%
        missing_precip = N.where(N.isnan(data))
        pop = N.zeros(data.shape, dtype=int)
        pop[missing_precip] = -32768
        data[missing_precip] = -32768
        pop[N.where(data >= 0.01)] = 100

        # update reanalysis POP
        update_start, pop_end_time = updateReanalysis(manager, 'POP', start_time, pop, debug)
        info = (timeString(update_start), timeString(pop_end_time))
        print 'PCPN forecast for %s thru %s was estimated using POP' % info

    manager.close()
    del manager

    # return max end time in case RHUM or POP/PCPN spills over into next month
    return max(rhum_end_time, pcpn_end_time)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# create a factory for access to reanalysis files
turf_factory = TurfWeatherFileFactory()
if dev_mode: turf_factory.useDirpathsForMode('dev')

# get a factory for access to forecast files
anal_factory = ReanalysisGridFileFactory()
if dev_mode: anal_factory.useDirpathsForMode('dev')

# get a factory for forecast file ndfd_readers
ndfd_factory = NdfdGridFileFactory()
if dev_mode: ndfd_factory.useDirpathsForMode('dev')

# update waether temps file (temperature and dew point)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# reanalysis files cover a single month
weather_end_time = updateTempsFileReanalysis(anal_factory, turf_factory, THIS_YEAR, THIS_MONTH, debug)
# updateTempsFileReanalysis can only return data thru the last hour of the last day the month
if weather_end_time.date() == LAST_DAY_OF_MONTH and weather_end_time.hour == 23:
    # end of data was also the end of the previous month
    # check for reanalysis data beginning in the next month
    weather_end_time = updateTempsFileReanalysis(anal_factory, turf_factory, NEXT_YEAR, NEXT_MONTH, debug)
print '...'

# forcast must start at least one hour after last hour with reanalysis data
fcast_start_time = weather_end_time + ONE_HOUR
# forecast files cover a single month
fcast_end_time = updateTempsFileForecast(ndfd_factory, turf_factory, fcast_start_time, debug)
# updateTempsFileForecast can only return data thru the last hour of the last day the month

if fcast_end_time.date() == LAST_DAY_OF_MONTH and fcast_end_time.hour == 23:
    # end of forecast was also the end of the previous month
    # check for forecaast data beginning in the next month
    fcast_end_time = updateTempsFileForecast(ndfd_factory, turf_factory, fcast_end_time+ONE_HOUR, debug)
print '...'

# update weather wetness file (hunidity and precip)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# reanalysis files cover a single month
wetness_end_time = updateWetnessFileReanalysis(anal_factory, turf_factory, THIS_YEAR, THIS_MONTH, debug)
if wetness_end_time.date() == LAST_DAY_OF_MONTH and wetness_end_time.hour == 23:
    wetness_end_time = updateWetnessFileReanalysis(anal_factory, turf_factory, NEXT_YEAR, NEXT_MONTH, debug)
print '...'

fcast_start_time = wetness_end_time + ONE_HOUR
fcast_end_time = updateWetnessFileForecast(ndfd_factory, turf_factory, fcast_start_time, debug)
if fcast_end_time.date() == LAST_DAY_OF_MONTH and fcast_end_time.hour == 23:
    fcast_end_time = updateWetnessFileForecast(ndfd_factory, turf_factory, fcast_end_time+ONE_HOUR, debug)

elapsed_time = elapsedTime(UPDATE_START_TIME, True)
print '\nCompleted weather file updates in %s' % elapsed_time

