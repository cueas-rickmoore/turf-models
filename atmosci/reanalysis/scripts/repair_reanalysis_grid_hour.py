#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(hours=23)

import numpy as N

from atmosci.utils.tzutils import asUTCTime
from atmosci.units import convertUnits

from atmosci.reanalysis.smart_grib import ReanalysisDownloadFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


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
grib_region = options.grib_region
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
    max_hours = datetime.timedelta(hours=max_hours)

reanalysis = 'rtma'

file_variable = args[0].upper()

now = datetime.datetime.now()
num_date_args = len(args) - 1
if num_date_args == 1:
    repair_time = asUTCTime(datetime.datetime(now.year, now.month, now.day, int(args[1])))
elif num_date_args == 2:
    repair_time = asUTCTime(datetime.datetime(now.year, now.month, int(args[1]), int(args[2])))
elif num_date_args == 3:
    repair_time = asUTCTime(datetime.datetime(now.year, int(args[1]), int(args[2]), int(args[3])))
else: repair_time = asUTCTime(datetime.datetime(int(args[1]), int(args[2]), int(args[3]), int(args[4])))

# create a factory for access to grid files
factory = ReanalysisDownloadFactory(reanalysis, grib_source, grib_server)
if dev_mode: factory.useDirpathsForMode('dev')
factory._initStaticResources_()

manager = factory.gridFileManager(repair_time, file_variable, grid_region, mode='r')
grid_units = manager.datasetAttribute(file_variable, 'units')
manager.close()

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

reasons = [ ]
valid_data = False
prev_data = None
next_data = None

success, info = factory.dataFromGrib(file_variable, repair_time, return_units=True)
if success:
    units, data = info
    if len(N.where(N.isfinite(data))[0]) > 0:
        manager.open('a')
        manager.updateReanalysisData(reanalysis, file_variable, repair_time, data, units=units)
        manager.close()

        grib_filename = factory.gribFilename(repair_time, file_variable, grib_region)
        info = (repair_time.strftime('%Y-%m-%d:%H'), grib_filename)
        print 'Repaired data for %s with data from grib file %s' % info
        # turn annoying numpy warnings back on before exiting
        warnings.resetwarnings()
        exit()
    reasons.append('    grib file for missing hour contains no valid data')
else:
    reasons.append('    no grib file found for missing hour')
    prev_time = repair_time - ONE_HOUR
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
    if len(N.where(N.isfinite(data))[0]) > 0: prev_data = data
    else: reasons.append('    grid file contains missing data for previous hour')

if next_data is None:
    next_time = repair_time - ONE_HOUR
    manager.open('r')
    next_data = manager.dataForHour(file_variable, next_time)
    manager.close()
    if len(N.where(N.isfinite(data))[0]) > 0: next_data = data
    else: reasons.append('    grid fiel contains missing data for next hour')

if prev_data is not None and next_data is not None:
    fudge = (prev_data + next_data) / 2.
    manager.open('a')
    manager.insertFudgedData(file_variable, repair_time, fudge)
    manager.close()
    msg = 'Data for %s @ %s was interpolated using data from previous and next hours'
    print msg % (file_variable, repair_time.strftime('%Y-%m-%d:%H'))

else:
    print 'Unable to repair data for %s @ %s' % (file_variable, repair_time.strftime('%Y-%m-%d:%H'))
    for reason in reasons: print reason

# turn annoying numpy warnings back on
warnings.resetwarnings()

