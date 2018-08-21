#! /usr/bin/env python

import datetime
ONE_HOUR = datetime.timedelta(hours=1)

from atmosi.utils.tzutils import asUTCTime

from atmosci.reanalysis.factory import ReanalysisGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store', dest='analysis', default='rtma')
parser.add_option('-r', action='store', dest='grid_region',
                        default=CONFIG.sources.reanalysis.grid.region)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-s', action='store_true', dest='grid_source', default='acis')
parser.add_option('-u', action='store_false', dest='utc_file', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

analysis = options.analysis
debug = options.debug
dev_mode = options.dev_mode
grid_region = options.grid_region
utc_file = options.utc_file
verbose = options.verbose or debug

variable = args[0].upper()

num_time_args = len(args) - 1
now = datetime.date.today()
if num_time_args == 0: 
    errmsg = 'No time arguments passed to script. You must at least specify'
    raise RuntimeError, '%s an hour on the current day.' % errmsg
elif num_time_args == 1: 
    new_obs_time = datetime.datetime(now.year, now.month, now.day, int(args[1])
elif num_time_args == 2: 
    new_obs_time = datetime.datetime(now.year, now.month, int(args[1]), int(args[1]))
elif num_time_args == 3:
    new_obs_time = datetime.datetime(now.year, int(args[1]), int(args[2]), int(args[3]))
else:
    errmsg = 'Too many time arguments (%d) passed to script. Up to 3 are supported.'
    raise RuntimeError, errmsg % num_time_args

# create a factory for access to grid files
factory = ReanalysisGridFileFactory(analysis, grib_source, grib_server)
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(grid_region)

manager = factory.gridFileManager(new_obs_time, variable, grid_region, mode='r')
print '\nBefore repairs to %s variable:' % variable
print '    last_obs_time :', manager.dateAttribute(variable, 'last_obs_time', None)
print '    rtma_end_time :', manager.dateAttribute(variable, 'rtma_end_time')
print '  last_valid_time :', manager.dateAttribute(variable, 'last_valid_time', None)
manager.close()

manager.open(mode='a')
manager.setTimeAttribute(variable, 'last_obs_time', new_obs_time)    
manager.setTimeAttribute(variable, 'rtma_end_time', new_obs_time)
manager.setTimeAttribute(variable, 'last_valid_time', new_obs_time)
manager.close()

print '\nAfter repairs to %s variable:' % variable
manager.open(mode='r')
print '    last_obs_time :', manager.timeAttribute(variable, 'last_obs_time')
print '    rtma_end_time :', manager.timeAttribute(variable, 'rtma_end_time')
print '  last_valid_time :', manager.timeAttribute(variable, 'last_valid_time')

print '\nBefore repairs to %s variable:' % 'provenance'
print '    last_obs_time :', manager.timeAttribute('provenance', 'last_obs_time', None)
print '    rtma_end_time :', manager.timeAttribute('provenance', 'rtma_end_time')
print '  last_valid_time :', manager.timeAttribute('provenance', 'last_valid_time', None)
manager.close()

manager.open(mode='a')
manager.setTimeAttribute('provenance', 'last_obs_time', new_obs_time)    
manager.setTimeAttribute('provenance', 'rtma_end_time', new_obs_time)
manager.setTimeAttribute('provenance', 'last_valid_time', new_obs_time)
manager.close()

print '\nAfter repairs to %s variable:' % 'provenance'
manager.open(mode='r')
print '    last_obs_time :', manager.timeAttribute('provenance', 'last_obs_time')
print '    rtma_end_time :', manager.timeAttribute('provenance', 'rtma_end_time')
print '  last_valid_time :', manager.timeAttribute('provenance', 'last_valid_time')
manager.close()

