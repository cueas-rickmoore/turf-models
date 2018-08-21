#! /Volumes/Transport/venvs/atmosci/bin/python

import os, sys
import warnings

import datetime
ONE_HOUR = datetime.timedelta(hours=1)
SCRIPT_START = datetime.datetime.now()

import numpy as N
import urllib

from atmosci.utils.timeutils import elapsedTime
from atmosci.utils.tzutils import asUTCTime

from atmosci.equations import rhumFromDpt
from atmosci.units import convertUnits

from atmosci.reanalysis.smart_grib import ReanalysisDownloadFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CACHE_SERVER_BUFFER_MIN = 20

NOMADS_SERVER = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod'
NOMADS_SUBDIR = 'rtma2p5.%(utc_date)s'
NOMADS_ACPC_DATA = 'rtma2p5.%(utc_time)s.pcp.184.grb2'
NOMADS_ACPC_URL = '/'.join((NOMADS_SERVER, NOMADS_SUBDIR, NOMADS_ACPC_DATA))
NOMADS_DATA = 'rtma2p5.t%(utc_hour)sz.2dvaranl_ndfd.grb2'

THREDDS_SERVER = \
    'http://thredds.ucar.edu/thredds/fileServer/grib/NCEP/RTMA/CONUS_2p5km/'
THREDDS_DATA = 'RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2'

DATA_URLS = { 'nomads': '/'.join((NOMADS_SERVER, NOMADS_SUBDIR, NOMADS_DATA)),
              'thredds': '/'.join((THREDDS_SERVER, THREDDS_DATA)) }

RTMA_DIRPATH = '/data2/weather-data/shared/reanalysis/conus/rtma'
RTMA_SUBDIR_PATH = os.path.join(RTMA_DIRPATH, '%(utc_date)s')
APCP_FILENAME = 'rtma.%(utc_time)sz.precip.grb2'
APCP_FILEPATH = os.sep.join((RTMA_SUBDIR_PATH, APCP_FILENAME))
DATA_FILENAME = 'rtma.%(utc_time)sz.data.grb2'
DATA_FILEPATH = os.sep.join((RTMA_SUBDIR_PATH, DATA_FILENAME))

UTC_FORMAT = '%Y.%m.%d:%HUTC'

