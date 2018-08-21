#! /usr/bin/env python

import datetime
import warnings

from turf.weather.factory import TurfWeatherFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

usage = '%prog weather [OPTIONS] (build file for current month in current year)'
usage += '\n    %prog weather month [OPTIONS] (build file for month in current year)'
usage += '\n    %prog weather year month [OPTIONS] (build file for year/month)'

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-r', action='store', dest='grid_region', default='NE',
       help='NWS region in grid file (default="NE")')
                        
parser.add_option('-s', action='store', dest='grid_source', default='acis',
       help='NRCC grid format to use for datasets (default="acis")')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

text = 'boolean: use UTC timezone for datasets new grid file (default=True).'
text += ' If False, the local timezone will be used. See --localtz option.'
parser.add_option('-u', action='store_false', dest='utc_file', default=True,
       help=text)
del text

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

options, args = parser.parse_args()

num_date_args = len(args) - 1
if num_date_args not in (0,1,2):
    errmsg = '%d date arguments passed. 0, 1 or 2 arguments are supported.'
    errmsg += '\nUsage: %s'
    raise RuntimeError, errmsg % (num_date_args, usage)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
periods = ('daily','average')
region_key = options.grid_region
source_key = options.grid_source
verbose = options.verbose or debug

weather_key = args[0]

if num_date_args == 0 :
    target = datetime.date.today()
    target_year = target.year
    target_month = target.month
elif num_date_args == 1 :
    target_year = datetime.date.today().year
    target_month = int(args[1])
elif num_date_args == 2:
    target_year = int(args[1])
    target_month = int(args[2])

# create a factory for disease file access
factory = TurfWeatherFileFactory()
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(region_key)
source = factory.sourceConfig(source_key)

print '\nBuilding weather grid file for "%s"' % weather_key

# tell factory what to build
builder = factory.buildWeatherFile(weather_key, target_year, target_month,
                                   region, source, 'UTC')

# build was a success
builder.open('r')
print 'Created weather grid file :\n    ', builder.filepath
print '\nKey attributes of file :'
for key, value in builder.fileAttributes().items():
    print '   %s : %s' % (key, str(value))
if debug:
    for dataset in builder.config.filetypes[weather_key].datasets:
        if not dataset in ('lat','lon'):
            print '\nAttributes of %s dataset :' % dataset
            for key, value in builder.datasetAttributes(dataset).items():
                print '   %s : %s' % (key, str(value))
builder.close()

