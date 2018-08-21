#! /usr/bin/env python

import os, sys
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import pytz
import numpy as N
import urllib

from atmosci.utils.timeutils import elapsedTime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.urma.config import CONFIG
SOURCE = CONFIG.sources.urma.ncep

# should be 'http://www.ftp.ncep.noaa.gov/data/nccf/com/urma/prod'
REMOTE_SERVER = SOURCE.http.url
REMOTE_SUBDIR = SOURCE.http.subdir # should be 'urma2p5.%(utc_date)s'
# should be 'urma2p5.%(utc_time)s.pcp_06h.184.grb2'
APCP_SOURCE = SOURCE.source_file_map.APCP
APCP_URL = '/'.join((REMOTE_SERVER, REMOTE_SUBDIR, APCP_SOURCE))
# sgould be 'urma2p5.t%(utc_hour)sz.2dvaranl_ndfd.grb2'
DATA_SOURCE = SOURCE.source_file_map.data
DATA_URL = '/'.join((REMOTE_SERVER, REMOTE_SUBDIR, DATA_SOURCE))

URMA_DIRPATH = '/Volumes/data/app_data/shared/reanalysis/conus/urma/'
URMA_SUBDIR_PATH = os.path.join(URMA_DIRPATH, '%(utc_date)s')
APCP_FILENAME = 'urma.%(utc_time)sz.pcp_06h.grb2'
APCP_FILEPATH = os.sep.join((URMA_SUBDIR_PATH, APCP_FILENAME))
DATA_FILENAME = 'urma.%(utc_time)sz.data.grb2'
DATA_FILEPATH = os.sep.join((URMA_SUBDIR_PATH, DATA_FILENAME))

UTC_FORMAT = '%Y.%m.%d:%HUTC'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def utcTimes(utc_time):
    return { 'utc_date': utc_time.strftime('%Y%m%d'),
             'utc_hour': utc_time.strftime('%H'), 
             'utc_time': utc_time.strftime('%Y%m%d%H') }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def downloadURMA(utc_time, verbose=False, debug=False):
    files = [ ]
    utc_time_str =utc_time.strftime(UTC_FORMAT)
    utc_times = utcTimes(utc_time)
    urma_dirpath = URMA_SUBDIR_PATH % utc_times
    if debug: print 'isdir() :', os.path.isdir(urma_dirpath), urma_dirpath
    if not os.path.isdir(urma_dirpath): os.makedirs(urma_dirpath)

    # download main data file
    local_filepath = DATA_FILEPATH % utc_times
    # don't download a file it already exists
    if not os.path.exists(local_filepath):
        remote_url = DATA_URL % utc_times
        if verbose:
            print '\ndownloading :', remote_url
            print 'to :', local_filepath
        try:
            (destfile, info) = urllib.urlretrieve(remote_url, local_filepath)
        except Exception as e:
            print '*** download of "%s" failed' % remote_url.split('prod')[1]
        else:
            if int(info['Content-Length']) < 300:
                print 'Data download failed for %s' % utc_time_str
                if os.path.exists(local_filepath):
                    os.remove(local_filepath)
            else:
                files.append((utc_times['utc_time'], local_filepath))

    # download the precip file
    if utc_time.hour in (0,6,12,18):
        local_filepath = APCP_FILEPATH % utc_times
        # don't download a file it already exists
        if not os.path.exists(local_filepath):
            remote_url = APCP_URL % utc_times
            if verbose:
                print '\ndownloading :', remote_url
                print 'to :', local_filepath
            try:
                urllib.urlretrieve(remote_url, local_filepath)
            except:
                errmsg = '*** download of "%s" failed'
                print errmsg % remote_url.split('prod')[1]
            else:
                if int(info['Content-Length']) < 300:
                    print 'Precip download failed for %sUTC' % utc_time_str
                    if os.path.exists(local_filepath):
                        os.remove(local_filepath)
                else:
                    files.append((utc_times['utc_time'], local_filepath))

    return tuple(files)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-b', action='store', type=int, dest='hours_behind',
                        default=5)
parser.add_option('-n', action='store', type=int, dest='num_hours', default=4)
parser.add_option('-u', action='store_true', dest='utc_date', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

download_start = datetime.datetime.now()

debug = options.debug
file_count = 0
num_hours = options.num_hours
hours_behind = options.hours_behind
utc_date = options.utc_date
verbose = options.verbose or debug

if debug:
    print 'num_hours :', num_hours
    print 'hours_behind :', hours_behind

tz = pytz.timezone('US/Eastern')
if len(args) > 0:
    date_args = tuple([int(arg) for arg in args[:4]])
    if utc_date: # input date is already UTC corrected
        end_hour = tzutils.asHourInTimezone(date_args, 'UTC')
        local_hour = tzutils.asHourInTimezone(end_hour,'US/Eastern')
    else:
        local_hour = tzutils.asHourInTimezone(date_args,'US/Eastern')
        end_hour = tzutils.asHourInTimezone(hour, 'UTC')
        end_hour -= datetime.timedelta(hours=hours_behind)
else:
    local_hour = datetime.datetime.now()
    local_hour = tzutils.asHourInTimezone(local_hour,'US/Eastern')
    end_hour = tzutils.asHourInTimezone(local_hour, 'UTC')
    end_hour -= datetime.timedelta(hours=hours_behind)

if debug:
    print 'local hour :', tzutls.hourAsString(local_hour, True)
    print 'UTC hour :', tzutls.hourAsString(end_hour, True)

utc_hour = start_hour = end_hour - datetime.timedelta(hours=num_hours-1)
while utc_hour <= end_hour:
    if debug: print '\nprocessing download for', utc_hour
    files = downloadURMA(utc_hour, verbose, debug)
    file_count += len(files)
    utc_hour += ONE_HOUR

elapsed_time = elapsedTime(download_start, True)
print '\ncompleted download of %d files in %s' % (file_count, elapsed_time)

transport_dirpath = \
    '/Volumes/Transport/data/app_data/shared/reanalysis/conus/urma'
if file_count > 0 and os.path.exists(transport_dirpath):
    command = \
        '/usr/bin/rsync -cgloprtuD %s %s' % (URMA_DIRPATH, transport_dirpath)
    print '\n', command
    os.system(command)

