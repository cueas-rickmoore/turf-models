
import os
import datetime
ONE_DAY = datetime.timedelta(days=1)
ONE_HOUR = datetime.timedelta(hours=1)

from atmosci.utils import tzutils

from atmosci.seasonal.methods.access  import BasicFileAccessorMethods
from atmosci.seasonal.methods.factory import BasicProjectFactoryMethods
from atmosci.seasonal.methods.paths   import PathConstructionMethods
from atmosci.seasonal.methods.static  import StaticFileAccessorMethods

from atmosci.seasonal.factory  import registerStaticAccessManagers

from turf.factory import TurfProjectFactoryMethods

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import CONFIG, THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfThreatGridFileFactory(TurfProjectFactoryMethods,
                                PathConstructionMethods,
                                StaticFileAccessorMethods,
                                BasicFileAccessorMethods,
                                BasicProjectFactoryMethods, object):
    """
    Basic factory for accessing data in TurfThreat grib files.
    """
    def __init__(self, config_object=CONFIG, **kwargs):
        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, None)
        registerStaticAccessManagers(self)
        self._initTurfFactory_()

        # initialize reanalysis grib-specific configuration
        self._initTurfThreatGridFactory_(THREATS, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildThreatGridFile(self, threat, period, threat_date,
                                  source_key='acis'):

        builder = self.threatFileBuilder(threat, period, threat_date.year,
                                         source_key, None, None, None)
        region = self.regionConfig(self.region)
        source = self.sourceConfig(source_key)
        reader = self.staticFileReader(source, region)
        lats = reader.getData('lat')
        lons = reader.getData('lon')
        reader.close()
        del reader

        # build all of the datasets
        builder.build(lons=lons, lats=lats)
        del lats, lons
        builder.close()
        return builder

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def filenameTemplate(self, *args):
        if len(args) == 1:
            return self.config.filenames.get(args[0], None)
        else:
            for filename_key in args:
                filename = self.config.filenames.get(filename_key, None)
                if filename is not None: return filename
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileTimespan(self, threat, year):
        """
        Returns
            tuple with file start date and end date in timezone
            and forecast end date
        """
        start_day = (year,) + self.project.start_day
        start_date = datetime.date(*start_day)

        end_day = (year,) + self.project.end_day
        end_date = datetime.date(*end_day)

        return start_date, end_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def obsTimeForDate(self, date, hour, timezone):
        obs_time = datetime.datetime.combine(date, datetime.time(hour))
        return tzutils.asLocalTime(obs_time, timezone)

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

    def threatFileBuilder(self, threat, period, year, source, lons=None,
                              lats=None, filepath=None, **kwargs):
        if filepath is None:
            filepath = self.threatGridFilepath(threat, period, year)
        threat_config = self.threats[threat]

        Class = self.fileAccessorClass('threats', 'build')
        return Class(self.config, threat_config, filepath, period, year,
                     source, self.region, lons, lats, **kwargs)
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatFileExists(self, threat, period, year):
        filepath = self.threatGridFilepath(threat, period, year)
        return os.path.exists(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatFileManager(self, threat, period, year, filepath=None,
                              mode='a'):
        if filepath is None:
            filepath = self.threatGridFilepath(threat, period, year)
        if not os.path.isfile(filepath):
            errmsg = '%s %s grid file does not exist :\n    %s'
            raise IOError, errmsg % (threat.upper(), period, filepath)

        Class = self.fileAccessorClass('threats', 'manage')
        return Class(filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatFileReader(self, threat, period, year, filepath=None):
        if filepath is None:
            filepath = self.threatGridFilepath(threat, period, year)
        if not os.path.isfile(filepath):
            errmsg = '%s %s grid file does not exist :\n    %s'
            raise IOError, errmsg % (threat.upper(), period, filepath)

        Class = self.fileAccessorClass('threats', 'read')
        return Class(filepath)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatGridDirpath(self, threat, year, **kwargs):
        dirpath = self.projectDirpath('threats', 'turf', 'project')
        subdir = self.subdirPath(threat, 'threats')
        template = os.path.join(dirpath, subdir)

        template_args = self._templateArgs(threat, year, 'dir')
        if '%(group)s' in template and 'group' not in template_args:
            template = template.replace('%s%%(group)s' % os.sep, '')

        grid_dirpath = template % template_args
        if not os.path.exists(grid_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Turf threat directory does not exist :\n%s'
                raise IOError, errmsg % grid_dirpath
            else: os.makedirs(grid_dirpath)
        return grid_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatGridFilename(self, threat, period, year):
        if isinstance(period, basestring): period_key = period
        else: period_key = period.name
        template = self.filenameTemplate(threat, period_key)
        if template is None:
            errmsg = 'No template for %s %s period grid file'
            raise LookupError, errmsg % (threat, period_key)

        template_args = self._templateArgs(threat, year, 'file')
        if '%(group)s' in template and 'group' not in template_args:
            template = template.replace('%s%%(group)s' % os.sep, '')
        return template % template_args
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatGridFilepath(self, threat, period, year):
        dirpath = self.threatGridDirpath(threat, year)
        filename = self.threatGridFilename(threat, period, year)
        filepath = os.path.join(dirpath, filename)
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatJsonDirpath(self, threat_key, year, **kwargs):
        dirpath = self.projectDirpath('threats', 'turf', 'project')
        subdir_path = self.subdirPath('threatjson', 'turfjson')

        template = os.path.join(dirpath, subdir_path)
        template_args = self._templateArgs(threat_key, year, 'dir')
        if '%(group)s' in template and 'group' not in template_args:
            template = template.replace('%s%%(group)s' % os.sep, '')

        json_dirpath = template % template_args
        if not os.path.exists(json_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Turf threat directory does not exist :\n%s'
                raise IOError, errmsg % json_dirpath
            else: os.makedirs(json_dirpath)
        return json_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatJsonFilename(self, threat_key, node, year):
        template = self.filenameTemplate('threatjson','turfjson')
        template_args = \
            self._templateArgs(threat_key, year, 'file', node=node)
        if '%(group)s' in template and 'group' not in template_args:
            template = template.replace('%s%%(group)s' % os.sep, '')

        return template % template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatJsonFilepath(self, threat_key, node, year):
        dirpath = self.threatJsonDirpath(threat_key, year)
        filename = self.threatJsonFilename(threat_key, node, year)
        return os.path.join(dirpath, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatName(self, threat_key):
        return self.threats[threat_key].fullname

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatWeather(self, threat_key):
        return self.threats[threat_key].weather

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _normalizeThreatPath(self, threat, path_type):
        threat_obj = self.threats.get(threat, None)
        if threat_obj is not None and 'fullname' in threat_obj:
            fullname = threat_obj.fullname
        else: fullname = threat.title()

        return fullname.replace(' ','-')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from turf.threats.grid import TurfThreatGridFileReader, \
                                      TurfThreatGridFileManager, \
                                      TurfThreatGridFileBuilder
        self._registerAccessManagers('threats', TurfThreatGridFileReader,
                                                TurfThreatGridFileManager,
                                                TurfThreatGridFileBuilder)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _templateArgs(self, threat_type, year, path_type, node=None):
        template_args = { 'year':year, }
        if path_type == 'file':
            template_args['region'] = self.regionToFilepath(self.region)
        else: template_args['region'] = self.regionToDirpath(self.region)

        if '.' in threat_type:
            group, threat = threat_type.split('.')
            template_args['group'] = \
                self._normalizeThreatPath(group, path_type)
            template_args['threat'] = \
                self._normalizeThreatPath(threat, path_type)
        else:
            template_args['threat'] = \
                self._normalizeThreatPath(threat_type, path_type)

        if node is not None:
            if isinstance(node, tuple):
                template_args['node'] = self.gridNodeToFilename(*node)
            else: template_args['node'] = node # assumes it is a string

        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initTurfThreatGridFactory_(self, threat_config, **kwargs):
        if kwargs.get('use_dev_env', False): self.useDirpathsForMode('dev')
        self.threats = threat_config
        self.local_timezone = kwargs.get('local_timezone',
                                     self.project.get('local_timezone',
                                          tzutils.localTimezone()))
        self.region = kwargs.get('region', self.project.region)

