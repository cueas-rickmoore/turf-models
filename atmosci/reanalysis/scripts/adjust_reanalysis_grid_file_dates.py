#! /usr/bin/env python

import os, sys

import datetime
ONE_HOUR = datetime.timedelta(hours=1)

from atmosci.utils import tzutils

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='conus')
parser.add_option('-s', action='store', dest='source', default='acis')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-t', action='store_true', dest='use_time_in_path',
                        default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-x', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--localtz', action='store', dest='local_timezone',
                               default='US/Eastern')
parser.add_option('--target', action='store', type=int, dest='target_hour',
                              default=7)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

dev_mode = options.dev_mode
local_timezone = options.local_timezone
region_key = options.region
source_key = options.source
target_hour = options.target_hour
use_time_in_path = options.use_time_in_path

test_run = options.test
debug = options.debug or test_run
verbose = options.verbose or debug

num_args = len(args)

if len(args) == 2:
    variable_name = args[0].upper()
    num_hours = int(args[1])
    today = datetime.date.today()
    time_tuple = (today.year, today.month, today.day, target_hour)
elif num_args == 5:
    variable_name = args[0].upper()
    time_tuple = (int(args[1]), int(args[2]), int(args[3]), target_hour)
    num_hours = int(args[4])
else:
    allowed_args = 'You may pass 2 arguments (variable name, number of hours)'
    allowed_args += ' or 5 arguments (variable name, year, month, day, number'
    allowed_args += ' of hours).'
    if num_args == 0:
        errmsg = 'No arguments passed to script. %s' % allowed_args
    else: errmsg = 'Incorrect number of argumets. %s' % allowed_args
    raise RuntimeError, errmsg

reference_time = \
    tzutils.asLocalTime(datetime.datetime(*time_tuple), local_timezone)

# create a factory for access to grid files
grid_factory = \
    ReanalysisGridFileFactory('reanalysis', timezone=local_timezone)
if dev_mode: grid_factory.useDirpathsForMode('dev')
region = grid_factory.regionConfig(region_key)

# get manager for the reference time span
manager = grid_factory.gridFileManager(reference_time, variable_name,
                                       region_key, num_hours=num_hours,
                                       use_time_in_path=use_time_in_path)
time_attrs = manager.timeAttributes(variable_name)
if debug:
    print 'updating file for ...'
    print '     variable :', variable_name
    print '    file date :', reference_time.date()
    print '    ', manager.filepath
manager.close()

valid_time = time_attrs['last_valid_time']
fcast_end = time_attrs.get('fcast_end_time', None)
fcast_start = time_attrs.get('fcast_start_time', None)
rtma_time = time_attrs.get('rtma_end_time', None)
urma_time = time_attrs.get('urma_end_time', None)
if debug:
    print '\nexisting times in file :'
    print '     urma_end_time   :', urma_time
    print '     rtma_end_time   :', rtma_time
    print '     fcast_start_time :', fcast_start
    print '     fcast_end_time   :', fcast_end
    print '     last_valid_time  :', valid_time

attrs_changed = [ ]
attrs_to_delete = [ ]

if urma_time is None:
    urma_time = time_attrs.get('last_urma_time', None)
    if urma_time is None:
        if rtma_time is None: urma_time = valid_time
        else: urma_time = rtma_time - ONE_HOUR
    else:
       attrs_to_delete.append('last_urma_time')
    attrs_changed.append(('urma_end_time', urma_time))

# RTMA cannot overlap URMA
if rtma_time is None:
    rtma_time = time_attrs.get('last_rtma_time', None)
    if rtma_time is not None:
        attrs_to_delete.append('last_rtma_time')
        if rtma_time > urma_time:
            attrs_changed.append(('rtma_end_time', rtma_time))
        else: rtma_time = None
else:
    if rtma_time <= urma_time:
        attrs_to_delete.append('rtma_end_time')
        rtma_time = None

if fcast_start is not None:
    if rtma_time is None:
        # forecast cannot overlap URMA
        if fcast_start <= urma_time:
            if fcast_end <= urma_time:
                # forecast has been completely replaced by URMA
                attrs_to_delete.append('fcast_start_time')
                attrs_to_delete.append('fcast_end_time')
                fcast_start = fcast_end = None
            else: # part of forecast has been replaced by URMA
                fcast_start = urma_time + ONE_HOUR
                attrs_changed.append(('fcast_start_time', fcast_start))
    else:
        # forecast cannot overlap RTMA
        if fcast_start <= rtma_time:
            if fcast_end <= rtma_time:
                # forecast has been completely replaced by RTMA
                attrs_to_delete.append('fcast_start_time')
                attrs_to_delete.append('fcast_end_time')
                fcast_start = fcast_end = None
            else: # part of forecast has been replaced by RTMA
                fcast_start = rtma_time + ONE_HOUR
                attrs_changed.append(('fcast_start_time', fcast_start))

if test_run:
    print '\nattrs to be changed :\n', attrs_changed
    print '\nattrs to be deleted :\n', attrs_to_delete
    exit()

if attrs_changed:
    print '\n'
    for attr_name, attr_value in attrs_changed:
        print 'updating "%s" : %s' % (attr_name, str(attr_value))
        manager.open('a')
        manager.setTimeAttribute(variable_name, attr_name, attr_value)
        if manager.datasetExists('provenance'):
            manager.setTimeAttribute('provenance', attr_name, attr_value)
        manager.close()
else: print '\nNo time atrributes were changed.'

if attrs_to_delete:
    print '\n'
    for attr_name in attrs_to_delete:
        print 'deleting "%s"' % attr_name
        manager.open('a')
        manager.deleteDatasetAttribute(variable_name, attr_name)
        if manager.datasetExists('provenance'):
            manager.deleteDatasetAttribute('provenance', attr_name)
        manager.close()
else: print '\nNo time atrributes were deleted.'

