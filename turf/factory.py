
import os
import datetime
import json

from atmosci.acis.nodefinder import AcisGridNodeFinder, AcisGridNodeIndexer

from atmosci.seasonal.factory import SeasonalProjectFactory
from atmosci.seasonal.methods.season import SeasonDateMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.config import CONFIG

from atmosci.seasonal.registry import REGBASE as REGISTRY


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfProjectFactoryMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def seasonDates(self, year):
        return (datetime.date(year, *self.project.start_day),
                datetime.date(year, *self.project.end_day))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceToToolDirpath(self, source):
        if source is None:
            return self.sourceToDirpath(self.project.source)
        return self.sourceToDirpath(source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceToToolFilepath(self, source):
        if source is None:
            return self.sourceToFilepath(self.project.source)
        return self.sourceToFilepath(source)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def tightJsonString(self, value):
        return json.dumps(value, separators=(',', ':'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initTurfFactory_(self):
        self.acisNodeFinder = AcisGridNodeFinder(self.project.region)
        self.acisNodeIndexer = AcisGridNodeIndexer(self.project.region)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfProjectFactory(TurfProjectFactoryMethods, SeasonDateMethods,
                         SeasonalProjectFactory):

    def __init__(self, config=CONFIG, registry=REGISTRY):
        SeasonalProjectFactory.__init__(self, config, registry)
        self._initTurfFactory_()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        SeasonalProjectFactory._registerAccessClasses(self)

