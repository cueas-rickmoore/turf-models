
import os, sys

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.hourly.config import CONFIG as HOURLY_CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CONFIG = HOURLY_CONFIG.copy('reanalysis_config', None)
del HOURLY_CONFIG

CONFIG.project.update( {
    'analysis':'rtma',
    'data_timezone':'UTC',
    'download':{ 'attempts':3, 'wait_times':(15,30,40) },
    'fcast_days':6,
    'local_timezone':'US/Eastern',
    'obs_days':30,
    'shared_grib_dir': True,
    'shared_grid_dir': True,
    'source_priority':('urma','rtma'),
    'tag':'reanalysis',
    'target_hour':7,
} )

# add reanalysis as a source
REANALYSIS = ConfigObject('reanalysis', None)
REANALYSIS.source_priority = ('rtma','urma') # higher index = higher priority
REANALYSIS.tag = 'Reanalysis'
REANALYSIS.grib = {
    'bbox':{ 'conus':'-125.25,23.749,-65.791,50.208',
             'NE':'-83.125,36.75,-66.455,48.075' },
     'bbox_offset':{'lat':0.375,'lon':0.375},
     'data_chunks':1024000,
     'dimensions':{ 'conus':{'lat':1377,'lon':2145},
                    'NE':{'lat':598,'lon':635}
     },
     'indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                'NE':{'x':(1468,2104),'y':(641,1240)}
     },
     'lat_spacing':(0.0198,0.0228),
     'lon_spacing':(0.0238,0.0330),
     'region':'conus',
     'resolution':'~2.5km',
     'root_dir':'weather',
     'search_radius':0.0413,
     'server':'nomads',
     'source':'ncep',
     'subdir':('reanalysis','%(region)s','%(analysis)s','%(utc_date)s'),
     'timezone':'UTC',
     'variable_map':{ # maps common variable names to reanalysis variables
          'dewpt':'DPT','pcpn':'APCP','pressure':'PRES',
          'rh':'RHUM','temp':'TMP'
     },
     'variable_names':('APCP','CEIL','DPT','GUST','HGT','PRES', 'RHUM','SPFH',
                       'TCDC','TMP','UGRD','VGRD','VIS','WDIR','WIND'),
}

REANALYSIS.grid = {
    'bbox':{ 'conus':CONFIG.regions.conus.data, 'NE':CONFIG.regions.NE.data },
    'description':'Reanalysis model data resampled to ACIS HiRes grid',
    'dimensions':CONFIG.sources.acis.grid_dimensions,
    'grid_type':'ACIS HiRes',
    'node_spacing':CONFIG.sources.acis.node_spacing,
    'root_dir':'weather',
    'region':'NE',
    'resolution':'~2.5km',
    'search_radius':CONFIG.sources.acis.search_radius,
    'subdir':('grid','%(region)s','reanalysis','%(target_year)s','%(target_month)s'),
    'source':'acis',
    'sources':'RTMA/URMA',
    'timezone':'UTC',
    'variable_map':{ # maps common variable names to reanalysis variables
       'apcp':'PCPN','dewpt':'DPT','pressure':'PRES','rh':'RHUM','temp':'TMP'
    },
    'variable_names':('CEIL','DPT','GUST','HGT','PCPN','PRES','RHUM','SPFH',
                      'TCDC','TMP','UGRD','VGRD','VIS','WDIR','WIND'),
}

# map the individual reanalysis data types to filename templates
# 'data' files shold contain multiple data types
REANALYSIS.grid_file_map = {
    'data':'%(target_month)s-Data.h5',
    'APCP':'%(target_month)s-Precipitation.h5',
    'CEIL':'%(target_month)s-Cloud-Ceiling.h5',
    'DPT' :'%(target_month)s-Dewpoint.h5',
    'GUST':'%(target_month)s-Wind-Gust.h5',
    'HGT' :'%(target_month)s-Geopotential-Height.h5',
    'PCPN':'%(target_month)s-Precipitation.h5',
    'PRES':'%(target_month)s-Surface-Pressure.h5',
    'RHUM':'%(target_month)s-Relative-Humidity.h5',
    'SPFH':'%(target_month)s-Specific-Humidity.h5',
    'TCDC':'%(target_month)s-Total-Cloud-Cover.h5',
    'TMP' :'%(target_month)s-Temperature.h5',
    'UGRD':'%(target_month)s-U-Wind,h5',
    'VGRD':'%(target_month)s-V-Wind,h5',
    'VIS' :'%(target_month)s-Visibility,h5',
    'WDIR':'%(target_month)s-Wind-Direction,h5',
    'WIND':'%(target_month)s-Wind-Speed,h5',
}

CONFIG.sources.link(REANALYSIS)

