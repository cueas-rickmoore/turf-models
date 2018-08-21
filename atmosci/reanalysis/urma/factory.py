
import os

from atmosci.utils import tzutils

from atmosci.reanalysis.factory import ReanalysisGribFileFactory, \
                                       ReanalysisGridFileFactory

from atmosci.reanalysis.urma.grib import URMAGribFileReader
#from atmosci.reanalysis.urma.grid import URMAGridFileReader, \
#                                         URMAGridFileManager, \
#                                         URMAGridFileBuilder

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.urma.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAGribFactoryMethods:
    """
    Methods for accessing URMA grib files.

    The URMAFactoryMethods class must also be included in any class
    derived from URMAGridFactoryMethods
    """
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGribFilepath(self, target_hour, variable, region, **kwargs):
        filepath = self.gribFilepath(target_hour, file_type, region, **kwargs)
        Class = self.fileAccessorClass('urma_grib', 'read')
        return Class(filepath, self.grib_source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initUrmaGribFactory_(self, region, **kwargs):
        self.grib_region = region
        # must be called in constructor of any factory that includes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)
        self._registerAccessManager('urma_grib', 'read', URMAGribFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAGribFileFactory(URMAGribFactoryMethods,
                          ReanalysisGribFileFactory):
    """
    Basic factory for accessing data in URMA grib files.
    """
    def __init__(self, grib_source, region, config_object=CONFIG, **kwargs):
        grib_source_path = 'urma.%s' % grib_source
        ReanalysisGribFileFactory.__init__(self, grib_source_path, CONFIG)
        self._initUrmaGribFactory_(region, **kwargs)
 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAGridFactoryMethods:
    """
    Methods for accessing data in URMA grid files.

    The URMAFactoryMethods class must also be included in any class
    derived from URMAGridFactoryMethods
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFilenameTemplate(self, variable):
        template = self.anal_config.get(variable,
                        self.anal_config.get('grid_filename', None))
        if template is None:
            errmsg = 'No template found for "%s" data type.'
            raise ValueError, errmsg % dtatype
        return template

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setNumHours(self, num_hours): self.urma_hours = num_hours
    def setRegion(self, region): self.urma_region = region

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGridFilename(self, target_hour, variable, **kwargs):
        return self.analysisGridFilename(target_hour, variable, self.region,
                                         self.num_hours, **kwargs)
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGridFilepath(self, target_hour, variable, **kwargs):
        return self.analysisGridFilepath(target_hour, variable, self.region,
                                         self.num_hours, **kwargs)
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGridDirpath(self, target_hour, variable, **kwargs):
        return self.analysisGridDirpath(target_hour, self.num_hours,
                                        variable, self.region, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGridFileBuilder(self, target_hour, variable, **kwargs):
        Class = self.fileAccessorClass('urma_grid', 'build')
        filepath = self.urmaGridFilepath(target_hour, variable, **kwargs)
        print 'creating builder for :\n    ', filepath
        return Class(filepath, self.grib_source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGridFileReader(self, target_hour, variable, **kwargs):
        Class = self.fileAccessorClass('urma_grid', 'read')
        filepath = self.urmaGridFilepath(target_hour, variable, **kwargs)
        print 'creating reader for :\n    ', filepath
        return Class(filepath, self.grib_source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def urmaGridFileManager(self, target_hour, variable, **kwargs):
        Class = self.fileAccessorClass('urma_grid', 'managw')
        filepath = self.urmaGridFilepath(target_hour, variable, **kwargs)
        print 'creating manager for :\n    ', filepath
        return Class(filepath, self.grib_source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initUrmaGridFactory_(self, num_hours, region, **kwargs):
        self.setNumHours(num_hours)
        self.setRegion(region)
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)
        # register file reader, manager, builder
        self._registerAccessManager('urma_grid', 'read', URMAGridFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAGridFileFactory(URMAGribFactoryMethods,
                          ReanalysisGridFileFactory):
    """
    Basic factory for accessing data in URMA grib files.
    """
    def __init__(self, num_hours, region, config_object=CONFIG, **kwargs):
        ReanalysisGridFileFactory.__init__(self, 'urma.%s' % grib_source,
                                                 CONFIG)
        self._initUrmaGridFactory_(num_hours, region, **kwargs)
