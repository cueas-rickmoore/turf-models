#! /usr/bin/env python

import os

import datetime
ONE_DAY = datetime.timedelta(days=1)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
verbose = options.verbose or debug

today = datetime.date.today()
# get the start & end dates
num_date_args = len(args)
if num_date_args == 0:
    start_date = end_date = today
elif num_date_args == 1:
    year = int(args[0])
    start_date = datetime.date(year, *map_factory.config.project.start_day)
    if year == today.year: end_date = today
    else: end_date = datetime.date(year, *map_factory.config.project.end_day)
elif num_date_args in (3,4,5):
    year = int(args[0])
    month = int(args[1])
    start_date = datetime.date(year,month,int(args[2]))
    if num_date_args == 3: # single day
        end_date = start_date
    elif num_date_args == 4: # end on different day
        end_date = datetime.date(year,month,int(args[3]))
    elif num_date_args == 5: # end at different month and day
        end_date = datetime.date(year,int(args[3]),int(args[4]))
else:
    errmsg = 'Invalid number of date arguments (%d).' % num_date_args
    raise ValueError, errmsg

# make maps for a treatments
for treatment in ('Amine','Ester'):
    map_dirpath = "/Volumes/Transport/data/app_data/turf/NE/2017/maps/Dandelion/%s/" % treatment
    old_mapfile = '-Dandelion-%s-Map.png' % treatment
    new_mapfile = '-%s-Dandelion-Control-Map.png' % treatment

    thumb_dirpath = "/Volumes/Transport/data/app_data/turf/NE/2017/thumbs/Dandelion/%s/" % treatment
    old_thumbfile = '-Dandelion-%s-Control-Thumbnail.png' % treatment
    new_thumbfile = '-%s-Dandelion-Control-Thumbnail.png' % treatment

    date = start_date
    while date <= end_date:
        date_str = date.strftime('%Y%m%d')
        print date_str

        old_path = map_dirpath + date_str + old_mapfile
        new_path = map_dirpath + date_str + new_mapfile
        if os.path.isfile(old_path):
            if debug: print '\nrenaming map\n', old_path, '\nto\n', new_path
            os.rename(old_path, new_path)

        old_path = thumb_dirpath + date_str + old_thumbfile
        new_path = thumb_dirpath + date_str + new_thumbfile
        if os.path.isfile(old_path):
            if debug: print '\nrenaming thumbnail :\n', old_path, '\nto\n', new_path
            os.rename(old_path, new_path)

        date += ONE_DAY

