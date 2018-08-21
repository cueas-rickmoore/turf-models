
import numpy as N

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.config import CONFIG as CFGBASE
CONFIG = CFGBASE.copy('config', None)
del CFGBASE

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

project = CONFIG.project
project.data_timezone = 'US/Eastern'
project.gdd_thresholds = [32,50]
project.control_json_template = '{"name":"%(control)s","group":"controls","dates":%(dates)s,"location":{"lon":%(lon)s,"lat":%(lat)s},"data":%(data)s}'
    
CONFIG.controls = {
    'dandelion': {
        'description':'Prevention of Dandelion Bud Development in Turf Grass',
        'fullname':'Dandelion',
        'gdd_threshold':50,
        'group':'treatment',
        'treatments':{
            'amine': {
                'description':'Amine',
                'stages':['early','marginal','favorable'],
                'thresholds':(0,150,180),
            },
            'ester': {
                'description':'Ester',
                'stages':['early','marginal','favorable'],
                'thresholds':(0,130,145),
            },
        },
    },
    'seedhead': {
        'description':'Prevention of Seedhead Development in Turf Grass',
        'fullname':'Seedhead',
        'gdd_threshold':32,
        'group':'treatment',
        'treatments':{
            'embark': {
                'description':'Embark',
                'stages':['early','ideal','marginal','late'],
                'thresholds':(0,350,450,650),
            },
            'proxy': { 
                'description':'Proxy',
                'stages':['early','ideal','marginal','late'],
                'thresholds':(0,200,300,500),
            },
        },
    },
}


CONFIG.datasets.gdd32 = CONFIG.datasets.dategrid.copy()
CONFIG.datasets.gdd32.description = 'Accumulated Base 32 Growing Degree Days'

CONFIG.datasets.gdd50 = CONFIG.datasets.dategrid.copy()
CONFIG.datasets.gdd50.description = 'Accumulated Base 50 Growing Degree Days'

CONFIG.dirpaths.project = '/data2/weather-data/gdd'

CONFIG.filenames.gddapp = '%(year)d-GDD-ACIS-HiRes-Daily.h5'
CONFIG.filenames.gdd = '%(year)s-Accumulated-GDD.h5'
CONFIG.filenames.json = '%(year)s-%(node)s-%(control)s.json'

CONFIG.filetypes.gdd = { 
       'scope':'year', 'period':'date', 
       'datasets':('lon','lat','gdd32','gdd50'),
       'description':'Growing Degree Days for turf grass management app.',
       'start_day':(3,1), 'end_day':(10,31)
}

CONFIG.subdir_paths.gdd = ('%(region)s','%(year)d','grids')
CONFIG.subdir_paths.gddapp = ('gdd','%(region)s','acis_hires','por')
CONFIG.subdir_paths.json = ('%(region)s','%(year)d','json','%(control)s')
CONFIG.subdir_paths.maps = ('%(region)s','%(year)d','maps','%(control)s')

