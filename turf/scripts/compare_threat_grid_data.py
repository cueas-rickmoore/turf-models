#! /usr/bin/env python

import datetime
import numpy as N

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
parser.add_option('-r', action='store', dest='region', default=default,
       help='NWS region in grid file (default="%s")' % default)

parser.add_option('-s', action='store', dest='suffix', default='-prev',
       help='suffix to append to current filename (default="-prev")')

parser.add_option('-t', action='store', dest='threat_dsname', default='threat',
       help='Name of threat datasset (default="threat")')
                        
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
region_key = options.region
suffix = options.suffix
threat_dsname = options.threat_dsname
verbose = options.verbose or debug

today = datetime.date.today()
target_year = today.year

threat_key = args[0]

# create a factory for disease file access
factory = TurfThreatGridFileFactory(CONFIG)
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(region_key)
threat = factory.threatConfig(threat_key)

reader = factory.threatFileReader(threat_key, target_year, region)
print 'comparing :', reader.filepath
first_valid = reader.dateAttribute(threat_dsname, 'first_valid_date')
last_valid = reader.dateAttribute(threat_dsname, 'last_valid_date')
current_threat = reader.dateSlice(threat_dsname, first_valid, last_valid)
current_risk = reader.dateSlice('risk', first_valid, last_valid)
missing_risk = reader.datasetAttribute('risk', 'missing')
reader.close()
current_risk[N.where(current_risk == missing_risk)] = 0

other_filepath = reader.filepath.replace('.h5', '%s.h5' % suffix)
print 'to :', other_filepath
reader.setFilepath(other_filepath)
reader.open()
other_threat = reader.dateSlice(threat_dsname, first_valid, last_valid)
other_risk = reader.dateSlice('risk', first_valid, last_valid)
missing_risk = reader.datasetAttribute('risk', 'missing')
reader.close()
other_risk[N.where(other_risk == missing_risk)] = 0

threat_diff = current_threat - other_threat
print '\n"%s" dataset differences :' % threat_dsname
print '    min difference =', N.nanmin(threat_diff)
print '    max difference =', N.nanmax(threat_diff)
print '   mean difference =', N.nanmean(threat_diff)

risk_diff = current_risk - other_risk
total = float(N.prod(risk_diff.shape))
max_diff = N.max(risk_diff)+1
min_diff = N.min(risk_diff)
print '\n"risk" dataset differences :'
for n in range(min_diff, max_diff):
    count = len(N.where(risk_diff == n)[0])
    percent = (count / total) * 100
    print '   diff == %d @ %d (%.2f%%)' % (n, count, percent)

print '\n"risk" values counts :'
message = '    risk = %d : before = %8d : after = %6d'
for n in range(3):
    before = len(N.where(other_risk == n)[0])
    after = len(N.where(current_risk == n)[0])
    print message % (n, before, after)

