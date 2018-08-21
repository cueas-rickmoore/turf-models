#! /usr/bin/env python

import os, sys
import datetime
JSON_START_TIME = datetime.datetime.now()

import numpy as N
import json

from atmosci.utils.timeutils import elapsedTime

from turf.threats.factory import TurfThreatGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def extractCommonJsonDates(avg_dates, daily_dates):
    # key common dates that better be the same between files
    dates = { 'seasonEnd': daily_dates['end_date'].timetuple()[:3],
              'seasonStart': daily_dates['start_date'].timetuple()[:3],
            }

    # get latest first valid date
    first_valid = avg_dates.get('first_valid_date', None)
    daily_first_valid = daily_dates.get('first_valid_date', None)
    if first_valid is None:
        if daily_first_valid is None:
            first_valid = daily_dates['start_date']
    else:
        if daily_first_valid is not None:
            first_valid = max(first_valid, daily_first_valid)
    dates['firstValid'] = first_valid.timetuple()[:3]

    # get the earliest last_valid_date
    last_valid = avg_dates.get('last_valid_date', None)
    daily_last_valid = daily_dates.get('last_valid_date', None)
    if last_valid is None:
        if daily_last_valid is None:
            last_valid = daily_dates['end_date']
        else: last_valid = daily_last_valid
    else:
        if daily_last_valid is not None:
            last_valid = min(last_valid, daily_last_valid)
    dates['lastValid'] = last_valid.timetuple()[:3]

    # forecast dates
    fcast_start = daily_dates.get('fcast_start_date', None)
    if fcast_start is not None:
        dates['fcastStart'] = fcast_start.timetuple()[:3]
        dates['fcastEnd'] = min(daily_dates['fcast_end_date'],last_valid).timetuple()[:3]

    # generate the json string for the dates
    json_dates = json.dumps(dates,separators=(',',':'))
    return first_valid, last_valid, json_dates.replace('(','[').replace(')',']')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def extractJsonDates(date_dict):
    # key common dates that better be the same between files
    dates = { 'seasonEnd': date_dict['end_date'].timetuple()[:3],
              'seasonStart': date_dict['start_date'].timetuple()[:3],
            }

    # get latest first valid date
    first_valid = date_dict.get('first_valid_date', None)
    if first_valid is None: first_valid = date_dict['start_date']
    dates['firstValid'] = first_valid.timetuple()[:3]

    # get the earliest last_valid_date
    last_valid = date_dict.get('last_valid_date', None)
    if last_valid is None: last_valid = date_dict['end_date']
    dates['lastValid'] = last_valid.timetuple()[:3]

    # forecast dates
    fcast_start = date_dict.get('fcast_start_date', None)
    if fcast_start is not None:
        dates['fcastStart'] = fcast_start.timetuple()[:3]
        dates['fcastEnd'] = min(date_dict['fcast_end_date'],last_valid).timetuple()[:3]

    # generate the json string for the dates
    json_dates = json.dumps(dates,separators=(',',':'))
    return first_valid, last_valid, json_dates.replace('(','[').replace(')',']')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='sub_region', default=None)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()
num_args = len(args)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
sub_region = options.sub_region
verbose = options.verbose or debug

threat = args[0]
path_key = 'threats.%s' % threat
include_avg = threat != 'hstress'

if num_args == 1: target_year = datetime.date.today().year
elif num_args == 2: target_year = int(args[1])

# create a factory for access to the threat file
factory = TurfThreatGridFileFactory()
if dev_mode: factory.useDirpathsForMode('dev')
region = factory.regionConfig(factory.project.region)

if include_avg:
    # open average data file and extract lat, lon, data and it's dates
    avg_reader = factory.threatFileReader(threat, 'average', target_year)
    avg_dates = avg_reader.dateAttributes('risk', True)
    avg_reader.close()

# open daily data file and extract lat, lon, data and it's dates
daily_reader = factory.threatFileReader(threat, 'daily', target_year)
daily_dates = daily_reader.dateAttributes('risk', True)
daily_reader.close()

# extract the dates needed for the json files and create the common json template
if include_avg:
    data_start, data_end, json_dates = extractCommonJsonDates(avg_dates, daily_dates)
    params = { 'name':threat, 'lat':'%(lat)s', 'lon':'%(lon)s', 'dates':json_dates,
               'data':'{"average":[%(avg)s],"daily":[%(daily)s]}' }
