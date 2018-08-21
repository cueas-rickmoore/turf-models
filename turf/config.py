
import os, sys

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# take advantage of the default seasonal project configuration
# this helps keep common things consistent between projects
from atmosci.seasonal.config import CFGBASE
CONFIG = CFGBASE.copy('config', None)
del CFGBASE

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.dirpaths.project = '/data2/web-app-data/turf'
CONFIG.dirpaths.turf = '/data2/web-app-data/turf'
CONFIG.dirpaths.weather = '/data2/weather-data'
CONFIG.dirpaths.working = '/data2/web-app-data'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CONFIG.modes.dev.dirpaths['project'] = '/Volumes/Transport/data/app_data/turf'
CONFIG.modes.dev.dirpaths['turf'] = '/Volumes/Transport/data/app_data/turf'
CONFIG.modes.dev.dirpaths['weather'] = '/Volumes/Transport/data/app_data'
CONFIG.modes.dev.dirpaths['working'] = '/Volumes/Transport/data/app_data'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# project configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.project.data_timezone = 'UTC'
CONFIG.project.end_day = (10,31)
CONFIG.project.fcast_days = 6
CONFIG.project.local_timezone = 'US/Eastern'
CONFIG.project.obs_days = 15
CONFIG.project.region = 'NE'
CONFIG.project.root = 'turf'
CONFIG.project.source = 'acis'
CONFIG.project.start_day = (3,1)
CONFIG.project.subdir_path = ('%(region)s','%(source)s')
CONFIG.project.target_hour = 7

CONFIG.subdir_paths.turfjson = ('%(region)s','%(year)d','json','%(datatype)s')
