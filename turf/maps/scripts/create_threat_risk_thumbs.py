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

dirpath_template = map_factory.turfMapDirpath(threat_key, None, region) 
map_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)

mapfile_template = map_factory.turfMapFilename(threat_key, None, region)

dirpath_template = map_factory.turfThumbnailDirpath(threat_key, None, region) 
thumbnail_dirpath = dirpath_template.replace('||YEAR||',str(target_year))
if not os.path.exists(thumbnail_dirpath): os.makedirs(thumbnail_dirpath)

thumbfile_template = map_factory.turfThumbnailFilename(threat_key, None, region)

thumbnail_shape = map_factory.maps.thumbnail_shape

print 'creating %s thumbnails for %s thru %s' % (threat_key.upper(), 
       start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

date = start_date
while date <= end_date:
    # get map filepath for this date
    date_str = date.strftime('%Y%m%d')
    map_filename = mapfile_template.replace('||DATE||', date_str)
    map_filepath = os.path.join(map_dirpath, map_filename)

    # get filepath for generate thumbnail
    thumbnail_filename = thumbfile_template.replace('||DATE||', date_str)
    thumbnail_filepath = os.path.join(thumbnail_dirpath, thumbnail_filename)

    image = PIL.Image.open(map_filepath)
    image.thumbnail(thumbnail_shape, PIL.Image.ANTIALIAS)
    print '   saving', thumbnail_filepath
    image.save(thumbnail_filepath, 'PNG', quality=100, optimize=True)

    date += ONE_DAY

