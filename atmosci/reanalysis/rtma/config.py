
import os, sys

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG as REANALYSIS_CONFIG
CONFIG = REANALYSIS_CONFIG.copy('rtma_config', None)
del REANALYSIS_CONFIG

CONFIG.project.shared_source = True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# define RTMA as the project
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.project.update( {
       # GRIB file bounding box (equivalent coverage to ACIS grid bounds)
       'bbox':{'conus':'-125.25,23.749,-65.791,50.208',
               'NE':'-83.125,36.75,-66.455,48.075'},
       'bbox_offset':{'lat':0.375,'lon':0.375},
       'description':'Real-Time Mesoscale Analysis',
       'grib_source':'ncep',
       'grid_dimensions':{'conus':{'lat':1377,'lon':2145},
                          'NE':{'lat':598,'lon':635}},
       'hours_behind':2,
       'indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                  'NE':{'x':(1468,2104),'y':(641,1240)}},
       'lat_spacing':(0.0198,0.0228),
       'lon_spacing':(0.0238,0.0330),
       'node_spacing':0.0248, 'resolution':'~2.5km',
       'search_radius':0.0413,
       'shared_source':True,
       'tag':'RTMA',
} )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# RTMA data sources
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# subdir templates for URMA sources need :
#        %(region)s = NWS URMA region str
#        %(utc_date)s = UTC date as 8 digit int str (YYYYMMDDHH)
#              NOTE: NOT necessarily the same day as the current day in USA
#              NOTE: UTC time lags 4 to 5 hours behind US/Eastern depending
#                    Standard Time or Daylight Savings Time 
#                    e.g. 4:00 US/Eastern is 23:00 UTC on the previous day
#                    in winter and Midnight UTC the same day in summer.
#              NOTE: URMA lags about 6 hours behind current UTC time
#        %(utc_hour)s = UTC hour as 2 digit int str)
#              NOTE: NOT the same hour as the current hour in USA
#              NOTE: UTC lags 4 or 5 hours behind in US Eastern time zone
#              NOTE: URMA lags about 6 hours behind current UTC time
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# hourly files from NDGD via NWS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

RTMA_SOURCES = ConfigObject('rtma',None)
RTMA_SOURCES.nws = {
    # lag_hours = number of hours that data availability lags behind
    #             current UTC/GMT time 
    # num_days = number of days avaiable from this site
    'ftp':{ 'lag_hours':1, 'num_days':1, 'timeunit':'hour',
        'subdir':'AR.%(region)s/RT.%(utc_hour)s',
        'url':'ftp://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndgd/GT.rtma',
    },
    
    'http':{ 'lag_hours':4, 'num_days':1, 'timeunit':'hour',
        'subdir':'AR.%(region)s/RT.%(utc_hour)s',
        'url':'http://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndgd/GT.rtma',
    },
    'interval':1, # time interval between files
    'timezone':'UTC',
    'region':'conus',
}

# attributes of variables
RTMA_SOURCES.nws.variables = {
    'APCP': {'description':'Total Accumulated Precipitation',
             'missing':'NaNf', 'type':float, 'units':'kg/m^2',
             'variable':'Total_precipitation_surface_1_Hour_Accumulation',
    },
    'DPT':  {'description':'Dew Point',
             'missing':'NaNf', 'type':float, 'units':'K',
             'variable':'Dewpoint_temperature_height_above_ground',
    },
    'GUST': {'description':'Speed of Maximum Wind Gust',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'Wind_speed_gust_height_above_ground',
    },
    'PCPN': {'description':'Total Accumulated Precipitation',
             'missing':'NaNf', 'type':float, 'units':'kg/m^2',
             'variable':'Total_precipitation_surface_1_Hour_Accumulation',
    },
    'PRES': {'description':'Surface Pressure', 
             'missing':'NaNf', 'type':float, 'units':'Pa',
             'variable':'Pressure_surface',
    },
    'TCDC': {'description':'Total Cloud Cover',
             'missing':'NaNf', 'type':float, 'units':'%',
             'variable':'Total_cloud_cover_entire_atmosphere_single_layer',
    },
    'TMP':  {'description':'Temperature',
             'missing':'NaNf', 'type':float, 'units':'K',
             'variable':'Temperature_height_above_ground',
    },
    'VIS':  {'description':'Visibility',
             'missing':'NaNf', 'type':float, 'units':'m',
             'variable':'Visibility_surface',
    },
    'WDIR': {'description':'Wind Direction',
             'missing':'NaNf', 'type':float, 'units':'degtrue',
             'variable':'Wind_direction_from_which_blowing_height_above_ground',
    },
    'WIND': {'description':'Wind Speed',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'Wind_speed_height_above_ground',
    },
}

