#! /usr/bin/env python

import os, sys
import datetime

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store', dest='analysis',
                        default=CONFIG.project.analysis)
parser.add_option('-r', action='store', dest='grid_region',
                        default=CONFIG.sources.reanalysis.grid.region)
parser.add_option('-s', action='store', dest='grid_source',
                        default=CONFIG.sources.reanalysis.grid.source)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-n', action='store_true', dest='next_month', default=False)
parser.add_option('-t', action='store_true', dest='use_time_in_path',
                        default=False)
parser.add_option('-u', action='store_false', dest='utc_file', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--grib_region', action='store', dest='grib_region',
                        default=CONFIG.sources.reanalysis.grib.region)
parser.add_option('--grib_source', action='store', dest='grib_source',
                        default=CONFIG.sources.reanalysis.grib.source)
parser.add_option('--gribtz', action='store', dest='grib_timezone',
                        default=CONFIG.sources.reanalysis.grib.timezone)
parser.add_option('--localtz', action='store', dest='local_timezone',
                        default=CONFIG.project.local_timezone)
parser.add_option('--target', action='store', type=int, dest='target_hour',
                        default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

analysis = options.analysis
debug = options.debug
dev_mode = options.dev_mode
grib_region = options.grib_region
grib_source = options.grib_source
grib_timezone = options.grib_timezone
grid_region = options.grid_region
grid_source = options.grid_source
local_timezone = options.local_timezone
next_month = options.next_month
target_hour = options.target_hour
today = datetime.date.today()
use_time_in_path = options.use_time_in_path
utc_file = options.utc_file
verbose = options.verbose or debug

if utc_file: file_timezone = 'UTC'
else: file_timezone = local_timezone

grib_var_name = args[0].upper()

num_date_args = len(args) - 1
if num_date_args == 0:
    if next_month:
        reference_date = datetime.date(today.year, today.month+1, 1)
    else: reference_date = datetime.date(today.year, today.month, 1)
elif num_date_args == 1:
    reference_date =  datetime.date(today.year, int(args[1]), 1)
elif num_date_args > 1:
    reference_date =  datetime.date(int(args[1]), int(args[2]), 1)
else:
    errmsg = 'No arguments passed to script. You must at least specify'
    raise RuntimeError, '%s the grib variable name.' % errmsg

if verbose:
    print 'requesting ...'
    print '    variable :', grib_var_name
    print '    ref date :', reference_date
    print '    timezone :', file_timezone

# create a factory for access to grid files
factory = ReanalysisGridFileFactory(timezone=file_timezone)
if dev_mode: factory.useDirpathsForMode('dev')

# look for overrides of the default timespan parameters
kwargs = { 'timezone':file_timezone, }
if target_hour is not None: kwargs['target_hour'] = target_hour

timespan = factory.fileTimespan(reference_date, **kwargs)
if verbose:
    grid_start_time, reference_time, grid_end_time, num_hours = timespan
    print ' grid file timespan in %s timeszone :' % file_timezone
    print '    start hour :', grid_start_time
    print '      ref hour :', reference_time
    print '      end hour :', grid_end_time
    print '     num hours :', num_hours
    print '     file date :', reference_time.date()
else:
    reference_time = timespan[1]
del kwargs['timezone']

# build grid file
print '\nBuilding "%s" grid file for %s' % (grib_var_name, reference_time.strftime('%B, %Y'))
manager = factory.buildReanalysisGridFile(reference_time, grib_var_name, grid_region, 
                                          file_timezone, grid_source)

if debug:
    manager.open('r')
    time_attrs = manager.timeAttributes(grib_var_name)
    manager.close()
    print '\ngrid file time attrs :\n', time_attrs

print '\nCompleted build for "%s" grid file.' % grib_var_name

