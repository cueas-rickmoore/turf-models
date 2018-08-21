#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(hours=23)

import numpy as N

from atmosci.units import convertUnits

from atmosci.reanalysis.smart_grib import ReanalysisDownloadFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def repairOneHour(factory, manager, repair_time, variable, grib_region):
    success, info = factory.dataFromGrib(file_variable, repair_time, return_units=True)
    if success:
        units, data = info
        if len(N.where(N.isfinite(data))[0]) > 0:
            manager.open('a')
            manager.updateReanalysisData(reanalysis, file_variable, repair_time, data, units=units)
            manager.close()
            grib_filename = factory.gribFilename(repair_time, file_variable, grib_region)
            info = (repair_time.strftime('%Y-%m-%d:%H'), grib_filename)
            return 'Repaired data for %s with data from grib file %s' % info
        else: reasons.append('    grib file for missing hour contains no valid data')
    else:
        reasons.append('    no grib file found for missing hour')
        prev_time = repair_time - ONE_HOUR
        manager.open('r')
        grid_units = manager.datasetAttribute(file_variable, 'units')
        manager.close()
        success, info = factory.dataFromGrib(file_variable, prev_time, return_units=True)
        if success:
            units, data = info
            if len(N.where(N.isfinite(data))[0]) > 0:
                if units != grid_units: prev_data = convertUnits(data, units, grid_units)
                else: prev_data = data
            else: reasons.append('    grib file for previous hour contains no valid data')
        else: reasons.append('    no grib file found for previous hour')
    
        next_time = repair_time + ONE_HOUR
        success, info = factory.dataFromGrib(file_variable, next_time, return_units=True)
        if success:
            units, data = info
            if len(N.where(N.isfinite(data))[0]) > 0:
                if units != grid_units: next_data = convertUnits(data, units, grid_units)
                else: next_data = data
            else: reasons.append('    grib file for next hour contains no valid data')
        else: reasons.append('    no grib file found for next hour')

    if prev_data is None:
        prev_time = repair_time - ONE_HOUR
        manager.open('r')
        data = manager.dataForHour(file_variable, prev_time)
        manager.close()
        if len(N.where(N.isfinite(data))[0]) > 0: prev_data = data
        else: reasons.append('    grid file contains missing data for previous hour')

    if next_data is None:
        next_time = repair_time - ONE_HOUR
        manager.open('r')
        next_data = manager.dataForHour(file_variable, next_time)
        manager.close()
        if len(N.where(N.isfinite(data))[0]) > 0: next_data = data
        else: reasons.append('    grid file contains missing data for next hour')

    if prev_data is not None and next_data is not None:
        fudge = (prev_data + next_data) / 2.
        manager.open('a')
        manager.insertFudgedData(file_variable, repair_time, fudge)
        manager.close()
        msg = 'Data for %s @ %s was interpolated using data from previous and next hours'
        return msg % (file_variable, repair_time.strftime('%Y-%m-%d:%H'))

    return reasons


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store', dest='analysis', default='rtma')
parser.add_option('-n', action='store', type=int, dest='max_hours', default=None)
parser.add_option('-r', action='store', dest='grid_region',
                        default=CONFIG.sources.reanalysis.grid.region)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-s', action='store_true', dest='grid_source', default='acis')
parser.add_option('-t', action='store_true', dest='use_time_in_path', default=False)
parser.add_option('-u', action='store_false', dest='utc_file', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--fcast_days', action='store', type=int, dest='fcast_days', default=None)
parser.add_option('--grib_region', action='store', dest='grib_region', default='conus')
parser.add_option('--grib_server', action='store', dest='grib_server', default='nomads')
parser.add_option('--grib_source', action='store', dest='grib_source', default='ncep')
parser.add_option('--obs_days', action='store', type=int, dest='obs_days', default=None)
parser.add_option('--target', action='store', type=int, dest='target_hour', default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
fcast_days = options.fcast_days
grib_region = options.grid_region
grib_server = options.grib_server
grib_source = options.grib_source
grid_region = options.grid_region
grid_source = options.grid_source
max_hours = options.max_hours
obs_days = options.obs_days
target_hour = options.target_hour
use_time_in_path = options.use_time_in_path
utc_file = options.utc_file
verbose = options.verbose or debug

if max_hours is not None:
    max_hours = datetime.timedelta(hours=max_hours-1)

reanalysis = 'rtma'

file_variable = args[0].upper()

num_args = len(args)
now = datetime.date.today()
if len(args) == 1: # fix current month
    date_tuple = (now.year, now.month, now.day)
elif num_args == 2: # fix specific month in current year
    date_tuple = (now.year, int(args[1]), 1)
elif num_args == 3: # fix year/month
    date_tuple = (int(args[1]), int(args[2]), 1)
else:
    errmsg = 'No arguments passed to script. You must at least specify'
    raise RuntimeError, '%s the grib variable name.' % errmsg

reference_date = datetime.date(*date_tuple)

# create a factory for access to grid files
factory = ReanalysisDownloadFactory(reanalysis, grib_source, grib_server)
if dev_mode: factory.useDirpathsForMode('dev')
factory._initStaticResources_()
region = factory.regionConfig(grid_region)

grid_start_time, reference_time, grid_end_time, num_hours = factory.fileTimespan(reference_date)
if debug:
    print ' grid file timespan :'
    print '      variable :', file_variable
    print '    start hour :', grid_start_time
    print '      ref hour :', reference_time
    print '      end hour :', grid_end_time
    print '     num hours :', num_hours
    print '     file date :', reference_time.date()

# get reguired information from static file
manager = factory.gridFileManager(reference_date, file_variable, grid_region, mode='r')
time_attrs = manager.timeAttributes(file_variable)
manager.close()
file_end_time = time_attrs['end_time']
file_start_time = time_attrs['start_time']
last_valid_time = time_attrs['last_valid_time']
if max_hours is None:
    data_start_time = time_attrs['start_time']
else: # need to make sure that max_hours does not take is into the previous month
    data_start_time = max(time_attrs['start_time'], last_valid_time - max_hours)

if verbose:
    print 'repair timespan :'
    print '  repairs start :', data_start_time
    print '    repairs end :', last_valid_time

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


# assumes first hour in file is not all N.nan and can be used
manager.open('r')
available_data = manager.timeSlice(file_variable, data_start_time, last_valid_time)
last_hour = available_data.shape[0]
manager.close()

repaired = 0
failed = [ ]

hour = 0
while hour < last_hour:
    data = available_data[hour,:,:]
    if len(N.where(N.isfinite(data))[0]) == 0:
        repair_time = data_start_time + datetime.timedelta(hours=hour)
        result = repairOneHour(factory, manager, repair_time, file_variable, grib_region)
        if isinstance(result, basestring):
            repaired += 1
            print result
        else: failed.append(repair_time, result)
    hour += 1


# turn annoying numpy warnings back on
warnings.resetwarnings()

not_repaired = len(failed)

if repaired + not_repaired == 0:
    info = (file_variable, reanalysis.upper(), reference_date.strftime('%Y-%m-%d'))
    print 'Found no missing hours for %s in %s grid file for %s' % info

else:
    if repaired > 0:
        print '\n%d hours of %s %s data was repaired' % (repaired, reanalysis.upper(), file_variable)

    if not_repaired > 0:
        print '\nFailed to repair %d hours of %s %s data\v' % (not_repaired, reanalysis.upper(), file_variable)
        for repair_time, reasons in failed:
            print 'Unable to repair data for %s :' % repair_time.strftime('%Y-%m-%d:%H')
            for reason in reasons: print reason

