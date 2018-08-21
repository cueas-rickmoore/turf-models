#! /usr/bin/env python

import datetime

from turf.threats.factory import TurfThreatGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import CONFIG, THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

target_year = datetime.date.today().year
usage = '%prog threat dataset lat lon first_day last_day (of current month)'
usage += '\n       %prog threat dataset lat lon month first_day last_day)'
usage += '\n       %prog threat dataset lat lon month day month day)'

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

today = datetime.date.today()
target_year = today.year

threat_key = args[0]
dataset = args[1]
lat = float(args[2])
lon = float(args[3]) * -1

num_date_args = len(args[4:])
if num_date_args == 2:
    month = today.month
    first_day = datetime.date(target_year, month, int(args[4]))
    last_day = datetime.date(target_year, month, int(args[5]))
elif num_date_args in (3,4):
    month = int(args[4])
    first_day = datetime.date(target_year, month, int(args[5]))
    if num_date_args == 4:
        last_day = datetime.date(target_year, int(args[6]), int(args[7]))
    else: last_day = datetime.date(target_year, month, int(args[6]))

print 'first_day :', first_day
print ' last_day :', last_day

# create a factory for disease file access
factory = TurfThreatGridFileFactory(CONFIG)
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(region_key)
threat = factory.threatConfig(threat_key)

reader = factory.threatFileReader(threat_key, target_year, region)

print 'retriveing data for:', lon, lat
print reader.sliceAtNode(dataset, first_day, last_day, lon, lat)




