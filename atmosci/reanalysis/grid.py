
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N

from atmosci.utils.config import ConfigObject
from atmosci.utils import tzutils

from atmosci.hourly.grid import HourlyGridFileReader, \
                                HourlyGridFileManager
from atmosci.hourly.builder import HourlyGridBuilderMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileReader(HourlyGridFileReader):
    pass


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileManagerMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def adjustReanalysisDates(self, analysis, dataset_path, start_time,
                                    end_time):
        start_time_attr = '%s_start_time' % analysis
        end_time_attr = '%s_end_time' % analysis

        analysis_end_time = \
            self.timeAttribute(dataset_path, end_time_attr, None)

        if analysis_end_time is not None:
            analysis_start_time = \
                self.timeAttribute(dataset_path, start_time_attr)

            if analysis_end_time <= start_time:
                # forecast was completely overwritten by observation data
                self.deleteDatasetAttribute(dataset_path, end_time_attr)
                if analysis_start_time is not None:
                    self.deleteDatasetAttribute(dataset_path, start_time_attr)

            else: # analysis was partially overwritten by new data
                self.setTimeAttribute(dataset_path, end_time_attr,
                                      analysis_end_time)
                if analysis_start_time is not None \
                and analysis_start_time <= start_time:
                    analysis_start_time = start_time + ONE_HOUR
                    self.setTimeAttribute(dataset_path, start_time_attr,
                                          analysis_start_time)
       
        # else: analysis times have never been set

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def inputProcessor(self, dataset_path):
        if '.' in dataset_path: key = dataset_path.split('.')[-1]
        else: key = dataset_path
        return self.processors.get(key.upper(), None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insertFudgedData(self, dataset_path, start_time, data, **kwargs):
        time_index = self.indexForTime(dataset_path, start_time, **kwargs)
        num_hours = \
            self._insertTimeSlice(dataset_path, data, time_index, **kwargs)
        prov_path = kwargs.get('provenance_path', 'provenance')
        self.insertProvenance(prov_path, start_time, data, source='fudged',
                              **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def isForecast(self, **kwargs):
        return kwargs.get('forecast', False)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def isReanalysis(self, **kwargs):
        source = kwargs.get('source', None)
        return source in self.source.source_priority

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def manageTimeDependencies(self, dataset_path, prov_path, start_time,
                                     end_time, source):
        if source == 'forecast':
            self.setForecastTimes(dataset_path, start_time, end_time)
            if prov_path is not None:
                self.setForecastTimes(prov_path, start_time, end_time)
        elif source == 'rtma':
            self.setRtmaTimespan(dataset_path, start_time, end_time)
            if prov_path is not None:
                self.setRtmaTimespan(prov_path, start_time, end_time)
        elif source == 'urma':
            self.setUrmaTimespan(dataset_path, start_time, end_time)
            if prov_path is not None:
                self.setUrmaTimespan(prov_path, start_time, end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setRtmaTimespan(self, dataset_path, start_time, end_time):
        rtma_end_time = self.timeAttribute(dataset_path, 'rtma_end_time')
        if rtma_end_time is None or end_time > rtma_end_time:
            self.setTimeAttribute(dataset_path, 'rtma_end_time', end_time)

            last_obs_time = self.timeAttribute(dataset_path, 'last_obs_time')
            if last_obs_time is None or end_time > last_obs_time:
                self.setTimeAttribute(dataset_path, 'last_obs_time', end_time)
                self.adjustForecast(dataset_path, end_time)
                self.setLastValidTime(dataset_path, end_time, 'rtma')

            self.adjustReanalysisDates('urma', dataset_path, start_time,
                                       end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setUrmaTimespan(self, dataset_path, start_time, end_time):
        urma_end_time = self.timeAttribute(dataset_path, 'urma_end_time')
        if urma_end_time is None or end_time > urma_end_time:
            self.setTimeAttribute(dataset_path, 'urma_end_time', end_time)

            last_obs_time = self.timeAttribute(dataset_path, 'last_obs_time')
            if last_obs_time is None or end_time > last_obs_time:
                self.setTimeAttribute(dataset_path, 'last_obs_time', end_time)
                self.adjustForecast(dataset_path, end_time)
                self.setLastValidTime(dataset_path, end_time, 'urma')

            self.adjustReanalysisDates('rtma', dataset_path, start_time,
                                       end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setValidationTime(self, dataset_path, start_time, end_time, source):
        # dataset period must be 'hour'
        period = self.getDatasetAttribute(dataset_path, 'period', None)

        # data was either source observations or from a forecast
        if source == 'urma':
            self.setUrmaTimespan(dataset_path, start_time, end_time)
        elif source == 'rtma':
            self.setRtmaTimespan(dataset_path, start_time, end_time)
        elif source in ('ndfd','forecast'):
            self.setForecastTimes(dataset_path, start_time, end_time)
        else: self.setLastObsTime(dataset_path, end_time, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourcePriority(self, source):
        sources = self.source.source_priority
        if source in sources: return sources.index(source), sources
        return -1, sources

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceTimespan(self, dataset_path, source):
        period = self.getDatasetAttribute(dataset_path, 'period', None)
        if period != 'hour':
            errmsg = 'Period for "%s" dataset is not "hour"'
            raise KeyError, errmsg % dataset_path

        start_attr = '%s_start_time' % source
        start_time = self.timeAttribute(dataset_path, start_attr, None)
        end_attr = '%s_end_time' % source
        end_time = self.timeAttribute(dataset_path, end_attr, None)
        if end_time is None:
            if start_time is None:
                errmsg = '"%s" dataset has neither a "%s" or "%s" attribute.'
                raise LookupError, errmsg % (dataset_path,start_attr,end_attr)
            else:
                errmsg = '"%s" dataset does not have a "%s" attribute.'
                raise LookupError, errmsg % (dataset_path, end_attr)

        if start_time is None:
            if source == 'urma':
                # when present, URMA should start at beginning of dataset
                start_time = self.timeAttribute(dataset_path, 'start_time')

            elif source == 'rtma':
                urma_end_time = \
                    self.timeAttribute(dataset_path, 'urma_end_time', None)
                if urma_end_time is None:
                    # no URMA, RTMA should start at beginning of dataset
                    start_time = self.timeAttribute(dataset_path, 'start_time')
                # URMA present, RTMA should start one hour after URMA 
                elif end_time > urma_end_time:
                    start_time = urma_end_time + ONE_DAY 
                # should never get here, this means dataset is broken
                else:
                    errmsg = 'RTMA timespan overlaps URMA in "%s"'
                    raise ValueError, errmsg % dataset_path

        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateDataFromSource(self, dataset_path, source, start_time, data,
                                   **kwargs):
        time_index = self.indexForTime(dataset_path, start_time, **kwargs)

        processor = self.inputProcessor(dataset_path)
        if processor is not None: data = processor(data)

        num_hours = \
            self._insertTimeSlice(dataset_path, data, time_index, **kwargs)

        prov_path = kwargs.get('provenance_path', 'provenance')
        self.insertProvenance(prov_path, start_time, data,
                              source=source.lower(), **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateForecast(self, dataset_path, start_time, data, **kwargs):
        obs_end_time = self.timeAttribute(dataset_path, 'rtma_end_time', None)
        if obs_end_time is None:
            obs_end_time = \
                self.timeAttribute(dataset_path, 'urma_end_time', None)
            analysis = 'URMA'
        else: analysis = 'RTMA'
        if obs_end_time is not None and start_time <= obs_end_time:
            data_hour = obs_end_time.strftime('%H on %m/%d,%Y')
            errmsg = 'Forecast data may not replace or overlap %s.' % analysis
            errmsg += '\n%s end time = %s.' % (analysis, data_hour)
            errmsg += '\nforecast start time = %s.' 
            raise IndexError, errmsg % start_time.strftime('%H on %m/%d,%Y')

        processor = self.inputProcessor(dataset_path)
        if processor is not None: data = processor(data)

        time_index = self.indexForTime(dataset_path, start_time, **kwargs)
        num_hours = \
            self._insertTimeSlice(dataset_path, data, time_index, **kwargs)
        fcast_end_time = start_time + datetime.timedelta(hours=num_hours-1)

        prov_path = kwargs.get('provenance_path', 'provenance')
        self.insertProvenance(prov_path, start_time, data, **kwargs)

        if set_fcast_start:
            self.setForecastTimes(dataset_path, start_time, fcast_end_time)
            self.setForecastTimes(prov_path, start_time, fcast_end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateReanalysisData(self, source, dataset_path, start_time, data,
                                  **kwargs):
        if source.lower() == 'urma':
            self.updateWithUrmaData(dataset_path, start_time, data, **kwargs)
        elif source.lower() == 'rtma':
            self.updateWithRtmaData(dataset_path, start_time, data, **kwargs)
        elif source.lower() == 'fcast':
            self.updateForecast(dataset_path, start_time, data, **kwargs)
        else:
            self.updateDataFromSource(dataset_path, source, start_time, data,
                                      **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateWithRtmaData(self, dataset_path, start_time, data, **kwargs):
        if not kwargs.get('force',False): # allow override of this rule
            urma_end_time = self.timeAttribute(dataset_path, 'urma_end_time')
            if urma_end_time is not None and start_time <= urma_end_time:
                hours = (urma_end_time.strftime('%H on %m/%d,%Y'),
                         start_time.strftime('%H on %m/%d,%Y'))
                errmsg = 'RTMA data may not replace or overlap URMA.'
                errmsg += '\nURMA end time = %s.\nRTMA start time = %s.'
                raise IndexError, errmsg % hours

        processor = self.inputProcessor(dataset_path)
        if processor is not None: data = processor(data)

        time_index = self.indexForTime(dataset_path, start_time, **kwargs)
        num_hours = \
            self._insertTimeSlice(dataset_path, data, time_index, **kwargs)
        
        prov_path = kwargs.get('provenance_path', 'provenance')
        self.insertProvenance(prov_path, start_time, data, source='rtma',
                              **kwargs)

        rtma_end_time = start_time + datetime.timedelta(hours=num_hours-1)
        self.manageTimeDependencies(dataset_path, prov_path, start_time,
                                    rtma_end_time, 'rtma')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateWithUrmaData(self, dataset_path, start_time, data, **kwargs):
        time_index = self.indexForTime(dataset_path, start_time, **kwargs)

        processor = self.inputProcessor(dataset_path)
        if processor is not None: data = processor(data)

        num_hours = \
            self._insertTimeSlice(dataset_path, data, time_index, **kwargs)

        prov_path = kwargs.get('provenance_path', 'provenance')
        self.insertProvenance(prov_path, start_time, data, source='urma',
                              **kwargs)

        urma_end_time = start_time + datetime.timedelta(hours=num_hours-1)
        self.manageTimeDependencies(dataset_path, prov_path, start_time,
                                    urma_end_time, 'urma')

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initDataProcessors_(self, **kwargs):
        # special processing rules for datasets
        self.processors = ConfigObject('processors', None)
        # humidity data input processor
        def processRhum(data):
            rhum = N.around(data, 2)
            rhum[N.where(rhum > 100)] = 100.
            rhum[N.where(rhum < 0)] = 0.
            return rhum
        self.processors.RHUM = processRhum

        # temperature data input processor
        def processTemp(data):
            return N.around(data, 2)
        self.processors.DPT = processTemp
        self.processors.TMP = processTemp

        # precip data input processor
        def processPcpn(data):
            nans = N.where(N.isnan(data))
            if len(nans[0]) > 0:
                data[nans] = 0.
                data[N.where(data < 0.01)] = 0.
                data[nans] = N.nan
            else: data[N.where(data < 0.01)] = 0.
            return N.around(data, 2)
        self.processors.PCPN = processPcpn

        processors = kwargs.get('processors', None)
        if processors is not None:
            if isinstance(processors, dict):
                for key, function in processors.items():
                    self.processors[key] = function
            elif isinstance(processors, (tuple, dict)):
                for key, function in processors:
                    self.processors[key] = function
            else:
                errmsg = '"processors" kwarg must be dict,tuple or list : NOT '
                TypeError, errmsg + str(type(processors))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileManager(ReanalysisGridFileManagerMethods,
                                HourlyGridFileManager):

    def __init__(self, hdf5_filepath, mode='r', **kwargs):
        HourlyGridFileManager.__init__(self, hdf5_filepath, mode)
        self._initDataProcessors_(**kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        HourlyGridFileManager._loadManagerAttributes_(self)
        self._loadHourGridAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileBuilder(HourlyGridBuilderMethods,
                                ReanalysisGridFileManager):
    """ Creates a new HDF5 file with read/write access to hourly 3D
        gridded data.
    """
    def __init__(self, hdf5_filepath, config, filetype, region, source,
                       reference_time, timezone, lons=None, lats=None,
                       kwarg_dict={}):
        self.preInitBuilder(config, filetype, region, source, reference_time,
                            timezone, kwarg_dict)

        mode = kwarg_dict.get('mode', 'w')
        if mode == 'w':
            self.load_manager_attrs = False
        else: self.load_manager_attrs = True

        ReanalysisGridFileManager.__init__(self, hdf5_filepath, mode)
        # set the time span for this file
        #self.initTimeAttributes(**kwargs)
        # close the file to make sure attributes are saved
        self.close()
        # reopen the file in append mode
        self.open(mode='a')
        # build lat/lon datasets if they were passed
        if lons is not None:
            self.initLonLatData(lons, lats, **kwarg_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def preInitBuilder(self, config, filetype, region, source, reference_time,
                             timezone, kwarg_dict={}):
        HourlyGridBuilderMethods.preInitBuilder(self, config, filetype,
                                 region, source, timezone, kwarg_dict)
        self.reference_time = reference_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceFileAttributes(self, **kwargs):
        """ 
        resolve data source attributes for the file
        """
        grid = self.config.sources.reanalysis.grid
        region = kwargs.get('region', grid.region)
        attrs = { 'data_bbox': grid.bbox[region],
                  'data_sources': grid.sources, 
                  'description': kwargs.get('description', grid.description),
                  'grid_type': grid.grid_type,
                  'node_search_radius': grid.search_radius,
                  'node_spacing': grid.node_spacing,
                  'region': region,
                  'resolution':grid.resolution,
                  'source': grid.source,
                  'sources': grid.sources,
                }

        return attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveSourceAttributes(self, **kwargs): 
        """
        resolve data source attributes for a dataset
        """
        return self.sourceFileAttributes(**kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        if self.load_manager_attrs:
            ReanalysisGridFileManager._loadManagerAttributes_(self)
        else:
            self.time_attr_cache = { }

