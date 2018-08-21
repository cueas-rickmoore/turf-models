
import os
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.seasonal.methods.access  import BasicFileAccessorMethods
from atmosci.seasonal.methods.factory import MinimalFactoryMethods
from atmosci.seasonal.methods.paths   import PathConstructionMethods
from atmosci.seasonal.methods.static  import StaticFileAccessorMethods

from atmosci.seasonal.factory  import registerStaticAccessManagers


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisFactoryMethods(PathConstructionMethods,
                               BasicFileAccessorMethods,
                               MinimalFactoryMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def asLocalHour(self, datetime_hour, local_timezone=None):
        return tzutils.asLocalHour(datetime_hour, local_timezone)

    def asUtcHour(self, datetime_hour, local_timezone=None):
        return tzutils.asUtcHour(datetime_hour, local_timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fcastObsTimespan(self, reference_date_or_time, **kwargs):
        if isinstance(reference_date_or_time, datetime.date):
            target = kwargs.get('target_hour', self.project.target_hour)
            ref_time = datetime.datetime.combine(reference_date_or_time,
                                                 datetime.time(target))
        else: # assume it is already a datetime.datetime
            ref_time = reference_date_or_time

        timezone = kwargs.get('timezone', 'UTC')
        ref_time = tzutils.asHourInTimezone(ref_time, timezone)
        
        fcast_days = kwargs.get('fcast_days',self.project.fcast_days)
        fcast_hours = fcast_days * 24
        end_time = ref_time + datetime.timedelta(hours=fcast_hours)

        obs_days = kwargs.get('obs_days',self.project.obs_days)
        obs_hours = obs_days * 24
        start_time = ref_time - datetime.timedelta(hours=obs_hours)

        return start_time, ref_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribVariableName(self, key):
        var_name = self.reanalysis.grib.variable_map.get(key, key.upper())
        if var_name in self.reanalysis.grib.variable_names:
            return var_name
        raise KeyError, '"%s" is not a valid GRIB variable key' % key

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridVariableName(self, key):
        var_name = self.reanalysis.grid.variable_map.get(key, key.upper())
        if var_name in self.reanalysis.grid.variable_names:
            return var_name
        raise KeyError, '"%s" is not a valid GRID variable key' % key

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def monthTimespan(self, reference_date, **kwargs):
        if reference_date.day == 1: ref_date = reference_date
        else: ref_date = reference_date.replace(day=1) 
        ref_time = \
            datetime.datetime.combine(ref_date,datetime.time(hour=0))

        timezone = kwargs.get('timezone', 'UTC')
        start_time = ref_time = tzutils.asHourInTimezone(ref_time, timezone)
        num_days = lastDayOfMonth(ref_date.year, ref_date.month)
        end_time = start_time.replace(day=num_days, hour=23)

        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileTimespan(self, reference_date, **kwargs):
        if isinstance(reference_date, tuple):
            if len(reference_date == 2):
                ref_date = reference_date + (1,)
            else: ref_date = reference_date
        else: # assume it is datetime.date or datetime.date_time
            ref_date = \
                (reference_date.year, reference_date.month, reference_date.day)

        ref_date = datetime.date(*ref_date)
        if kwargs.get('grid_subdir_by_hours',False):
            # timespan based number of hours in obs_days + fcast_days
            start_time, ref_time, end_time = \
                self.fcastObsTimespan(reference_date, **kwargs)

        else: # timespan based on number of days in a month 
            start_time, end_time = self.monthTimespan(ref_date, **kwargs)
            ref_time = start_time
        
        num_hours = tzutils.hoursInTimespan(start_time, end_time)
        return start_time, ref_time, end_time, num_hours

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAnalysisType(self, analysis, **kwargs):
        if '.' in analysis:
            atype, source = analysis.split('.')
            self.analysis_type = atype
        else:
            self.analysis_type = analysis
            source = None

        if self.analysis_type == 'rtma':
            from atmosci.reanalysis.rtma.config import CONFIG
            self.anal_config = CONFIG.sources.rtma
        elif self.analysis_type == 'urma':
            from atmosci.reanalysis.urma.config import CONFIG
            self.anal_config = CONFIG.sources.urma
        else:
            errmsg = '"%s" is an unsupported reanalysis.'
            raise KeyError, errmsg % analysis_type

        if source is None:
            self.setGribSource(CONFIG.project.grib_source)
        else: self.setGribSource(source)

        return CONFIG 

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setGribSource(self, grib_source, **kwargs):
        self.grib_source = self.anal_config[grib_source]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setTimezone(self, timezone):
        if tzutils.isValidTimezone(timezone):
            self.timezone = tzutils.timezoneAsString(timezone)
            self.tzinfo = timezone
        else:
            self.timezone = timezone
            self.tzinfo = tzutils.asTimezoneObj(timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def utcTimes(self, datetime_hour, **kwargs):
        if kwargs.get('use_latest_time', False):
            return {'utc_date':'latest', 'utc_time':'latest',
                    'utc_hour':'latest'}
        elif kwargs.get('use_previous_time', False):
            return {'utc_date':'previous', 'utc_time':'previous',
                    'utc_hour':'previous'}
        elif kwargs.get('use_time_in_path', False):
            return tzutils.utcTimeStrings(datetime_hour)
        else: 
            utc_times = tzutils.utcTimeStrings(datetime_hour)
            utc_times['utc_time'] = utc_times['utc_date']
            return utc_times

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisFactory_(self, analysis_type, **kwargs):
        config = self.setAnalysisType(analysis_type)
        self.project = config.project
        self.reanalysis = config.sources.reanalysis

        timezone = kwargs.get('timezone', self.project.data_timezone)
        self.setTimezone(timezone)

        if kwargs.get('use_dev_env', False): self.useDirpathsForMode('dev')

        return config


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribFactoryMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribDirpath(self, target_hour, region, **kwargs):
        root_dir = self.config.dirpaths[self.reanalysis.grib.root_dir]
        # check for subdir path definition
        subdir = self.gribSubdirTemplate()
        if subdir is not None: root_dir = os.path.join(root_dir, subdir)

        # get all possible template arguments for the directory path
        arg_dict = self.utcTimes(target_hour)
        arg_dict['analysis'] = self.anal_config.name
        if isinstance(region, basestring): arg_dict['region'] = region
        else: arg_dict['region'] = region.name
        arg_dict['source'] = self.grib_source.name
        grib_dirpath = root_dir % arg_dict
        # check for existence of the directory
        if not os.path.exists(grib_dirpath):
            # user is expecting the file to exist, fail when missing
            if kwargs.get('file_must_exist', False):
                errmsg = 'Reanalysis directory does not exist :\n%s'
                raise IOError, errmsg % grib_dirpath
            elif kwargs.get('make_directory', True): os.makedirs(grib_dirpath)
        return grib_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFileExists(self, target_hour, variable, region, **kwargs):
        filepath = self.gribFilepath(target_hour, variable, region, **kwargs)
        return os.path.exists(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilename(self, target_hour, variable, region, **kwargs):
        template = self.gribFilenameTemplate(variable)
        arg_dict = \
            self._gribTemplateArgs(target_hour, variable, region, **kwargs)
        if kwargs: arg_dict.update(dict(kwargs))
        return template % arg_dict

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilenameTemplate(self, variable, **kwargs):
        template = self.grib_source.local_file_map.get(variable,
                        self.grib_source.local_file_map.get('default', None))
        if template is None:
            errmsg = 'No filename template for "%s" variable.'
            raise LookupError, errmsg % variable
        return template
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilepath(self, target_hour, variable, region, **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            root_dir = self.gribDirpath(target_hour, region, **kwargs)
            filename =  self.gribFilename(target_hour, variable, region,
                                          **kwargs)
            filepath = os.path.join(root_dir, filename)
        # check for existence of the file
        if kwargs.get('file_must_exist', False):
            # user is expecting the file to exist, fail when missing
            if not os.path.isfile(filepath):
                errmsg = 'Reanalysis grib file does not exist :\n    %s'
                raise IOError, errmsg % filepath
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFileReader(self, target_hour, variable, region, **kwargs):
        filepath = self.gribFilepath(target_hour, variable, region, **kwargs)
        Class = self.fileAccessorClass('grib', 'read')
        debug = kwargs.get('debug',False)
        source = kwargs.get('source', self.grib_source)
        return Class(filepath, source, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribReader(self, filepath):
        Class = self.fileAccessorClass('grib', 'read')
        return Class(filepath, self.grib_source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribSubdirTemplate(self):
        subdir = self.project.get('grib_subdir',
                      self.reanalysis.get('grib.subdir', None))
        if isinstance(subdir, tuple): return os.path.join(*subdir)
        return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _gribTemplateArgs(self, target_hour, variable, region, **kwargs):
        template_args = tzutils.utcTimeStrings(target_hour)
        template_args['analysis'] = self.analysis_type
        template_args['region'] = region
        template_args['source'] = self.grib_source.name
        template_args['variable'] = variable
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerGribAccessClasses(self):
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from atmosci.reanalysis.grib import ReanalysisGribReader
        self._registerAccessManager('grib', 'read', ReanalysisGribReader)

    _registerAccessClasses = _registerGribAccessClasses

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisGribFactory_(self, **kwargs):
        self.grib_region = \
             kwargs.get('grib_region', self.reanalysis.grib.region)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribFileFactory(StaticFileAccessorMethods,
                                ReanalysisGribFactoryMethods,
                                ReanalysisFactoryMethods, object):
    """
    Basic factory for accessing data in Reanalysis grib files.
    """
    def __init__(self, analysis_type, analysis_source='ncep', **kwargs):
        analysis = '%s.%s' % (analysis_type, analysis_source)
        config_object = self._initReanalysisFactory_(analysis, **kwargs)

        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGribFactory_(**kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFactoryMethods:
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridDirpath(self, reference_time, variable, region, **kwargs):
        root_dir = self.config.dirpaths[self.reanalysis.grid.root_dir]
        subdir = self.gridSubdir(**kwargs)
        if subdir is not None: root_dir = os.path.join(root_dir, subdir)

        arg_dict = \
            self._gridTemplateArgs(reference_time, variable, region, **kwargs)
        arg_dict['region'] = self.regionToDirpath(arg_dict['region'])
        grid_dirpath = root_dir % arg_dict
        if not os.path.exists(grid_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Reanalysis directory does not exist :\n%s'
                raise IOError, errmsg % grid_dirpath
            elif kwargs.get('make_grid_dirs', True):
                os.makedirs(grid_dirpath)
        return grid_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridFilename(self, ref_time, variable, region, **kwargs):
        template = self.gridFilenameTemplate(variable, **kwargs)
        if template is None:
            raise LookupError, 'No template for "%s" grid file name' % variable
        arg_dict = self._gridTemplateArgs(ref_time, variable, region, **kwargs)
        arg_dict['region'] = self.regionToFilepath(arg_dict['region'])
        return template % arg_dict
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridFilepath(self, reference_time, variable, region, **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            root_dir = self.analysisGridDirpath(reference_time, variable,
                                                region, **kwargs)
            filename = self.analysisGridFilename(reference_time, variable,
                                                region, **kwargs)
            filepath = os.path.join(root_dir, filename)
        if kwargs.get('file_must_exist', False):
            if not os.path.isfile(filepath):
                errmsg = 'Reanalysis grid file does not exist :\n    %s'
                raise IOError, errmsg % filepath
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableMonths(self, reference_time, region, variable=None):
        months = [ ]

        ref_time = reference_time.replace(day=1, hour=0)
        dirpath = self. analysisGridDirpath(ref_time, variable, region,
                                            make_grid_dirs=False)
        if os.path.exists(dirpath): months.append(ref_time.month)
        prev_month_str = ref_time.strftime('%Y%m')

        if ref_time.month < 12:
            for month in range(ref_time.month+1, 13):
                ref_time = ref_time.replace(month=month)
                month_str = ref_time.strftime('%Y%m')
                dirpath = dirpath.replace(prev_month_str, month_str)
                if os.path.exists(dirpath):
                    months.append(ref_time)
                prev_month_str = month_str

        return tuple(months)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildReanalysisGridFile(self, reference_time, variable, grid_region,
                                timezone, grid_source='acis'):
        builder = self.gridFileBuilder(reference_time, variable, grid_region,
                                       timezone, None, None, grid_source)
        region = self.regionConfig(grid_region)
        source = self.sourceConfig(grid_source)

        reader = self.staticFileReader(source, region)
        lats = reader.getData('lat')
        lons = reader.getData('lon')
        reader.close()
        del reader

        # build all of the datasets
        builder.build(lons=lons, lats=lats)
        del lats, lons
        print '\nBuilt "%s" reanalysis grid file :' % variable
        print '    ', builder.filepath
        builder.close()
        return builder

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileBuilder(self, reference_time, variable, region, timezone,
                              lons=None, lats=None, grid_source='acis',
                              **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            filepath = self.analysisGridFilepath(reference_time, variable,
                                                 region, **kwargs)
        kwargs['timezone'] = timezone
        kwargs.update(self._extractTimes(reference_time, **kwargs))
        del kwargs['timezone']
        Class = self.fileAccessorClass('reanalysis', 'build')
        return Class(filepath, self.config, variable, region, grid_source,
                     reference_time, timezone, lons, lats, kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileExists(self, reference_time, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(reference_time, variable,
                                             region, **kwargs)
        return os.path.exists(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileManager(self, reference_time, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(reference_time, variable,
                                             region, **kwargs)
        Class = self.fileAccessorClass('reanalysis', 'manage')
        return Class(filepath, kwargs.get('mode','a'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileReader(self, reference_time, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(reference_time, variable,
                                             region, **kwargs)
        Class = self.fileAccessorClass('reanalysis', 'read')
        return Class(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFilenameTemplate(self, variable, **kwargs):
        template = self.grid_file_map.get(variable, None)
        if template is None:
            errmsg = 'No template found for "%s" variable.'
            raise ValueError, errmsg % variable
        return template

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridSubdir(self, **kwargs):
        subdir = self.reanalysis.grid.subdir
        if isinstance(subdir, tuple): return os.path.join(*subdir)
        else: return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def lastAvailableGridHour(self, variable, year, month, region):
        file_time = datetime.datetime(year, month, 1, 0)
        while True:
            filepath = self.analysisGridFilepath(file_time, variable, region,
                                                 make_directory=False)
            if os.path.exists(filepath):
                Class = self.fileAccessorClass('reanalysis', 'read')
                reader = Class(filepath)
                last = reader.timeAttribute(variable, 'last_vallid_time')
                if last is not None: return last

            # only continue backward within current year
            if file_time.month == 1: return None

            file_time.replace(month=file_time.month - 1)

        # failsafe
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def repairMissingReanalysis(self, error_time, variable, region):
        prev_time = error_time - ONE_HOUR
        prev_time_str = prev_time.strftime('%Y-%m-%d:%H')
        if not self.gridFileExists(prev_time, variable, region):
            errmsg = 'Repair failed, file for previous hour (%s) does not exist.'
            return False, errmsg % prev_time_str

        next_time = error_time + ONE_HOUR
        next_time_str = next_time.strftime('%Y-%m-%d:%H')
        if not self.gridFileExists(next_time, variable, region):
            errmsg = 'Repair failed, file for next hour (%s) does nto exist.'
            return False, errmsg % next_time_str

        reader = self.gridFileManager(prev_time, variable, region)
        prev_grid = reader.dataForHour(variable, prev_time)
        num_nans = len(N.where(N.isnan(prev_grid))[0])
        if num_nans == N.product(prev_grid.shape):
            errmsg = 'Repair failed, data also missing for previous hour (%s).'
            return False, errmsg % prev_time_str

        if next_time.month != prev_time.month:
            reader.close()
            reader = self.gridFileManager(next_time, variable, region)
        next_grid = reader.dataForHour(variable, prev_time)
        reader.close()
        del reader

        num_nans = len(N.where(N.isnan(prev_grid))[0])
        if num_nans == N.product(next_grid.shape):
            errmsg = 'Repair failed, data also missing for next hour (%s).'
            return False, errmsg % next_time_str

        fudged = (prev_grid + next_grid) / 2.
        if variable.lower() == 'pcpn':
            nans = N.where(N.isnan(fudged))
            prev_grid[nans] = 0.
            fudged[N.where(prev_grid < 0.02)] = 0.
            next_grid[nans] = 0.
            fudged[N.where(next_grid < 0.02)] = 0.
            fudged[nans] = N.nan

        manager = self.gridFileManager(error_time, variable, region)
        manager.updateDataFromSource(variable, 'fudged', error_time, fudged)

        times = (prev_time_str, next_time_str)
        return True, 'Missing data repaired using data from %s and %s.' % times

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _extractTimes(self, ref_time, **kwargs):
        start_time = kwargs.get('start_time', None)
        if start_time is None:
            if kwargs.get('grid_subdir_by_hours',False):
                start_time, xxx, end_time = \
                    self.fcastObsTimespan(ref_time, **kwargs)
            else:
                start_time, end_time = self.monthTimespan(ref_time, **kwargs)
        else: end_time = kwargs.get('end_time')
        num_hours = tzutils.hoursInTimespan(start_time, end_time)
                
        return { 'end_time': end_time,
                 'num_hours': num_hours,
                 'start_time': start_time }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _gridTemplateArgs(self, ref_time, variable, region, grid_source='acis',
                            **kwargs):
        template_args = tzutils.tzaTimeStrings(ref_time, 'target')
        times = self._extractTimes(ref_time, **kwargs)
        if kwargs.get('grid_subdir_by_hours',False):
            template_args['num_hours'] = times['num_hours']

        template_args['analysis'] = self.analysis_type
        template_args['region'] = region

        template_args['source'] = grid_source
        if variable is not None:
            template_args['variable'] = variable
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerGridAccessClasses(self):
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from atmosci.reanalysis.grid import ReanalysisGridFileReader, \
                                            ReanalysisGridFileManager, \
                                            ReanalysisGridFileBuilder
        self._registerAccessManagers('reanalysis', ReanalysisGridFileReader,
                                                   ReanalysisGridFileManager,
                                                   ReanalysisGridFileBuilder)
        registerStaticAccessManagers(self)

    _registerAccessClasses = _registerGridAccessClasses

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisGridFactory_(self, **kwargs):
        self.grid_file_map = self.reanalysis.grid_file_map
        self.grid_region = kwargs.get('grid_region',
                                 kwargs.get('region', 
                                       self.reanalysis.grid.region))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileFactory(StaticFileAccessorMethods,
                                ReanalysisGridFactoryMethods,
                                ReanalysisFactoryMethods, object):
    """
    Basic factory for accessing data in Reanalysis grid files.
    """
    def __init__(self, analysis_type='rtma', analysis_source='ncep', **kwargs):
        analysis = '%s.%s' % (analysis_type, analysis_source)
        config_object = self._initReanalysisFactory_(analysis, **kwargs)

        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, None)

        self._initReanalysisGridFactory_(**kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