DATA_GRID_SIZE = 50000000
APCP_GRID_SIZE = 400000


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-b', action='store', type=int, dest='max_backward', default=48)
parser.add_option('-n', action='store', type=int, dest='num_hours', default=4)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-m', action='store_true', dest='only_missing', default=False)
parser.add_option('-u', action='store_true', dest='utc_date', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--data', action='store_false', dest='download_data', default=True)
parser.add_option('--pcpn', action='store_false', dest='download_pcpn', default=True)

parser.add_option('--grib_region', action='store', dest='grib_region', default='conus')
parser.add_option('--grib_server', action='store', dest='grib_server', default='nomads')
parser.add_option('--grib_source', action='store', dest='grib_source', default='ncep')

options, args = parser.parse_args()

debug = options.debug
dev_mode = options.dev_mode
download_data = options.download_data
download_pcpn = options.download_pcpn
grib_region = options.grib_region
grib_server = options.grib_server
grib_source = options.grib_source
max_backward = options.max_backward
num_hours = options.num_hours
only_missing = options.only_missing
utc_date = options.utc_date
verbose = options.verbose or debug

reanalysis = 'rtma'
reanalysis_name = 'RTMA'

if len(args) > 0:
    date_args = tuple([int(n) for n in args])
    if utc_date: # input date is already UTC corrected
        end_hour = asUTCTime(datetime.datetime(*date_args))
    else: end_hour = asUTCTime(datetime.datetime(*date_args),'US/Eastern')
    start_hour = end_hour - datetime.timedelta(hours=num_hours-1)
else:
    now = datetime.datetime.now()
    end_hour = asUTCTime(datetime.datetime.combine(now.date(), datetime.time(now.hour)), 'US/Eastern')
    start_hour = None


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def utcTimes(utc_time):
    return { 'utc_date': utc_time.strftime('%Y%m%d'),
             'utc_hour': utc_time.strftime('%H'), 
             'utc_time': utc_time.strftime('%Y%m%d%H') }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def determineTimespan(factory, end_hour, variable, region, max_backward, verbose, debug):
    first_hour = end_hour - datetime.timedelta(hours=max_backward-1)
    if debug:
        print 'determineTtimespan :'
        print '    earliest_hour =', first_hour
        print '      latest_hour =', end_hour
    return missingHoursInTimespan(factory, first_hour, end_hour, variable, region, verbose, debug)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def downloadData(factory, utc_time, grib_server, verbose=False, debug=False):
    utc_time_str = utc_time.strftime(UTC_FORMAT)
    utc_times = utcTimes(utc_time)

    #rtma_dirpath = RTMA_SUBDIR_PATH % utc_times
    #if debug: print 'dirpath', os.path.isdir(rtma_dirpath), rtma_dirpath
    #if not os.path.isdir(rtma_dirpath): os.makedirs(rtma_dirpath)

    #rtma_dirpath = RTMA_SUBDIR_PATH % utc_times
    #if debug: print 'dirpath', os.path.isdir(rtma_dirpath), rtma_dirpath
    #if not os.path.isdir(rtma_dirpath): os.makedirs(rtma_dirpath)

    # download main data file
    #local_filepath = DATA_FILEPATH % utc_times
    local_filepath = factory.gribFilepath(utc_time, 'data', 'conus')

    # don't download a file it already exists and contain enough data
    if os.path.exists(local_filepath):
        should_download = os.path.getsize(local_filepath) < DATA_GRID_SIZE
    else: should_download = True

    if should_download:
        remote_url = DATA_URLS[grib_server] % utc_times
        if verbose:
            print '\ndownloading :', remote_url
            print 'to :', local_filepath
        try:
            (destfile, info) = urllib.urlretrieve(remote_url, local_filepath)
            if debug: print '\nurllib.urlretrieve.info :\n', info
        except Exception as e:
            errmsg = '*** download of "%s" failed : %s' 
            print errmsg % (remote_url.split('prod')[1], str(e))
            should_remove = os.path.exists(local_filepath) and \
                            os.path.getsize(local_filepath) < DATA_GRID_SIZE
            if should_remove: os.remove(local_filepath)
        else:
            filesize = os.path.getsize(local_filepath)
            should_remove = os.path.exists(local_filepath) and \
                            os.path.getsize(local_filepath) < DATA_GRID_SIZE
            if should_remove:
                msg = 'Data download failed for %s\n Downloaded data file was too small (%d bytes),' 
                msg += ' should have been at least %d bytes.'
                print msg % (utc_time_str, filesize, DATA_GRID_SIZE)
                os.remove(local_filepath)
            else:
                return local_filepath

    return None

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def downloadPcpn(factory, utc_time, grib_server, verbose=False, debug=False):
    utc_time_str = utc_time.strftime(UTC_FORMAT)
    utc_times = utcTimes(utc_time)

    # download the precip file
    local_filepath = factory.gribFilepath(utc_time, 'APCP', 'conus')

    # don't download a file it already exists and contain enough data
    if os.path.exists(local_filepath):
        should_download = os.path.getsize(local_filepath) < APCP_GRID_SIZE
    else: should_download = True

    if should_download:
        remote_url = NOMADS_ACPC_URL % utc_times
        if verbose:
            print '\ndownloading :', remote_url
            print 'to :', local_filepath
        try:
            (destfile,info) = urllib.urlretrieve(remote_url, local_filepath)
            if verbose: print info
        except Exception as e:
            errmsg = '*** download of "%s" failed : %s' 
            print errmsg % (remote_url.split('prod')[1], str(e))
            should_remove = os.path.exists(local_filepath) and \
                            os.path.getsize(local_filepath) < APCP_GRID_SIZE
            if should_remove: os.remove(local_filepath)
        else:
            filesize = os.path.getsize(local_filepath)
            should_remove = os.path.exists(local_filepath) and \
                            os.path.getsize(local_filepath) < APCP_GRID_SIZE
            if should_remove:
                msg = 'Precip download failed for %s\n Downloaded data file was too small (%d bytes),' 
                msg += ' should have been at least %d bytes.'
                print msg % (utc_time_str, filesize, DATA_GRID_SIZE)
                os.remove(local_filepath)
            else:
                return local_filepath

    return None

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def extractData(factory, reader, variable, debug):
    if debug: print 'extractData :', variable
    message = reader.messageFor(variable)
    if debug: print '    message :', message
    missing_value = float(message.missingValue)
    units = message.units
    if debug:
        print '    missing :', missing_value
        print '      units :', units
    data = message.values[factory.grib_indexes]
    if debug: print ' data shape :', data.shape
    if N.ma.is_masked(data): data = data.data
    data = data.reshape(factory.grid_shape)
    data[N.where(data >= missing_value)] = N.nan
    data[N.where(factory.data_mask == True)] = N.nan
    return units, data

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def missingHoursInTimespan(factory, first_hour, last_hour, variable, region, verbose, debug):
    download_hours = [ ]
    test_hour = first_hour
    # look for last available file .. no more than max_backward hours ago
    while test_hour <= last_hour:
        grib_filepath = factory.gribFilepath(test_hour, variable, 'conus', make_directory=False)
        if os.path.exists(grib_filepath):
            if debug: print 'TRUE :', grib_filepath
        else:
            if verbose: print 'FALSE :', grib_filepath
            download_hours.append(test_hour)
        test_hour += ONE_HOUR

    return tuple(download_hours)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateDataGrids(factory, utc_time, filepath, debug):
    # get a reader for the grib file
    Class = factory.fileAccessorClass('grib', 'read')
    reader = Class(filepath, factory.grib_source)
    # update temp
    tmp_units, temp = extractData(factory, reader, 'TMP', debug)
    updateGridFile(factory, 'TMP', utc_time, temp, tmp_units, debug)
    # update dew point
    dpt_units, dewpt = extractData(factory, reader, 'DPT', debug)
    updateGridFile(factory, 'DPT', utc_time, dewpt, dpt_units, debug)
    # update humidity
    if dpt_units != tmp_units: dpt = convertUnits(dpt, dpt_units, tmp_units)
    rhum = N.around(rhumFromDpt(temp, dewpt, tmp_units), 2)
    updateGridFile(factory, 'RHUM', utc_time, rhum, '%', debug)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updateGridFile(factory, variable, utc_time, data, units, debug):
    filepath = factory.analysisGridFilepath(utc_time, variable, 'NE')
    if not os.path.exists(filepath):
        factory.buildReanalysisGridFile(utc_time, variable, 'NE', 'UTC')
    Class = factory.fileAccessorClass('reanalysis', 'manage')
    manager = Class(filepath, 'a')
    manager.updateReanalysisData('RTMA', variable, utc_time, data, units=units)
    manager.close()
    print '        updated %s grid for %s' % (variable, utc_time.strftime('%Y-%m-%d:%H'))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def updatePrecpGrid(factory, utc_time, filepath, debug):
    # get a reader for the grib file
    Class = factory.fileAccessorClass('grib', 'read')
    reader = Class(filepath, factory.grib_source)
    # update precip
    pcpn_units, pcpn = extractData(factory, reader, 'PCPN', debug)
    updateGridFile(factory, 'PCPN', utc_time, pcpn, pcpn_units, debug)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = ReanalysisDownloadFactory(reanalysis, grib_source, grib_server)
if dev_mode: factory.useDirpathsForMode('dev')
factory._initStaticResources_()

# start with data file downloads
data_count = 0

if download_data:
    if start_hour is None:
        download_hours = determineTimespan(factory, end_hour, 'DATA', grib_region, max_backward, verbose, debug)
        if len(download_hours) == 0:
            info = (end_hour.strftime('%Y=%m-%d:%H UTC'), max_backward, reanalysis.upper())
            print '\nSearched from %s back %d hours. No previous %s DATA grib files were found.' % info
    else:
        if only_missing:
            download_hours = missingHoursInTimespan(factory, start_hour, end_hour, 'DATA', region, verbose, debug)
            if len(download_hours) == 0:
                info = (start_hour.strftime('%Y=%m-%d:%H UTC'), end_hour.strftime('%Y=%m-%d:%H UTC'), reanalysis.upper())
                print '\nSearched from %s thru %s. No previous %s DATA grib files were found.' % info
        else:
            download_hours = [ ]
            hour = start_hour
            while hour <= end_hour:
                download_hours.append(hour)
                hour += ONE_HOUR
            download_hours = tuple(download_hours)

    if len(download_hours) > 0:
        if debug:
            print 'for DATA download :'
            print '    first_hour =', download_hours[0] 
            print '      end_hour =', download_hours[-1]

        SECTION_START = datetime.datetime.now()

        # filter annoying numpy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',"invalid value encountered in greater")
        warnings.filterwarnings('ignore',"invalid value encountered in less")
        warnings.filterwarnings('ignore',"Mean of empty slice")
        # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

        for utc_hour in download_hours:
            info = (reanalysis_name, utc_hour.strftime('%Y-%m-%d:%H'))
            print '\nProcessing %s DATA download for %s' % info
            grib_filepath = downloadData(factory, utc_hour, grib_server, verbose, debug)
            if grib_filepath is not None:
                data_count += 1
                if debug: print '    saved DATA grib file to :', grib_filepath
                updateDataGrids(factory, utc_hour, grib_filepath, debug)

        # turn annoying numpy warnings back on
        warnings.resetwarnings()

        if data_count > 0:
            info = (data_count, reanalysis.upper(), elapsedTime(SECTION_START, True))
            print '\nCompleted download of %d %s DATA grib files in %s' % info


# download precip files
pcpn_count = 0
pcpn_files = [ ]

if download_pcpn:
    if start_hour is None:
        download_hours = determineTimespan(factory, end_hour, 'PCPN', grib_region, max_backward, verbose, debug)
        if len(download_hours) == 0:
            info = (end_hour.strftime('%Y=%m-%d:%H UTC'), max_backward, reanalysis.upper())
            print '\nSearched from %s back %d hours. No previous %s DATA grib files were found.' % info
    else:
        if only_missing:
            download_hours = missingHoursInTimespan(factory, start_hour, end_hour, 'PCPN', region, verbose, debug)
            if len(download_hours) == 0:
                info = (start_hour.strftime('%Y=%m-%d:%H UTC'), end_hour.strftime('%Y=%m-%d:%H UTC'), reanalysis.upper())
                print '\nSearched from %s thru %s. No previous %s PCPN grib files were found.' % info
        else:
            download_hours = [ ]
            hour = start_hour
            while hour <= end_hour:
                download_hours.append(hour)
                hour += ONE_HOUR
            download_hours = tuple(download_hours)

    if len(download_hours) > 0:

        if debug:
            print 'for PCPN download :'
            print '    first_hour =', download_hours[0] 
            print '      end_hour =', download_hours[-1]
        
        SECTION_START = datetime.datetime.now()

        # filter annoying numpy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',"invalid value encountered in greater")
        warnings.filterwarnings('ignore',"invalid value encountered in less")
        warnings.filterwarnings('ignore',"Mean of empty slice")
        # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

        for utc_hour in download_hours:
            info = (reanalysis_name, utc_hour.strftime('%Y-%m-%d:%H'))
            print '\nProcessing %s PCPN download for %s' % info
            grib_filepath = downloadPcpn(factory, utc_hour, grib_server, verbose, debug)
            if grib_filepath is not None:
                pcpn_count += 1
                if debug: print '    saved PCPN grib file to :', grib_filepath
                updatePrecpGrid(factory, utc_hour, grib_filepath, debug)

        # turn annoying numpy warnings back on
        warnings.resetwarnings()

        if pcpn_count > 0:
            info = (reanalysis_name, pcpn_count, elapsedTime(SECTION_START, True))
            print 'Completed download and update of %s PCPN for %d hours in %s' % info

    else:
        info = (end_hour.strftime('%Y=%m-%d:%H UTC'), max_backward, reanalysis_name)
        print '\nSearched from %s back %d hours. No %s grib files were found.' % info

# downloads are all complete
total_count = data_count + pcpn_count
if total_count > 0:
    info = (total_count, reanalysis_name, elapsedTime(SCRIPT_START, True))
    print '\nCompleted processing %d %s grib files in %s' % info
else: print '\nNo %s grib files downloaded this run' % reanalysis_name

