
import os, sys

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG as REANALYSIS_CONFIG
CONFIG = REANALYSIS_CONFIG.copy('urma_config', None)
del REANALYSIS_CONFIG

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# define URMA as the project
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.project.update( {
       # GRIB file bounding box (equivalent coverage to ACIS grid bounds)
       'bbox':{'conus':'-125.25,23.749,-65.791,50.208',
               'NE':'-83.125,36.75,-66.455,48.075'},
       'bbox_offset':{'lat':0.375,'lon':0.375},
       'hours_behind':6,
       'description':'Unrestricted Mesoscale Analysis',
       'grib_subdir':('reanalysis','%(region)s','urma','%(utc_date)s'),
       'grid_dimensions':{'conus':{'lat':1377,'lon':2145},
                          'NE':{'lat':598,'lon':635}},
       'indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                  'NE':{'x':(1468,2104),'y':(641,1240)}},
       'lat_spacing':(0.0198,0.0228),
       'lon_spacing':(0.0238,0.0330),
       'node_spacing':0.0248, 'resolution':'~2.5km',
       'search_radius':0.0413,
       'shared_source':True,
       'tag':'URMA',
} )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# URMA DATA SOURCES 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Daily files from NWS and NDGD
#
# subdir templates need :
#        %(region)s = NWS URMA region str
#        %(utc_hour)s = UTC hour as 2 digit int str)
#        NOTE: NOT necessarily the same as the current day in USA
#        NOTE: GMT lags ~7 hours behind in US Eastern time zone
#
URMA_SOURCES = ConfigObject('urma',None)
URMA_SOURCES.nws = {
    # interval = time interval between files
    'interval':1,
    # lag_hours = number of hours that file availability lags
    #             behind current UTC time
    # num_days = number of days avaiable from this site
    'ftp':{ 'lag_hours':7, 'num_days':1, 'timeunit':'hour',
        'subdir':'AR.%(region)s/RT.%(utc_hour)s',
        'url':'ftp://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndgd/GT.urma',
    },
    'http':{ 'lag_hours':7, 'num_days':1, 'timeunit':'hour',
        'subdir':'AR.%(region)s/RT.%(utc_hour)s',
        'url':'http://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndgd/GT.urma',
    },
    'num_days':2,
    'region':'conus',
}

# attributes of variables
URMA_SOURCES.nws.variables = {
    'DPT': {'description':'Dew Point Temperature',
            'missing':'NaNf', 'type':float, 'units':'K',
            'panoply':'Dewpoint_temperature_height_above_ground',
    },
    'GUST': {'description':'Speed of Maximum Wind Gust',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'Panoply':'Wind_speed_gust_height_above_ground',
    },
    'PRES': {'description':'Surface Pressure', 
             'missing':'NaNf', 'type':float, 'units':'Pa',
             'Panoply':'Pressure_surface',
    },
    'TCDC': {'description':'Total Cloud Cover',
             'missing':'NaNf', 'type':float, 'units':'%',
             'Panoply':'Total_cloud_cover_entire_atmosphere_single_layer',
    },
    'TMP': {'description':'Temperature',
            'missing':'NaNf', 'type':float, 'units':'K',
            'Panoply':'Temperature_height_above_ground',
    },
    'VIS': {'description':'Visibility',
            'missing':'NaNf', 'type':float, 'units':'m',
            'Panoply':'Visibility_surface',
    },
    'WDIR': {'description':'Wind Direction',
             'missing':'NaNf', 'type':float, 'units':'degtrue',
             'Panoply':'Wind_direction_from_which_blowing_height_above_ground',
    },
    'WIND': {'description':'Wind Speed',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'Panoply':'Wind_speed_height_above_ground',
    },
}

# UPDATE pygrib variable names to match names in NCEP files
URMA_SOURCES.nws.variables.DPT.pygrib = '2 metre dewpoint temperature'
URMA_SOURCES.nws.variables.GUST.pygrib = 'Wind speed (gust)'
URMA_SOURCES.nws.variables.PRES.pygrib = 'Surface pressure'
URMA_SOURCES.nws.variables.TCDC.pygrib = 'Total Cloud Cover'
URMA_SOURCES.nws.variables.TMP.pygrib = '2 metre temperature'
URMA_SOURCES.nws.variables.VIS.pygrib = 'Visibility'
# 2017/06/09 -- pygrib has "unknown" for WDIR variable name but str()
# 2017/06/09 -- displays variable as "Wind direction [from which blowing]"
# 2017/06/09 -- for record number 8 in NCEP URMA files
URMA_SOURCES.nws.variables.WDIR.pygrib = \
                                   'Wind direction [from which blowing]'
URMA_SOURCES.nws.variables.WIND.pygrib = '10 metre wind speed'

# map of variable to file that contains it
URMA_SOURCES.nws.source_file_map = {
        'DPT':'ds.td.bin',
        'GUST':'ds.wgust.bin',
        'PRES':'ds.press.bin',
        'TCDC':'ds.tcdc.bin',
        'TMP':'ds.temp.bin',
        'VIS':'ds.viz.bin',
        'WDIR':'ds.wdir.bin',
        'WIND':'ds.wspd.bin',
    }
def urmaNwsFilenames():
    return tuple(sorted(list(URMA_SOURCES.nws.source_file_map.attr_values)))
URMA_SOURCES.nws.sourceFilenames = urmaNwsFilenames
URMA_SOURCES.nws.localFilenames = urmaNwsFilenames

URMA_SOURCES.nws.local_file_map = URMA_SOURCES.nws.source_file_map
def urmaNwsFilename(variable):
    filename = URMA_SOURCES.nws.source_file_map.get(variable, None)
    if variable is not None: return filename
    raise LookupError, 'No filename found for "%s".' % variable
