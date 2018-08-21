#! /usr/bin/env python

import os, sys
import datetime
SCRIPT_START_TIME = datetime.datetime.now()

import numpy as N
import json

from atmosci.utils.timeutils import elapsedTime

#from turf.threats.factory import TurfThreatGridFileFactory
from turf.threats.generators import TurfThreatJsonGeneratorFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='NE')
parser.add_option('-s', action='store', dest='source', default='acis')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--sub', action='store', dest='sub_region', default=None)

options, args = parser.parse_args()
num_args = len(args)

debug = options.debug
dev_mode = options.dev_mode
region = options.region
source = options.source
sub_region = options.sub_region
verbose = options.verbose or debug

if num_args == 0: target_year = datetime.date.today().year
elif num_args == 1: target_year = int(args[0])


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
            first_vali = daily_dates['start_date']
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def generateComboJsonFiles(factory, threat, target_year, region_indexes):
    # open average data file and extract lat, lon, data and it's dates
    avg_reader = factory.threatFileReader(threat, 'average', target_year)
    avg_dates = avg_reader.dateAttributes('risk', True)
    avg_reader.close()

    # open daily data file and extract lat, lon, data and it's dates
    daily_reader = factory.threatFileReader(threat, 'daily', target_year)
    daily_dates = daily_reader.dateAttributes('risk', True)
    daily_reader.close()

    # create JSON content template
    data_start, data_end, json_dates = extractCommonJsonDates(avg_dates, daily_dates)
    params = { 'name':threat, 'lat':'%(lat)s', 'lon':'%(lon)s', 'dates':json_dates,
               'data':'{"average":[%(avg)s],"daily":[%(daily)s]}' }
    json_template = factory.threats.json_template % params

    # JSON file path templates
    json_dirpath, json_filename = jsonPathTemplates(threat, target_year)
    
    daily_risk, lats, lons = threatRisk(daily_reader, data_start, data_end, True)
    del daily_reader

    avg_risk = threatRisk(avg_reader, data_start, data_end, False)
    del avg_reader

    num_files = 0

    for y, x in region_indexes:
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

        else:
            threat_name = factory.threatName(threat)
            if num_nans == avg.size:
                location = (threat_name, y, x, lons[y,x], lats[y,x])
                print '%s : all NAN average risk @ node[%s,%d] (%.5f, %.5f)' % location
            else:
                location = (threat_name, len(N.where(N.isnan(avg))[0]), y, x, lons[y,x], lats[y,x])
                print '%s : %d NANs in average risk @ node[%s,%d] (%.5f, %.5f)' % (num_nans,) + location

            if num_nans == daily.size:
                location = (threat_name, y, x, lons[y,x], lats[y,x])
                print '%s : all NAN daily risk @ node[%s,%d] (%.5f, %.5f)' % location
            else:
                location = (threat_name, len(N.where(N.isnan(daily))[0]), y, x, lons[y,x], lats[y,x])
                num_nans = len(N.where(N.isnan(daily))[0])
                print '%s : %d NANs in daily risk @ node[%s,%d] (%.5f, %.5f)' % (num_nans,) + location

    return num_files

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def generateDailyJsonFiles(factory, threat, target_year, region_indexes):
    # open daily data file and extract lat, lon, data and it's dates
    daily_reader = factory.threatFileReader(threat, 'daily', target_year)
    daily_dates = daily_reader.dateAttributes('risk', True)
    daily_reader.close()

    # create JSON content template
    data_start, data_end, json_dates = extractJsonDates(daily_dates)
    params = { 'name':threat, 'lat':'%(lat)s', 'lon':'%(lon)s', 'dates':json_dates,
               'data':'{"daily":[%(daily)s]}' }
    json_template = factory.threats.json_template % params

    # JSON file path templates
    json_dirpath, json_filename = jsonPathTemplates(threat, target_year)

    daily_risk, lats, lons = threatRisk(daily_reader, data_start, data_end, True)
    del daily_reader

    num_files = 0

    for y, x in region_indexes:
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

        else:
            threat_name = factory.threatName(threat)
            num_nans = len(N.where(N.isnan(daily))[0])
            if num_nans == daily.size:
                location = (threat_name, y, x, lons[y,x], lats[y,x])
                print '%s : all NAN daily risk @ node[%s,%d] (%.5f, %.5f)' % location
            else:
                location = (threat_name, len(N.where(N.isnan(daily))[0]), y, x, lons[y,x], lats[y,x])
                print '%s : %d NANs in daily risk @ node[%s,%d] (%.5f, %.5f)' % location

    return num_files

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def jsonPathTemplates(threat, target_year):
    # create templates for constructing json data file paths 
    path_key = 'threats.%s' % threat
    dirpath = factory.threatJsonDirpath(path_key, target_year)
    if not os.path.isdir(dirpath): os.makedirs(dirpath)
    filename = factory.threatJsonFilename(path_key, '%(node)s', target_year)
    
    return dirpath, filename

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def threatRisk(reader, data_start, data_end, return_coords):
    reader.open()
    risk = reader.timeSlice('risk', data_start, data_end)
    if return_coords:
        lats = reader.lats
        lons = reader.lons
        package = (risk, lats, lons)
    else: package = risk
    reader.close()
    return package


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


print 'MAIN PROGRAM', debug

# create a factory for access to the threat file
#factory = TurfThreatGridFileFactory(source, region, sub_region)
factory = TurfThreatJsonGeneratorFactory()
if dev_mode: factory.useDirpathsForMode('dev')

grand_total = 0

# generate JSON files for threats that have both daily and average risk data
generator = factory.riskFileGenerator('avg,daily', source, region, sub_region)

for threat in ('anthrac','bpatch','dspot','pblight'):
    threat_fullname = factory.threatName(threat)
    JSON_START_TIME = datetime.datetime.now()
    count = generator(threat, target_year, debug)

    if count > 0:
        elapsed_time = elapsedTime(JSON_START_TIME, True)
        info = (threat_fullname, count, elapsed_time)
        print 'Generated JSON files for %s @ %d grid nodes in %s' % info
        grand_total += count

    else:
        print 'No valid data for %s yet.' % threat_fullname


# generate JSON files for threats that have only daily risk data
threat_fullname = factory.threatName('hstress')
generator = factory.riskFileGenerator('daily', source, region, sub_region)

JSON_START_TIME = datetime.datetime.now()
count = generator('hstress', 'daily', target_year, debug)

if count > 0:
    elapsed_time = elapsedTime(JSON_START_TIME, True)
    info = (threat_fullname, count, elapsed_time)
    print 'Generated JSON files for %s @ %d grid nodes in %s' % info
    grand_total += count

else:
    print 'No valid data for %s yet.' % threat_fullname


elapsed_time = elapsedTime(SCRIPT_START_TIME, True)
print '\nGenerated total of %d JSON files in %s' % (grand_total, elapsed_time)

