#! /usr/bin/env python

import os, sys
import warnings

import datetime
SCRIPT_START_TIME = datetime.datetime.now()
ONE_DAY = datetime.timedelta(days=1)
TODAY = datetime.date.today()

import PIL
import numpy as N

from atmosci.utils.timeutils import elapsedTime

from turf.controls.factory import TurfControlsFactory
from turf.maps.factory import TurfMapFileFactory
from turf.maps.visual import drawScatterMap, finishMap

def dateStr(date_obj): return date_obj.strftime('%Y-%m-%d')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-c', action='store', dest='control', default=None)
parser.add_option('-p', action='store', type=int, dest='max_previous', default=7)
parser.add_option('-r', action='store', dest='region', default='NE')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

debug = options.debug
dev_mode = options.dev_mode
max_previous = options.max_previous
region_key = options.region
verbose = options.verbose or debug

year = TODAY.year
month = TODAY.month

num_date_args = len(args)
if num_date_args == 0:
    # go back from current day until the last map made, then
    # make all maps beginning max_backwards dayas from there
    requested_start = None
    requested_end = None

# build maps for particular dates
elif num_date_args == 1:
    if 'd' in args[0]:
        requested_start = requested_end = datetime.date(year, month, int(args[0].replace('d','')))
    else:
        requested_start = datetime.date(year, month, int(args[0]))
        requested_end = None

elif num_date_args == 2:
    requested_start = datetime.date(year, month, int(args[0]))
    requested_end = datetime.date(year, month, int(args[1]))

elif num_date_args == 3:
    month = int(args[0])
    requested_start = datetime.date(year, month, int(args[1]))
    requested_end = datetime.date(year, month, int(args[2]))

elif num_date_args == 4:
    arg_0 = int(args[0])
    if arg_0 > 99:
        month = int(args[1])
        requested_start = datetime.date(arg_0, month, int(args[2]))
        requested_end = datetime.date(arg_0, month, int(args[3]))
    else:
        requested_start = datetime.date(year, arg_0, int(args[1]))
        requested_end = datetime.date(year, int(args[2]), int(args[3]))

elif num_date_args == 5:
    year = int(args[0])
    requested_start = datetime.date(year, int(args[1]), int(args[2]))
    requested_end = datetime.date(year, int(args[3]), int(args[4]))

