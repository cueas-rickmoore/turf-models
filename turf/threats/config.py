
import numpy as N

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.config import CONFIG as CFGBASE
CONFIG = CFGBASE.copy('config', None)
del CFGBASE

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

COMMON = ConfigObject('common', None)
COMMON.project = {
    'fcast_days': 6, # number of days in file for forecast risk
    'obs_days': 7, # number of days in file for observed risk
    # a day begins at 8AM and ends at 7AM the next day
    'target_hour': 7,
    'diseases': ('anthrac','bpatch','dspot','pblight'),
}
CONFIG.merge(COMMON.project)

CONFIG.datasets.risk = {
    'description':'%(threat)s risk level',
    'dtype':int,
    'dtype_packed':'<i2',
    'compression':'gzip',
    'chunks':('num_days',1,1),
    'missing_data':-999,
    'missing_packed':-999,
    'period':'date',
    'scope':'season',
    'view':('time','lat','lon'),
}

CONFIG.datasets.stress = {
    'description': 'Number of hours in stress',
    'dtype':'<i2',
    'dtype_packed':'<i2',
    'compression':'gzip',
    'chunks':('num_days',1,1),
    'missing_data':-999,
    'missing_packed':-999,
    'period':'date',
    'scope':'season',
    'view':('time','lat','lon'),
}

CONFIG.datasets.threat = {
    'description':'%(threat)s threat index',
    'dtype':float,
    'dtype_packed':float,
    'compression':'gzip',
    'chunks':('num_days',1,1),
    'missing_data':N.nan,
    'missing_packed':N.nan,
    'period':'date',
    'scope':'season',
    'view':('time','lat','lon'),
}

CONFIG.filenames = {
    'average':'%(year)s-%(threat)s-Average-Risk.h5',
    'daily':'%(year)s-%(threat)s-Daily-Risk.h5',
    'threats':'%(year)s-%(threat)s-Daily-Risk.h5',
    'threatjson':'%(year)s-%(node)s-%(threat)s-Risk.json',
}

CONFIG.filetypes.anthrac = {
    'scope':'season', 'period':'date', 
    'datasets':('lat','lon','threat','risk'),
    'description':'Risk of Anthracnose disease in Turf Grass',
    'threat':'Anthracnose',
}

CONFIG.filetypes.bpatch = {
    'scope':'season', 'period':'date', 
    'datasets':('lat','lon','threat','risk'),
    'description':'Risk of Brown Patch disease in Turf Grass',
    'threat':'Brown Patch',
}

CONFIG.filetypes.dspot = {
    'scope':'season', 'period':'date', 
    'datasets':('lat','lon','threat','risk'),
    'description':'Risk of Dollarspot disease in Turf Grass',
    'threat':'Dollarspot',
}

CONFIG.filetypes.hstress = {
    'scope':'season', 'period':'date', 
    'datasets':('lat','lon','stress','risk'),
    'description':'Risk for Heat Stress in Turf Grass',
    'threat':'Heat Stress',
}

CONFIG.filetypes.pblight = {
    'scope':'season', 'period':'date', 
    'datasets':('lat','lon','threat','risk'),
    'description':'Risk of Pythium Blight disease in Turf Grass',
    'threat':'Pythium Blight',
}

CONFIG.subdir_paths.threats = ('%(region)s','%(year)d','grids')
CONFIG.subdir_paths.turfjson = ('%(region)s','%(year)d','json','%(threat)s')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

THREATS = ConfigObject('threats', None)
THREATS.json_template = '{"name":"%(name)s","group":"threats","dates":%(dates)s,"location":{"lon":%(lon)s,"lat":%(lat)s},"data":%(data)s}'

# padding = number of hours required prior to target_hour of first day
THREATS.anthrac = {
    'fullname':'Anthracnose', 
    'day_begins':8, # a day begins at 8AM and ends at 7AM the next day
    'default_period':'daily',
    'min_precip':0.01, # minimum valid precip for counting leaf wetness
    'offset':0, # amount of time to skip before beginning calcs
    # padding = number of hours required before first day in result
    # 'padding':3*24, # 3 days for threat index averaging
    'periods': {
        'daily': {
             'coverage':'3 day average',
             'num_days':1, # each day already is 3 day average index components
             'padding':2*24, # 3 days for threat index averaging
             'risk_thresholds':(0.4, 1.5), # 3 day thresholds
        },
        'average': {
             'coverage':'7 day average',
             'num_days':7, # 7 day average of 3 day threat index components
             # 7 day average ??? plus another 3 day cushion for index
             'padding':8*24, # ???
             #'padding':7*24, # ???
             'risk_thresholds':(0.4, 1.5), # 7 day thresholds
        },
    },
    'timespan':72, # 3 days * 24
    'timestep':24, 
    'units': { 'dpt':'C', 'pcpn':'in', 'tmp':'C' },
    'weather':{'temps':('TMP','DPT'),'wetness':('PCPN',)},
    'wet_count_avg':3,
    'wet_function':'EQ',
    'wet_threshold':1,
}

