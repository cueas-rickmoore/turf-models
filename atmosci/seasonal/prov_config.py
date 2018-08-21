
import copy

import numpy as N

from atmosci.utils.config import ConfigObject
PROVENANCE = ConfigObject('provenance', None, 'generators', 'types', 'views')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record generators
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# record generator for date series - data with accumulation
def dateAccumStatsProvenanceGenerator(date, timestamp, daily, accumulated):
    return ( asAcisQueryDate(date), N.nanmin(daily), N.nanmax(daily),
             N.nanmean(daily), nanmedian(daily,axis=None),
             N.nanmin(accumulated), N.nanmax(accumulated),
             N.nanmean(accumulated), nanmedian(accumulated,axis=None),
             timestamp )
PROVENANCE.generators.dateaccum = dateAccumStatsProvenanceGenerator

# record generator for day of year series - data with accumulation
def doyAccumStatsProvenanceGenerator(doy, timestamp, daily, accumulated):
    return ( doy, N.nanmin(daily), N.nanmax(daily), N.nanmean(daily),
             nanmedian(daily,axis=None), N.nanmin(accumulated),
             N.nanmax(accumulated), N.nanmean(accumulated),
             nanmedian(accumulated,axis=None), timestamp ) 
PROVENANCE.generators.doyaccum = doyAccumStatsProvenanceGenerator

# record generator for date series statistics - no accumulation
def dateStatsProvenanceGenerator(date, timestamp, data):
    return ( asAcisQueryDate(date), N.nanmin(data), N.nanmax(data),
             N.nanmean(data), nanmedian(data,axis=None), timestamp )
PROVENANCE.generators.datestats = dateStatsProvenanceGenerator

# record generator for day of year series statistics - no accumulation
def doyStatsProvenanceGenerator(doy, timestamp, data):
    return ( doy, N.nanmin(data), N.nanmax(data), N.nanmean(data), 
             nanmedian(data,axis=None), timestamp )
PROVENANCE.generators.doystats = doyStatsProvenanceGenerator

# record generator for observed date series
def observedProvenanceGenerator(date, timestamp, data):
    return ( asAcisQueryDate(date), N.nanmin(data), N.nanmax(data), 
             N.nanmean(data), nanmedian(data,axis=None), timestamp )
PROVENANCE.generators.observed = observedProvenanceGenerator

# record generator for min/max temperature estremes group
def tempExtremesProvenanceGenerator(date, timestamp, mint, maxt, source):
    return ( asAcisQueryDate(date),
             N.nanmin(mint), N.nanmax(mint), N.nanmean(mint),
             N.nanmin(maxt), N.nanmax(maxt), N.nanmean(maxt),
             source, timestamp )
PROVENANCE.generators.tempexts = tempExtremesProvenanceGenerator

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record type definitions for date-based datasets
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# statistics for time series data with accumulation
accum = { 'empty':('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,''),
          'formats':['|S10','f4','f4','f4','f4','f4','f4','f4','f4','|S20'],
          'names':['time','min','max','mean','median', 'min accum','max accum',
                   'mean accum','median accum','processed'],
          'type':'cumstats' }
# date series - data with accumulation
PROVENANCE.types.dateaccum = copy.deepcopy(accum)
PROVENANCE.types.dateaccum.names[0] = 'date'
PROVENANCE.types.dateaccum.period = 'date'
# day of year series - data with accumulation
PROVENANCE.types.doyaccum = copy.deepcopy(accum)
PROVENANCE.types.doyaccum.formats[0] = '<i2'
PROVENANCE.types.doyaccum.names[0] = 'doy'
PROVENANCE.types.doyaccum.period = 'doy'

# provenance for time series statistics only
stats = { 'empty':('',N.nan,N.nan,N.nan,N.nan,''),
          'formats':['|S10','f4','f4','f4','f4','|S20'],
          'names':['time','min','max','mean','median','processed'],
          'type':'stats' }
# date series stats
PROVENANCE.types.datestats = copy.deepcopy(stats)
PROVENANCE.types.datestats.names[0] = 'date'
PROVENANCE.types.datestats.period = 'date'
# day of year series stats
PROVENANCE.types.doystats = copy.deepcopy(stats) 
PROVENANCE.types.doystats.formats[0] = '<i2'
PROVENANCE.types.doystats.names[0] = 'doy'
PROVENANCE.types.doystats.period = 'doy'

# time series observations
observed = { 'empty':('',N.nan,N.nan,N.nan,N.nan,''),
             'formats':['|S10','f4','f4','f4','f4','|S20'],
             'names':['time','min','max','avg','median','dowmload'],
             'type':'stats' }
PROVENANCE.types.observed = copy.deepcopy(observed)
PROVENANCE.types.observed.names[0] = 'date'
PROVENANCE.types.observed.period = 'date'

# temperature extremes group provenance
PROVENANCE.types.tempexts = \
        { 'empty':('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,'',''),
          'formats':['|S10','f4','f4','f4','f4','f4','f4','|S20','|S20'],
          'names':['date','min mint','max mint','avg mint','min maxt',
                   'max maxt','avg maxt','source','processed'],
          'period':'date', 'scope':'year', 'type':'tempexts' }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance time series views
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PROVENANCE.views.date = ('date','obs_date')
PROVENANCE.views.doy = ('day','doy')

