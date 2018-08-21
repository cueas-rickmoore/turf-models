
import os, sys

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# take advantage of the default seasonal project configuration
# this helps keep common things consistent between projects
from atmosci.hourly.config import CONFIG as CFGBASE
CONFIG = CFGBASE.copy('config', None)
del CFGBASE

from turf.config import CONFIG as CFGBASE
CONFIG.dirpaths.merge(CFGBASE.dirpaths)
CONFIG.modes.merge(CFGBASE.modes)
CONFIG.project.merge(CFGBASE.project)
del CFGBASE

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# add weather related project attributes
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.project.min_pop = 50
CONFIG.project.pcpn = { 'fudge': 0.01, 'min': 0.01, 'replace': 0 }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# add weather datasets
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CONFIG.datasets.timegrid.copy('DPT', CONFIG.datasets)
CONFIG.datasets.DPT.description = 'Renalysis & forecast dewpoint temperature @ 2 meters'
CONFIG.datasets.DPT.frequency = 1
CONFIG.datasets.DPT.source = 'RTMA & NDFD model data resampled to ACIS HiRes grid'
CONFIG.datasets.DPT.timezone = 'UTC'
CONFIG.datasets.DPT.units = 'K'

CONFIG.datasets.timegrid.copy('PCPN', CONFIG.datasets)
CONFIG.datasets.PCPN.description = 'Renalysis & forecast precipitation @ surface'
CONFIG.datasets.PCPN.frequency = 1
CONFIG.datasets.PCPN.source = 'RTMA & NDFD model data resampled to ACIS HiRes grid'
CONFIG.datasets.PCPN.timezone = 'UTC'
CONFIG.datasets.PCPN.units = 'in'

CONFIG.datasets.timegrid.copy('POP', CONFIG.datasets)
CONFIG.datasets.POP.description = 'Forecast probability of precipitation'
CONFIG.datasets.POP.dtype = '<i2'
CONFIG.datasets.POP.dtype_packed = '<i2'
CONFIG.datasets.POP.frequency = 1
CONFIG.datasets.POP.missing = 32768
CONFIG.datasets.POP.missing_packed = 32768
CONFIG.datasets.POP.note = 'when source is reanaysis, probability is always 100%'
CONFIG.datasets.POP.source = 'RTMA & NDFD model data resampled to ACIS HiRes grid'
CONFIG.datasets.POP.timezone = 'UTC'
CONFIG.datasets.POP.units = '%'

CONFIG.datasets.timegrid.copy('RHUM', CONFIG.datasets)
CONFIG.datasets.RHUM.description = 'Renalysis & forecast precipitation (surface)'
CONFIG.datasets.RHUM.frequency = 1
CONFIG.datasets.RHUM.source = 'RTMA & NDFD model data resampled to ACIS HiRes grid'
CONFIG.datasets.RHUM.timezone = 'UTC'
CONFIG.datasets.RHUM.units = '%'

CONFIG.datasets.timegrid.copy('TMP', CONFIG.datasets)
CONFIG.datasets.TMP.description = 'Renalysis & forecast temperature @ 2 meters'
CONFIG.datasets.TMP.frequency = 1
CONFIG.datasets.TMP.source = 'RTMA & NDFD model data resampled to ACIS HiRes grid'
CONFIG.datasets.TMP.timezone = 'UTC'
CONFIG.datasets.TMP.units = 'K'

CONFIG.dsname_map = { 'ndfd':{'TMP':'TEMP'}, }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# weather files and directories
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CONFIG.filenames.temps = '%(target_month)s-Hourly-Temperature-Variables.h5'
CONFIG.filenames.wetness = '%(target_month)s-Hourly-Wetness-Variables.h5'

CONFIG.filetypes.temps = {
    'scope':'month', 'period':'time', 
    'datasets':('lat','lon','DPT','TMP'),
    'description':'Reanalysis & forecast temperatures',
}

CONFIG.filetypes.wetness = {
    'scope':'month', 'period':'time', 
    'datasets':('lat','lon','PCPN','POP','RHUM'),
    'description':'Reanalysis & forecast wetness variables',
}

CONFIG.subdir_paths.weather = ('%(region)s','%(year)d','grids','%(weather)s')
