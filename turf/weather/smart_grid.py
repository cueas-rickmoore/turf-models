
import datetime
import warnings

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from turf.weather.factory import TurfWeatherFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartWeatherDataMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableForecastTimes(self, weather_key, fcast_start, fcast_end):
        found_start = None
        found_end = None

        if isinstance(weather_key, tuple):
            weather = self.weatherFileKey(weather_key[0])
        else: weather = weather_key

        slices = self.timeSlices(fcast_start, fcast_end)
        for index, (slice_start, slice_end) in enumerate(slices):
            start_time, end_time = \
                self.weatherForecastTimes(weather, slice_start)
            if start_time is not None:
                if end_time >= fcast_end:
                    if found_start is None or fcast_start > found_start:
                        return fcast_start, fcast_end
                    return found_start, fcast_end
                
                if found_start is None:
                    found_start = start_time
                found_end = end_time
            else:
                if found_start is not None:
                    return found_start, found_end

        return found_start, found_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableReanalysisTimes(self, weather_key, request_start, request_end):
        analysis_start = None
        analysis_end = None

        if isinstance(weather_key, tuple):
            weather = self.weatherFileKey(weather_key[0])
        else: weather = weather_key

        slices = self.timeSlices(request_start, request_end)
        last_index = len(slices) -1

        for index, (slice_start, slice_end) in enumerate(slices):
            status, end_time = \
                self.weatherReanalysisEnd(weather, slice_start, slice_end)

            if status == 0: # continue to next slice 
                analysis_end = end_time
            elif status == 1: # end of data before request_end
                return 0, request_start, end_time
            else: # status = -1 ... no analysis in latest weather file  
                if index == 0: # first slice, no reanalysis yet 
                    return -1, None, None
                # reanalysis ended at end of previous file
                return 0, request_start, analysis_end

        # reanalysis data present in every slice
        return 1, request_start, analysis_end
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def keyWeatherTimes(self, weather, date_or_time):
        weather_key = self.weatherFileKey(weather)
        if weather_key == 'temps': dataset = 'TMP'
        elif weather_key == 'wetness': dataset = 'RHUM'
        else: dataset = weather

        return {
          'last_obs_time': self.timeAttribute(dataset, 'rmta_end_time',
                                self.timeAttribute(dataset, 'last_obs_time')),
          'fcast_start_time': self.timeAttribute(dataset, 'fcast_start_time'),
          'fcast_end_time': self.timeAttribute(dataset, 'fcast_end_time'),
          'last_valid_time': self.timeAttribute(dataset, 'last_valid_time'),
        }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def lastWeatherHour(self, weather, date_or_time):
        weather_key = self.weatherFileKey(weather)
        reader = self.weatherFileReader(weather_key, date_or_time.year,
                                        date_or_time.month, self.region)
        if weather == weather_key:
            if weather_key == 'temps':
                hour = reader.timeAttribute('TMP', 'last_valid_time', None)
            elif weather_key == 'wetness':
                hour = reader.timeAttribute('POP', 'last_valid_time', None)
        else: hour = reader.timeAttribute(weather, 'last_valid_time', None)
        reader.close()

        return hour

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeSlices(self, slice_start_time, slice_end_time):

        slices = [ ]
        start_time = tzutils.tzaDatetime(slice_start_time, self.data_tzinfo)
        end_time = tzutils.tzaDatetime(slice_end_time, self.data_tzinfo)

        if start_time.month == end_time.month:
            slices.append((start_time, end_time))
        else:
            last_day = lastDayOfMonth(start_time)
            month_end = start_time.replace(day=last_day, hour=23)
            slices.append((start_time, month_end))
            
            month = start_time.month + 1
            while month < end_time.month:
                month_start = start_time.replace(month=month, day=1, hour=0)
                last_day = lastDayOfMonth(month_start)
                month_end = month_start.replace(day=last_day, hour=23)
                slices.append((month_start, month_end))
            
            slices.append((end_time.replace(day=1, hour=0), end_time))

        return tuple(slices)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def variableSlice(self, variable, slice_start_time, slice_end_time):
        slices = self.timeSlices(slice_start_time, slice_end_time)
        num_hours = tzutils.hoursInTimespan(slices[0][0], slices[-1][1])

        # filter annoying numpy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',"invalid value encountered in greater")
        warnings.filterwarnings('ignore',"invalid value encountered in less")
        warnings.filterwarnings('ignore',"Mean of empty slice")
        # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

        data = N.empty((num_hours,) + self.grid_dimensions, dtype=float)
        data.fill(N.nan)

        units = None
        prev_indx = 0
        for first_hour, last_hour in slices:
            year = first_hour.year
            month = first_hour.month

            sindx = prev_indx
            eindx = sindx + tzutils.hoursInTimespan(first_hour, last_hour)
            reader = self.weatherFileReader(variable, year, month, region)
            data[sindx:eindx,:,:] = \
                reader.timeSlice(variable, first_hour, last_hour)
            if sindx == 0: units = reader.datasetAttribute(variable, 'units')
            prev_indx = eindx
            reader.close()

        # turn annoying numpy warnings back on
        warnings.resetwarnings()

        return units, data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherForecastTimes(self, weather, target_date_or_time):
        if isinstance(weather, tuple):
            variable = weather[0]
            weather_key = self.weatherFileKey(variable)
        else:
            weather_key = weather
            if weather == 'temps': variable = 'TMP'
            elif weather == 'wetness': variable = 'RHUM'
        reader = self.weatherFileReader(weather_key, target_date_or_time.year,
                                        target_date_or_time.month, self.region)
        fcast_start = reader.timeAttribute(variable, 'fcast_start_time', None)
        fcast_end = reader.timeAttribute(variable, 'fcast_end_time', None)
        reader.close()

        return fcast_start, fcast_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherReanalysisEnd(self, weather, slice_start, slice_end):
        if isinstance(weather, tuple):
            variable = weather[0]
            weather_key = self.weatherFileKey(variable)
        else:
            weather_key = weather
            if weather == 'temps': variable = 'TMP'
            elif weather == 'wetness': variable = 'RHUM'

        # first check file for month at end of slice
        reader = self.weatherFileReader(weather_key, slice_start.year,
                                        slice_start.month, self.region)
        last_obs = reader.timeAttribute(variable, 'last_obs_time',
                       reader.timeAttribute(variable, 'rtma_end_time', None))
        file_end_time = reader.timeAttribute(variable, 'end_time')
        reader.close()

        if last_obs is None: return -1, None
        if last_obs == file_end_time: return 0, last_obs 
        if last_obs <= slice_end:
            return 1, last_obs
        else: return 1, slice_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherSlice(self, variables, slice_start_time, slice_end_time):
        weather_key = self.weatherFileKey(variables[0])
        region = self.region

        slices = self.timeSlices(slice_start_time, slice_end_time)
        num_hours = tzutils.hoursInTimespan(slices[0][0], slices[-1][1])

        data = {}
        units = {}
        for variable in variables:
            empty = N.empty((num_hours,) + self.grid_dimensions, dtype=float)
            empty.fill(N.nan)
            data[variable] = empty

        # filter annoying numpy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',"invalid value encountered in greater")
        warnings.filterwarnings('ignore',"invalid value encountered in less")
        warnings.filterwarnings('ignore',"Mean of empty slice")
        # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

        first_hour = slices[0][0]
        reader = self.weatherFileReader(weather_key, first_hour.year,
                                        first_hour.month, region)
        prev_month = first_hour.month
        prev_indx = 0
        for first_hour, last_hour in slices:
            year = first_hour.year
            month = first_hour.month

            sindx = prev_indx
            eindx = sindx + tzutils.hoursInTimespan(first_hour, last_hour)
            if first_hour.month != prev_month:
                if reader is not None: reader.close()
                reader = \
                    self.weatherFileReader(weather_key, year, month, region)
                prev_month = first_hour.month

            for variable in variables:
                data[variable][sindx:eindx,:,:] = \
                    reader.timeSlice(variable, first_hour, last_hour)
                if sindx == 0:
                    units[variable] = reader.datasetAttribute(variable,'units')

            prev_indx = eindx
        reader.close()


        # turn annoying numpy warnings back on
        warnings.resetwarnings()

        results = { }
        for variable in variables:
            results[variable] = (units[variable], data[variable])

        return results

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherTimeAttributes(self, weather_key, date):
        reader = self.weatherFileReader(weather_key, date.year, date.month,
                                        self.region)
        if weather == 'temps':
            time_attrs = reader.timeAttributes('TMP')
        elif weather == 'wetness':
            time_attrs = reader.timeAttributes('RHUM')
        else: time_attrs = reader.timeAttributes(weather_key)
        reader.close()

        return time_attrs


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartWeatherDataReader(SmartWeatherDataMethods, TurfWeatherFileFactory):

    def __init__(self, region, **kwargs):
        TurfWeatherFileFactory.__init__(self, **kwargs)
        if isinstance(region, basestring):
            self.region = self.config.regions[region]
        else: self.region = region
        source = kwargs.get('source', self.config.project.source)
        self.source = self.config.sources[source]
        dims = self.source.grid_dimensions[self.region.name]
        self.grid_dimensions = (dims.lat, dims.lon)

        self.data_tzinfo = tzutils.asTzinfo(self.project.data_timezone)
        self.local_tzinfo = tzutils.asTzinfo(self.project.local_timezone)