# UPDATE pygrib variable names to match names in NCEP files
RTMA_SOURCES.nws.variables.APCP.pygrib = 'Total Precipitation'
RTMA_SOURCES.nws.variables.DPT.pygrib = '2 metre dewpoint temperature'
RTMA_SOURCES.nws.variables.GUST.pygrib = 'Wind speed (gust)'
RTMA_SOURCES.nws.variables.PCPN.pygrib = 'Total Precipitation'
RTMA_SOURCES.nws.variables.PRES.pygrib = 'Surface pressure'
RTMA_SOURCES.nws.variables.TCDC.pygrib = 'Total Cloud Cover'
RTMA_SOURCES.nws.variables.TMP.pygrib = '2 metre temperature'
RTMA_SOURCES.nws.variables.VIS.pygrib = 'Visibility'
# 2017/06/09 -- pygrib has "unknown" for WDIR variable name but str()
# 2017/06/09 -- displays variable as "Wind direction [from which blowing]"
# 2017/06/09 -- for record number 8 in NCEP URMA files
RTMA_SOURCES.nws.variables.WDIR.pygrib = 'Wind direction [from which blowing]'
RTMA_SOURCES.nws.variables.WIND.pygrib = '10 metre wind speed'

# map of variable to file that contains it
RTMA_SOURCES.nws.source_file_map = {
        'APCP':'ds.precipa.bin',
        'DPT':'ds.td.bin',
        'GUST':'ds.wgust.bin',
        'PCPN':'ds.precipa.bin',
        'PRES':'ds.press.bin',
        'TCDC':'ds.tcdc.bin',
        'TMP':'ds.temp.bin',
        'VIS':'ds.viz.bin',
        'WDIR':'ds.wdir.bin',
        'WIND':'ds.wspd.bin',
    }


def rtmaNwsFilenames(): 
    return tuple(sorted(list(RTMA_SOURCES.nws.source_file_map.attr_values)))
RTMA_SOURCES.nws.sourceFilenames = rtmaNwsFilenames
RTMA_SOURCES.nws.localFilenames = rtmaNwsFilenames

RTMA_SOURCES.nws.local_file_map = RTMA_SOURCES.nws.source_file_map
def rtmaNwsFilename(variable):
    filename = RTMA_SOURCES.nws.source_file_map.get(variable, None)
    if filename is not None: return filename
    raise LookupError, 'No filename found for "%s" variable.' % variable
RTMA_SOURCES.nws.sourceFilename = rtmaNwsFilename
RTMA_SOURCES.nws.localFilename = rtmaNwsFilename

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# RTMA hourly files from NCCF via NOMADS at NCEP
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
RTMA_SOURCES.ncep = {
    # NCEP has multiple servers for RTMA data
    'ftp': {'lag_hours':2, 'num_days':2, 'timeunit':'hour',
            'subdir':'rtma2p5.%(utc_date)s',
            'url':'ftp://ftp.ncep.noaa.gov/pub/data/nccf/com/rtma/prod',
    },
    'http': {'lag_hours':2, 'num_days':2, 'timeunit':'hour',
             'subdir':'rtma2p5.%(utc_date)s',
             'url':'http://www.ftp.ncep.noaa.gov/data/nccf/com/rtma/prod',
    },
    'nomads': {'lag_hours':2, 'num_days':2, 'timeunit':'hour',
               'subdir':'rtma2p5.%(utc_date)s',
               'url':'http://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod',
    'interval':1, # time interval between files
    'num_days':2,
    'region':'conus',
    'timezone':'UTC',
    },
}


# NCEP servers have all of the variables defined for NWS
RTMA_SOURCES.nws.variables.copy('variables', RTMA_SOURCES.ncep)
# NCEP servers also have additional variables available
RTMA_SOURCES.ncep.variables.update( {
    'CEIL': {'desription':'Cloud Ceiling',
             'missing':'NaNf', 'type':float, 'units':'m',
             'variable':'Ceiling_cloud_ceiling',
    },
    'HGT':  {'description':'Geopotential Height',
             'missing':'NaNf', 'type':float, 'units':'gpm',
             'variable':'Geopotential_height_surface',
    },
    'SPFH': {'description':'Specific Humidity',
             'missing':'NaNf', 'type':float, 'units':'kg/kg',
             'variable':'Specific_humidity_height_above_ground',
    },
    'UGRD': {'description':'U component of Wind',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'u-component_of_wind_height_above_ground',
    },
    'VGRD': {'description':'V component of Wind',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'v-component_of_wind_height_above_ground',
    },
} )

