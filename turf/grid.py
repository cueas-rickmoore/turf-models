
import datetime
ONE_DAY = datetime.timedelta(days=1)
import warnings

import numpy as N

from atmosci.acis.nodefinder import AcisGridNodeFinder, AcisGridNodeIndexer

from atmosci.seasonal.grid import SeasonalGridFileReader, \
                                  SeasonalGridFileManager, \
                                  SeasonalDateGridFileBuilder

def dateStr(date_obj): return date_obj.strftime('%Y-%m-%d')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.seasonal.registry import REGBASE as REGISTRY


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGridFileMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def allPossibleDates(self, dataset_path):
        date_attrs = self.dateAttributes(dataset_path, True)
        return { 'end_date': date_attrs.get('end_date', None),
                 'start_date': date_attrs.get('start_date', None),
                 'fcast_end_date': date_attrs.get('fcast_end_date', None),
                 'fcast_start_date': date_attrs.get('fcast_start_date', None),
                 'last_obs_date': date_attrs.get('last_obs_date', None),
                 'last_valid_date': date_attrs.get('last_valid_date', None),
                 'first_valid_date': date_attrs.get('first_valid_date', None),
               }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def allValidData(self, dataset_path):
        dates = self.allPossibleDates(dataset_path)

        # there is no available data unless last_valid_Date has been set
        last_valid_date = dates['last_valid_date']
        if last_valid_date is None: return None, dates
        end_date = last_valid_date

        first_valid_date = dates['first_valid_date']
        if first_valid_date is not None:
            data = self.dateSlice(dataset_path, first_valid_date, end_date)
            return data, dates

        missing = self.datasetAttribute(dataset_path, 'missing')
        if N.isnan(missing):
            def numMissing(data): return len(N.where(N.isnan(data))[0])
        else:
            def numMissing(data): return len(N.where(data == missing)[0])

        start_date = dates['start_date']
        data = self.dateSlice(dataset_path, start_date, end_date)
        num_days = data.shape[0]
        num_nodes = N.product(data.shape[1:])

        day = 0
        while day < num_days:
            num_missing = numMissing(data)
            if num_missing < num_nodes:
                if day > 0:
                    first_date = start_date + datetime.timedelta(days=day)
                    dates['first_valid_date'] = first_date
                break
            day += 1

        if last_valid_date == dates['end_date']:
            if day == 0: return data, dates
            return data[day:,:,:], dates

        end_indx = self._dateToIndex(dataset_path, last_valid_date)+1
        if day == 0: return data[:end_indx,:,:], dates
        return data[day:end_indx,:,:], dates

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def datesToStrings(self, date_dict, key_translations={}):
        string_dict = { }
        for key, date in date_dict.items():
            if date is not None:
                date_key = key_translations.get(key, key)
                if date_key is not None:
                    string_dict[date_key] = dateStr(date)

        return string_dict

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    #def ll2index(self, lon, lat):
    #    if hasattr(self, 'acisNodeIndexer'):
    #        return self.acisNodeIndexer(lon, lat)
    #    else: return self._indexOfClosestNode(lon, lat)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initTurfGridDataAccesseors_(self):
        if hasattr(self, 'region'):
            self.nodeFinder = AcisGridNodeFinder(self.region)
            self.nodeFinder = AcisGridNodeFinder(self.region)
        else:
            self.nodeIndexer = AcisGridNodeIndexer('NE')
            self.nodeIndexer = AcisGridNodeIndexer('NE')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGridFileReader(TurfGridFileMethods, SeasonalGridFileReader):
    """ reader = TurfGridFileReader(filePath, registry)
    """
    def __init__(self, filepath, registry=REGISTRY):

        SeasonalGridFileReader.__init__(self, filepath, registry)
        self._initTurfGridDataAccesseors_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGridFileManagerMethods(TurfGridFileMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def manageForecastDates(self, dataset_path, obs_end_date):
        if obs_end_date == self.dateAttribute(dataset_path, 'end_date'):
            self.removeForecast(dataset_path)
            return True
        
        # return True when forcecast is changed, otherwise returns False
        # adjust forecast dates that were replaced by reanalysis
        fcast_start = self.dateAttribute(dataset_path, 'fcast_start_date', None)
        fcast_end = self.dateAttribute(dataset_path, 'fcast_end_date', None)
        # no forecast in file
        if fcast_start is None:
            if fcast_end is None: # OK, do nothing
                return False

            # fcast_end but no start
            errmsg = 'ERROR in file :\n%s\n"fcast_start_date"'
            errmsg += ' attribute is not set for dataset "%s",\n'
            errmsg += 'but "forecast_end_date" attribute is set to %s.'
            args = (self.filepath, dataset_path, dateStr(fcast_end))
            raise AttributeError, errmsg % args

        if fcast_end is None: # fcast_start butno end
            errmsg = 'ERROR in file :\n%s\n"fcast_start_date"' 
            errmsg += ' attribute for dataset "%s" was set to %s,\n'
            errmsg += 'but "forecast_end_date" attribute is not present.'
            args = (self.filepath, dataset_path, dateStr(fcast_start))
            raise AttributeError, errmsg % args

        if fcast_start <= obs_end_date:
            # some part of forecast survived reanalysis update
            fcast_start = obs_end_date + ONE_DAY

            if fcast_end <= obs_end_date: # forecast completely overwritten
                self.removeForecast(dataset_path)
            else:
                season_end = self.dateAttribute(dataset_path, 'end_date')
                if fcast_start < fcast_end and fcast_start < season_end:
                    # adjust forecast start to be after new obs_end_date
                    # potentially a daily occurrence
                    self.setDateAttribute(dataset_path, 'fcast_start_date',
                                          fcast_start)
                else:
                    # this will happen at end of season
                    self.removeForecast(dataset_path)
            return True

        return False

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def manageObsDates(self, dataset_path, new_date):
        last_obs_date = self.dateAttribute(dataset_path, 'last_obs_date', None)
        last_valid_date = \
            self.dateAttribute(dataset_path, 'last_valid_date', None)
        
        if last_obs_date is None: # should only happen once
            self.setDateAttribute(dataset_path, 'last_obs_date', new_date)
            self.setDateAttribute(dataset_path, 'rtma_end_date', new_date)

        elif new_date > last_obs_date:
            self.setDateAttribute(dataset_path, 'last_obs_date', new_date)
            self.setDateAttribute(dataset_path, 'rtma_end_date', new_date)

        if last_valid_date is None or new_date > last_valid_date:
            self.setDateAttribute(dataset_path, 'last_valid_date', new_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def removeForecast(self, dataset_path):
        # new data stomped on entire forecast
        if self.datasetHasAttribute(dataset_path, 'fcast_start_date'):
            self.deleteDatasetAttribute(dataset_path, 'fcast_start_date')
            last_valid = self.dateAttribute(dataset_path, 'last_valid_date')
            fcast_end = self.dateAttribute(dataset_path, 'fcast_end_date')
            self.deleteDatasetAttribute(dataset_path, 'fcast_end_date')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateReanalysis(self, dataset_path, start_date, data, **kwargs):
        #print 'updateForecast :', start_date, start_date + datetime.timedelta(days=data.shape[0]-1)
        #exit()

        # save the data and get new end date
        num_days =  self.insertByDate(dataset_path, data, start_date, **kwargs)
        data_end_date = start_date + datetime.timedelta(days=num_days-1)

        self.manageObsDates(dataset_path, data_end_date)
        last_obs = self.dateAttribute(dataset_path, 'last_obs_date')
        self.manageForecastDates(dataset_path, last_obs)

        return data_end_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateForecast(self, dataset_path, start_date, data, **kwargs):
        #print 'updateForecast :', start_date, start_date + datetime.timedelta(days=data.shape[0]-1)
        #exit()
        
        season_start = self.dateAttribute(dataset_path, 'start_date')

        if start_date < season_start:
            errmsg = 'Attempt to insert forecast outside season limits.\n'
            errmsg += 'Forecast must be within %s and %s.'
            end = self.dateAttribute(dataset_path, 'end_date')
            season = (dateStr(season_start), dateStr(end))
            raise IndexError, errmsg % season

        last_obs_date = \
            self.dateAttribute(dataset_path, 'last_obs_date', None)
        if last_obs_date is None: # no data in file
            return self._insertForecast(dataset_path, start_date, data,
                                        **kwargs)

        if start_date > last_obs_date:
            # forecast begins and ends after last obs
            return self._insertForecast(dataset_path, start_date, data,
                                         **kwargs)

        # forecast starts before end of obs data > > > this should NEVER happen
        if len(data.shape) == 3:
            end_date = start_date + datetime.timedelta(days=data.shape[0]-1)
        dates = (dateStr(start_date), dateStr(end_date), dateStr(last_obs_date))
        # forecast starts before last obs, trim it
        if end_date > last_obs_date:
            adjusted_start = last_obs_date + ONE_DAY
            offset = (last_obs_date - start_date).days + 1
            info = self._insertForecast(dataset_path, adjusted_start,
                                        data[offset:,:,:], **kwargs)
            errmsg = 'Attempt to insert forecast (%s thru %s)\nover '
            errmsg += 'existing obs data ending at %s\nForecast start'
            errmsg += 'was adjusted to %s'
            dates += (dateStr(adjusted_start),)
            warnings.warn(errmsg % dates, warnings.UserWarning)

        # all of the data is before the current forecast
        # requires stomping on reanalysis which is not allowed
        errmsg = 'Attempted to insert forecast (%s thru %s)\nover'
        errmsg += 'existing obs data ending at %s'
        raise IndexError, errmsg % dates

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _insertForecast(self, dataset_path, fcast_starts, data, **kwargs):
        # assume caller has made sure forecast is not stomping on reanalysis
        num_days = self.insertByDate(dataset_path, data, fcast_starts, **kwargs)
        fcast_ends = fcast_starts + datetime.timedelta(days=num_days-1)

        fcast_start_date = \
            self.dateAttribute(dataset_path, 'fcast_start_date', None)

        if fcast_start_date is None: # no forecast yet
            self.setDateAttribute(dataset_path, 'fcast_end_date', fcast_ends)
            self.setDateAttribute(dataset_path, 'fcast_start_date', fcast_starts)

        else:
            if fcast_ends > self.dateAttribute(dataset_path, 'fcast_end_date'):
                # only change end date when new data goes beyond older forecast
                self.setDateAttribute(dataset_path, 'fcast_end_date', fcast_ends)

        # last valid should always end of forecast
        last_valid = self.dateAttribute(dataset_path, 'last_valid_date', None)
        if last_valid is None or fcast_ends > last_valid:
            self.setDateAttribute(dataset_path, 'last_valid_date', fcast_ends)

        return fcast_ends


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGridFileManager(TurfGridFileManagerMethods, SeasonalGridFileManager):
    """ manager = TurfGridFileManager(filePath, registry, mode='r')
    """
    def __init__(self, filepath, mode='r', registry=REGISTRY):

        SeasonalGridFileManager.__init__(self, filepath, registry, mode)
        self._initTurfGridDataAccesseors_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfGridFileBuilder(TurfGridFileManagerMethods,
                          SeasonalDateGridFileBuilder):
    """ builder = TurfGridFileBuilder(filePath, filetype, project_config, 
                                      start_date, end_date, source,
                                      region, mode='w', **kwargs)
    """
    def __init__(self, filepath, threat, config, start_date, end_date, source,
                       region, mode='w', **kwargs):
        registry = kwargs.get('registry', REGISTRY)

        year = start_date.year
        SeasonalDateGridFileBuilder.__init__(self, filepath, threat, registry,
                                    config, year, start_date, end_date, source,
                                    region, mode, **kwargs)
        if source.name == 'acis':
            self.nodeFinder = AcisGridNodeFinder(region.name)
            self.nodeIndexer = AcisGridNodeIndexer(region.name)

