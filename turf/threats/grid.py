
import datetime

from atmosci.utils.timeutils import dateAsString

from atmosci.hdf5.dategrid import Hdf5DateGridFileBuilder

from atmosci.seasonal.methods.builder  import TimeGridFileBuildMethods
from atmosci.seasonal.methods.timegrid import TimeGridFileManagerMethods

from turf.grid import TurfGridFileManagerMethods, \
                      TurfGridFileReader, \
                      TurfGridFileManager


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfThreatGridFileReader(TurfGridFileReader):

    def __init__(self, filepath):
        TurfGridFileReader.__init__(self, filepath)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfThreatGridFileManager(TurfGridFileManager):

    def __init__(self, filepath, mode='r'):
        TurfGridFileManager.__init__(self, filepath, mode=mode)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfThreatGridFileBuilder(TurfGridFileManagerMethods,
                                TimeGridFileBuildMethods,
                                TimeGridFileManagerMethods,
                                Hdf5DateGridFileBuilder):

    def __init__(self, config, threat_config, filepath, period, target_year,
                       source, region, lons=None, lats=None, **kwargs):
        self.threat_period = period
        self.threat_config = threat_config
        self._preInitProject_()
        self.preInitBuilder(config, threat_config.name, source, target_year,
                            region, **kwargs)
        mode = kwargs.get('mode', 'w')
        Hdf5DateGridFileBuilder.__init__(self, filepath, self.start_date, 
                                               self.end_date, lons, lats, mode)
        self.initFileAttributes(**kwargs)
        self.postInitBuilder(**kwargs)
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def additionalFileAttributes(self, **kwargs):
        attrs = { 'end_date':self.dateAsString(self.end_date),
                  'coverage':self._threatPeriodCoverage(),
                  'target_year': self.target_year,
                  'threat':self.filetype.threat,
                  'start_date':self.dateAsString(self.start_date),
                  # 'num_days':self.num_days,
                }
        reference_date = kwargs.get('reference_date', None)
        if reference_date is not None:
            attrs['reference_date'] = reference_date
        return attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisEndDate(self, dataset_path):
        last_obs_date = self.dateAttribute(dataset_path, 'last_obs_date', None)
        rtma_end_date = self.dateAttribute(dataset_path, 'rtma_end_date', None)
        if last_obs_date is None: return rtma_end_date
        if rtma_end_date is None: return last_obs_date
        return max(last_obs_date,rtma_end_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def preInitTimeAttributes(self, target_year, **kwargs):
        project = self.config.project
        self.target_year = target_year

        start_date = kwargs.get('start_date', None)
        if start_date is None:
            day = (target_year,) + self.project.start_day
            start_date = datetime.date(*day)
        self.start_date = start_date

        end_date = kwargs.get('end_date', None)
        if end_date is None:
            day = (target_year,) + self.project.end_day
            end_date = datetime.date(*day)
        self.end_date = end_date

        self.num_days = (self.end_date - self.start_date).days + 1

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _projectEndDate(self, year, **kwargs):
        return self.end_date

    def _projectStartDate(self, year, **kwargs):
        return self.start_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveDatasetDescription(self, dataset, **kwargs):
        if '%(threat)s' in dataset.description:
            threat = { 'threat':self.filetype.threat, }
            return dataset.description % threat
        return dataset.description % kwargs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveDatasetChunks(self, dataset, shape, view, **kwargs):
        chunks = kwargs.get('chunks', None)
        if chunks is None: chunks = dataset.get('chunks', None)
        if chunks:
            if 'num_days' in chunks:
                if isinstance(chunks, tuple): chunks = list(chunks)
                chunks[chunks.index('num_days')] = self.num_days
            return tuple(chunks)
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveTimeAttributes(self, dataset_config, **kwargs):
        time_attrs = self._resolveDateAttributes(dataset_config, **kwargs)
        time_attrs['coverage'] = self._threatPeriodCoverage()
        return time_attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _threatPeriodCoverage(self):
        if 'periods' in self.threat_config:
            return self.threat_config.periods[self.threat_period].coverage
        else: return self.threat_config.coverage