else:
    errmsg = 'Invalid number of date arguments (%d).' % num_date_args
    raise ValueError, errmsg


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def findPreviousMap(factory, map_path_key, min_possible_date, end_date):
    season = end_date.year
    test_date = end_date
    while test_date > min_possible_date:
        filepath = factory.turfMapFilepath(map_path_key, test_date, region)
        if os.path.exists(filepath): return test_date
        test_date -= ONE_DAY
    return min_possible_date


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawControlStageMaps(threat, treatment, data_factory, map_factory, region, start_date,
                         end_date, max_previous, use_cicss_gdd, verbose, debug):
    
    MAPS_START_TIME = datetime.datetime.now()
    
    threat_key = threat.name
    treatment_key = treatment.name
    map_path_key = '%s.%s' % (threat_key, treatment_key)

    # configuration for control treatment
    control_config = map_factory.controlMapConfig(threat_key, treatment_key)
    treatment_thresholds = control_config[treatment_key].thresholds
    gdd_threshold = control_config.gdd_threshold
    gdd_dataset = 'gdd%d.accumulated' % gdd_threshold
    del control_config

    # no date args, find start and end dates
    if start_date is None:
        gdd_reader = data_factory.gddFileReader(TODAY.year, region, use_cicss_gdd=use_cicss_gdd)
        if end_date is None:
            end_date = gdd_reader.dateAttribute(gdd_dataset, 'last_valid_date', None)
            if end_date is None:
                print 'No valid %s data in file :\n%s' % gdd_reader.filepath
                print '\nExecution terminated.'
                gdd_reader.close()
                exit()

        print 'BEFORE:'
        print '    start_date :', start_date
        print '      end_date :', end_date

        # now find the date to start making maps
        min_possible_date = gdd_reader.dateAttribute(gdd_dataset, 'first_valid_date',
                                       gdd_reader.dateAttribute(gdd_dataset, 'start_date'))
        start_date = findPreviousMap(map_factory, map_path_key, min_possible_date, end_date)
        diff_in_days = (start_date - min_possible_date).days
        if diff_in_days >= max_previous:
            start_date -= datetime.timedelta(days=max_previous)
        else: start_date = min_possible_date

        print 'AFTER:'
        print '    start_date :', start_date
        print '      end_date :', end_date

    # start date was specified
    else:
        gdd_reader = data_factory.gddFileReader(TODAY.year, region, use_cicss_gdd=use_cicss_gdd)
        # when end date is not specfied, it should be the last_valid_date in the file
        if end_date is None:
            end_date = gdd_reader.dateAttribute(gdd_dataset, 'last_valid_date', None)
            if end_date is None:
                print 'No valid %s data in file :\n%s' % gdd_reader.filepath
                print '\nExecution terminated.'
                gdd_reader.close()
                exit()

    if debug: print 'reading data from :\n', gdd_reader.filepath
    gdd_reader.close()

    info = (treatment.description, threat.fullname, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print 'Creating %s %s control maps for %s thru %s' % info

    target_year = start_date.year
    target_year_str = str(target_year)

    # map options and templates
    map_options = map_factory.mapOptions(map_path_key).attrs
    mapfile_template = map_factory.turfMapFilename(map_path_key, None, region)
    map_title_template = map_options['title'] % {'treatment':treatment.description,}

    dirpath_template = map_factory.turfMapDirpath(map_path_key, None, region) 
    map_dirpath = dirpath_template.replace('||YEAR||',target_year_str)
    if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)

    thumbnail_shape = map_factory.maps.thumbnail_shape
    thumbfile_template = map_factory.turfThumbnailFilename(map_path_key, None, region)

    dirpath_template = map_factory.turfThumbnailDirpath(map_path_key, None, region) 
    thumb_dirpath = dirpath_template.replace('||YEAR||',target_year_str)
    if not os.path.exists(thumb_dirpath): os.makedirs(thumb_dirpath)

    no_data_config = map_factory.maps.no_threat


    # filter annoying numpy warnings
    warnings.filterwarnings('ignore',"All-NaN axis encountered")
    warnings.filterwarnings('ignore',"All-NaN slice encountered")
    warnings.filterwarnings('ignore',"invalid value encountered in greater")
    warnings.filterwarnings('ignore',"invalid value encountered in less")
    warnings.filterwarnings('ignore',"Mean of empty slice")
    # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


    # lat/lon coords are the same for all maps
    gdd_reader.open()
    lats = gdd_reader.lats
    lons = gdd_reader.lons
    # get all date attributes for the dataset as Datetime.Date objects
    gdd_dates = gdd_reader.dateAttributes(gdd_dataset, True)
    gdd_reader.close()
    # make maps for treatment

    maps = 0
    date = start_date
    while date <= end_date:
        file_date_str = date.strftime('%Y%m%d')
        map_filename = mapfile_template.replace('||DATE||', file_date_str)
        map_filepath = os.path.join(map_dirpath, map_filename)

        gdd_reader.open()
        gdd = gdd_reader.dataForDate(gdd_dataset, date)
        gdd_reader.close()

        stages = N.zeros(gdd.shape, dtype='<i2')
        for index, threshold in enumerate(treatment_thresholds):
            if threshold > 0:
                where = N.where(gdd >= threshold)
                if len(where[0] > 0): stages[where] = index

        # date-specific map options
        map_date_str = date.strftime('%Y-%m-%d')
        map_options['date'] = map_date_str
        args = { 'date':map_date_str, 'treatment':treatment.description }
        map_options['title'] = map_title_template % args
        if debug:
            print '\ncreating %s treatment map for %s' % (treatment_key, map_date_str)
        map_options['finish'] = False

        # map filepath
        map_options['outputfile'] = map_filepath

        options, _map_, fig, axes, fig1, xy_extremes = \
                 drawScatterMap(stages, lats, lons, **map_options)

        finishMap(fig, axes, fig1, **map_options)
        if verbose: print '    ', map_filepath
        else: print '    ', map_filename

        thumb_filename = thumbfile_template.replace('||DATE||', file_date_str)
        thumb_filepath = os.path.join(thumb_dirpath, thumb_filename)
        image = PIL.Image.open(map_filepath)
        image.thumbnail(thumbnail_shape, PIL.Image.ANTIALIAS)
        if debug: print '    ', thumb_filepath
        image.save(thumb_filepath, 'PNG', quality=100, optimize=True)

        date += ONE_DAY
        maps += 1

    # turn annoying numpy warnings back on
    warnings.resetwarnings()

    info = (maps, start_date, end_date)
    print '\nProcessed maps for %d days : %s thru %s' % info
    elapsed_time = elapsedTime(MAPS_START_TIME, True)
    info = (treatment.description, threat.fullname, elapsed_time)
    print 'Completed %s %s control maps in %s' % info

    return maps


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# factory for accessing data for maps
data_factory = TurfControlsFactory()
if dev_mode: data_factory.useDirpathsForMode('dev')
if options.control is None:
    controls = data_factory.config.controls.items()
else: controls = { options.control : data_factory.config.controls[options.control], }

# factory for building and accessing map files
map_factory = TurfMapFileFactory()
if dev_mode: map_factory.useDirpathsForMode('dev')
region = map_factory.regionConfig(region_key)

num_maps = 0
threat_count = 0
treatment_count = 0

for threat_key, threat in data_factory.config.controls.items():
    threat_count += 1

    for treatment_key, treatment in threat.treatments.items():
        treatment_count += 1

        map_count = drawControlStageMaps(threat, treatment, data_factory, map_factory,
                               region, requested_start, requested_end, max_previous,
                               use_cicss_gdd, verbose, debug)
        num_maps += map_count

elapsed_time = elapsedTime(SCRIPT_START_TIME, True)
info = (num_maps, treatment_count, threat_count, elapsed_time)
print '\nDrew a total of %d maps for %d treatments of %d threats in %s' % info

