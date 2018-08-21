# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import os, sys

from atmosci.utils.config import ConfigObject


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CACHE_SERVER_BUFFER_MIN = 20
# discontinued 'http://weather.noaa.gov/pub/SL.us008001/ST.opnl/DF.gr2/'
NDFD_REMOTE_SERVER = 'http://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/'
NDFD_FILE_TEMPLATE = 'DC.ndfd/AR.{0}/VP.{1}/ds.{2}.bin'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.hourly.config import CONFIG as HOURLY_CONFIG
CONFIG = HOURLY_CONFIG.copy('config', None)
del HOURLY_CONFIG

CONFIG.project.update( {
    'downloads':{ 'attempts':3, 'wait_times':(15,30,40) },
    'local_timezone':'US/Eastern',
    'shared_grib_dir': True,
    'shared_grid_dir': True,
    'tag':'forecast',
} )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data sources
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#ConfigObject('sources', CONFIG)

CONFIG.sources.ndfd = {
    'days_behind':0,
    'default_region':'conus',
    'default_source':'nws',
    'description':'National Digital Forecast Database',

    'grib':{
        'bbox':{'conus':'-125.25,23.749,-65.791,50.208',
                'NE':'-83.125,36.75,-66.455,48.075'},
        'bbox_offset':{'lat':0.375,'lon':0.375},
        'download_template':'%(timespan)s-%(variable)s.grib',
        'file_template':'%(timespan)s-%(variable)s.grib',
        'dimensions':{'conus':{'lat':1377,'lon':2145},
                      'NE':{'lat':598,'lon':635}},
        'indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                   'NE':{'x':(1468,2104),'y':(641,1240)}},
        'lat_spacing':(0.0198,0.0228),
        'lon_spacing':(0.0238,0.0330),
        'node_spacing':0.0248,
        'region':'conus',
        'resolution':'~2.5km',
        'root_dir':'weather',
        'search_radius':0.0413,
        'size_tolerance':0.75,
        'subdirs':('forecast', '%(region)s','%(source)s','%(date)s'),
        'timezone':'UTC',
        'wait_attemps':5, # number of failed download attempts before quitting
        'wait_seconds':10, # time to wait between failed download attempts
    },
    'grid': {
        'bbox':{ 'conus':CONFIG.regions.conus.data,
                 'NE':CONFIG.regions.NE.data
        },
        'description':'NDFD model data resampled to ACIS HiRes grid',
        'dimensions':CONFIG.sources.acis.grid_dimensions,
        'file_timezone':'UTC',
        'grid_type':'ACIS HiRes',
        'node_spacing':CONFIG.sources.acis.node_spacing,
        'region':'NE',
        'resolution':'~2.5km',
        'root_dir':'weather',
        'search_radius':CONFIG.sources.acis.search_radius,
        'source':'acis',
        'subdirs':('grid','%(region)s','%(source)s','%(year)d','%(month)s'),
        'tag':'NDFD',
        'timezone':'UTC',
    },
}

CONFIG.sources.ndfd.nws = {
    'filename':'ds.%(variable)s.bin',
    'server_subdirs':('AR.%(region)s','VP.%(timespan)s'),
    'server_url':'http://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd',
    'timespans':('001-003','004-007','008-450'),
}

CONFIG.sources.ndfd.nws.filedata = {
    '001-003': ['apt','conhazo','critfireo','drtfireo','fret','fretdep',
                'iceaccum','maxrh','maxt','minrh','mint','phail','pop12',
                'ptornado','ptotsvrtstm','ptotxsvrtstm','ptstmwinds',
                'pxhail','pxtornado','pxtstmwinds','qpf','rhm','sky','snow',
                'tcfrt','tcsst','tctt','tcwspdabv34c','tcwspdabv34i',
                'tcwspdabv50c','tcwspdabv50i','tcwspdabv64c','tcwspdabv641',
                'tcwt','td','temp','waveh','wdir','wgust','wspd','wwa','wx'],
    '004-007': ['apt','critfireo','drtfireo','fret','fretdep','frettot',
                'maxrh','maxt','minrh','mint','pop12','ptotsvrtstm',
                'rhm','sky','tcwspdabv34c','tcwspdabv34i','tcwspdabv50c',
                'tcwspdabv50i','tcwspdabv64c','tcwspdabv641','td','temp',
                'waveh','wdir','wspd','wwa','wx'],
    '008-450': ['prcpabv14d','prcpabv30d','prcpabv90d','prcpblw14d',
                'prcpblw30d','prcpblw90d','tmpabv14d','tmpabv30d','tmpabv90d',
                'tmpblw14d','tmpblw30d','tmpblw90d']
}

