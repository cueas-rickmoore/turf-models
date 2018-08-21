#! /usr/bin/env python

import datetime
ONE_DAY = datetime.timedelta(days=1)

from turf.threats.factory import TurfThreatGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import CONFIG, THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

target_year = datetime.date.today().year
text = '%%prog threat [year]\n\nWhere threat = one of %s'
text += '\nand default value for year = %d'
usage = text % (str(sorted(THREATS.keys())).replace(' ',''),target_year)

from optparse import OptionParser
parser = OptionParser(usage)

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

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
region_key = options.grid_region
verbose = options.verbose or debug

threat_key = args[0]
period = args[1]
new_date = datetime.date(*[int(arg) for arg in args[2:]])
if threat_key == 'hstess':
    datasets = ('stress', 'risk')
else: datasets = ('threat', 'risk')

# create a factory for disease file access
factory = TurfThreatGridFileFactory(CONFIG)
if dev_mode: factory.useDirpathsForMode('dev')
threat_name = factory.threatName(threat_key)

# get grid file builder
manager = factory.threatFileManager(threat_key, period, new_date.year)
manager.close()
msg = '\nAttempting to repair obs dates in %s %s threat/risk file :\n%s'
print msg % (threat_name, period.title(), manager.filepath)

for dataset in datasets:
    manager.open('r')
    fcast_start_date = manager.dateAttribute(dataset, 'fcast_start_date', None)
    last_valid_date = manager.dateAttribute(dataset, 'last_valid_date', None)
    last_obs_date = manager.dateAttribute(dataset, 'last_obs_date', None)
    print '\nBefore repairs to %s dataset:' % dataset
    print '    last_obs_date :', last_obs_date
    print '    rtma_end_date :', manager.dateAttribute(dataset, 'rtma_end_date')
    print ' fcast_start_date :', fcast_start_date
    print '  last_valid_date :', last_valid_date
    manager.close()

    manager.open(mode='a')
    manager.setDateAttribute(dataset, 'last_obs_date', new_date)    
    manager.setDateAttribute(dataset, 'rtma_end_date', new_date)
    if fcast_start_date is None:
        if last_valid_date is None or last_valid_date > new_date:
            manager.setDateAttribute(dataset, 'last_valid_date', new_date)
    else:
        manager.setDateAttribute(dataset, 'fcast_start_date', new_date+ONE_DAY)
        if last_valid_date is None or new_date > last_valid_date:
            manager.setDateAttribute(dataset, 'last_valid_date', new_date)
    manager.close()

    print '\nAfter repairs to %s dataset:' % dataset
    manager.open(mode='r')
    print '    last_obs_date :', manager.dateAttribute(dataset, 'last_obs_date')
    print '    rtma_end_date :', manager.dateAttribute(dataset, 'rtma_end_date')
    print ' fcast_start_date :', manager.dateAttribute(dataset, 'fcast_start_date')
    print '  last_valid_date :', manager.dateAttribute(dataset, 'last_valid_date')
    manager.close()

