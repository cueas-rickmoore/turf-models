
import os
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import requests

import numpy as N
import pygrib

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.seasonal.methods.static  import StaticFileAccessorMethods

from atmosci.reanalysis.factory import ReanalysisGribFactoryMethods, \
                                       ReanalysisGridFactoryMethods, \
                                       ReanalysisFactoryMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartReanalysisGribMethods:

    def completeInitialization(self, **kwargs):
        self.data_mask = None
        self.grib_indexes = None
        self.grib_region = kwargs.get('grib_region', 'conus')
        self.shared_grib_dir = kwargs.get('shared_grib_dir', True)
        self.setGridParameters(kwargs.get('grid_source','acis'),
                               kwargs.get('grid_region','NE'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataFromGrib(self, variable, grib_hour, **kwargs):
        debug = kwargs.get('debug', False)
        return_units = kwargs.get('return_units', False)

        found, reader = self._readerForHour(variable, grib_hour)
        if not found:
            hour, filepath = reader
            if debug:
                errmsg = '\nWARNING : %s : grib file not found\n%s\n'
                print errmsg % (hour, filepath)
            return False, ('grib file not found', hour, filepath)
        else:
            if debug: print '\nreading data from :\n    ', reader.filepath

        # read the message
        try:
            message = reader.messageFor(variable)
        except Exception as e:
            why = 'variable not in grib file'
            if debug:
                errmsg = '\nWARNING : %s %s for %s\n'
                print errmsg % (variable, why, grib_hour)
            return False, (why, grib_hour, reader.filepath)

        units = message.units
        if debug:
            time_str = grib_hour.strftime('%Y-%m-%d:%H')
            print 'processing reanalysis grib for', time_str
            print 'message retrieved :\n    ', message
            print '\n            grib_time :', message.dataTime
            print '             analDate :', message.analDate
            print '            validDate :', message.validDate
            print '             dataDate :', message.dataDate
            print '             dataTime :', message.dataTime
            print '         forecastTime :', message.forecastTime
            print '         validityDate :', message.validityDate
            print '           data units :', units

        data = message.values[self.grib_indexes]
        missing_value = float(message.missingValue)
        reader.close()
        del message
        del reader

        if N.ma.is_masked(data): data = data.data
        if debug: print '      retrieved shape :', data.shape
        data = data.reshape(self.grid_shape)
        if debug: print '           grid shape :', data.shape

        data[N.where(data >= missing_value)] = N.nan

        if debug:
            print '... before applying mask'
            print '        missing value :', missing_value
            print '         missing data :', len(N.where(N.isnan(data))[0])
            print '           valid data :', len(N.where(N.isfinite(data))[0])
            print '\n        data extremes :', N.nanmin(data), N.nanmean(data), N.nanmax(data)

        # apply the regional boundary mask
        data[N.where(self.data_mask == True)] = N.nan

        if debug:
            print '... after applying mask'
            print '         missing data :', len(N.where(N.isnan(data))[0])
            print '           valid data :', len(N.where(N.isfinite(data))[0])

        if return_units: package = (units, data)
        else: package = data

        return True, package

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def lastAvailableGribHour(self, variable, reference_time):
        year = reference_time.year
        month = reference_time.month
        last_day = lastDayOfMonth(year, month)
        last_hour = datetime.datetime(year, month, last_day, 23)
        target_hour = tzutils.asUtcTime(last_hour, 'UTC')
        # look for the last available file in the month
        while target_hour.month == month:
            filepath = self.gribFilepath(target_hour, variable, 
                            self.grib_region, make_directory=False)
            if os.path.exists(filepath): return target_hour
            target_hour -= ONE_HOUR
        # no data available for the month
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setGridParameters(self, grid_source='acis', grid_region='NE'):
        self.grid_region = self.regionConfig(grid_region)
        self.grid_source = self.sourceConfig(grid_source)
        self.grid_shape = None
        dims = self.sourceConfig('reanalysis.grid').dimensions[grid_region]
        self.grid_dimensions = (dims.lat, dims.lon)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def slices(self, data_start_time, data_end_time, hours_per_slice=24):

        prev_month = data_start_time.month
        num_hours = tzutils.hoursInTimespan(data_start_time, data_end_time)
        if data_end_time.month == data_start_time.month:
            return ((data_start_time, data_end_time),)

        slices = [ ]
        slice_start = data_start_time
        slice_month = slice_start_month

        while slice_start.month < data_end_time.month:
            last_day = lastDayOfMonth(slice_start.year,slice_start.month)
            slice_end = slice_start.replace(day=last_day, hour=23)
            slices.append((slice_start, slice_end))
            slice_start = slice_end + ONE_HOUR

        slices.append((slice_start, data_end_time))

        return tuple(slices)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeSlice(self, variable, slice_start_time, slice_end_time, **kwargs):
        debug = kwargs.get('debug', False)
        failed = [ ]

        if self.grib_indexes is None: self._initStaticResources_()

        region = kwargs.get('region', self.grib_region)
        
        grib_start_time = tzutils.tzaDatetime(slice_start_time, self.tzinfo)
        if slice_end_time > slice_start_time:
            grib_end_time = tzutils.tzaDatetime(slice_end_time, self.tzinfo)

            # a requested end time is not necessarily available
            # so strip off missing hours from end of time span
            while grib_end_time >= grib_start_time:
                filepath = self.gribFilepath(grib_end_time, variable, region)
                if os.path.exists(filepath): break
                grib_end_time -= ONE_HOUR

            num_hours = tzutils.hoursInTimespan(grib_start_time, grib_end_time)
            data = N.empty((num_hours,)+self.grid_dimensions, dtype=float)
            data.fill(N.nan)

            units = None
            date_indx = 0
            grib_time = grib_start_time
            while units is None and grib_time <= grib_end_time:
                success, package = self.dataFromGrib(variable, grib_time,
                                        return_units=True, **kwargs)
                if success:
                    units, data_for_hour = package
                    data[date_indx,:,:] = data_for_hour
                else: failed.append(package)

                grib_time += ONE_HOUR
                date_indx += 1

            while grib_time <= grib_end_time:
                OK, package = self.dataFromGrib(variable, grib_time, **kwargs)
                if OK: data[date_indx,:,:] = package
                else: failed.append(package)

                grib_time += ONE_HOUR
                date_indx += 1

        else:
            success, package = self.dataFromGrib(variable, grib_start_time,
                                                return_units=True, **kwargs)
            if not success:
                data = N.empty(self.grid_dimensions, dtype=float)
                units = None
                failed.append(package)
            else: units, data = package 

        return units, data, tuple(failed)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _readerForHour(self, variable, hour):
        try:
            reader = self.gribFileReader(hour, variable, self.grib_region,
                                         shared_grib_dir=self.shared_grib_dir,
                                         file_must_exist=True)
            return True, reader

        except IOError: # IOError means file for this hour does not exist
            filepath = self.gribFilepath(hour, variable, self.grib_region)
            return False, (hour, filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initStaticResources_(self):
        reader = \
            self.staticFileReader(self.grid_source, self.grid_region)
        self.grid_shape, self.grib_indexes = reader.gribSourceIndexes('ndfd')
        # get the region boundary mask
        self.data_mask = reader.getData('cus_mask')
        reader.close()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartReanalysisGribReader(SmartReanalysisGribMethods,
                                ReanalysisGribFactoryMethods,
                                StaticFileAccessorMethods,
                                ReanalysisFactoryMethods, object):

    def __init__(self, analysis_source, **kwargs):
        config_object = self._initReanalysisFactory_(analysis_source)
        self.degug = kwargs.get('debug', False)

        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGribFactory_(**kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        self._registerGribAccessClasses()

        from atmosci.seasonal.static import StaticGridFileReader
        self._registerAccessManager('static', 'read', StaticGridFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisDownloadFactory(SmartReanalysisGribMethods,
                                ReanalysisGribFactoryMethods,
                                ReanalysisGridFactoryMethods,
                                StaticFileAccessorMethods,
                                ReanalysisFactoryMethods, object):
    """
    Basic factory for accessing data in Reanalysis grib files.
    """
    def __init__(self, analysis_type, grib_source, grib_server, **kwargs):
        analysis = '%s.%s' % (analysis_type, grib_source)
        
        config_object = self._initReanalysisFactory_(analysis, **kwargs)
        self.grib_server = self.grib_source[grib_server]

        # initialize common configuration structure
        # self._initFactoryConfig_(config_object, None, None)
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grid-specific configuration
        self._initReanalysisGridFactory_(**kwargs)

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGribFactory_(**kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataForVariable(self, reader, variable):
        # read the message
        try:
            message = reader.messageFor(variable)
        except Exception as e:
            return False, (grib_time, reader.filepath)

        units = message.units
        data = message.values[self.grib_indexes]
        missing_value = float(message.missingValue)
        del message

        if N.ma.is_masked(data): data = data.data
        data = data.reshape(self.grid_shape)
        # set all missing values to NaN
        data[N.where(data >= missing_value)] = N.nan
        # apply the regional boundary mask
        data[N.where(self.data_mask == True)] = N.nan

        return True, (units, data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def downloadChunkedGrib(self, utc_time, variable, region, acceptable_size, 
                                  timeout, chunk_size, debug=False):
        download_attempts = self.project.download.attempts
        wait_times = self.project.download.wait_times

        url_template = self.gribUrlTemplate(variable)
        url = url_template % tzutils.tzaTimeStrings(utc_time, 'utc')
        if debug: print '\nAttempting to download :', url

        filename = self.gribFilename(utc_time, variable, region)
        filepath = self.gribFilepath(utc_time, variable, region)
        if debug: print 'to :', filepath

        attempt = 0
        while True:
            packet_size = 0
            wait_time = wait_times[attempt]
            attempt += 1

            try: 
                if timeout > 0:
                    req = requests.get(url, stream=True, timeout=timeout)
                else: req = requests.get(url, stream=True)

                expected_size = int(req.headers['content-length'])
                if expected_size >= acceptable_size:
                    packet_size = 0
                    with open(filepath,'wb') as file_obj:
                        for data in req.iter_content(chunk_size):
                            packet_size += len(data)
                            file_obj.write(data)

                    if packet_size >= expected_size:
                        return 200, filepath, url, variable

            except requests.exceptions.Timeout as e:
                if attempt < download_attempts:
                    time.sleep(wait_time)
                    continue
                else:
                    status = req.status_code
                    msg = '%d : socket timeout. Download failed after %s attempts to download "%s" :: %s.'
                    info = (status, download_attempts, variable, str(e))
                    return status, filename, url, msg % info

            except requests.exceptions.ConnectionError as e:
                if attempt < download_attempts:
                    time.sleep(wait_time)
                    continue
                else:
                    status = req.status_code
                    msg = 'Download of "%s" failed after %d attempts. Unable to connect to server :: %s'
                    info = (variable, download_attempts, str(e))
                    return status, filename, url, msg % info

            except requests.exceptions.HTTPError as e:
                if attempt < download_attempts:
                    time.sleep(wait_time)
                    continue
                else:
                    status = req.status_code
                    if packet_size > 0:
                        msg = '"%s" download failed with HTTP error code %s after %d attempts'
                        msg += ' (%d bytes downloaded) :: %s'
                        info = (variable, status, download_attempts, packet_size, str(e))
                    else:
                        msg = '"%s" download failed with HTTP error code %s after %d attempts :: %s'
                        info = (variable, status, download_attempts, str(e))
                    return status, filename, url, msg % info

            except requests.exceptions.RequestException as e:
                status = req.status_code
                why = (e.code, e.reason, packet_size)
                msg = 'Download failed with HTTP error code %s (%s), %d bytes downloaded'
                return e.code, filename, url, msg % why

            except Exception as e:
                raise e

            else:
                if os.path.exists(filepath): os.remove(filepath)
                print 'response package :\n', req.text, '\n'

                if attempt == download_attempts:
                    msg = 'HTTP response for %s contains %d bytes, expecting at least %d bytes.'
                    msg += '\nThe incomplete file was deleted :\n    %s'
                    info = (variable, expected_size, acceptable_size, filepath)
                    return 999, filename, url, msg % info

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def downloadGribFile(self, utc_time, variable, region, acceptable_size, 
                               timeout, debug=False):
        download_attempts = self.project.download.attempts
        wait_times = self.project.download.wait_times

        url_template = self.gribUrlTemplate(variable)
        url = url_template % tzutils.tzaTimeStrings(utc_time, 'utc')
        if debug: print '\nAttempting to download :', url

        filename = self.gribFilename(utc_time, variable, region)
        filepath = self.gribFilepath(utc_time, variable, region)
        if debug: print 'to :', filepath

        attempt = 0
        while True:
            packet_size = 0
            wait_time = wait_times[attempt]
            attempt += 1

            try: 
                if timeout > 0:
                    req = requests.get(url, stream=True, timeout=timeout)
                else: req = requests.get(url, stream=True)

                packet_size = int(req.headers['content-length'])
                if packet_size >= acceptable_size:
                    file_obj = open(filepath,'wb')
                    file_obj.write(req.content)
                    file_obj.close()
                    return 200, filepath, url, variable

            except requests.exceptions.Timeout as e:
                if attempt < download_attempts:
                    time.sleep(wait_time)
                    continue
                else:
                    status = req.status_code
                    msg = '%d : socket timeout. Download failed after %s attempts to download "%s" :: %s.'
                    info = (status, download_attempts, variable, str(e))
                    return status, filename, url, msg % info

            except requests.exceptions.ConnectionError as e:
                if attempt < download_attempts:
                    time.sleep(wait_time)
                    continue
                else:
                    status = req.status_code
                    msg = 'Download of "%s" failed after %d attempts. Unable to connect to server :: %s'
                    info = (variable, download_attempts, str(e))
                    return status, filename, url, msg % info

            except requests.exceptions.HTTPError as e:
                if attempt < download_attempts:
                    time.sleep(wait_time)
                    continue
                else:
                    status = req.status_code
                    if packet_size > 0:
                        msg = '"%s" download failed with HTTP error code %s after %d attempts'
                        msg += ' (%d bytes downloaded) :: %s'
                        info = (variable, status, download_attempts, packet_size, str(e))
                    else:
                        msg = '"%s" download failed with HTTP error code %s after %d attempts :: %s'
                        info = (variable, status, download_attempts, str(e))
                    return status, filename, url, msg % info

            except requests.exceptions.RequestException as e:
                status = req.status_code
                why = (e.code, e.reason, packet_size)
                msg = 'Download failed with HTTP error code %s (%s), %d bytes downloaded'
                return e.code, filename, url, msg % why

            except Exception as e:
                raise e

            else:
                if attempt == download_attempts:
                    msg = 'HTTP response for "%s" contains %d bytes, expecting at least %d bytes.'
                    msg += ' No data was saved.'
                    info = (variable, packet_size, acceptable_size)
                    return 999, filename, url, msg % info

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribDownloadUrl(self, variable, utc_time):
        template_args = {
            'utc_date': utc_time.strftime('%Y%m%d'),
            'utc_hour': utc_time.strftime('%H'), 
            'utc_time': utc_time.strftime('%Y%m%d%H'),
        }
        return self.gribUrlTemplate(variable) % template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribUrlTemplate(self, variable):
        source = self.grib_source
        print 'gribUrlTemplate :', source.name
        filename = source.source_file_map.get(variable.upper(),
                          source.source_file_map.get('data',
                              source.source_file_map.get('default', None)))
        print '    filename :', filename
        if filename is not None:
            server = self.grib_server
            print '    server :', server.name
            print '       url :', server.url
            print '    subdir :', server.subdir
            return os.path.join(server.url, server.subdir, filename)

        info = (source_key, server_key, variable)
        errmsg = 'Unable to construct URL template for %s.%s.%s' % info
        raise LookupError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def serverURL(self, server_type='http'):
        return self.grib_source.get(server_type, None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        self._registerGribAccessClasses()
        self._registerGridAccessClasses()

        from atmosci.seasonal.static import StaticGridFileReader
        self._registerAccessManager('static', 'read', StaticGridFileReader)


