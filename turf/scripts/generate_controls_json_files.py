#! /usr/bin/env python

import os, sys
import warnings

import datetime
JOB_START_TIME = datetime.datetime.now()

import numpy as N
import json

from atmosci.utils.timeutils import elapsedTime

from turf.controls.factory import TurfControlsFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='NE')

parser.add_option('-c', action='store_true', dest='use_cicss_gdd', default=False)
parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

debug = options.debug
dev_mode = options.dev_mode
use_cicss_gdd = options.use_cicss_gdd
verbose = options.verbose or debug

if len(args) == 1: target_year = int(args[1])
else: target_year = datetime.date.today().year


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def resolveJsonDates(turf_dates, gdd_dates):
    season_start, season_end = turf_dates
    # always start with season start/end
    season_end = min(gdd_dates['end_date'], season_end)
    season_start = max(gdd_dates['start_date'], season_start)
    dates = { 'seasonEnd': season_end.timetuple()[:3],
              'seasonStart': season_start.timetuple()[:3],
            }

    # determine the date of the first valid data entry
    first_valid = gdd_dates.get('first_valid_date', None)
    if first_valid is None: first_valid = season_start
    else: first_valid = max(first_valid,season_start)
    dates['firstValid'] = first_valid.timetuple()[:3]

    # get the date for hte last valid data entry
    last_valid = gdd_dates.get('last_valid_date', gdd_dates.get('last_obs_date', None))
    if last_valid is None: last_valid = season_end
    else: last_valid = min(last_valid,season_end)
    dates['lastValid'] = last_valid.timetuple()[:3]

    # forecast start/end dates
    fcast_end = gdd_dates.get('fcast_end_date', None)
    if fcast_end is not None:
        fcast_start = gdd_dates['fcast_start_date']
        if fcast_start <= last_valid:
            dates['fcastStart'] = fcast_start.timetuple()[:3]
            dates['fcastEnd'] = min(fcast_end,last_valid).timetuple()[:3]

    # generate the json string for the dates
    json_dates = json.dumps(dates,separators=(',',':'))
    return first_valid, last_valid, json_dates.replace('(','[').replace(')',']')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = TurfControlsFactory()
if dev_mode: factory.useDirpathsForMode('dev')

region = factory.regionConfig(options.region)
source = factory.sourceConfig('acis')
project = factory.projectConfig()

# get the indexes of all valid grid nodes from region's static file 
static_reader = factory.staticFileReader(source, region)
cus_mask = static_reader.getData('cus_mask')
indexes = N.where(cus_mask == False)
valid_indexes = zip(indexes[0], indexes[1])
del cus_mask, indexes
static_reader.close()
del static_reader

total_files = 0
num_threats = 0
num_treatments = 0

for control_key, control in factory.controls.items():
    JSON_START_TIME = datetime.datetime.now()
    num_threats += 1
    treatments = control.treatments.items()
    num_treatments += len(treatments)

    # filter annoying numpy warnings
    warnings.filterwarnings('ignore',"All-NaN axis encountered")
    warnings.filterwarnings('ignore',"All-NaN slice encountered")
    warnings.filterwarnings('ignore',"invalid value encountered in greater")
    warnings.filterwarnings('ignore',"invalid value encountered in less")
    warnings.filterwarnings('ignore',"Mean of empty slice")
    # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

    # create templates for constructing json data file paths 
    json_dirpath = factory.jsonFileDirpath(target_year, control, region, source)
    json_filename = factory.jsonFilename(target_year, '%(node)s', control, region, source)
    if debug:
        print 'default templates :'
        print '    dirpath   :', json_dirpath
        print '    filename  :', json_filename

    # get a readr for the GDD app POR file
    gdd_reader = factory.gddFileReader(target_year, region, use_cicss_gdd=use_cicss_gdd)
    lats = gdd_reader.lats
    lons = gdd_reader.lons

    # get all date attributes for the dataset as Datetime.Date objects
    gdd_dataset_path = 'gdd%d.accumulated' % control.gdd_threshold
    gdd_dates = gdd_reader.dateAttributes(gdd_dataset_path, True)
    gdd_reader.close()

    # get first and last data dates along with a json string of all dates
    start_date, end_date, json_dates = \
        resolveJsonDates(factory.seasonDates(target_year), gdd_dates)
    if debug:
        print '\nresolved dates :', start_date, end_date
        print json_dates, '\n'

    # create the common json template
    json_template = factory.project.control_json_template
    if debug: print 'json_template :', json_template
    json_template = json_template.replace('%(control)s',control.name)
    json_template = json_template.replace('%(dates)s',json_dates)

    gdd_reader.open()
    gdd_data = gdd_reader.dateSlice(gdd_dataset_path, start_date, end_date)
    gdd_reader.close()
    del gdd_reader

    # create a json file for each valid grid node
    json_fmt = '"%s":[%s]'
    num_days = gdd_data.shape[0]
    num_files = 0

    for y, x in valid_indexes:
        node_data = gdd_data[:,y,x]
        if len(N.where(node_data < 0)[0]) == 0:
            lat = N.round(lats[y,x],3)
            lon = N.round(lons[y,x],3)
            params = { 'lat':lat, 'lon':lon }
            filename = json_filename % {'node':factory.gridNodeToFilename((lon,lat)),}
            filepath = os.path.join(json_dirpath, filename)

            control_json = [ ]
            for name, treatment in treatments:
                stages = N.zeros(num_days, dtype='<i2')
                for index, threshold in enumerate(treatment.thresholds[1:]):
                    where = N.where(node_data >= threshold)
                    if len(where[0] > 0): stages[where] = index+1
                control_json.append(json_fmt % (name, ','.join(['%d' % s for s in stages])))

            params['data'] = '{%s}' % ','.join(control_json)

            with open(filepath, 'w') as writer:
                writer.write(json_template % params)

            num_files += 1
            if verbose: print num_files, filepath
        else:
            print 'ISSUE : All NAN node found at :', y, x, lons[y,x], lats[y,x]

    # turn annoying numpy warnings back on
    warnings.resetwarnings()

    total_files += num_files

    elapsed_time = elapsedTime(JSON_START_TIME, True)
    msg = 'Generated %d json files for %d treatments of %s in %s'
    print msg % (total_files, len(treatments), control.fullname, elapsed_time)


elapsed_time = elapsedTime(JOB_START_TIME, True)
msg = 'Generated a total of %d json files for %d threats in %s'
print msg % (total_files, num_threats, elapsedTime(JOB_START_TIME, True))
