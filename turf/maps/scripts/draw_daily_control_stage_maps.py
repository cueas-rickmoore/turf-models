#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

import PIL
import numpy as N

from nrcc_viz.maps import drawFilledContours, finishMap

from gdd.factory import GDDGridFileFactory

from turftool.maps.factory import TurfMapFileFactory
from turftool.maps.visual import drawScatterMap


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='NE')

parser.add_option('-c', action='store_true', dest='contours', default=False)
parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

contours = options.contours
debug = options.debug
dev_mode = options.dev_mode
region_key = options.region
verbose = options.verbose or debug

threat_key = args[0]

map_factory = TurfMapFileFactory()
if dev_mode: map_factory.useDirpathsForMode('dev')
region = map_factory.regionConfig(region_key)
source = map_factory.sourceConfig('acis')

# configuration for threat
threat = map_factory.configForControl(threat_key)
gdd_threshold = threat.gdd_threshold

today = datetime.date.today()
# get the start & end dates
num_date_args = len(args) - 1
if num_date_args == 0:
    start_date = end_date = today
elif num_date_args == 1:
    year = int(args[1])
    start_date = datetime.date(year, *map_factory.config.project.start_day)
    if year == today.year: end_date = today
    else: end_date = datetime.date(year, *map_factory.config.project.end_day)
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

# make sure that the directories exist before we go too far
for treatment_key, treatment in threat.treatments.items():
    treatment_path = '%s.%s' % (threat.name, treatment_key)
    map_dirpath = map_factory.turfMapDirpath(treatment_path, target_year, region)
    thumb_dirpath = map_factory.turfThumbnailDirpath(treatment_path, target_year, region)

# get the POR file reader
gdd_factory = GDDGridFileFactory()
if dev_mode: gdd_factory.useDirpathsForMode('dev')
gdd_reader = gdd_factory.porFileReader(target_year, source, region)
# lat/lon coords for map
lats = gdd_reader.lats
lons = gdd_reader.lons

# get all date attributes for the dataset as Datetime.Date objects
gdd_dates = gdd_reader.gddDatasetDates('accumulated', gdd_threshold, True)
gdd_reader.close()


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


print 'creating %s maps for %s thru %s' % (threat.name, 
                                           start_date.strftime('%Y-%m-%d'),
                                           end_date.strftime('%Y-%m-%d'))

no_data_config = map_factory.maps.no_threat
thumbnail_shape = map_factory.maps.thumbnail_shape

# make maps for a treatments
for treatment_key, treatment in threat.treatments.items():
    treatment_path = '%s.%s' % (threat.name, treatment_key)
    mapfile_template = map_factory.turfMapFilepath(treatment_path, target_year, region)
    thumbfile_template = map_factory.turfThumbnailFilepath(treatment_path, target_year, region)

    map_options = map_factory.mapOptions(treatment_path, region).attrs
    map_title_template = map_options['title']

    date = start_date
    while date <= end_date:
        file_date_str = date.strftime('%Y%m%d')
        map_filepath = mapfile_template.replace('||DATE||', file_date_str)
        thumb_filepath = thumbfile_template.replace('||DATE||', file_date_str)

        gdd_reader.open()
        gdd = gdd_reader.gddData('accumulated', gdd_threshold, date)
        gdd_reader.close()

        stages = N.zeros(gdd.shape, dtype='<i2')
        for index, threshold in enumerate(treatment.thresholds):
            if threshold > 0:
                where = N.where(gdd >= threshold)
                if len(where[0] > 0): stages[where] = index

        # date-specific map options
        map_date_str = date.strftime('%Y-%m-%d')
        map_options['date'] = map_date_str
        args = { 'date':map_date_str, 'treatment':treatment.fullname }
        map_options['title'] = map_title_template % args
        if debug:
            print '\ncreating %s treatment map for %s' % (treatment_key, map_date_str)
        map_options['finish'] = False

        # map filepath
        map_options['outputfile'] = map_filepath

        if contours:
            options, _map_, fig, axes, fig1, xy_extremes = \
                drawFilledContours(stages, lats, lons, **map_options)
        else:
            options, _map_, fig, axes, fig1, xy_extremes = \
                drawScatterMap(stages, lats, lons, **map_options)

        finishMap(fig, axes, fig1, **map_options)
        print 'created', map_filepath

        image = PIL.Image.open(map_filepath)
        image.thumbnail(thumbnail_shape, PIL.Image.ANTIALIAS)
        print '   thumbnail', thumb_filepath
        image.save(thumb_filepath, 'PNG', quality=100, optimize=True)

        date += ONE_DAY

# turn annoying numpy warnings back on
warnings.resetwarnings()

