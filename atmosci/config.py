
import os, sys

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

ATMOSCFG = ConfigObject('atmosci', None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
default = { 'data':'/data2/web-app-data',
            'shared':'/data2/weather-data/shared',
            'static':'/data2/weather-data/shared/grid/static',
            'weather':'/data2/weather-data/shared',
            'working':'/data2/web-app-data' }

# SET THE CONFIGURED dirpath TO THE default DIRECTORY PATHS
ATMOSCFG.dirpaths = default
# only set the following configuration parameter when multiple apps are
# using the same data source file - set it in each application's config
# file - NEVER set it in the default (global) config file.
# CONFIG.dirpaths.source = CONFIG.dirpaths.shared

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# MODES ALLOW FOR DIFFERENT DIRECTORY PATHS FOR DIFFERENT PURPOSES
ATMOSCFG.modes = { 
    'default':{'dirpaths':default,},
    'dev':{'dirpaths':{
           'data':'/Volumes/Transport/data/app_data',
           'shared':'/Volumes/Transport/data/app_data/shared',
           'static':'/Volumes/Transport/data/app_data/shared/grid/static',
           'weather':'/Volumes/Transport/data/app_data/shared',
           'working':'/Volumes/Transport/data'
          },
    },
    'prod':{'dirpaths':default,},
    'test': {'dirpaths':{
             'data':'/Volumes/Transport/data/test_data',
             'shared':'/Volumes/Transport/data/test_data/shared',
             'static':'/Volumes/Transport/data/test_data/shared/grid/static',
             'weather':'/Volumes/Transport/data/test_data/shared',
             'working':'/Volumes/Transport/data'
            },
    },
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# regional coordinate bounding boxes for data and maps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ATMOSCFG.regions = {
         'conus': { 'description':'Continental United States',
                    'data':'-125.00001,23.99999,-66.04165,49.95834',
                    'maps':'-125.,24.,-66.25,50.' },
         'flny': { 'description':'NY Finger Lakes',
                   'data':'-78.0,42.0,-74.5,47.0',
                   'maps':'-77.9,41.9,-74.6,47.1' },
         'NE': { 'description':'NOAA Northeast Region (U.S.)',
                 'data':'-82.75,37.125,-66.83,47.708',
                 'maps':'-82.70,37.20,-66.90,47.60' },
}