# UPDATE pygrib variable names to match names in NCEP files
RTMA_SOURCES.ncep.variables.CEIL.pygrib = 'Ceiling'
RTMA_SOURCES.ncep.variables.HGT.pygrib = 'Orography'
RTMA_SOURCES.ncep.variables.SPFH.pygrib = 'Specific humidity'
RTMA_SOURCES.ncep.variables.UGRD.pygrib = '10 metre U wind component'
RTMA_SOURCES.ncep.variables.VGRD.pygrib = '10 metre V wind component'

# NCEP servers only supply 2 files. One for precip and one for eveything else
# source data file name uses only UTC hour
RTMA_SOURCES.ncep.source_file_map = {
    'APCP':'rtma2p5.%(utc_time)s.pcp.184.grb2',
    'data':'rtma2p5.t%(utc_hour)sz.2dvaran1_ndfd.grb2',
    'default':'rtma2p5.t%(utc_hour)sz.2dvaran1_ndfd.grb2',
    'PCPN':'rtma2p5.%(utc_time)s.pcp.184.grb2'
}
def rtmaNcepSourceFilenames():
    return ('rtma2p5.t%(utc_hour)sz.2dvaran1_ndfd.grb2', 
            'rtma2p5.%(utc_time)s.pcp.184.grb2')
RTMA_SOURCES.ncep.sourceFilenames = rtmaNcepSourceFilenames

RTMA_SOURCES.ncep.source_filesizes = {
    'APCP':450, 'PCPN':450, 'data':65000000, 'default':65000000,
}
def rtmaNcepSourceFileSize(variable):
    size = RTMA_SOURCES.ncep.source_filesizes.get(variable, None)
    if size == None and variable in RTMA_SOURCES.ncep.variables.attrs:
        return RTMA_SOURCES.ncep.source_filesizes.default

RTMA_SOURCES.ncep.sourceFilenames = rtmaNcepSourceFilenames

def rtmaNcepSourceFilename(variable):
    filename = RTMA_SOURCES.ncep.source_file_map.get(variable, None)
    if filename is not None: return filename
    if variable in RTMA_SOURCES.ncep.variables.keys():
         return RTMA_SOURCES.ncep.source_file_map.default
    raise LookupError, 'No filename found for "%s" variable.' % variable
RTMA_SOURCES.ncep.sourceFilename = rtmaNcepSourceFilename

# local data file name uses full UTC time (date + hour)
RTMA_SOURCES.ncep.local_file_map = {
    'APCP':'rtma.%(utc_time)sz.precip.grb2',
    'data':'rtma.%(utc_time)sz.data.grb2',
    'default':'rtma.%(utc_time)sz.data.grb2',
    'PCPN':'rtma.%(utc_time)sz.precip.grb2',
}
def rtmaNcepLocalFilenames():
    return ('rtma.%(utc_time)sz.data.grb2', 
            'rtma.%(utc_time)sz.precip.grb2')
RTMA_SOURCES.ncep.sourceFilenames = rtmaNcepLocalFilenames

def rtmaNcepLocalFilename(variable):
    filename = RTMA_SOURCES.ncep.local_file_map.get(variable, None)
    if filename is not None: return filename
    if variable in RTMA_SOURCES.ncep.variables.keys():
         return RTMA_SOURCES.ncep.local_file_map.default
    raise LookupError, 'No filename found for "%s" variable.' % variable
RTMA_SOURCES.ncep.localFilename = rtmaNcepLocalFilename

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# RTMA hourly files from UCAR via THREDDS
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# for the subdir template needs :
#    %(utc_hour)s = GMT hour as 2 digit int str)
#
RTMA_SOURCES.ucar = {
    # lag_hours = number of hours that data availability lags behind
    #             current UTC/GMT time 
    # num_days = number of days avaiable from this site
    'thredds': {'lag_hours':2, 'num_days':14, 'timeunit':'hour',
                'subdir':'rtma2p5.%(utc_hour)s',
                'url':'http://thredds.ucar.edu/thredds/fileServer/grib/NCEP/RTMA/CONUS_2p5km/',
    },
    'interval':1, # time interval between files
    'region':'conus',
    'timezone':'UTC',
}

