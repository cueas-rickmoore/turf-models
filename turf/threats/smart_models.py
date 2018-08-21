
import os
import datetime
ONE_DAY = datetime.timedelta(days=1)

from atmosci.units import convertUnits
from atmosci.utils import tzutils

from turf.threats.factory import TurfThreatGridFileFactory
from turf.weather.smart_grid import SmartWeatherDataReader


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# risk data retirevers
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getAnthracWeatherData(factory, start_time, end_time):
    weather_vars = factory.threatWeatherVariables('anthrac')

    weather = factory.weatherSlice(weather_vars.temps, start_time, end_time)
    tmp_units, temp = weather['TMP']
    dpt_units, dewpt = weather['DPT']

    # also need precip for leaf wetness
    weather = factory.weatherSlice(weather_vars.wetness, start_time, end_time)
    pcpn_units, pcpn = weather['PCPN']

    return temp, dewpt, pcpn, tmp_units, pcpn_units

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def getBpatchWeatherData(factory, start_time, end_time):
    weather_vars = factory.threatWeatherVariables('bpatch')

    weather = factory.weatherSlice(weather_vars.temps, start_time, end_time)
    tmp_units, temp = weather['TMP']
    dpt_units, dewpt = weather['DPT']

    weather = factory.weatherSlice(weather_vars.wetness, start_time, end_time)
    pcpn_units, pcpn = weather['PCPN']
    rh_units, rhum = weather['RHUM']

    return start_time, temp, rhum, pcpn, dewpt, tmp_units, pcpn_units

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def getDspotWeatherData(factory, start_time, end_time):
    weather_vars = factory.threatWeatherVariables('dspot')

    weather = factory.weatherSlice(weather_vars.temps, start_time, end_time)
    tmp_units, temp = weather['TMP']

    weather = factory.weatherSlice(weather_vars.wetness, start_time, end_time)
    pcpn_units, pcpn = weather['PCPN']
    rh_units, rhum = weather['RHUM']

    return temp, rhum, pcpn, tmp_units, pcpn_units

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def getHstressWeatherData(factory, start_time, end_time):
    weather_vars = factory.threatWeatherVariables('hstress')

    weather = factory.weatherSlice(weather_vars.temps, start_time, end_time)
    tmp_units, temp = weather['TMP']

    weather = factory.weatherSlice(weather_vars.wetness, start_time, end_time)
    rh_units, rhum = weather['RHUM']

    return temp, rhum, tmp_units

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def getPblightWeatherData(factory, start_time, end_time):
    weather_vars = factory.threatWeatherVariables('pblight')

    weather = factory.weatherSlice(weather_vars.temps, start_time, end_time)
    tmp_units, temp = weather['TMP']

    weather = factory.weatherSlice(weather_vars.wetness, start_time, end_time)
    rh_units, rhum = weather['RHUM']

    return temp, rhum, tmp_units


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# reanalysis data models
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def anthracRiskModel(period, start_date, debug=False):
    from turf.threats.anthrac import Anthracnose
    return Anthracnose(period, debug)

def bpatchRiskModel(period, start_date, debug=False):
    from turf.threats.bpatch import BrownPatch
    return BrownPatch(start_date.year, period, debug)

def dspotRiskModel(period, start_date, debug=False):
    from turf.threats.dspot import DollarSpot
    return DollarSpot(period, debug)

def hstressRiskModel(period, start_date, debug=False):
    from turf.threats.hstress import HeatStress
    return HeatStress()