# datasets common to all reanalysis sources
CONFIG.datasets.timegrid.copy('APCP', CONFIG.datasets)
CONFIG.datasets.APCP.description = 'Accumulated precipitation'
#CONFIG.datasets.APCP.timezone = 'US/Eastern'
CONFIG.datasets.APCP.units = 'kg/m^2'
CONFIG.datasets.APCP.hours = 6
CONFIG.datasets.APCP.copy('CEIL', CONFIG.datasets)
CONFIG.datasets.CEIL.description = 'Cloud ceiling'
CONFIG.datasets.CEIL.units = 'm'
CONFIG.datasets.CEIL.hours = 1
CONFIG.datasets.CEIL.copy('DPT', CONFIG.datasets)
CONFIG.datasets.DPT.description = 'Dew point temperature'
CONFIG.datasets.DPT.units = 'K'
CONFIG.datasets.CEIL.copy('GUST', CONFIG.datasets)
CONFIG.datasets.GUST.description = 'Speed of wind gust'
CONFIG.datasets.GUST.units = 'm/s'
CONFIG.datasets.CEIL.copy('HGT', CONFIG.datasets)
CONFIG.datasets.HGT.description = 'Geopotential height @ surface'
CONFIG.datasets.HGT.units = 'gpm'
CONFIG.datasets.CEIL.copy('PCPN', CONFIG.datasets)
CONFIG.datasets.PCPN.description = 'Hourly precipitation'
CONFIG.datasets.PCPN.units = 'in'
CONFIG.datasets.CEIL.copy('PRES', CONFIG.datasets)
CONFIG.datasets.PRES.description = 'Surface pressure'
CONFIG.datasets.PRES.units = 'Pa'
CONFIG.datasets.CEIL.copy('RHUM', CONFIG.datasets)
CONFIG.datasets.RHUM.description = 'Relative humidity'
CONFIG.datasets.RHUM.units = '%'
CONFIG.datasets.CEIL.copy('SPFH', CONFIG.datasets)
CONFIG.datasets.SPFH.description = 'Specific humidity'
CONFIG.datasets.SPFH.units = 'kg/kg'
CONFIG.datasets.CEIL.copy('TCDC', CONFIG.datasets)
CONFIG.datasets.TCDC.description = 'Total cloud cover over entire atmosphere'
CONFIG.datasets.TCDC.units = '%'
CONFIG.datasets.DPT.copy('TMP', CONFIG.datasets)
CONFIG.datasets.TMP.description = '2 meter temperature'
CONFIG.datasets.GUST.copy('UGRD', CONFIG.datasets)
CONFIG.datasets.UGRD.description = 'U wind component @ 10 meters'
CONFIG.datasets.GUST.copy('VGRD', CONFIG.datasets)
CONFIG.datasets.VGRD.description = 'V wind component @ 10 meters'
CONFIG.datasets.CEIL.copy('VIS', CONFIG.datasets)
CONFIG.datasets.VIS.description = 'Visibility at surface'
CONFIG.datasets.VIS.units = 'm'
CONFIG.datasets.CEIL.copy('WDIR', CONFIG.datasets)
CONFIG.datasets.WDIR.description = 'Wind direction'
CONFIG.datasets.WDIR.units = 'degtrue'
CONFIG.datasets.GUST.copy('WIND', CONFIG.datasets)
CONFIG.datasets.WIND.description = 'Wind speed @ 10 meters'

# filetypes common to all reanalysis sources
CONFIG.filetypes.APCP = { 'scope':'hours',
       'datasets':('PCPN','lon','lat','provenance:PCPN:timestats'),
       'description':'Hourly precipition from reanalysis models'}
CONFIG.filetypes.CEIL = { 'scope':'hours',
       'datasets':('CEIL','lon','lat','provenance:CEIL:timestamp'),
       'description':'Hourly cloud ceiling from reanalysis models'}
CONFIG.filetypes.DPT = { 'scope':'hours',
       'datasets':('DPT','lon','lat','provenance:DPT:timestats'),
       'description':'Hourly dew point temperature from reanalysis models'}
CONFIG.filetypes.HGT = { 'scope':'hours',
       'datasets':('HGT','lon','lat','provenance:HGT:timestats'),
       'description':'Hourly geopotential height from reanalysis models'}
CONFIG.filetypes.GUST = { 'scope':'hours',
       'datasets':('GUST','lon','lat','provenance:GUST:timestats'),
       'description':'Hourly wind gust from reanalysis models'}
CONFIG.filetypes.PCPN = { 'scope':'hours',
       'datasets':('PCPN','lon','lat','provenance:PCPN:timestats'),
       'description':'Hourly precipition from reanalysis models'}
CONFIG.filetypes.PRES = { 'scope':'hours',
       'datasets':('PRES','lon','lat','provenance:PRES:timestats'),
       'description':'Hourly surface pressure from reanalysis models'}
CONFIG.filetypes.RHUM = { 'scope':'hours',
       'datasets':('RHUM','lon','lat','provenance:RHUM:timestats'),
       'description':'Hourly relative humidity from reanalysis models'}
CONFIG.filetypes.SPFH = { 'scope':'hours',
       'datasets':('SPFH','lon','lat',' provenance:SPFH:timestats'),
       'description':'Hourly specific humidity from reanalysis models'}
CONFIG.filetypes.TCDC = { 'scope':'hours',
       'datasets':('TCDC','lon','lat','provenance:TCDC:timestamp'),
       'description':'Hourly total cloud cover from reanalysis models'}
CONFIG.filetypes.TMP = { 'scope':'hours',
       'datasets':('TMP','lon','lat','provenance:TMP:timestats'),
       'description':'Hourly temperature from reanalysis models'}
CONFIG.filetypes.UGRD = { 'scope':'hours',
       'datasets':('UGRD','lon','lat','provenance:UGRD:timestamp'),
       'description':'Hourly U wind component from reanalysis models'}
CONFIG.filetypes.VGRD = { 'scope':'hours',
       'datasets':('VGRD','lon','lat','provenance:VGRD:timestamp'),
       'description':'Hourly V wind component from reanalysis models'}
CONFIG.filetypes.VIS = { 'scope':'hours',
       'datasets':('VIS','lon','lat','provenance:VIS:timestats'),
       'description':'Hourly surface visibility from reanalysis models'}
CONFIG.filetypes.WDIR = { 'scope':'hours',
       'datasets':('WDIR','lon','lat','provenance:WDIR:timestamp'),
       'description':'Hourly wind direction from reanalysis models'}
CONFIG.filetypes.WIND = { 'scope':'hours',
       'datasets':('WIND','lon','lat','provenance:WIND:timestats'),
       'description':'Hourly wind speed from reanalysis models'}