RTMA_SOURCES.ucar.variables = {
    'APCP': {'description':'Total Accumulated Precipitation',
             'missing':'NaNf', 'type':float, 'units':'kg/m^2',
             'variable':'Total_precipitation_Forecast_surface_1_Hour_Accumulation',
    },
    'DPT':  {'description':'Dew Point',
             'missing':'NaNf', 'type':float, 'units':'K',
             'variable':'Dewpoint_temperature_Analysis_height_above_ground',
    },
    'HGT':  {'description':'Geopotential Height',
             'missing':'NaNf', 'type':float, 'units':'gpm',
             'variable':'Geopotential_height_Analysis_surface',
    },
    'GUST': {'description':'Speed of Maximum Wind Gust',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'Wind_speed_gust_Analysis_height_above_ground',
    },
    'PRES': {'description':'Surface Pressure', 
             'missing':'NaNf', 'type':float, 'units':'Pa',
             'variable':'Pressure_Analysis_surface',
    },
    'TCDC': {'description':'Total Cloud Cover',
             'missing':'NaNf', 'type':float, 'units':'%',
             'variable':'Total_cloud_cover_Analysis_entire_atmosphere_single_layer',
    },
    'TMP':  {'description':'Temperature',
             'missing':'NaNf', 'type':float, 'units':'K',
             'variable':'Temperature_Analysis_height_above_ground',
    },
    'UGRD': {'description':'U component of Wind',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'u-component_of_wind_Analysis_height_above_ground',
    },
    'VGRD': {'description':'V component of Wind',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'v-component_of_wind_Analysis_height_above_ground',
    },
    'VIS':  {'description':'Visibility',
             'missing':'NaNf', 'type':float, 'units':'m',
             'variable':'Visibility_Analysis_surface',
    },
    'WDIR': {'description':'Wind Direction',
             'missing':'NaNf', 'type':float, 'units':'degtrue',
             'variable':'Wind_direction_from_which_blowing_Analysis_height_above_ground',
    },
    'WIND': {'description':'Wind Speed',
             'missing':'NaNf', 'type':float, 'units':'m/s',
             'variable':'Wind_speed_Analysis_height_above_ground',
    },
}
#TODO: need to get names/strings for accessing these datasets using PYGRIB


RTMA_SOURCES.ucar.source_file_map = {
    'APCP':'RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2',
    'data':'RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2',
    'default':'RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2',
    'PCPN':'RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2',
}
def rtmaUcarSourceFilenames():
    return ('RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2',) 
RTMA_SOURCES.ucar.sourceFilenames = rtmaUcarSourceFilenames

def rtmaUcarSourceFilename(variable):
    filename = RTMA_SOURCES.ucar.source_file_map.get(variable, None)
    if filename is not None: return filename
    if variable in RTMA_SOURCES.ucar.variables.keys():
         return RTMA_SOURCES.ucar.source_file_map.default
    raise LookupError, 'No filename found for "%s" variable.' % variable
RTMA_SOURCES.ucar.sourceFilename = rtmaUcarSourceFilename

RTMA_SOURCES.ucar.local_file_map = {
    'APCP':'rtma2p5.t%(utc_time)sz.data.grb2',
    'data':'rtma2p5.t%(utc_time)sz.data.grb2',
    'default':'rtma2p5.t%(utc_time)sz.data.grb2',
    'PCPN':'rtma2p5.t%(utc_time)sz.data.grb2',
}
def rtmaUcarLocalFilenames():
    return ('rtma2p5.t%(utc_time)sz.data.grb2',) 
RTMA_SOURCES.ucar.localFilenames = rtmaUcarLocalFilenames

def rtmaUcarLocalFilename(variable):
    filename = RTMA_SOURCES.ucar.local_file_map.get(variable, None)
    if filename is not None: return filename
    if variable in RTMA_SOURCES.ucar.variables.keys():
         return RTMA_SOURCES.ucar.local_file_map.default
    raise LookupError, 'No filename found for "%s" variable.' % variable
RTMA_SOURCES.ucar.localFilename = rtmaUcarLocalFilename

# add RTMA sources to the list of sources copied from reanalysis config
CONFIG.sources.link(RTMA_SOURCES)