THREATS.bpatch = {
    'fullname':'Brown Patch',
    'day_begins':8, # a day begins at 8AM and ends at 7AM the next day
    'default_period':'daily',
    'min_precip':0.01, # minimum valid precip for counting leaf wetness
    'offset':0, # amount of time to skip before beginning calcs
    # padding = number of hours required before first day in result
    # 'padding':3*24, # 3 days for threat index averaging
    'periods': {
        'daily': {
             'coverage':'3 day average',
             'num_days':3, # 3 day average of threat indexes
             'padding':2*24, # 3 days for threat index averaging
             'risk_thresholds':(0.3, 0.9), # 3 day thresholds
        },
        'average': {
             'coverage':'7 day average',
             'num_days':7, # 7 day average of threat indexes
             'padding':6*24, # 7 days for threat index averaging
             'risk_thresholds':(0.4, 0.9), # 7 day thresholds
        },
    },
    'rh_threshold':95,
    'season': { 'end_day':(9,30), 'start_day':(7,1) },
    'timespan':24,
    'timestep':24,
    'units': { 'dpt':'C', 'tmp':'C', 'pcpn':'in' },
    'weather':{'temps':('TMP','DPT'),'wetness':('PCPN','RHUM')},
    'wet_function':'GT',
    'wet_threshold':0,
}

THREATS.dspot = {
    'fullname':'Dollarspot',
    'count_thresholds':{ # minimum values for counts
         'consec_rain':2,
         'rain_count':0,
         'rh_component':3,
         'wet_count':1,
    },
    'day_begins':8, # a day begins at 8AM and ends at 7AM the next day
    'default_period':'daily',
    'min_precip':0.01, # minimum valid precip for counting leaf wetness
    # padding = number of hours required before first day in result
    # need 7 days to handle consecutive day variables
    # also add another 2 day cushion for threat index averaging
    #'padding':9*24, # 9 days
    'offsets':{ # amount of time to skip before beginning calcs
         'consec_rain':1, # skip 1 day
         'maxrh_avgt_count':0,
         'rain_count':0,
         'rh_component':0,
         'rh_factors':0,
         'threat':0,
         'wet_count':96, # skip 4 days * 24 hours
    },
    'periods': {
        'daily': {
             'coverage':'3 day average',
             'num_days':3, # 3 day average of threat indexes
             # need 7 days to handle consecutive day variables
             # also add another 1 day cushion for threat index averaging
             'padding':8*24, # 8 days for threat index averaging
             'risk_thresholds':(0.4, 0.7), # 3 day thresholds
        },
        'average': {
             'coverage':'7 day average',
             'num_days':7, # 7 day average of threat indexes
             # need 7 days to handle consecutive day variables
             # also add another 5 day cushion for threat index averaging
             'padding':12*24, # 12 days for threat index averaging
             'risk_thresholds':(0.4, 0.7), # 7 day thresholds
        },
    },
    'timespans':{ # amount of time to include in calculations
         # 5 consecutive days (not including current day)
         'consec_rain':5, # based on daily rain_count
         'maxrh_avgt_count':7, # 7 days
         'rain_count':24, # 24 hours
         'rh_component':1,
         'rh_factors':24, # # 24 hours
         'threat':3, # 3 days
         'wet_count':72, # 3 days * 24 hours
    },
    'timesteps':{ # incremental time between calculations
         'consec_rain':1, # 1 day
         'maxrh_avgt_count':1, # 1 day
         'rain_count':24, # 24 hours
         'rh_component':1, # 1 day
         'rh_factors':24, # 24 hours
         'threat':1, # 1 day
         'wet_count':24, # 24 hours
    },
    'weather':{'temps':('TMP',),'wetness':('PCPN','RHUM')},
}

THREATS.hstress = {
    'fullname':'Heat Stress',
    'coverage':'3 day average',
    'day_begins':8, # a day begins at 8AM and ends at 7AM the next day
    # 'default_period':'daily',
    'default_period':3,
    'offset':11, # 11 hours to get to 8PM
    'padding':0, # 1 day
    # actual level 1 risk is stress hours >=2 and < 5
    # since stress hours is an int, we use > 1 and < 5
    'risk_thresholds':(0, 1, 5),
    'stress_thresholds':{ 'temp':70, 'rhum':150 },
    'timespan':12, # 12 hours over night (8pm to 7AM)
    'timestep':24,
    'weather':{'temps':('TMP',),'wetness':('RHUM',)},
}

THREATS.pblight = {
    'fullname':'Pythium Blight',
    'day_begins':8, # a day begins at 8AM and ends at 7AM the next day
    'default_period':'daily',
    'offset':0, # amount of time to skip before beginning calcs
    # padding = number of hours required before first day in result
    # 'padding':3*24, # 3 days for threat index averaging
    'periods': {
        'daily': {
             'coverage':'3 day average',
             'num_days':3, # 3 day average of threat indexes
             'padding':2*24, # 3 days for threat index averaging
             'risk_thresholds':(0.4, 3.6), # 3 day thresholds
        },
        'average': {
             'coverage':'7 day average',
             'num_days':7, # 7 day average of threat indexes
             'padding':6*24, # 7 days for threat index averaging
             'risk_thresholds':(0.4, 3.6), # 7 day thresholds
        },
    },
    'timespan':24,
    'timestep':24,
    'weather':{'temps':('TMP',),'wetness':('RHUM',)},
}

