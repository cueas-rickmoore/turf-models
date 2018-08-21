
import os

from atmosci.utils import tzutils

from atmosci.seasonal.access import BasicFileAccessorMethods
from atmosci.seasonal.paths import PathConstructionMethods

from atmosci.hourly.grid import HourlyGridFileReader # \
#                               HourlyGridFileManager, \
#                               HourlyGridFileBuilder

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HourlyGridFactoryMethods:
    """
    Methods for accessing Hourly grid files.
    """
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFilenameTemplate(self, filetype):
        template = self.anal_config.get(filetype,
                        self.anal_config.get('grid_filename', None))
        if template is None:
            errmsg = 'No template found for "%s" data type.'
            raise ValueError, errmsg % dtatype
        return template

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlyGridDirpath(self, filetype, target_hour, source, region,
                                **kwargs):
        root_dir = self.hourlyGridRootDir(filetype, **kwargs)
        template = self.anal_config.grid_subdir
        if isinstance(subdir, tuple): template = os.sep.join(template)

        if 'utc' in template:
            template_args = tzutils.utcTimeStrings(target_hour)
        else: template_args = self.timeToFilepath(target_hour)

        template_args.update(self.pathTemplateArgs(filetype, source, region))
        dirpath = os.path.join(root_dir, template % arg_dict) 
        if not os.path.exists(dirpath):
            if kwargs.get('dir_must_exist',kwargs.get('file_must_exist',False)):
                errmsg = 'Hourly grid directory does not exist :\n%s'
                raise IOError, errmsg % dirpath
            else: os.makedirs(dirpath)
        return dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlyGridFilename(self, filetype, target_hour, source, region,
                                 **kwargs):
        template = self.gridFilenameTemplate(filetype)
        if 'utc' in template:
            template_args = tzutils.utcTimeStrings(target_hour)
        else: template_args = self.timeToFilepath(target_hour)

        template_args.update(self.pathTemplateArgs(filetype, source, region))
        if kwargs: template_args.update(dict(kwargs))
        return template % template_args
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlyGridFilepath(self, filetype, target_hour, source, region,
                                 **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is not None: return filepath

        grid_dirpath = self.hourlyGridDirpath(target_hour, filetype, source,
                                              region, **kwargs)
        filename = \
            self.hourlyGridFilename(target_hour, filetype, region, **kwargs)
        filepath = os.path.join(grid_dirpath, filename)
        if kwargs.get('file_must_exist', False):
            if not os.path.isfile(filepath):
                errmsg = 'Hourly grid file does not exist :\n    %s'
                raise IOError, errmsg % filepath
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlyGridFileManager(self, filetype,  target_hour,source, region,
                                    **kwargs):
        filepath =  self.hourlyGridFilepath(target_hour, filetype, source,
                                            region, **kwargs)
        mode = kwargs.get('mode','r')
        msg = 'creating manager (mode="%s") for :\n    %s'
        print msg % (mode, filepath)
        return self.gridFileManager(filepath, filetype, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlyGridFileReader(self, filetype, target_hour, source, region,
                                   **kwargs):
        filepath =  self.hourlyGridFilepath(target_hour, filetype, source,
                                            region, **kwargs)
        print 'creating reader for :\n    ', filepath
        return self.gridFileReader(filepath, filetype)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlyGridRootDir(self, filetype, source, **kwargs):
        shared = source.get('shared_datadir',
                            source.get('shared_rootdir', False))
        if shared:
            return self.config.dirpaths.shared
        else:
            root_dir = self.config.dirpaths.get(filetype, None)
            if root_dir is None: 
                if 'filetype' == 'appdata': return self.appdataRootDir()
                return self.dataRootDir()
            else return root_dir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def pathTemplateArgs(self, filetype, source, region):
        template_args = { 'filetype':filetype, }
        if region is not None:
            template_args['region'] = self.regionToFilepath(region)
        if source is not None:
            template_args['source'] = self.sourceToFilepath(source)
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeToDirpath(self, fcast_date):
        return attrs = { 'date':fcast_date.strftime('%Y%m%d'),
                         'month':fcast_date.strftime('%Y%m'),
                         'year':fcast_date.year }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeToFilepath(self, fcast_date):
        return attrs = { 'date':fcast_date.strftime('%Y-%m-%d'),
                         'month':fcast_date.strftime('%Y-%m'),
                         'year':fcast_date.year }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initHourlyGridFactory_(self, **kwargs):
        if kwargs.get('use_dev_env', False): self.useDirpathsForMode('dev')
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)
        self._registerAccessManager('urma_grid', 'read', HourlyGridFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HourlyGridFileFactory(HourlyGridFactoryMethods,
                            BasicFileAccessorMethods,
                            object):
    """
    Basic factory for accessing data in Hourly grib files.
    """
    def __init__(self, grib_source, config_object=None, **kwargs):
        grib_source_path = 'urma.%s' % grib_source
        if config_object is None:
            ReanalysisGribFileFactory.__init__(self, grib_source_path)
        else:
            ReanalysisGribFileFactory.__init__(self, grib_source_path,
                                                     config_object)
        self._initUrmaGribFactory_(grib_source)

