#! /usr/bin/env python

import datetime
import warnings

import numpy as N

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

from atmosci.seasonal.factory import SeasonalStaticFileFactory
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
                        
default = CONFIG.project.source
parser.add_option('-s', action='store', dest='grid_source', default=default,
       help='NRCC grid format to use for datasets (default="%s")' % default)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

text = 'boolean: use UTC timezone for datasets new grid file (default=True).'
text += ' If False, the local timezone will be used. See --localtz option.'
parser.add_option('-u', action='store_false', dest='utc_file', default=True,
       help=text)

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

text = 'name of local timezone used in date args (default=None).'
text += ' If None, the timezone in config.project.local_timezone will'
text += ' be used (currently "%s").' % CONFIG.project.local_timezone
parser.add_option('--localtz', action='store', dest='localtz',
       default=None, help=text)
del text

options, args = parser.parse_args()

num_args = len(args)
if num_args not in (1,2):
    errmsg = '%d arguments passed. Only 1 or 2 arguments are supported.'
    errmsg += '\nUsage: %s'
    raise RuntimeError, errmsg % (num_args, usage)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
local_timezone = options.localtz
periods = ('daily','average')
region_key = options.grid_region
source_key = options.grid_source
target_year = datetime.date.today().year
verbose = options.verbose or debug

threat_key = args[0]
all_datasets = CONFIG.filetypes[threat_key].datasets
threat_datasets = tuple(
    [dsname for dsname in CONFIG.filetypes[threat_key].datasets
                if dsname not in ('lat','lon')]
)

num_args = len(args)
if num_args > 1:
    if args[1].isdigit(): # target year passed
        target_year = int(args[1])
        if num_args == 3: # a single period was also passed
            periods = (args[2],)
    else:  # a single period was passed
        periods = (args[1],)

# get reguired information from static file
factory = SeasonalStaticFileFactory()
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(region_key)
source = factory.sourceConfig(source_key)
reader = factory.staticFileReader(source, region)
lats = reader.getData('lat')
lons = reader.getData('lon')
reader.close()
del reader, factory

# create a factory for disease file access
factory = TurfThreatGridFileFactory(CONFIG)
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(region_key)
source = factory.sourceConfig(source_key)
threat = factory.threatConfig(threat_key)


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


for period_key in periods:
    # get grid file builder
    builder = \
        factory.threatFileBuilder(threat_key, period_key, target_year, source)
    print '\nbuilding grid file for %s %s:\n    %s' % (threat_key, period_key, builder.filepath)

    # create coordinates datasets and build empty datasets
    builder.build(lons=lons, lats=lats)

    builder.open('r')
    date_attrs = builder.dateAttributes()
    print '\nKey attributes of file'
    print '    threat :', builder.fileAttribute('threat')
    print '            ', builder.fileAttribute('description')
    print '    target year :', builder.fileAttribute('target_year')
    print '    key dates :', date_attrs

    for dsname in threat_datasets:
        try:
            date_attrs = builder.dateAttributes(dsname)
        except:
            print '\nERROR: "%s" dataset does not exist' % dsname
        else:
            print '\nKey attributes for "%s" dataset' % dsname
            print '    description :', builder.datasetAttribute(dsname, 'description')
            print '    shape :', builder.datasetShape(dsname)
            print '    dtype :', builder.datasetType(dsname)
            print '    key dates :', date_attrs
    builder.close()


# turn annoying numpy warnings back on
warnings.resetwarnings()