"""
for temp, td, rhm
utc_day =   [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
             1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,
             3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6]
utc_hour =  [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,
             0,1,2,3,4,5,6,7,8,9,10,11,12,15,18,21,0,3,6,9,12,15,18,21,
             0,6,12,18,0,6,12,18,0,6,12,18,0,6,12,18]
grib_hour = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,
             24,25,26,27,28,29,30,31,32,33,34,35,36,39,42,45,48,51,54,57,
             60,64,66,69,72,78,84,90,96,102,108,114,120,126,132,138,144,
             150,156,162]

qpf_day =   [0,0,0,0,1,1,1,1,2,2,2,2,3]
qpf_hour =  [0,6,12,18,0,6,12,18,0,6,12,18,0]
qpf_grib = [0,6,12,18,24,30,36,42,48,54,60,66,72]

pop_day =   [0,1,1,2,2,3,3,4,4,5,5,6,6,7]
pop_hour =  [12,0,12,0,12,0,12,0,12,0,12,0,12,0]
pop_grib = [12,24,36,48,60,72,84,96,108,120,132,144,156,168]
"""

# variable attributes
CONFIG.sources.ndfd.variables = {
    '001-003': {
       'maxt':{'grib':'Maximum temperature',
               'grib_size':2500000,
               'description':'12 hr Maximum temperature @ surface',
               'fill_method':None, # cannot be fudged
               'grib_dataset':'maxt',
               'grid_dataset':'maxt',
               'grid_filetype':'tempext',
               'missing':'NaNf', 'type':float, 'units':'K',
               'time':'minutes', 'count':2, 'span':1440, # three 24 hour intervals
        },
       'mint':{'grib':'Minimum temperature',
               'grib_size':2500000,
               'description':'12 hr Minimum temperature @ surface',
               'fill_method':None, # cannot be fudged
               'grib_dataset':'mint',
               'grid_dataset':'mint',
               'grid_filetype':'tempext',
               'missing':'NaNf', 'type':float, 'units':'K',
               'time':'minutes', 'count':2, 'span':1440, # two 24 hour intervals
        },
       'pop':{'grib':'Total_precipitation_surface_12_Minute_Accumulation_probability_above_0p254',
              'grib_size':2500000,
              'description':'Total precipitation',
              'fill_method':'copy', # same value at each hour in timespan
              'grib_dataset':'pop12',
              'grid_dataset':'POP',
              'grid_filetype':'POP12',
              'missing':'NaNf', 'type':float, 'units':'kg/m^2',
              'time':'hours', 'count':8, 'span':12, # eight 12 hour intervals
        },
       'pop12':{'grib':'Total_precipitation_surface_12_Minute_Accumulation_probability_above_0p254',
                'grib_size':2000000,
                'description':'Total precipitation',
                'fill_method':'copy', # same value at each hour in timespan
                'grib_dataset':'pop12',
                'grid_dataset':'POP',
                'grid_filetype':'POP12',
                'missing':'NaNf', 'type':float, 'units':'kg/m^2',
                'time':'hours', 'count':8, 'span':12, # eight 12 hour intervals
        },
       'qpf':{'grib':'Total precipitation',
              'grib_size':3000000,
              'description':'6 hour accumulated precipitation @ surface',
              'grid_filetype':'PCPN',
              'fill_method':'spread', # spread amount/span equally to all hours
              'grib_dataset':'qpf',
              'grid_dataset':'PCPN',
              'grid_filetype':'PCPN',
              'missing':'NaNf', 'type':float, 'units':'kg/m^2',
              'time':'hours', 'count':9, 'span':6, # nine 6 hour intervals
        },
       'rhm':{'grib':'Relative humidity',
              'grib_size':30000000,
              'description':'Relative humidity @ surface',
              'fill_method':'scaled', # by avg from prev hour to fcast hour
              'grib_dataset':'rhm',
              'grid_dataset':'RHUM',
              'grid_filetype':'RHUM',
              'missing':'NaNf', 'type':float, 'units':'kg/m^2',
              # 36 one hour intervals, six 3 hour intervals
              'time':'hours', 'count':(36,1), 'span':(1,3),
        },
       'td':{'grib':'Dewpoint temperature',
             'grib_size':35000000,
             'description':'Dewpoint temperature @ surface',
             'fill_method':'scaled', # by avg from prev hour to fcast hour
             'grib_dataset':'td',
             'grid_dataset':'DPT',
             'grid_filetype':'DPT',
             'missing':'NaNf', 'type':float, 'units':'K',
             # 36 one hour intervals, six 3 hour intervals
             'time':'minutes', 'count':(36,6), 'span':(1,3),
        },
       'temp':{'grib':'Temperature',
               'grib_size':43000000,
               'description':'Maximum temperature @ surface',
               'fill_method':'scaled', # by avg from fcast hour to prev hour
               'grib_dataset':'temp',
               'grid_dataset':'TEMP',
               'grid_filetype':'TEMP',
               'missing':'NaNf', 'type':float, 'units':'K',
               # 36 one hour intervals, six 3 hour intervals
               'time':'minutes', 'count':(36,6), 'span':(1,3),
        },
       'wx':{'grib':'Wx',
             'grib_size':11000000,
             'description':'Weather @ surface',
             'fill_method':'copy', # same value at each hour in timespan
             'grib_dataset':'wx',
             'grid_dataset':'WX',
             'grid_filetype':'WX',
             'missing':'', 'type':'string', 'units':None,
             # 36 one hour intervals, one 2 hour interval, five 3 hour intervals
             'time':'hour', 'count':(36,1,5), 'span':(1,2,3), 
        },
    },
    '004-007': {
       'maxt':{'grib':'Maximum temperature',
               'grib_size':3500000,
               'description':'12 hr Maximum temperature @ surface',
               'fudge_type':None, # cannot be fudged
               'grib_dataset':'maxt',
               'grid_dataset':'maxt',
               'grid_filetype':'tempext',
               'missing':'NaNf', 'type':float, 'units':'K',
               'time':'hours', 'count':4, 'span':24, # four 24 hour intervals
        },
       'mint':{'grib':'Minimum temperature',
               'grib_size':3500000,
               'description':'12 hr Minimum temperature @ surface',
               'fudge_type':None, # cannot be fudged
               'grib_dataset':'mint',
               'grid_dataset':'mint',
               'grid_filetype':'tempext',
               'missing':'NaNf', 'type':float, 'units':'K',
               'time':'hours', 'count':4, 'span':24, # four 24 hour intervals
        },
       'pop12':{'grib':'Total_precipitation_surface_12_Minute_Accumulation_probability_above_0p254',
                'grib_size':3000000,
                'description':'Total precipitation',
                'fill_method':'copy', # same value at each hour in timespan
                'grib_dataset':'pop12',
                'grid_dataset':'POP',
                'grid_filetype':'PCPN',
                'missing':'NaNf', 'type':float, 'units':'kg/m^2',
                'time':'hours', 'count':8, 'span':12, # eight 12 hour intervals
        },
       'rhm':{'grib':'Relative humidity',
              'grib_size':11000000,
              'description':'Relative humidity @ surface',
              'fill_method':'scaled', # by avg from fcast hour to prev hour
              'grib_dataset':'rhm',
              'grid_dataset':'RHUM',
              'grid_filetype':'RHUM',
              'missing':'NaNf', 'type':float, 'units':'kg/m^2',
              'time':'hours', 'count':16, 'span':6, # sixteen 6 hour intervals
        },
       'td':{'grib':'Dewpoint temperature',
             'grib_size':12000000,
             'description':'Dewpoint temperature @ surface',
             'fill_method':'scaled', # by avg from fcast hour to prev hour
             'grib_dataset':'td',
             'grid_dataset':'DPT',
             'grid_filetype':'DPT',
             'missing':'NaNf', 'type':float, 'units':'K',
             'time':'hours', 'count':16, 'span':6, # sixteen 6 hour intervals
        },
       'temp':{'grib':'Temperature',
               'grib_size':15000000,
               'description':'Maximum temperature @ surface',
               'fill_method':'scaled', # by avg from fcast hour to prev hour
               'grib_dataset':'temp',
               'grid_dataset':'TEMP',
               'grid_filetype':'TEMP',
               'missing':'NaNf', 'type':float, 'units':'K',
               'time':'hours', 'count':16, 'span':6, # sixteen 6 hour intervals
        },
       'wx':{'grib':'Wx',
             'grib_size':3600000,
             'description':'Weather @ surface',
             'fill_method':'copy', # same value at each hour in timespan
             'grib_dataset':'wx',
             'grid_dataset':'WX',
             'grid_filetype':'WX',
             'missing':'', 'type':'string', 'units':None,
             'time':'hours', 'count':16, 'span':6, # sixteen 6 hour intervals
        },
    },
}


