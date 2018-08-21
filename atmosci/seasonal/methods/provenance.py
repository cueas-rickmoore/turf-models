
import os
import datetime

import numpy as N

from atmosci.seasonal.methods.builder import FileBuilderMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#  provenance template definitons and data generators 
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.seasonal.prov_config import PROVENANCE

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ProvenanceManagerMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def generateEmptyProvenance(self, provenance_key, num_records):
        prov_type = self.provenanceType(provenance_key)
        empty_record = prov_type.empty
        return [empty_record for record in range(num_records)]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initProvenanceConfig(self, prov_config=PROVENANCE):
        self.prov_config = prov_config.copy('provenance', None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def provenanceConfig(self, provenance_key):
        reference = None
        if ':' in provenance_key:
            parts = provenance_key.split(':')
            if len(parts) == 2: name, key = parts
            elif len(parts) == 3: name, reference, key = parts
        else: name = key = provenance_key
        prov_type = self.prov_config.types[key]
        return ( prov_type.get('path', name), reference, prov_type,
                 self.prov_config.views )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def provenanceGenerator(self, prov_path):
        key = self.provenanceGeneratorKey(prov_path)
        return self.prov_config.generators.get(prov_path,
                                           self.prov_config.generators[key])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def provenanceGeneratorKey(self, prov_path):
        return self.datasetAttribute(prov_path, 'key',
                    self.datasetAttribute(prov_path, 'provenance',
                         self.datasetAttribute(prov_path, 'generator',
                              'default')))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def provenanceType(self, provenance_key):
        reference = None
        if ':' in provenance_key:
            parts = provenance_key.split(':')
            if len(parts) == 2: name, key = parts
            elif len(parts) == 3: name, reference, key = parts
        else: name = key = provenance_key
        return self.prov_config.types[key]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def registerProvenanceGenerator(self, provenance_key, generator):
        self.prov_config.generators[provenance_key] = generator

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def registerProvenanceType(self, provenance_key, provenance_type):
        self.prov_config.types[provenance_key] = provenance_type

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def registerProvenanceView(self, provenance_key, provenance_view):
        self.prov_config.views[provenance_key] = provenance_view

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateProvenanceConfig(self, prov_config):
        self.prov_config.update(prov_config)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ProvenanceBuilderMethods(ProvenanceManagerMethods, FileBuilderMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def preInitBuilder(self, project_config, filetype, source, region, 
                             kwarg_dict={}):
        prov_config = kwarg_dict.get('prov_config', PROVENANCE)
        self.initProvenanceConfig(prov_config)
        FileBuilderMethods.preInitBuilder(self, project_config, filetype,
                                                source, region, **kwarg_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # build everything
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def build(self, build_groups=True, build_datasets=True, lons=None,
                    lats=None, kwarg_dict={}):

        # initiaize file attributes
        self.initFileAttributes(**kwarg_dict)

        # build data groups
        groups = self.filetype.get('groups',None)
        if groups and build_groups:
            if self.debug: print 'building file level groups'
            for group_key in groups:
                if not self.groupExists(group_key):
                    self.open('a')
                    self.buildGroup(group_key, build_datasets, kwarg_dict)
                    self.close()

        # build file-level datasets
        datasets = self.filetype.get('datasets',None)
        # initialze lat and lon datasets if the data was passed
        if datasets and build_datasets:
            if lons is not None and lats is not None:
                self.initLonLatData(lons, lats)
                datasets = list(datasets)
                datasets.remove('lon')
                datasets.remove('lat')
        # test again, in case lats and lons were the only datasets in the list
        if datasets and build_datasets:
            if self.debug: print 'building file level datasets'
            for dataset_key in datasets:
                self.open('a')
                if 'provenance' in dataset_key:
                    self.buildProvenance(dataset_key, kwarg_dict)
                else: self.buildDataset(dataset_key, None, None, **kwarg_dict)
                self.close()

        # return with file open for updates
        self.open('a')


    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # data group initiailzation methods
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def buildGroup(self, group_key, build_datasets, root_path=None,
                         kwarg_dict={}):
        group_name, group, group_keydict = self._groupConfig(group_key)
        if self.groupExists(group_name, root_path): return

        if root_path is not None:
            group_path = '%s.%s' % (root_path, group_name)
        else: group_path = group_name
        if self.debug: print 'building %s group' % group_path

        attrs = \
            self._resolveGroupBuildAttributes(group, group_keydict, kwarg_dict)

        self.open('a')
        self.createGroup(group_path, **attrs)
        self.close()

        # build this group's sub-groups
        groups = group.get('groups', None)
        if groups:
            if self.debug: print 'building subgroups of', group_path
            for name in groups:
                self.buildGroup(name, build_datasets, group_path, kwarg_dict)

        # build this group's datasets
        datasets = group.get('datasets', None)
        if datasets and build_datasets:
            if self.debug: print 'building datasets in group', group_path
            for dataset_key in datasets:
                if 'provenance' in dataset_key:
                    self.buildProvenance(dataset_key, 
                                         {'group_path':group_path})
                else:
                    self.buildDataset(dataset_key, group_path, group_keydict,
                                      **kwarg_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # dataset build methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildProvenance(self, provenance_key, kwarg_dict={}):
        dataset_name, reference, prov_type, prov_views = \
                                         self.provenanceConfig(provenance_key)
        group_name = kwarg_dict.get('group_name', None)
        group_path = kwarg_dict.get('group_path', group_name)
        if self.datasetExistsIn(dataset_name, group_path): return

        if group_path is not None:
            prov_path = '%s.%s' % (group_path ,dataset_name)
        else: prov_path = dataset_name

        attrs = self._resolveProvenanceBuildAttributes(prov_type, kwarg_dict)
        description = attrs.get('description', None)
        if description is None:
            if group_name is not None:
                attrs['description'] = 'Provenance for %s' % group_name
            else:
                attrs['description'] = 'Provenance for %s' % reference
        if reference is not None: attrs['reference'] = reference

        records = self.generateEmptyProvenance(prov_type, attrs)

        names = prov_type.names
        formats = prov_type.formats
        provenance = N.rec.fromrecords(records, shape=(len(records),),
                                       formats=formats, names=names)
        self.open('a')
        self.createDataset(prov_path, provenance, raw=True)
        self.setDatasetAttributes(prov_path, **attrs)
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveProvenanceBuildAttributes(self, prov_type, kwarg_dict={}):
        attrs = self._resolveCommonAttributes(**kwarg_dict)
        attrs['description'] = prov_type.get('description', None)
        attrs['key'] = prov_type.name
        view = prov_type.names[0]
        attrs.update(self._resolveScopeAttributes(prov_type, **kwarg_dict))

        attrs['generator'] = kwarg_dict.get('generator',
                                        prov_type.get('generator',
                                                  attrs['key']))
        return attrs
