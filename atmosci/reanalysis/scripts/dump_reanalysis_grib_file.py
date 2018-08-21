#! /usr/bin/env python

import os, sys
import warnings

import datetime
BUILD_START_TIME = datetime.datetime.now()
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N
import pygrib

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime

from atmosci.reanalysis.factory import ReanalysisGribFileFactory, \
                                       ReanalysisGridFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store', dest='analysis', default='rtma')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--grib_region', action='store', dest='grib_region',
                                   default='conus')
parser.add_option('--grib_source', action='store', dest='grib_source',
                                   default='ncep')
parser.add_option('--gribtz', action='store', dest='grib_timezone',
                              default='UTC')

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

analysis = options.analysis
debug = options.debug
dev_mode = options.dev_mode
grib_region = options.grib_region
grib_source = options.grib_source
grib_timezone = options.grib_timezone
verbose = options.verbose or debug

analysis_source = '.'.join((analysis,grib_source))

grib_var_name = args[0].upper()
grib_time = (int(args[1]),int(args[2]),int(args[3]),int(args[4]))
grib_time = tzutils.asHourInTimezone(grib_time, 'UTC')
print 'requesting dump of %s grib for %s' % (analysis_source, str(grib_time))

if analysis == 'urma':
    from atmosci.reanalysis.urma.config import URMA_SOURCES
    CONFIG.sources.link(URMA_SOURCES)
elif analysis == 'rtma':
    from atmosci.reanalysis.rtma.config import RTMA_SOURCES
    CONFIG.sources.link(RTMA_SOURCES)
else:
    errmsg = '"%s" is an unsupported reanalysis.'
    raise ValueError, errmsg % analysis

# create a factory for access to grib & static files
grib_factory = ReanalysisGribFileFactory(analysis_source, CONFIG)
if dev_mode: grib_factory.useDirpathsForMode('dev')

reader = grib_factory.gribFileReader(grib_time, grib_var_name,
                          grib_region, file_must_exist=True,
                          shared_grib_dir=True)
print '\ndumping info from :\n    ', reader.filepath
print '\nlong names in this file :\n', reader.grib_names
print '\nshort names in this file :\n', reader.short_names
print '\nmessage :\n', reader.messageFor(grib_var_name.lower())

