
import datetime

from atmosci.hdf5.dategrid import Hdf5DateGridFileBuilder

from atmosci.seasonal.methods.builder  import TimeGridFileBuildMethods
from atmosci.seasonal.methods.timegrid import TimeGridFileManagerMethods

from turf.grid import TurfGridFileManagerMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGddFileBuilder(TurfGridFileManagerMethods,
                         TimeGridFileBuildMethods,
                         TimeGridFileManagerMethods,
                         Hdf5DateGridFileBuilder):

    def __init__(self, config, filepath, year, source, region,
                       lons=None, lats=None, **kwargs):
        self._preInitProject_()
        self.preInitBuilder(config, 'gdd', source, year, region, **kwargs)
        mode = kwargs.get('mode', 'w')
        Hdf5DateGridFileBuilder.__init__(self, filepath, self.start_date, 
                                               self.end_date, lons, lats, mode)
        self.initFileAttributes(**kwargs)
        self.postInitBuilder(**kwargs)
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def additionalFileAttributes(self, **kwargs):
        attrs = { 'end_date':dateAsString(self.end_date),
                  'target_year': self.target_year,
                  'start_date':dateAsString(self.start_date),
                }
        return attrs

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

    def _resolveDatasetChunks(self, dataset, shape, view, **kwargs):
        chunks = kwargs.get('chunks', None)
        if chunks is None: chunks = dataset.get('chunks', None)
        if chunks:
            if 'num_days' in chunks:
                if isinstance(chunks, tuple): chunks = list(chunks)
                chunks[chunks.index('num_days')] = self.num_days
            return tuple(chunks)
        return None