else:
    data_start, data_end, json_dates = extractJsonDates(daily_dates)
    params = { 'name':threat, 'lat':'%(lat)s', 'lon':'%(lon)s', 'dates':json_dates,
               'data':'{"daily":[%(daily)s]}' }

# insert the params into the template
json_template = factory.threats.json_template % params

# get the indexes of all valid grid nodes from region's static file 
source = factory.sourceConfig(factory.config.project.source)
static_reader = factory.staticFileReader(source, region)
if sub_region is not None:
    static_reader.setCoordinateBounds(factory.regionConfig(sub_region).data)
    cus_mask = static_reader.getDataInBounds('cus_mask')
else: cus_mask = static_reader.getData('cus_mask')
indexes = N.where(cus_mask == False)
valid_indexes = zip(indexes[0], indexes[1])
del cus_mask, indexes, source
static_reader.close()
del static_reader

# create templates for constructing json data file paths 
json_dirpath = factory.threatJsonDirpath(path_key, target_year)
if not os.path.isdir(json_dirpath): os.makedirs(json_dirpath)
json_filename = factory.threatJsonFilename(path_key, '%(node)s', target_year)

# get the daily data
daily_reader.open()
daily_risk = daily_reader.timeSlice('risk', data_start, data_end)
lats = daily_reader.lats
lons = daily_reader.lons
daily_reader.close()
del daily_reader

# create a json file for each valid grid node
num_files = 0
if include_avg:
    avg_reader.open()
    avg_risk = avg_reader.timeSlice('risk', data_start, data_end)
    avg_reader.close()
    del avg_reader

    for y, x in valid_indexes:
        avg = avg_risk[:,y,x]
        daily = daily_risk[:,y,x]

        if len(N.where(N.isnan(avg))[0]) == 0 and len(N.where(N.isnan(daily))[0]) == 0:
            lat = N.round(lats[y,x],3)
            lon = N.round(lons[y,x],3)
            params = { 'lat':lat, 'lon':lon }
            params['avg'] = ','.join(['%d' % value for value in avg])
            params['daily'] = ','.join(['%d' % value for value in daily])

            filename = json_filename % {'node':factory.gridNodeToFilename((lon,lat)),}
            filepath = os.path.join(json_dirpath, filename)
        
            with open(filepath, 'w') as writer:
                writer.write(json_template % params)

            num_files += 1
            if verbose: print num_files, filepath
        else:
            num_nans = len(N.where(N.isnan(avg))[0])
            location = (y, x, lons[y,x], lats[y,x])
            if num_nans == avg.size:
                print 'All NAN average @ node[%s,%d] (%.5f, %.5f)' % location
            else:
                print '%d NANs in average @ node[%s,%d] (%.5f, %.5f)' % (num_nans,) + location

            num_nans = len(N.where(N.isnan(daily))[0])
            if num_nans == daily.size:
                print 'All NAN daily @ node[%s,%d] (%.5f, %.5f)' % location
            else:
                print '%d NANs in daily @ node[%s,%d] (%.5f, %.5f)' % (num_nans,) + location

else: # primarily used for Heat Stress
    for y, x in valid_indexes:
        daily = daily_risk[:,y,x]

        if len(N.where(N.isnan(daily))[0]) == 0:
            lat = N.round(lats[y,x],3)
            lon = N.round(lons[y,x],3)
            params = { 'lat':lat, 'lon':lon }
            params['daily'] = ','.join(['%d' % value for value in daily])

            filename = json_filename % {'node':factory.gridNodeToFilename((lon,lat)),}
            filepath = os.path.join(json_dirpath, filename)
        
            with open(filepath, 'w') as writer:
                writer.write(json_template % params)

            num_files += 1
            if verbose: print num_files, filepath
        else:
            num_nans = len(N.where(N.isnan(daily))[0])
            location = (y, x, lons[y,x], lats[y,x])
            if num_nans == daily.size:
                print 'All NAN daily @ node[%s,%d] (%.5f, %.5f)' % location
            else:
                print '%d NANs in daily @ node[%s,%d] (%.5f, %.5f)' % (num_nans,) + location


threat_fullname = factory.threatName(threat)
elapsed_time = elapsedTime(JSON_START_TIME, True)
info = (threat_fullname, num_files, elapsed_time)
print '\nGenerated %s JSON files for %d grid nodes in %s' % info

