
import datetime
ONE_HOUR = datetime.timedelta(hours=1)
import warnings

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.config import ConfigObject
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.hourly.grid import HourlyGridFileReader, HourlyGridFileManager
from atmosci.hourly.builder import HourlyGridFileBuilder


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def filterNumpyWarnings():
    # filter annoying numpy warnings in a function
    warnings.filterwarnings('ignore',"All-NaN axis encountered")
    warnings.filterwarnings('ignore',"All-NaN slice encountered")
    warnings.filterwarnings('ignore',"invalid value encountered in greater")
    warnings.filterwarnings('ignore',"invalid value encountered in less")
    warnings.filterwarnings('ignore',"Mean of empty slice")
    # MUST ALSO RESET WARNINGS AT END OF FUNCTION !!!!!

def resetNumpyWarnings():
    # turn annoying numpy warnings back on
    warnings.resetwarnings()

def timeString(time_obj): return time_obj.strftime('%m-%d:%H')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class WeatherFileMethods:

    def maxWeatherTime(self, weather):
        if weather == 'temps':
            return self.timeAttribute('TMP', 'last_valid_time',
                       self.timeAttribute('TMP', 'fcast_end_time',
                            self.timeAttribute('TMP', 'rtma_end_time', None)))
        elif weather == 'wetness':
            return self.timeAttribute('POP', 'last_valid_time',
                        self.timeAttribute('POP', 'fcast_end_time',
                             self.timeAttribute(POP, 'rtma_end_time', None)))
        else: return self.obsEndTime(weather)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def obsEndTime(self, dataset_path):
        return self.timeAttribute(dataset_path, 'rtma_end_time',
                    self.timeAttribute(dataset_path, 'last_valid_time', None))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class WeatherFileReader(WeatherFileMethods, HourlyGridFileReader):
    pass


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class WeatherManagerMethods(WeatherFileMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def inputProcessor(self, dataset_path):
        if '.' in dataset_path: key = dataset_path.split('.')[-1]
        else: key = dataset_path
        return self.processors.get(key.upper(), None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def lastObsTime(self, dataset_path):
        return self.timeAttribute(dataset_path, 'last_obs_time',
                    self.timeAttribute(dataset_path, 'rtma_end_time', None))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def processedPrecip(self, start_time, end_time):
        self.config.project.min_pop
        self.config.project.pcpn.fudge
        self.config.project.pcpn.min
        self.config.project.pcpn.replace

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def manageForecastTimes(self, dataset_path, obs_end_time):
        # return True when forcecast is changed, otherwise returns False
        # adjust forecast times that were replaced by reanalysis
        fcast_start = self.timeAttribute(dataset_path, 'fcast_start_time', None)
        fcast_end = self.timeAttribute(dataset_path, 'fcast_end_time', None)
        # no forecast in file
        if fcast_start is None:
            if fcast_end is None: # OK, do nothing
                return False

            # fcast_end but no start
            errmsg = 'ERROR in file :\n%s\n"fcast_start_time"'
            errmsg += ' attribute is not set for dataset "%s",\n'
            errmsg += 'but "forecast_end_time" attribute is set to %s.'
            args = (self.filepath, dataset_path, timeString(fcast_end))
            raise AttributeError, errmsg % args

        if fcast_end is None: # fcast_start but no end
            errmsg = 'ERROR in file :\n%s\n"fcast_start_time"' 
            errmsg += ' attribute for dataset "%s" was set to %s,\n'
            errmsg += 'but "forecast_end_time" attribute is not present.'
            args = (self.filepath, dataset_path, timeString(fcast_start))
            raise AttributeError, errmsg % args

        if fcast_start <= obs_end_time:

            if fcast_end <= obs_end_time: # forecast completely overwritten
                self.removeForecast(dataset_path)
            else:
                # some part of forecast survived reanalysis uptime
                fcast_start = obs_end_time + ONE_HOUR
                
                season_end = self.timeAttribute(dataset_path, 'end_time')
                if fcast_start < fcast_end and fcast_start < season_end:
                    # adjust forecast start to be after new obs_end_time
                    # potentially a daily occurrence
                    self.setTimeAttribute(dataset_path, 'fcast_start_time',
                                          fcast_start)
                else:
                    # this will happen at end of season
                    self.removeForecast(dataset_path)
            return True

        return False

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def manageObsTimes(self, dataset_path, end_time):
        last_obs_time = self.timeAttribute(dataset_path, 'last_obs_time', None)
        
        if last_obs_time is None: # should only happen once
            self.setTimeAttribute(dataset_path, 'last_obs_time', end_time)
            self.setTimeAttribute(dataset_path, 'rtma_end_time', end_time)

        elif end_time > last_obs_time:
            self.setTimeAttribute(dataset_path, 'last_obs_time', end_time)
            self.setTimeAttribute(dataset_path, 'rtma_end_time', end_time)

        last_valid_time = \
            self.timeAttribute(dataset_path, 'last_valid_time', None)
        if last_valid_time is None or end_time > last_valid_time:
            self.setTimeAttribute(dataset_path, 'last_valid_time', end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def removeForecast(self, dataset_path):
        # new data stomped on entire forecast
        if self.datasetHasAttribute(dataset_path, 'fcast_start_time'):
            self.deleteDatasetAttribute(dataset_path, 'fcast_start_time')
            self.deleteDatasetAttribute(dataset_path, 'fcast_end_time')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateForecast(self, dataset_path, start_time, data, **kwargs):
        process = self.inputProcessor(dataset_path)
        if process is not None: data = process(data)
        # by default, all data is valid
        valid_data = data

        last_obs_time = self.lastObsTime(dataset_path)

        start_adjusted = False
        # looks for exceptions, forecast data overlapping observations
        if last_obs_time is not None:
            if len(data.shape) == 3:
                fcast_hours = data.shape[0]
                end_time = start_time + datetime.timedelta(hours=fcast_hours-1)
                if end_time <= last_obs_time:
                    errmsg = 'Attempting to insert forecast data for %s '
                    errmsg += 'thru %s over observation data ending at %s'
                    times = (timeString(start_time), timeString(end_time),
                             timeString(last_obs_time))
                    raise IndexError, errmsg % times
    
                if start_time == last_obs_time:
                    if valid_hours > 1:
                        valid_data = data[1:,:,:]
                        start_time = last_obs_time + ONE_HOUR
                        start_adjusted = True
                    else:
                        errmsg = 'Attempting to insert forecast for %s over'
                        errmsg += ' observation data at %s'
                        times = (timeString(start_time), timeString(last_obs_time))
                        raise IndexError, errmsg % times

                elif start_time < last_obs_time:
                    hours = tzutils.hoursInTimespan(last_obs_time, start_time)
                    start_time = last_obs_time + datetime.timedelta(hours=hours)
                    valid_data = data[hours:,:,:]
                    start_adjusted = True

            else:
                if start_time <= last_obs_time:
                    errmsg = 'Attempting to insert forecast for %s over'
                    errmsg += ' observation data ending at %s'
                    times = (timeString(start_time), timeString(last_obs_time))
                    raise IndexError, errmsg % times

        time_index = self.indexForTime(dataset_path, start_time, **kwargs)
        num_hours = self._insertTimeSlice(dataset_path, valid_data, time_index,
                                          **kwargs)
        if num_hours > 1:
            end_time = start_time + datetime.timedelta(hours=num_hours-1)
        else: end_time = start_time

        prev_fcast_start = self.timeAttribute(dataset_path, 'fcast_start_time')
        if prev_fcast_start is None:
            self.setTimeAttribute(dataset_path, 'fcast_start_time', start_time)
            self.setTimeAttribute(dataset_path, 'fcast_end_time', end_time)

        else:
            if last_obs_time is None:
                first_valid_fcast = self.timeAttribute(dataset_path, 'start_time')
            else: first_valid_fcast = last_obs_time + ONE_HOUR

            if start_time == first_valid_fcast:
                self.setTimeAttribute(dataset_path, 'fcast_start_time', 
                                      start_time)
            if end_time > self.timeAttribute(dataset_path, 'fcast_end_time'):
                self.setTimeAttribute(dataset_path, 'fcast_end_time', end_time)

        # last valid "should" always end of forecast
        last_valid = self.timeAttribute(dataset_path, 'last_valid_date', None)
        if last_valid is None or end_time > last_valid:
            self.setTimeAttribute(dataset_path, 'last_valid_time', end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateReanalysis(self, dataset_path, start_time, data, **kwargs):

        process = self.inputProcessor(dataset_path)
        if process is not None: data = process(data)

        time_index = self.indexForTime(dataset_path, start_time, **kwargs)
        num_hours = \
            self._insertTimeSlice(dataset_path, data, time_index, **kwargs)

        end_time = start_time + datetime.timedelta(hours=num_hours-1)
        self.manageObsTimes(dataset_path, end_time)
        last_obs = self.timeAttribute(dataset_path, 'last_obs_time')
        self.manageForecastTimes(dataset_path, last_obs)

        return end_time


    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initDataProcessors_(self, **kwargs):
        # special processing rules for datasets
        self.processors = ConfigObject('processors', None)
        # humidity data input processor
        def processRhum(data):
            filterNumpyWarnings()
            rhum = N.around(data, 2)
            rhum[N.where(rhum > 100)] = 100.
            rhum[N.where(rhum < 0)] = 0.
            resetNumpyWarnings()
            return rhum
        self.processors.RHUM = processRhum

        # temperature data input processor
        def processTemp(data):
            return N.around(data, 2)
        self.processors.DPT = processTemp
        self.processors.TMP = processTemp

        # precip data input processor
        def processPcpn(data):
            filterNumpyWarnings()
            data[N.where(data < 0.01)] = 0.
            resetNumpyWarnings()
            return N.around(data, 2)
        self.processors.PCPN = processPcpn

        processors = kwargs.get('processors', None)
        if processors is not None:
            if isinstance(processors, dict):
                for key, function in processors.items():
                    self.processors[key] = function
            elif isinstance(processors, (tuple, dict)):
                for key, function in processors:
                    self.processors[key] = function
            else:
                errmsg = '"processors" kwarg must be dict,tuple or list : NOT '
                TypeError, errmsg + str(type(processors))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class WeatherFileManager(WeatherManagerMethods, HourlyGridFileManager):

    def __init__(self, hdf5_filepath, mode='r', **kwargs):
        HourlyGridFileManager.__init__(self, hdf5_filepath, mode)
        self._initDataProcessors_(**kwargs)
        if not self.fileHasAttribute('filetype'):
            self.close()
            self.open('a')
            if self.hasDataset('TMP'):
                self.setFileAttribute('filetype','temps')
            elif self.hasDataset('PCPN'):
                self.setFileAttribute('filetype','wetness')
            self.close()
            self.open(mode)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class WeatherFileBuilder(WeatherManagerMethods, HourlyGridFileBuilder):
    """ Creates a new HDF5 file with read/write access to 3D gridded data
    where the first dimension is time, the 2nd dimension is longitude and
    the 3rd dimension is latitude.
    """
    def __init__(self, hdf5_filepath, config, weather, year, month, timezone,
                       source, region, lons, lats, mode='w'):
        start_time = datetime.datetime(year, month, 1, 0)
        end_time = datetime.datetime(year,month,lastDayOfMonth(year,month),23)

        HourlyGridFileBuilder.__init__(self, hdf5_filepath, config, weather,
                              region, source, timezone, lons, lats, mode=mode,
                              start_time=start_time, end_time=end_time)
        self.open('a')
        self.setFileAttribute('filetype', weather)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveSourceAttributes(self, **kwargs): 
        """
        resolve data source attributes for a dataset
        """
        source = self.source
        attrs = {
            'grid_type': source.tag,
            'region': self.region.name,
            'source':'Reanalysis & forecast model data resampled to ACIS HiRes grid',
            'sources':'RTMA,URMA,NDFD'
        }
        
        node_spacing = source.get('node_spacing',None)
        if node_spacing is not None:
            attrs['node_spacing'] = node_spacing 

        search_radius = source.get('search_radius',None)
        if search_radius is not None:
            attrs['node_search_radius'] = search_radius

        return attrs