def pblightRiskModel(period, start_date, debug=False):
    from turf.threats.pblight import PythiumBlight
    return PythiumBlight(period, debug)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartThreatModelFactory(TurfThreatGridFileFactory):
    """
    Basic factory for accessing data in TurfThreat grib files.
    """
    def __init__(self, **kwargs):
        # initialize common configuration structure
        TurfThreatGridFileFactory.__init__(self, **kwargs)

        self.path_mode = 'default'

        self.riskModels = {
            'anthrac': anthracRiskModel,
            'bpatch':  bpatchRiskModel,
            'dspot':   dspotRiskModel,
            'hstress': hstressRiskModel,
            'pblight': pblightRiskModel,
        }

        self.weatherDataReaders = {
            'anthrac': getAnthracWeatherData,
            'bpatch':  getBpatchWeatherData,
            'dspot':   getDspotWeatherData,
            'hstress': getHstressWeatherData,
            'pblight': getPblightWeatherData,
        }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableForecastTimes(self, weather, slice_start, slice_end):
        """
        Returns:
            Python dict with values for all time attributes that are
            associated with datasets in the file.
            NOTE: "None" will be returned for any time attributes that
                   have not been set yet. This should only occured in
                   the first day or two of the season.
        """
        smart = self.smartWeatherReader()
        return smart.availableForecastTimes(weather,slice_start,slice_end)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableReanalysisTimes(self, weather, slice_start, slice_end):
        """
        Returns:
            Python dict with values for all time attributes that are
            associated with datasets in the file.
            NOTE: "None" will be returned for any time attributes that
                   have not been set yet. This should only occured in
                   the first day or two of the season.
        """
        smart = self.smartWeatherReader()
        return smart.availableReanalysisTimes(weather,slice_start,slice_end)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def commonFcastEnd(self, threat_key, date):
        weather = self.threatWeather(threat_key).attrs
        fcast_end = tzutils.asUTCTime(datetime.datetime(date.year,12,31,23))

        factory = self.smartWeatherReader()
        for weather_key, variables in weather.items():
            reader = factory.weatherFileReader(weather_key, date.year,
                                               date.month, 'NE')
            for variable in variables:
                var_end = reader.timeAttribute(variable, 'fcast_end_time')
                if var_end is None:
                    if variable.lower() == 'pcpn': continue
                    return None
                fcast_end = min(fcast_end, var_end)
        return fcast_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def commonObsEnd(self, threat_key, date):
        weather = self.threatWeather(threat_key).attrs
        last_obs = tzutils.asUTCTime(datetime.datetime(date.year,12,31,23))

        factory = self.smartWeatherReader()
        for weather_key, variables in weather.items():
            reader = factory.weatherFileReader(weather_key, date.year,
                                               date.month, 'NE')
            for variable in variables:
                var_end = reader.timeAttribute(variable, 'last_obs_time')
                if var_end is None: return None
                last_obs = min(last_obs, var_end)
        return last_obs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def discoverFcastStartDate(self, threat_key, period_key, dataset='risk'):
        today = datetime.date.today()
        # reader for date attributes in current season (today)
        reader = self.threatFileReader(threat_key, period_key, today.year)
        # last_obs is last date when reanalysis data occurs in the file
        last_obs = reader.dateAttribute(dataset, 'last_obs_date', None)
        season_start = reader.dateAttribute(dataset, 'start_date'),
        season_end = reader.dateAttribute(dataset, 'end_date')
        reader.close()

        if last_obs is not None: # some reanalysis data in file
            fcast_start = last_obs + ONE_DAY
        else: # no reanalysis data in the file
            fcast_start = today # today is always a forecast
            if fcast_start < season_start:
                # no updates before season begins
                if (season_start - fcast_start).days > 5:
                    return "Before season start, too early to do forecast."
                else: fcast_start = season_start

        # allow forecast to begin up to end of season
        if fcast_start > season_end: return "Season is over."
        return fcast_start

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def discoverObsStartDate(self, threat_key, period_key, dataset='risk'):
        # assume current day is always a forecast
        today = datetime.date.today()

        # reader for date attributes in current season (today)
        reader = self.threatFileReader(threat_key, period_key, today.year)
        # last_obs is last date when reanalysis data occurs in the file
        last_obs = reader.dateAttribute(dataset, 'last_obs_date', None)
        season_start = reader.dateAttribute(dataset, 'start_date')
        season_end = reader.dateAttribute(dataset, 'end_date')
        reader.close()

        if last_obs is not None: # some reanalysis data in file
            # check the day after the last reanalysis
            start_date = last_obs + ONE_DAY
            if start_date >= today: return 'Reanalysis already up to date.'
        else: # no reanalysis data in the file ... should only happen once !!
            start_date = today - ONE_DAY # today is always a forecast

        # no updates before season begins
        if start_date < season_start: return "Season is has not begun."
        # allow update thru end of season
        if start_date > season_end: return "Season is over."
        return start_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def discoverMaxEndDate(self, threat_key, period_key, start_date):
        today = datetime.date.today()
        # get end date for the current season (today)
        season_end = self.threatDateAttribute(threat_key, period_key,
                                              start_date.year, 'end_date')
        # today is always a forecast, yesterday is latest possible reanalysis
        yesterday = today - ONE_DAY
        if yesterday < season_end: return yesterday
        else: return season_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def discoverMaxFcastEnd(self, threat_key, period_key, fcast_start):
        # find max end of forecast beginning fcast_start 
        num_fcast_days = self.project.fcast_days
        fcast_end = fcast_start + datetime.timedelta(days=num_fcast_days)

        # fcast end cannot be after end of current season
        season_end = self.threatDateAttribute(threat_key, period_key,
                                              fcast_start.year, 'end_date')
        if fcast_end < season_end: return fcast_end
        else: return season_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def endInDays(self, threat_key, period_key, start_date, num_days):
        # returns end date for num_days, inclusive of start_date
        season_end = self.threatDateAttribute(threat_key, period_key,
                                              start_date.year, 'end_date')

        end_date = start_date + datetime.timedelta(days=num_days-1)
        if end_date < season_end: return end_date
        else: return season_end

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def filenameTemplate(self, *args):
        if len(args) == 1:
            return self.config.filenames.get(args[0], None)
        else:
            for filename_key in args:
                filename = self.config.filenames.get(filename_key, None)
                if filename is not None: return filename
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getModelWeatherData(self, threat_key, start_time, end_time):
        """
        Returns: tuple
            all weather data for the model and appropriate units
            
        NOTE: returned tuple contins data in the correct argument order
              to pass directly to the model's threatIndex method.

        e.g. data = factory.getModelWeatherData(......)
             threat_index = model.threatIndex(*data)
        """
        getWeatherData = self.weatherDataReader(threat_key)
        return getWeatherData(self, start_time, end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def numForecastDays(self): return self.config.project.fcast_days

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def riskModel(self, threat_key, start_date, period_key, debug=False):
        """
        Returns: fully initialized threat risk model ready to run
        """
        model = self.riskModels[threat_key]
        return model(period_key, start_date, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   
    def riskThresholds(self, threat_key, period_key):
        periods = self.threatParameter(threat_key, 'periods', None)
        if periods is None:
            thresholds = self.threatParameter(threat_key, 'risk_thresholds', None)
        else: thresholds = periods[period_key].risk_thresholds

        return thresholds
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def runRiskModel(self, threat_key, start_date, end_date, period_key,
                           debug=False):

        start_time, end_time = \
        self.threatDataTimespan(threat_key, start_date, end_date, period_key)

        weather_data = \
            self.getModelWeatherData(threat_key, start_date, end_date)

        model = self.riskModel(threat_key, start_date, period_key, debug)
        threat_index = model.threatIndex(*weather_data)
        risk = model.riskLevel(threat_index)

        return start_date, threat_index, risk

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def seasonDateLimits(self, threat_key, period_key, year):
        reader = self.threatFileReader(threat_key, period_key, year)
        start_date = reader.fileDateAttribute('start_date', None)
        end_date = reader.fileDateAttribute('end_date', None)
        reader.close()
        return start_date, end_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def smartWeatherReader(self):
        reader = SmartWeatherDataReader(self.region)
        if self.path_mode != 'default':
            reader.useDirpathsForMode(self.path_mode)
        return reader

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatConfig(self, threat_key): return self.threats[threat_key]

    def threatDayBegins(self, threat_key):
        return datetime.time(hour=self.threats[threat_key].day_begins)

    def threatDayEnds(self, threat_key):
        return datetime.time(hour=self.threats[threat_key].day_begins - 1)

    def threatPaddingHours(self, threat_key, period_key):
        config = self.threats[threat_key]
        if 'periods' in config:
            return config.periods[period_key].padding
        return config.padding

    def threatParameter(self, threat_key, parameter_name, default=None):
        return self.threats[threat_key].get(parameter_name, default)

    def threatPeriod(self, threat_key, period_key):
        config = self.threats[threat_key]
        if 'periods' in config: return config.periods[period_key]
        return config # anything used for a period is in main config

    def threatPaddingPadding(self, threat_key, period_key, snitch=True):
        pad_hours = self.threatPaddingHours(hreat_key, period_key)
        if snitch: pad_hours -= 1
        return datetime.timedelta(hours=pad_hours)

    def threatWeatherVariables(self, threat_key):
        return self.threats[threat_key].weather

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatDateAttribute(self, threat_key, period_key, year, attr,
                                  dataset='risk'):
        reader = self.threatFileReader(threat_key, period_key, year)
        date = reader.dateAttribute(dataset, attr, None)
        reader.close()
        return date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatDateAttributes(self, threat_key, period_key, year,
                                   dataset='risk'):
        reader = self.threatFileReader(threat_key, period_key, year)
        dates = (
            reader.dateAttribute(dataset, 'start_date'),
            reader.dateAttribute(dataset, 'first_valid_date', None),
            reader.dateAttribute(dataset, 'rtma_end_date'),
            reader.dateAttribute(dataset, 'last_obs_date', None),
            reader.dateAttribute(dataset, 'fcast_end_date', None),
            reader.dateAttribute(dataset, 'last_valid_date', None),
            reader.dateAttribute(dataset, 'end_date'),
            reader.lastUpdate(dataset),
        )
        reader.close()
        return dates
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatFileAttributes(self, threat_key, period_key, year):
        reader = self.threatFileReader(threat_key, period_key, year)
        attrs = reader.objectAttributes()
        attrs['filepath'] = reader.filepath
        reader.close()
        return attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatRiskThresholds(self, threat_key, period_key):
        periods = self.threatParameter(threat_key, 'periods', None)
        if periods is not None:
            return periods.get('%s.%s' % (period_key, risk_thresholds))
        return self.threatParameter(threat_key, 'risk_thresholds')
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatWeatherEndTime(self, threat_key, target_date, period_key):
        """
        This routine determines the date/time that input data must end in 
        order to obtain data for the target_date.

        Arguments:
            threat_key: short name for threat/disease configuration
            target_date: datetime.date object for the last date
                         desired in threat risk results.
            period_key: key string for accessing period configuration

        Turf threat/disease models require data for a "standard"
        24 hour day that begins on the morning of the previous day.

        e.g. a model run for target_date == 3/2/2018 would begin at
             8 AM on 3/1/2018 and end at 7 AM on 3/2/2018.

        Returns:
            datetime.datetime object with the UTC time of the last
            hour that data must contain in order to return results
            for the target_date.
            NOTE: this will always be an hour of the target_date
        """
        day_ends = self.threatDayEnds(threat_key)
        end_time = datetime.datetime.combine(target_date + ONE_DAY, day_ends)
        end_time = tzutils.asUTCTime(end_time, self.project.local_timezone)
        return end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatWeatherStartTime(self, threat_key, target_date, period_key):
        """
        This routine determines the time that input data must start in 
        order to return daily results beginning on the target_date.

        Arguments:
            threat_key: short name for threat/disease configuration
            target_date: datetime.date object for the first date
                         desired in threat risk results
            period_key: key string for accessing period configuration

        Turf threat/disease models require data for a "standard"
        24 hour day that begins on the morning of the previous day.

        e.g. a model run for target_date == 3/2/2018 would begin at
             8 AM on 3/1/2018 and end at 7 AM on 3/2/2018.

        Returns:
            datetime.datetime object with the UTC time of the first
            hour data must contain in order to return results for
            the target_date.
            NOTE: this will always be a time some number of days
                  (24 hour intervals) PRIOR to the target_date.
        """
        end_hour = self.threatDayEnds(threat_key)
        day_ends = datetime.datetime.combine(target_date + ONE_DAY, end_hour)
        day_ends = tzutils.asUtcTime(day_ends, self.project.local_timezone)
        period_hours = self.threatPeriodPadding(threat_key, period_key, True)
        period_starts = day_ends - period_hours 
        return period_starts

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatWeatherTimespan(self, threat_key, start_date, end_date,
                                    period_key=None):
        """
        Arguments:
            threat_key: short name for threat/disease configuration
            start_date: datetime.date object for the first date
                         desired in threat risk results.
            end_date: datetime.date object for the last date desired
                      in threat risk results.
            period_key: key string for accessing period configuration

        Returns: tuple with
            [0] : first date in threat risk/index results
            [1] : first hour needed to access weather data 
            [2] : last hour needed to access weather data

        NOTE: times in UTC timezone (required for accessing weather data)
        """
        if start_date is None: start_date = end_date
        elif end_date is None: end_date = start_date

        end_time = \
            self.threatWeatherEndTime(threat_key, end_date, period_key)

        if end_date > start_date:
            day_begins = self.threatDayBegins(threat_key)
            start_time = datetime.datetime.combine(start_date, day_begins)
            start_time = \
                tzutils.asUtcTime(start_time, self.project.local_timezone)
        else: start_time = end_time - datetime.timedelta(hours=24)

        # handle the daylight savings glitch
        dst_month, dst_day = self.project.dst_glitch
        if start_date.month == dst_month and start_date.day < dst_day+1:
           if (end_date.month == dst_month and end_date.day >= dst_day) \
               or end_date.month > dst_month:
            start_time -= datetime.timedelta(hours=1)

        padding_hours = self.threatPaddingHours(threat_key, period_key)
        if padding_hours > 0:
            start_time -= datetime.timedelta(hours=padding_hours)

        return start_date, start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def validateTimespan(self, threat_key, period_key, start_date, end_date):
        season_start, season_end = \
            self.seasonDateLimits(threat_key, period_key, start_date.year)
        changed = None
        if start_date < season_start:
            if end_date < season_start:
                return False, None, 'Requested dates are before season begins.'
            start_date = season_start
            changed = 'Start date adjusted to season start date.'
        if start_date > season_end:
            return False, None, 'Requested dates are after season ends.'

        if end_date > season_end:
            end_date = season_end
            adjusted = 'End date adjusted to season end date.'
            if changed is None: changed = adjusted
            else: changed = '%s\n%s' % (changed, adjusted)

        if changed is None: return True, (start_date, end_date), None
        return True, (start_date, end_date), changed

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherDataReader(self, threat_key):
        return self.weatherDataReaders[threat_key]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherSlice(self, weather_vars, start_time, end_time):
        smart = self.smartWeatherReader()
        return smart.weatherSlice(weather_vars, start_time, end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def useDirpathsForMode(self, mode):
        TurfThreatGridFileFactory.useDirpathsForMode(self, mode)
        self.path_mode = mode

