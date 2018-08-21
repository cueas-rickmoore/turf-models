#! /usr/bin/env python

import os, sys
import datetime
ONE_DAY = datetime.timedelta(days=1)
import PIL

from turftool.maps.factory import TurfMapFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default=None)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
region_key = options.region
verbose = options.verbose or debug

threat_key = args[0]
num_date_args = len(args) - 1

# get the start & end dates
if num_date_args == 1:
    start_date = end_date = datetime.date.today()
elif num_date_args in (3,4,5):
    year = int(args[1])
    month = int(args[2])
    start_date = datetime.date(year,month,int(args[3]))
    if num_date_args == 3: # single day
        end_date = start_date
    elif num_date_args == 4: # end on different day
        end_date = datetime.date(year,month,int(args[4]))
    elif num_date_args == 5: # end at different month and day
        end_date = datetime.date(year,int(args[4]),int(args[5]))
else:
    errmsg = 'Invalid number of date arguments (%d).' % num_date_args
    raise ValueError, errmsg

target_year = start_date.year

# factory for building and accessing map files
map_factory = TurfMapFileFactory()
if dev_mode: map_factory.useDirpathsForMode('dev')
if region_key is None:
    region = map_factory.regionConfig(map_factory.project.region)
else: region = map_factory.regionConfig(region_key)

mapdir_template = \
    map_factory.turfMapFileDir('diseases', threat_key, None, region) 
mapdir_template = mapdir_template.replace('||YEAR||',str(target_year))

mapfile_template = \
    map_factory.turfMapFilename('diseases', threat_key, None, region) 

print 'creating %s animation for %s thru %s' % (threat_key.upper(), 
       start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

def nextImage(num_days, *args):
    date = first_date + datetime.timedelta(days=num_days)
    date_str = date.strftime('%Y%m%d')
    map_dirpath = mapdir_template.replace('||DATE||',date_str)
    if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)
    map_filename = mapfile_template.replace('||DATE||', date_str)
    map_filepath = os.path.join(map_dirpath, map_filename)
    return PIL.Image.open(map_filepath)

num_dates = (end_date - start_date).days + 1
dates = tuple(range(num_dates))

anim = 
