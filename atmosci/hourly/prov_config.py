# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PROVENANCE = ConfigObject('provenance', None, 'generators', 'types', 'views')

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record generators
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def timeAccumStatsProvenanceGenerator(source, hour, timestamp, hourly,
                                      accumulated):
    return (tzutils.hourAsString(hour),
            N.nanmin(hourly), N.nanmax(hourly),
            N.nanmean(hourly), N.nanmedian(hourly,axis=None),
            N.nanmin(accumulated), N.nanmax(accumulated),
            N.nanmean(accumulated), N.nanmedian(accumulated,axis=None),
            timestamp, source)
PROVENANCE.generators.timeaccum = timeAccumStatsProvenanceGenerator

def timeStampProvenanceGenerator(source, hour, timestamp, data):
    return (tzutils.hourAsString(hour), timestamp, source)
PROVENANCE.generators.timestamp = timeStampProvenanceGenerator

def timeStatsProvenanceGenerator(source, hour, timestamp, data):
    return (tzutils.hourAsString(hour),
            N.nanmin(data), N.nanmax(data),
            N.nanmean(data), N.nanmedian(data,axis=None),
            timestamp, source)
PROVENANCE.generators.timestats = timeStatsProvenanceGenerator

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance type defintions
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# statistics for time series accumulation 
PROVENANCE.types.timeaccum = {
    'empty':('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,'',''),
    'formats':['|S14','f4','f4','f4','f4','f4','f4','f4','f4','|S20','|S12' ],
    'names':['time','min','max','mean','median', 'min accum','max accum',
             'mean accum','median accum','processed','source'],
    'period':'hour',
    'scope':'time',
    'type':'timeaccum'
}

# simple source time stamp
PROVENANCE.types.timestamp = {
    'empty':('','',''),
    'formats':['|S10','|S20','|S12'],
    'names':['time','processed','source'],
    'period':'hour',
    'scope':'time',
    'type':'timestamp'
}

# simple time series statistics
PROVENANCE.types.timestats = {
    'empty':('',N.nan,N.nan,N.nan,N.nan,'',''),
    'formats':['|S14','f4','f4','f4','f4','|S20','|S12'],
    'names':['time','min','max','mean','median','processed','source'],
    'period':'hour',
    'scope':'time',
    'type':'timestats'
}

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance view defintions
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PROVENANCE.views = { 'hour':('hour','time'), 'time':('time','hour') }

