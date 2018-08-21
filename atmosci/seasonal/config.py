
import os, sys
from collections import OrderedDict
import copy

import numpy as N
from scipy import stats as scipy_stats

from atmosci.utils.config import ConfigObject, OrderedConfigObject
from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# ACIS grids built by NRCC all have the same attributes
from atmosci.acis.gridinfo import ACIS_GRID_DIMENSIONS, ACIS_NODE_SPACING, \
                                  ACIS_SEARCH_RADIUS, PRISM_GRID_DIMENSIONS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# specialize the ConfigObject slightly
class SeasonalConfig(ConfigObject):

    def getFiletype(self, filetype_key):
        if '.' in filetype_key:
           filetype, other_key = filetype_key.split('.')
           return self[filetype][other_key]
        else: return self.filetypes[filetype_key]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CFGBASE = SeasonalConfig('seasonal_config', None)
COMMON = SeasonalConfig('seasonal_config', None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# basic atmosci package configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from atmosci.config import ATMOSCFG
# import any default directory paths
ATMOSCFG.dirpaths.copy('dirpaths', COMMON)
CFGBASE.link(COMMON.dirpaths)
# inport regional coordinate bounding boxes
ATMOSCFG.regions.copy('regions', COMMON)
CFGBASE.link(COMMON.regions)
# import mode-dependent defaults
ATMOSCFG.modes.copy('modes', COMMON)
CFGBASE.link(COMMON.modes)
del ATMOSCFG

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance dataset configurations
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
from atmosci.seasonal.prov_config import PROVENANCE
CFGBASE.link(PROVENANCE)
COMMON.link(PROVENANCE)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# default project configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('project', COMMON)
COMMON.project.bbox = { 'NE':COMMON.regions.NE.data,
                        'conus':COMMON.regions.conus.data }
COMMON.project.compression = 'gzip'
COMMON.project.dst_glitch = (3,10)
COMMON.project.forecast = 'ndfd'
COMMON.project.region = 'conus'
COMMON.project.source = 'acis'
COMMON.project.shared_forecast = True
COMMON.project.shared_source = True
COMMON.project.subproject_by_region = True

COMMON.project.copy('project', CFGBASE)
CFGBASE.project.end_day = (12,31)
CFGBASE.project.root = 'shared'
CFGBASE.project.start_day = (1,1)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dataset parameter definitions
#
#    description = brief description of data contained in dataset (string)
#
#    dtype = type for raw data when added to file
#            also used as type for extracted data
#    dtype_packed = type used when data is store in the file
#
#    missing_data = missing value in raw data when added to file
#                   also used as missing value for extracted data
#    missing_packed = value used for missing when stored in the file
#
#    units = units for values in raw data
#    packed_units = units for values in stored data
#                   if not specified, input units are used
#               
#    period = period of time covered by a single entry in the dataset
#             date = one calendar day per entry
#             doy = one day of an ideal year (0-365 or 0-366)
#                   used to map historical summary data to specific dates
#             time = one or more hours, minutes, seconds per entry
#             year = one calendar year per entry
#
#    scope = time covered by entire dataset
#            year = a single year
#            season = dataset spans parts of two or more years
#            por = dataset spans multiple years
#            hours = fixed number of hours
#
#    view = layout of the dataset
#           lat = latitude dimension
#           lon = longitude dimension
#           time dimensions :
#               date = dimension is span of dates 
#               doy = dimension is span of normalized days
#               year = dimension is years 
#               or time dimension in days, hours, minutes or seconds
#        example : 'view':('days','lat','lon')
#
#    interval = number of time units between items in the time dimension
#               Not required, 1 is assumed if not set.
#               e.g. period=hours, interval=3 : consecutive array elements
#                    are 3 hours apart, so consecutive array elements
#                    might exist for 2015-05-01:00, 2015-05-01:03,
#                    2015-05-01:06, etc.
#
#    time span parameters :
#        for date dimension :
#            start_day = first day in dataset ... as int tuple (MM,DD)
#            end_day = last day in dataset ... as int tuple (MM,DD)
#        for doy dimension :
#            start_doy = first doy in dataset ... as int tuple (MM,DD)
#            end_doy = last doy in dataset ... as int tuple (MM,DD)
#        for year dimension :
#            start_year = first year in dataset ... as int
#            end_year = last year in dataset ... as int
#        for time dimension :
#            start_time = first time in dataset ... as string
#            end_time = last time in dataset ... as string
#            e.g. for "hours" use 'YYYY-MM-DD:HH'
#                 for "minutes" use 'YYYY-MM-DD:HH:MM'
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dataset view mappings
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
COMMON.view_map = { ('time','lat','lon'):'tyx', ('lat','lon','time'):'yxt',
                    ('time','lon','lat'):'txy', ('lon','lat','time'):'xyt',
                    ('lat','lon'):'yx', ('lon','lat'):'xy',
                    ('time','lat',):'ty', ('lat','time'):'yt',
                    ('time','lon',):'tx', ('lon','time'):'xt',
                    ('time',):'t',
                  }
COMMON.view_map.copy('view_map', CFGBASE)
CFGBASE.view_map.update( {
     ('date','lat','lon'):'tyx', ('lat','lon','date'):'yxt',
     ('date','lon','lat'):'txy', ('lon','lat','date'):'xyt',
     ('doy','lat','lon'):'yxt', ('lat','lon','doy'):'yxt',
     ('doy','lon','lat'):'txy', ('lon','lat','doy'):'xyt',
} )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dataset configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('datasets', CFGBASE)
ConfigObject('datasets', COMMON)

# generic 2D datasets
COMMON.datasets.float2d = { 'dtype':float, 'dtype_packed':float,
                            'missing_packed':N.nan, 'missing_data':N.nan,
                            'view':('lat','lon') }
CFGBASE.datasets.link(COMMON.datasets.float2d)

COMMON.datasets.float2dPacked = { 'dtype':float, 'dtype_packed':'<i2',
                                  'missing_data':N.nan,
                                  'missing_packed':-32768,
                                  'view':('lat','lon') }
CFGBASE.datasets.link(COMMON.datasets.float2dPacked)

# generic time series datasets
COMMON.datasets.float3dPacked = { 'dtype':float, 'dtype_packed':'<i2',
                                  'missing_data':N.nan,
                                  'missing_packed':-32768,
                                  'scope':'season',
                                  'view':('time','lat','lon'),
                                  'start_day':(1,1), 'end_day':(12,31) }
CFGBASE.datasets.link(COMMON.datasets.float3dPacked)
 
CFGBASE.datasets.dateaccum = { 'base':'float3dPacked',
                               'description':'Accumlation',
                               'period':'date',
                               'provenance':'dateaccum' }

CFGBASE.datasets.doyaccum = { 'base':'float3dPacked',
                              'description':'Accumlation',
                              'period':'doy',
                              'provenance':'doyaccum' }

CFGBASE.datasets.dategrid = { 'base':'float3dPacked',
                              'description':'Raw Data',
                              'period':'date',
                              'provenance':'datestats', 
                              'chunk_type':('date','gzip') }

CFGBASE.datasets.doygrid = { 'base':'float3dPacked',
                             'description':'Raw Data',
                             'period':'doy',
                             'provenance':'doystats',
                             'chunk_type':('doy','gzip') }

# temperature datasets
CFGBASE.datasets.maxt = { 'base':'dategrid',
                          'description':'Daily maximum temperature',
                          'scope':'year', 'units':'F' }

CFGBASE.datasets.maxt = { 'base':'dategrid',
                          'description':'Daily minimum temperature',
                          'scope':'year', 'units':'F' }

# location datasets
COMMON.datasets.elev = { 'base':'float2dPacked', 'description':'Elevation',
                          'units':'meters' }
CFGBASE.datasets.link(COMMON.datasets.elev)

COMMON.datasets.lat = { 'base':'float2d', 'description':'Latitude',
                         'units':'degrees' }
CFGBASE.datasets.link(COMMON.datasets.lat)

COMMON.datasets.lon = { 'base':'float2d', 'description':'Longitude',
                         'units':'degrees' }
CFGBASE.datasets.link(COMMON.datasets.lon)

# mask datasets
COMMON.datasets.land_mask = { 'dtype':bool, 'dtype_packed':bool,
                 'view':('lat','lon'),
                 'description':'Land Mask (Land=True, Water=False)' }
CFGBASE.datasets.link(COMMON.datasets.land_mask)

COMMON.datasets.interp_mask = { 'dtype':bool, 'dtype_packed':bool,
                 'view':('lat','lon'),
                 'description':'Interpolation Mask (Use=True)' }
CFGBASE.datasets.link(COMMON.datasets.interp_mask)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# filename templates
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('filenames', COMMON)
COMMON.filenames.static = '%(type)s_%(region)s_static.h5'

ConfigObject('filenames', CFGBASE)
CFGBASE.filenames.project = '%(year)d-%(project)s-%(source)s-%(region)s.h5'
CFGBASE.filenames.source = '%(year)d-%(source)s-%(region)s-Daily.h5'
CFGBASE.filenames.static = '%(type)s_%(region)s_static.h5'
CFGBASE.filenames.temps = '%(year)d-%(source)s-%(region)s-Daily.h5'
CFGBASE.filenames.variety = '%(year)d-%(project)-%(source)s-%(variety)s.h5'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# filetypes
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('filetypes', CFGBASE)
ConfigObject('filetypes', COMMON)

CFGBASE.filetypes.source = { 'scope':'year',
                  'groups':('tempexts',), 'datasets':('lon','lat'), 
                  'description':'Data downloaded from %(source)s' }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data group configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('groups', CFGBASE)
ConfigObject('groups', COMMON)

# groups of observed data
CFGBASE.groups.tempexts = { 'path':'temps', 'description':'Daily temperatures',
                            'datasets':('maxt','mint','provenance:tempexts') }
CFGBASE.groups.maxt = { 'description':'Maximum daily temperature',
                        'datasets':('daily:maxt','provenance:observed') }
CFGBASE.groups.mint = { 'description':'Minimum daily temperature',
                        'datasets':('daily:mint','provenance:observed') }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data sources
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('sources', CFGBASE)
ConfigObject('sources', COMMON)

COMMON.sources.acis = { 'acis_grid':3,
                'bbox':{'NE':'-82.75,37.125,-66.83,47.70',
                        'conus':'-125.00001,23.99999,-66.04165,49.95834'},
                'days_behind':0,
                'description':'ACIS HiRes grid 3',
                'earliest_available_time':(10,30,0),
                'filepath':'acis5k',
                'grid_dimensions':ACIS_GRID_DIMENSIONS,
                'node_spacing':ACIS_NODE_SPACING,
                'search_radius':ACIS_SEARCH_RADIUS,
                'subdir':'acis_hires',
                'tag':'ACIS-HiRes' }
CFGBASE.sources.link(COMMON.sources.acis)

COMMON.sources.ndfd = { 'days_behind':0,
                'cache_server':'http://ndfd.eas.cornell.edu/',
                'bbox':{'conus':'-125.25,23.749,-65.791,50.208',
                        'NE':'-83.125,36.75,-66.455,48.075'},
                'bbox_offset':{'lat':0.375,'lon':0.375},
                'description':'National Digital Forecast Database',
                'download_template':'%(timespan)s-%(variable)s.grib',
                'grid_dimensions':{'conus':{'lat':1377,'lon':2145},
                                   'NE':{'lat':598,'lon':635}},
                'indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                           'NE':{'x':(1468,2104),'y':(641,1240)}},
                'lat_spacing':(0.0198,0.0228),
                'lon_spacing':(0.0238,0.0330),
                'node_spacing':0.0248, 'resolution':'~2.5km',
                'search_radius':0.0413,
                'tag':'NDFD' }
CFGBASE.sources.link(COMMON.sources.ndfd)

COMMON.sources.prism = { 'acis_grid':21,
                'bbox':{'NE':'-82.75,37.125,-66.7916,47.708',
                        'conus':'-125.00001,23.99999,-66.04165,49.95834'},
                'days_behind':1,
                'description':'PRISM Climate Data (ACIS grid 21)',
                'earliest_available_time':(10,30,0),
                'filepath':'prism5k',
                'grid_dimensions':PRISM_GRID_DIMENSIONS,
                'node_spacing':ACIS_NODE_SPACING,
                'search_radius':ACIS_SEARCH_RADIUS,
                'tag':'PRISM' }
CFGBASE.sources.link(COMMON.sources.prism)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# static grid file configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('static', CFGBASE)
ConfigObject('static', COMMON)

COMMON.static.acis = { 'type':'acis5k', 'tag':'ACIS',
              'description':'Static datasets for ACIS HiRes',
              'datasets':('lat', 'lon', 'elev'),
              'masks':('land_mask:cus_mask', 'interp_mask:cus_interp_mask'),
              'masksource':'dem5k_conus_static.h5', 'filetype':'static',
              'template':'acis5k_%(region)s_static.h5',
              }
CFGBASE.static.link(COMMON.static.acis)

COMMON.static.prism = { 'type':'prism5k', 'tag':'PRISM',
              'description':'Static datasets for PRISM model',
              'datasets':('lat', 'lon', 'elev'),
              'masks':('land_mask:cus_mask', 'interp_mask:cus_interp_mask'),
              'masksource':'dem5k_conus_static.h5', 'filetype':'static',
              'template':'prism5k_%(region)s_static.h5'
              }
CFGBASE.static.link(COMMON.static.prism)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# sub-directory hooks
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('subdir_paths', CFGBASE)
ConfigObject('subdir_paths', COMMON)

