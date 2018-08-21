#! /usr/bin/env python

import datetime
import warnings

import numpy as N

from turf.threats.factory import TurfThreatGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def seekFirstDate(manager, dataset_path, debug):
    # get all psssible dates for the dataset (those unset will be None)
    manager.open('r')
    dates = manager.allPossibleDates(dataset_path)
    if debug:
        print 'seekFirstDate for', dataset_path
        print dates
    date = dates.get('first_valid_date', None)
    if date is not None:
        print 'first_valid_date already in file :', date
        manager.close()
        return True, date

    # there is no available data unless last_valid_date has been set
    if dates['last_valid_date'] is None:
        manager.close()
        return None

    start_date = dates['start_date']
    end_date = dates['last_valid_date']

    missing = manager.datasetAttribute(dataset_path, 'missing')
    if debug: 'missing value :', missing

    if N.isnan(missing):
        def numMissing(data):
            return len(N.where(N.isnan(data))[0])
    else:
        def numMissing(data): return len(N.where(data == missing)[0])

    data = manager.dateSlice(dataset_path, start_date, end_date)
    manager.close()

    num_days = data.shape[0]
    num_nodes = N.product(data.shape[1:])

    day = 0
    while day < num_days:
        num_missing = numMissing(data[day,:,:])
        if num_missing < num_nodes:
            del data
            if day > 0: start_date += datetime.timedelta(days=day)
            return False, start_date
        day += 1


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def seekLastDate(manager, dataset_path, debug):
    # get all psssible dates for the dataset (those unset will be None)
    manager.open('r')
    end_date = manager.dateAttribute(dataset_path, 'end_date')
    last_valid = manager.dateAttribute(dataset_path, 'last_valid_date')
    if last_valid == end_date: return None

    missing = manager.datasetAttribute(dataset_path, 'missing')
    if debug:
        print 'seekLastDate for', dataset_path
        print '   last_valid :', last_valid
        print '     end_date :', end_date
        print 'missing value :', missing
        
    if N.isnan(missing):
        def numMissing(data): return len(N.where(N.isnan(data))[0])
    else:
        def numMissing(data): return len(N.where(data == missing)[0])

    start_date = manager.dateAttribute(dataset_path, 'start_date')
    data = manager.dateSlice(dataset_path, start_date, end_date)
    manager.close()

    num_days = data.shape[0]
    num_nodes = N.product(data.shape[1:])

    day = end_day = num_days - 1
    while day > 0:
        num_missing = numMissing(data[day,:,:])
        if num_missing < num_nodes:
            del data
            if day < end_day: end_date -= datetime.timedelta(days=day)
            return False, end_date
        day -= 1


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import CONFIG, THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

target_year = datetime.date.today().year
text = '%%prog threat [year]\n\nWhere threat = one of %s'
text += '\nand default value for year = %d'
usage = text % (str(sorted(THREATS.keys())).replace(' ',''),target_year)

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-f', action='store', dest='date_to_fix', default='first')
parser.add_option('-p', action='store', dest='period', default='daily')

default = CONFIG.project.region
parser.add_option('-r', action='store', dest='grid_region', default=default,
       help='NWS region in grid file (default="%s")' % default)
                        
parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

options, args = parser.parse_args()

num_args = len(args)
if num_args not in (1,2):
    errmsg = '%d arguments passed. Only 1 or 2 arguments are supported.'
    errmsg += '\nUsage: %s'
    raise RuntimeError, errmsg % (num_args, usage)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

date_to_fix = options.date_to_fix
debug = options.debug
dev_mode = options.dev_mode
period = options.period
region_key = options.grid_region
verbose = options.verbose or debug

threat_key = args[0]

num_args = len(args)
if num_args == 2: target_year = int(args[1])

# create a factory for disease file access
factory = TurfThreatGridFileFactory(CONFIG)
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(region_key)
threat = factory.threatConfig(threat_key)


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


# get grid file builder
manager = factory.threatFileManager(threat_key, period, target_year, region)
msg = '\nAttempting to repair first_valid date in %s threat/risk file :\n%s'
print msg % (threat.fullname, manager.filepath)
manager.close()

datasets = CONFIG.filetypes[threat_key].datasets
datasets_names = tuple([dsname for dsname in datasets
                               if dsname not in ('lat','lon')])

if date_to_fix == 'first':
    for dsname in datasets_names:
        result = seekFirstDate(manager, dsname, debug)
        if result is not None:
            present, first_date = result
            if not present:
                changed = '    setting "first_valid_date" in %s to %s'
                print changed % (dsname, str(first_date))
                manager.open(mode='a')
                manager.setDateAttribute(dsname, 'first_valid_date', first_date)    
                manager.close()

elif date_to_fix == 'last':
    for dsname in datasets_names:
        result = seekLastDate(manager, dsname, debug)
        if result is not None:
            present, last_date = result
            if not present:
                changed = '    setting "last_valid_date" in %s to %s'
                print changed % (dsname, str(last_date))
                manager.open(mode='a')
                manager.setDateAttribute(dsname, 'last_valid_date', last_date)    
                manager.close()

