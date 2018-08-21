
import os
import datetime

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.seasonal.factory  import SeasonalStaticFileFactory

from turf.factory import TurfProjectFactoryMethods

from turf.weather.grid import WeatherFileReader, \
                              WeatherFileManager, \
                              WeatherFileBuilder


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.weather.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfWeatherFileFactory(TurfProjectFactoryMethods,
                             SeasonalStaticFileFactory):
    """
    Basic factory for accessing data in TurfThreat grib files.
    """
    def __init__(self):
        # initialize common configuration structure
        SeasonalStaticFileFactory.__init__(self, CONFIG)
        self._initTurfFactory_()
        self._initTurfWeatherGridFactory_()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildWeatherFile(self, weather, year, month, region='NE',
                               timezone='UTC'):
        src_cfg = self.sourceConfig('acis')
        reader = self.staticFileReader(src_cfg, region)
        lats = reader.getData('lat')
        lons = reader.getData('lon')
        reader.close()
        del reader

        builder = self.weatherFileBuilder(weather, year, month, timezone,
                                          src_cfg, region, None, None, 'w')
        # build coordinate datasets and empty weather datasets
        builder.build(lons=lons, lats=lats)
        builder.close()

        return builder

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def isWeatherFile(self, weather, year, month, region='NE'):
        filepath = self.weatherFilepath(weather, year, month, region)
        return os.path.exists(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def obsTimeForDate(self, date, hour, timezone):
        obs_time = datetime.datetime.combine(date, datetime.time(hour))
        return tzutils.asLocalTime(obs_time, timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherDirpath(self, weather, year, month, region='NE', **kwargs):
        weather_key = self.weatherFileKey(weather)
        subdirs = os.sep.join(self.config.subdir_paths.weather)
        template = os.path.join(self.config.dirpaths.turf, subdirs)
                                
        template_args = {'year':year, 'month':month, 'weather':weather_key}
        template_args['region'] = self.regionToDirpath(region)
        
        grid_dirpath = template % template_args
        if not os.path.exists(grid_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Turf weather directory does not exist :\n%s'
                raise IOError, errmsg % grid_dirpath
            else: os.makedirs(grid_dirpath)
        return grid_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFileKey(self, variable):
        if variable in ('DPT','temps','TMP'): return 'temps'
        elif variable in ('PCPN','POP','RHUM','wetness'): return 'wetness'
        raise KeyError, 'Cannot map "%s" to a weather file key' % variable

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFilename(self, weather, year, month, region='NE'):
        weather_key = self.weatherFileKey(weather)
        template = self.config.filenames.get(weather_key, None)
        if template is None:
            raise LookupError, 'No template for "%s" grid file' % weather
        template_args = {
                'year':year, 'month':month,
                'weather':weather_key.title()}
        return template % { 'target_month':'%d%02d' % (year,month), }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFilepath(self, weather, year, month, region='NE', **kwargs):
        dirpath = self.weatherDirpath(weather, year, month, region, **kwargs)
        filename = self.weatherFilename(weather, year, month, region)
        filepath = os.path.join(dirpath, filename)
        return filepath
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFileBuilder(self, weather, year, month, timezone='UTC',
                                 source='acis', region='NE', lons=None,
                                 lats=None, mode='a', filepath=None):
        if filepath is None:
            filepath = self.weatherFilepath(weather, year, month, region)

        Class = self.AccessClasses.weather.build
        weather_key = self.weatherFileKey(weather)
        return Class(filepath, self.config, weather_key, year, month, timezone,
                     source, region, lons, lats, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFileManager(self, weather, year, month, region='NE', mode='r',
                                 filepath=None):
        if filepath is None:
            filepath = self.weatherFilepath(weather, year, month, region)
        if not os.path.isfile(filepath):
            errmsg = '%d/%d %s grid file does not exist :\n    %s'
            raise IOError, errmsg % (year, month, weather.upper(), filepath)

        Class = self.AccessClasses.weather.manage
        return Class(filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFileReader(self, weather, year, month, region='NE',
                                filepath=None):
        if filepath is None:
            filepath = self.weatherFilepath(weather, year, month, region)
        if not os.path.isfile(filepath):
            errmsg = '%d/%d %s grid file does not exist :\n    %s'
            raise IOError, errmsg % (year, month, weather.upper(), filepath)

        Class = self.AccessClasses.weather.read
        return Class(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def weatherFileTimespan(self, year, month, timezone='UTC'):
        """
        Returns tuple with start hour and end hour for the monthly file.
        If timezone is specified, times will be adjust to that timezone.
        Otherwise, times are in UTC timezones (same as times in file).
        """
        start_time = datetime.datetime(year,month,1,0)
        start_time = tzutils.tzaDatetime(start_time, 'UTC')
        last_day = lastDayOfMonth(year, month)
        end_time = datetime.datetime(year,month,last_day,23)
        end_time = tzutils.tzaDatetime(end_time, 'UTC')

        if timezone != 'UTC':
            start_time = tzutils.asLocalTime(start_time, timezone)
            end_time = tzutils.asLocalTime(end_time, timezone)

        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def projectDirpath(self, *args):
        if len(args) == 1:
            dirpath =  self.config.dirpaths.get(args[0], None)
        else:
            for dirpath_key in args:
                dirpath = self.config.dirpaths.get(dirpath_key, None)
                if dirpath is not None: break

        if isinstance(dirpath, tuple):
            return os.sep.join(dirpath)
        return dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def subdirPath(self, *args):
        if len(args) == 1:
            subdir = self.config.subdir_paths.get(args[0], None)
        else:
            for subdir_key in args:
                subdir = self.config.subdir_paths.get(subdir_key, None)
                if subdir is not None: break

        if isinstance(subdir, tuple):
            return os.sep.join(subdir)
        return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _extractTimes(self, year, **kwargs):
        start_date = kwargs.get('start_date', None)
        if start_date is None:
            date_tuple = (year,) + self.project.start_day
            start_date = datetime.date(*date_tuple)

        end_date = kwargs.get('end_date', None)
        if end_date is None:
            date_tuple = (year,) + self.project.end_day
            end_date = datetime.date(*date_tuple)
                
        return { 'end_date':end_date, 'start_date':start_date,
                 'target_year':year }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _normalizeWeatherPath(self, weather):
        weather = self.weather.get(weather, None)
        if weather is not None and 'fullname' in weather:
            fullname = weather.fullname
        else: fullname = weather.title()

        return fullname.replace(' ','-')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        SeasonalStaticFileFactory._registerAccessClasses(self)

        self.AccessClasses['weather'] = {
            'build': WeatherFileBuilder,
            'manage': WeatherFileManager,
            'read': WeatherFileReader,
        }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initTurfWeatherGridFactory_(self, **kwargs):
        if kwargs.get('use_dev_env', False): self.useDirpathsForMode('dev')
        self.local_timezone = kwargs.get('local_timezone',
                                     self.project.get('local_timezone',
                                          tzutils.localTimezone()))
        self.file_timezone = kwargs.get('timezone',
                                     self.project.get('file_timezone',
                                          self.local_timezone))