# create variables that are compatible with RTMA & URMA reanalysis datasets
CONFIG.sources.ndfd.variables['001-003'].qpf.copy('pcpn',
               CONFIG.sources.ndfd.variables['001-003'])
CONFIG.sources.ndfd.variables['001-003'].rhm.copy('rhum',
               CONFIG.sources.ndfd.variables['001-003'])
CONFIG.sources.ndfd.variables['001-003'].td.copy('dpt',
               CONFIG.sources.ndfd.variables['001-003'])
CONFIG.sources.ndfd.variables['001-003'].temp.copy('tmp',
               CONFIG.sources.ndfd.variables['001-003'])

CONFIG.sources.ndfd.variables['004-007'].rhm.copy('rhum',
               CONFIG.sources.ndfd.variables['004-007'])
CONFIG.sources.ndfd.variables['004-007'].td.copy('dpt',
               CONFIG.sources.ndfd.variables['004-007'])
CONFIG.sources.ndfd.variables['004-007'].temp.copy('tmp',
               CONFIG.sources.ndfd.variables['004-007'])

# forecast datasets
CONFIG.datasets.timegrid.copy('DPT', CONFIG.datasets)
CONFIG.datasets.DPT.description = 'Forecast dewpoint temperature @ 2 meters'
CONFIG.datasets.DPT.frequency = 1
CONFIG.datasets.DPT.source = 'NDFD model data resampled to ACIS HiRes grid'
CONFIG.datasets.DPT.units = 'K'
CONFIG.datasets.DPT.copy('GUST', CONFIG.datasets)
CONFIG.datasets.GUST.description = 'Forecast speed of wind gust @ 10 meters'
CONFIG.datasets.GUST.units = 'm/s'
CONFIG.datasets.DPT.copy('PCPN', CONFIG.datasets)
CONFIG.datasets.PCPN.description = 'Forecast precipitation (surface)'
CONFIG.datasets.PCPN.note = 'estimated from NDFD 6 hr QPF forecasts'
CONFIG.datasets.PCPN.units = 'in'
CONFIG.datasets.DPT.copy('POP12', CONFIG.datasets)
CONFIG.datasets.POP12.description = 'Forecast probability of precipitation > .01in'
CONFIG.datasets.POP12.frequency = 12
CONFIG.datasets.POP12.units = '%'
CONFIG.datasets.POP12.copy('POP', CONFIG.datasets)
CONFIG.datasets.POP.frequency = 1
CONFIG.datasets.POP.note = 'hourly values estimated from NDFD PoP12'
CONFIG.datasets.DPT.copy('QPF', CONFIG.datasets)
CONFIG.datasets.QPF.description = 'Forecast 6 hour accumulated precipitation (surface)'
CONFIG.datasets.QPF.frequency = 6
CONFIG.datasets.QPF.units = 'in'
CONFIG.datasets.DPT.copy('RHUM', CONFIG.datasets)
CONFIG.datasets.RHUM.description = 'Forecast relative humidity (surface)'
CONFIG.datasets.RHUM.units = '%'
CONFIG.datasets.DPT.copy('TEMP', CONFIG.datasets)
CONFIG.datasets.TEMP.description = 'Forecast temperature @ 2 meters'
CONFIG.datasets.DPT.copy('WDIR', CONFIG.datasets)
CONFIG.datasets.WDIR.description = 'Forecast wind direction @ 10 meters'
CONFIG.datasets.WDIR.units = 'degtrue'
CONFIG.datasets.GUST.copy('WIND', CONFIG.datasets)
CONFIG.datasets.WIND.description = 'Forecast wind speed @ 10 meters'

