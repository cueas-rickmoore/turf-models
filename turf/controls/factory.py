
import os

from atmosci.seasonal.factory import SeasonalStaticFileFactory

from turf.factory import TurfProjectFactoryMethods
from turf.controls.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGddFileMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildGddFile(self, year, source, region):
        builder = self.gddFileBuilder(year, source, region, False)
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

    def gddFileDirpath(self, year, region, use_cicss_gdd=False):
        args = { 'region':self.regionToDirpath(region), 'year':year }

        if use_cicss_gdd:
            root_dir = self.config.dirpaths.weather
            template = os.path.join(self.subdirTemplate('gddapp'))
        else:
            root_dir = self.config.dirpaths.working
            template = os.path.join(self.subdirTemplate('gdd'))

        gdd_dirpath = os.path.join(root_dir, template % args) 
        if not os.path.isdir(gdd_dirpath):
            os.makedirs(gdd_dirpath)
        return gdd_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gddFilename(self, year, region, use_cicss_gdd=False):
        if use_cicss_gdd: return self.config.filenames.gddapp % { 'year': year, }
        return self.config.filenames.gdd % { 'year': year, }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gddFilepath(self, year, region, use_cicss_gdd=False):
        grid_dir = self.gddFileDirpath(year, region, use_cicss_gdd)
        filename = self.gddFilename(year, region, use_cicss_gdd)
        return os.path.join(grid_dir, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gddFileBuilder(self, year, source, region, use_cicss_gdd=False):
        filepath = self.gddFilepath(year, region, use_cicss_gdd)

        Class = self.fileAccessorClass('gdd', 'build')
        return Class(CONFIG, filepath, year, source, region, None, None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gddFileManager(self, year, region, mode='a', use_cicss_gdd=False):
        filepath = self.gddFilepath(year, region, use_cicss_gdd)
        if not os.path.isfile(filepath):
            errmsg = 'GDD grid file for %d was not found :\n    %s'
            raise IOError, errmsg % (year, filepath)

        Class = self.fileAccessorClass('gdd', 'manage')
        return Class(filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gddFileReader(self, year, region, use_cicss_gdd=False):
        filepath = self.gddFilepath(year, region, use_cicss_gdd)
        if not os.path.isfile(filepath):
            errmsg = 'GDD grid file for %d was not found :\n    %s'
            raise IOError, errmsg % (year, filepath)

        Class = self.fileAccessorClass('gdd', 'read')
        return Class(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerGddAccessClasses(self):
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from turf.grid import TurfGridFileReader, TurfGridFileManager
        from turf.controls.grid import TurfGddFileBuilder

        self._registerAccessManagers('gdd', TurfGridFileReader,
                                            TurfGridFileManager,
                                            TurfGddFileBuilder)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfControlsJsonFileMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def jsonFileDirpath(self, year, control, region, source=None):
        root_dir = self.config.dirpaths.turf
        template = os.path.join(self.subdirTemplate('json'))
        args = {
            'control': control.fullname,
            'region':self.regionToDirpath(region),
            'year':year
            }
        if source is not None: args['source'] = self.sourceToDirpath(source)

        json_dirpath = os.path.join(root_dir, template % args) 
        if not os.path.isdir(json_dirpath):
            os.makedirs(json_dirpath)
        return json_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def jsonFilename(self, year, node, control, region, source=None):
        args = {
            'control': control.fullname,
            'node': self.gridNodeToPath(node),
            'region': self.regionToFilepath(region),
            'year': year
        }
        if source is not None: args['source'] = self.sourceToFilepath(source)

        return self.config.filenames.json % args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def jsonFilepath(self, year, node, control, region, source=None):
        json_dir = self.jsonFileDirpath(year, control, region, source)
        filename = self.jsonFilename(node, year, control, region, source)
        return os.path.join(josn_dir, filename)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfControlsFactory(TurfGddFileMethods, TurfControlsJsonFileMethods,
                         TurfProjectFactoryMethods, SeasonalStaticFileFactory):

    def __init__(self, config=CONFIG):
        SeasonalStaticFileFactory.__init__(self, config)
        self._initTurfFactory_()
        self.controls = config.controls

        self._registerGddAccessClasses()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def controlObject(self, control, default=None):
        return self.controls.get(control, default)

