
import os
import datetime

from turf.factory import TurfProjectFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def cleanObjDict(obj_dict):
    for key, value in obj_dict.items():
        if value is None:
            del obj_dict[key]
            continue

        if 'name' in value:
           obj_dict[key] = cleanObjDict(value)

        if key == 'name': del obj_dict[key]
        elif key == 'parent': del obj_dict[key]
        else: obj_dict[key] = value

    return obj_dict

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.config import CONFIG
from turf.maps.config import MAP_CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfMapFactoryMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def controlMapConfig(self, control_key, treatment_key):
        group_config = self.map_groups[control_key].copy()
        control_config = group_config.threats[control_key].copy()
        del group_config['threats']
        treatment = control_config.treatments[treatment_key]
        del control_config['treatments']
        control_config.treatment = treatment

        control_dict = cleanObjDict(group_config.dict)
        for key, value in control_dict.items():
            if key == 'attributes':
                for attr_name, attr_value in value.items():
                    control_config[attr_name] = attr_value
            else: control_config[key] = value

        control_config.thumbnail_shape = self.maps.thumbnail_shape

        return control_config

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def treatmentConfig(self, threat_key, treatment_key):
        threat = self.map_groups[threat_key].threats[threat_key]
        return threat.treatments[treatment_key]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def controlNames(self, threat_key, treatment_key):
        threat = self.map_groups[threat_key].threats[threat_key]
        return threat.fullname, threat.treatments[treatment_key].fullname

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapOptions(self, data_type):
        return self._mergeMapOptions_(data_type)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatMapConfig(self, threat_key):
        group_config = self.map_groups[threat_key].copy()
        threat_config = group_config.threats[threat_key].copy()

        group_dict = cleanObjDict(group_config.dict)
        for key, dict_value in group_dict.items():
            threat_config[key] = dict_value
        del threat_config['threats']

        threat_config.thumbnail_shape = self.maps.thumbnail_shape
        return threat_config

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatName(self, threat_key):
        return self.map_groups[threat_key].threats[threat_key].fullname

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatPathParams(self, threat_key, image_type, dirpath=False):
        if '.' in threat_key:
            threat_key, treatment_key = threat_key.split('.')
        else: treatment_key = None
        group_config = self.map_groups[threat_key]

        params = { 'data_group': threat_key, }
        if dirpath:
            subdirs = os.sep.join(group_config.get('subdirs',('%(threat)s',)))
            params['subdirs'] = subdirs
        else: params['filename'] = group_config['%s_filename' % image_type]
        
        threat_config = group_config.threats[threat_key]
        params['threat'] = threat_config.fullname.replace(' ','-')

        if treatment_key is not None:
            params['treatment'] = \
                  threat_config.treatments[treatment_key].fullname

        return params

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def treatmentsForThreat(self, threat_key):
        return self.map_groups[threat_key].threats[threat_key].treatments

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # map and image file directories and paths
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfAnimationDirpath(self, data_type, year, region):
        return self.turfImageDirpath('anim', data_type, year, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfAnimationFilename(self, data_type, year, region):
        return self.turfImageFilepath('anim', data_type, year, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfAnimationDirpath(self, data_type, year, region):
        return self.turfImageDirpath('anim', data_type, year, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfAnimationFilename(self, data_type, year, region):
        return self.turfImageFilepath('anim', data_type, year, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfAnimationFilepath(self, data_type, year, region):
        dirpath = self.turfAnimationDirpath(data_type, year, region)
        filename = self.turfAnimationFilename(data_type, year, region)
        return os.path.join(dirpath, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfImageDirpath(self, image_type, data_type, date_or_year, region):
        path_params = self.threatPathParams(data_type, image_type, True)
        group_subdirs = path_params['subdirs']
        del path_params['subdirs']

        template = self.config.dirpaths.get(image_type, None)
        if template is None: # build the template
            root_dir = self.config.dirpaths.project
            template = os.path.join(self.config.dirpaths.project,
                                    os.sep.join(self.maps.subdirs[image_type]))
        template = os.path.join(template, group_subdirs)

        path_params['region'] = self.regionToDirpath(region)

        if date_or_year is None: # creating a template for dirpath 
            path_params['date'] = '||DATE||'
            path_params['year'] = '||YEAR||'
        elif isinstance(date_or_year, (datetime.date, datetime.datetime)):
            path_params['date'] = date_or_year.strftime('%Y%m%d')
            path_params['year'] = date_or_year.year
        elif isinstance(date_or_year, int): # year was passed
            path_params['date'] = '||DATE||'
            path_params['year'] = date_or_year
        else:
            errmsg = '"%s" is an invalid type for "date_or_year"'
            TypeError, errmsg % str(type(date_or_year))

        dirpath = os.path.join(root_dir, template % path_params)
        if date_or_year is not None and not os.path.exists(dirpath):
            os.makedirs(dirpath)
        return dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfImageFilename(self, image_type, data_type, date_or_year, region):
        path_params = self.threatPathParams(data_type, image_type)
        template = path_params['filename']
        del path_params['filename']

        path_params['region'] = self.regionToFilepath(region)

        if date_or_year is None:
            path_params['date'] = '||DATE||'
            path_params['year'] = '||YEAR||'
        elif isinstance(date_or_year, (datetime.date, datetime.datetime)):
            path_params['date'] = date_or_year.strftime('%Y%m%d')
            path_params['year'] = str(date_or_year.year)
        elif isinstance(date_or_year, int): # year was passed
            path_params['date'] = '||DATE||'
            path_params['year'] = date_or_year
        else:
            errmsg = '"%s" is an invalid type for "date_or_year"'
            TypeError, errmsg % str(type(date_or_year))

        return template % path_params

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfMapDirpath(self, data_type, date_or_year, region):
        return self.turfImageDirpath('map', data_type, date_or_year, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfMapFilename(self, data_type, date, region):
        return self.turfImageFilename('map', data_type, date, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfMapFilepath(self, data_type, date, region):
        dirpath = self.turfMapDirpath(data_type, date, region)
        filename = self.turfMapFilename(data_type, date, region)
        return os.path.join(dirpath, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfThumbnailDirpath(self, data_type, date_or_year, region):
        return self.turfImageDirpath('thumb', data_type, date_or_year, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfThumbnailFilename(self, data_type, date, region):
        return self.turfImageFilename('thumb', data_type, date, region)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def turfThumbnailFilepath(self, data_type, date, region):
        dirpath = self.turfThumbnailDirpath(data_type, date, region)
        filename = self.turfThumbnailFilename(data_type, date, region)
        return os.path.join(dirpath, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initMapFileFactory_(self, map_config):
        self.maps = map_config
        self.map_groups = { }
        for group_name, group_config in self.maps.groups.items():
            for threat_name in group_config.threats.keys():
                self.map_groups[threat_name] = group_config

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _mergeMapOptions_(self, data_type):
        map_options = self.maps.default.map_options.copy()

        if '.' in data_type:
            threat_key, treatment_key = data_type.split('.')
            config = self.controlMapConfig(threat_key, treatment_key)
        else:
            config = self.threatMapConfig(data_type)
            threat_key = data_type
            treatment_key = None

        if config.has_key('map_options'):
            map_options.merge(config.map_options)

        threat = config[threat_key]
        if threat.has_key('map_options'):
            map_options.merge(threat.map_options)

        if treatment_key is not None:
            if threat.treatment.has_key('map_options'):
                map_options.merge(threat.treatment.map_options)

        return map_options


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfMapFileFactory(TurfMapFactoryMethods, TurfProjectFactory):

    def __init__(self, config=CONFIG):
        TurfProjectFactory.__init__(self, config)
        self._initMapFileFactory_(MAP_CONFIG)