URMA_SOURCES.nws.sourceFilename = urmaNwsFilename
URMA_SOURCES.nws.localFilename = urmaNwsFilename

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# URMA hourly files from NCCF via NCEP
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# subdir template needs :
#    %(utc_date)s = UTC date as 8 digit int str (YYYYMMDDHH)
#                   NOTE: NOT necessarily the same as the current day in USA
#                   NOTE: UTC time lags 4 to 5 hours behind US/Eastern

URMA_SOURCES.ncep = {
    # interval = time interval between files, tuple for URMA
    #            interval[0] = time interval for master file
    #            interval[1] = time interval for precipitation file
    'interval':(1,6),
    # NCEP has multiple servers for URMA data
    'ftp': {'lag_hours':7, 'num_days':11, 'timeunit':'hour',
            'subdir':'urma2p5.%(utc_date)s',
            'url':'http://www.ftp.ncep.noaa.gov/data/nccf/com/urma/prod',
    },
    'http': {'lag_hours':7, 'num_days':11, 'timeunit':'hour',
             'subdir':'urma2p5.%(utc_date)s',
             'url':'http://www.ftp.ncep.noaa.gov/data/nccf/com/urma/prod',
    },
    'nomads': { 'lag_hours':7, 'num_days':11, 'timeunit':'hour',
                'subdir':'urma2p5.%(utc_date)s',
                'url':'http://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod',
    },
    'num_days':11,
    'region':'conus',
}

# NCEP servers have all of the variables defined for NWS
URMA_SOURCES.nws.variables.copy('variables', URMA_SOURCES.ncep)
# NCEP servers also have additional variables available
URMA_SOURCES.ncep.variables.update( {
    'APCP': {'description':'Total Accumulated Precipitation',
             'hours':(0,6,12,18),
             'missing':'NaNf', 'type':float, 'units':'kg/m^2',
             'Panoply':'Total_precipitation_surface_1_Hour_Accumulation',
    },
    'CEIL': {'description':'Cloud ceiling',
             'missing':'NaNf', 'type':float, 'units':'m',
             'Panoply':'Ceiling_cloud_ceiling',
    },
    'HGT': {'description':'Geopotential Height',
            'missing':'NaNf', 'type':float, 'units':'gpm',
            'Panoply':'Geopotential_height_surface',
    },
    'SPFH': {'description':'Specific Humidity',
             'missing':'NaNf', 'type':float, 'units':'kg/kg',
             'Panoply':'Specific_humidity_height_above_ground',
    },
    'UGRD': {'description':'U component of Wind',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'Panoply':'u-component_of_wind_height_above_ground',
    },
    'VGRD': {'description':'V component of Wind',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'Panoply':'v-component_of_wind_height_above_ground',
    },
} )

# UPDATE pygrib variable names to match names in NCEP files
URMA_SOURCES.ncep.variables.APCP.pygrib = 'Total Precipitation'
URMA_SOURCES.ncep.variables.CEIL.pygrib = 'Ceiling'
URMA_SOURCES.ncep.variables.HGT.pygrib = 'Orography'
URMA_SOURCES.ncep.variables.SPFH.pygrib = 'Specific humidity'
URMA_SOURCES.ncep.variables.UGRD.pygrib = '10 metre U wind component'
URMA_SOURCES.ncep.variables.VGRD.pygrib = '10 metre V wind component'

# NCEP servers only supply 2 files. One for precip and one for eveything else
# source data file name uses only UTC hour
URMA_SOURCES.ncep.source_file_map = {
               'APCP':'urma2p5.%(utc_time)s.pcp_06h.184.grb2',
               'data':'urma2p5.t%(utc_hour)sz.2dvaran1_ndfd.grb2',
               'default':'urma2p5.t%(utc_hour)sz.2dvaran1_ndfd.grb2',
               }
def urmaNcepSourceFilenames():
    return ('urma2p5.t%(utc_hour)sz.2dvaran1_ndfd.grb2',
            'urma2p5.%(utc_time)s.pcp_06h.184.grb2')
URMA_SOURCES.ncep.sourceFilenames = urmaNcepSourceFilenames

def urmaNcepSourceFilename(variable):
    filename = URMA_SOURCES.ncep.source_file_map.get(variable, None)
    if filename is not None: return filename
    if variable in URMA_SOURCES.ncep.variables.keys():
         return URMA_SOURCES.ncep.source_file_map.default
    raise LookupError, 'No filename found for "%s" variable.' % variable
URMA_SOURCES.ncep.sourceFilename = urmaNcepSourceFilename

# local data file name uses full UTC time (date + hour)
URMA_SOURCES.ncep.local_file_map = {
               'APCP':'urma.%(utc_time)sz.pcp_06h.grb2',
               'data':'urma.%(utc_time)sz.data.grb2',
               'default':'urma.%(utc_time)sz.data.grb2',
               }
def urmaNcepLocalFilenames():
    return ('urma.%(utc_time)sz.data.grb2',
            'urma.%(utc_time)sz.pcp_06h.grb2')
URMA_SOURCES.ncep.localFilenames = urmaNcepLocalFilenames

def urmaNcepLocalFilename(variable):
    filename = URMA_SOURCES.ncep.local_file_map.get(variable, None)
    if filename is not None: return filename
    if variable in URMA_SOURCES.ncep.variables.keys():
         return URMA_SOURCES.ncep.local_file_map.default
    raise LookupError, 'No filename found for "%s" variable.' % variable
URMA_SOURCES.ncep.localFilenames = urmaNcepLocalFilenames

# add URMA sources to the list of sources copied from reanalysis config
CONFIG.sources.link(URMA_SOURCES)