# forecast filetypes
CONFIG.filetypes.DPT = { 'scope':'month',
       'content':'Forecast hourly dew point temperature',
       'datasets':('DPT','lon','lat','provenance:DPT:timestats'),
       'filename':'%(month)s-NDFD-Dewpoint.h5',
       'source':'NDFD - National Digial Forecast Database', }
CONFIG.filetypes.PCPN = { 'scope':'month',
       'content':'Forecast hourly precipition derived from QPF',
       'datasets':('PCPN','lon','lat','provenance:PCPN:timestats'),
       'filename':'%(month)s-NDFD-Precipitation-(QPF).h5',
       'source':'NDFD - National Digial Forecast Database', }
CONFIG.filetypes.POP12 = { 'scope':'month',
       'content':'Probability of precipition derived from POP12',
       'datasets':('POP','lon','lat','provenance:POP:timestats'),
       'filename':'%(month)s-NDFD-Precipitation-Probability.h5',
       'source':'NDFD - National Digial Forecast Database', }
CONFIG.filetypes.RHUM = { 'scope':'month',
       'content':'Forecast hourly relative humidity',
       'datasets':('RHUM','lon','lat','provenance:RHUM:timestats'),
       'filename':'%(month)s-NDFD-Relative-Humidity.h5',
       'source':'NDFD - National Digial Forecast Database', }
CONFIG.filetypes.TEMP = { 'scope':'month',
       'content':'Forecast hourly temperature',
       'datasets':('TEMP','lon','lat','provenance:TEMP:timestats'),
       'filename':'%(month)s-NDFD-Temperature.h5',
       'source':'NDFD - National Digial Forecast Database', }
CONFIG.filetypes.WIND = { 'scope':'month',
       'content':'Forecast hourly wind components',
       'datasets':('WIND','WDIR','GUST','lon','lat',
                   'provenance:Wind Data:timestats'),
       'filename':'%(month)s-NDFD-Wind.h5',
       'source':'NDFD - National Digial Forecast Database', }

