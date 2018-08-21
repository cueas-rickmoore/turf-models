#!/usr/bin/env python

import os, sys
import datetime
BUILD_START_TIME = datetime.datetime.now()

from dateutil.relativedelta import relativedelta

import numpy as N

from atmosci.utils.timeutils import elapsedTime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
verbose = options.verbose

source_key = args[0]
region_key = args[1]

if source_key in ('acis','prism'):
    from atmosci.seasonal.factory import AcisProjectFactory
    factory = AcisProjectFactory()
    # we should alwauys be able to get valid data from ACIS grids 10 days ago
    date = BUILD_START_TIME - relativedelta(days=10)
else:
    raise KeyError, 'No factory support for "%s" data source.' % source_key

bbox = factory.config.regions[region_key].data
source = factory.getSourceConfig(source_key)

builder = factory.getStaticFileBuilder(source, region_key)
builder.initFileAttributes()

data = factory.getAcisGridData(source_key, 'mint', date, None, False,
                               meta=('ll','elev'), bbox=bbox, debug=debug)
print builder.filepath

builder.build(True, True, data['lon'], data['lat'], elev_data=data['elev'],
              bbox=bbox)

elapsed_time = elapsedTime(BUILD_START_TIME, True)
print 'completed build of %s static file in' % source.tag, elapsed_time
