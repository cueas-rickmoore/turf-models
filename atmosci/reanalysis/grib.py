
import pygrib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# pygrib is a pain to use with some models due to parameter naming issues
#
# name of variable contained in the grib
#     u'name'
#     u'parameterName'
#     u'shortName'
#
# ?????
#     u'level'     
#
# analysis time as datetime.datetime ... first hour for multi-hour variables
#     u'analDate'
#
# valid time as datetime.datetime ... usually the same as analDate
#     u'validDate'
#
# number of data intervals (number of hours for hourly models)
#     u'lengthOfTimeRange',
# for hourly data models
#      end_hour = analDate + datetime.timedelta(hours=lengthOfTimeRange)
#
# individual components of analysis date as int
#     u'year', u'month', u'day', u'hour', u'minute', u'second'
#
# data start date as an int (value in tens of millions YYYYMMDD)
#     u'dataDate' 
# data start time as an int (value = hour*100 + minutes)
#     u'dataTime' 
#
# forecast hour as an int (hour at which data ends)
#     u'forecastTime'
#
# hour (as an int) at which last data value occurs
#     u'hourOfEndOfOverallTimeInterval',
#     (should be the same as forecastTime in most cases)
#
# date at end of time span for multi-hour variables
#     u'validityDate'
#     as an int (value in tens of millions YYYYMMDD)
#
# hour at end of time span for multi-hour variables
#     u'validityTime'
#     as an int (value = hour*100 + minutes)
#
# time step parameters
#     u'stepType'
#     u'startStep'
#     u'endStep'
#     u'stepRange'
#     u'stepUnits'
#     u'timeIncrement'
#
# array of data values
#     u'values'
#
# offset and scale applied to data values
#     u'offsetValuesBy'
#     u'scaleValuesBy'
#
# units for data values
#     u'units' ... units manipulated to make them easier to use
#                  e.g. "kg m**-2" for "kg m-2"
#     u'parameterUnits' ... units as actually in the file
#
# data statistics
#    u'average',
#    u'maximum'
#    u'minimum'
#    u'standardDeviation',
#    u'missingValue'
#
# data counters
#    u'numberOfValues' ... number of nodes with valid values
#    u'numberOfMissing' ...  number of nodes with missing values
#    total number of grid nodes
#    u'numberOfDataPoints' = u'numberOfValues' + u'numberOfMissing'
#
# coordinates
#    u'latLonValues'
#    u'latitudes'
#    u'longitudes'
#
# level in atmosphere
#    u'topLevel'
#    u'typeOfLevel'
#
# ???? not sure how to use it 
#    u'isHindcast'
#
# ????
#    u'gridType'
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribReader(object):

    def __init__(self, grib_filepath, grib_source, debug=False):
        self.__gribs = None
        self.__grib_filepath = None
        self.__grib_source = grib_source
        self.__source_variables = self.__grib_source.variables
        self.debug = debug
        self.open(grib_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @property
    def gribs(self): return self.__gribs

    @property
    def grib_names(self): return self.__gribname_indexes.keys()

    @property
    def grib_source(self): return self.__grib_source

    @property
    def filepath(self): return self.__grib_filepath

    @property
    def short_names(self): return self.__shortname_indexes.keys()

    @property
    def source_variables(self): return self.__source_variables

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def close(self):
        self.__gribs.close()
        self.__gribs == None

    def open(self, grib_filepath=None):
        if grib_filepath is None:
            self.__gribs = pygrib.open(self.__grib_filepath)
        else:
            self.__gribs = pygrib.open(grib_filepath)
            self.__grib_filepath = grib_filepath
        if self.debug: print 'opened grib file :\n    ', self.__grib_filepath

        # map name to indexes because pygrib doesn't get some variable
        # names right (or at all)
        self.__gribname_indexes = { } 
        for grib in self.__gribs:
            parts = str(grib).split(':')
            self.__gribname_indexes[parts[1]] = int(parts[0])
        # map the names in the grib file to the short names used
        # in the config files
        self.__shortname_indexes = { }
        for name, info in self.__source_variables.items():
            if info.pygrib in self.__gribname_indexes:
                self.__shortname_indexes[name.lower()] = \
                     self.__gribname_indexes[info.pygrib]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def configFor(self, short_name):
        self.__source_variables[short_name.upper]

    def messageFor(self, var_name):
        index = self.varnameToIndex(var_name)
        return self.__gribs[index]

    def varnameToIndex(self, var_name):
        if len(var_name) <= 4:
             return self.__shortname_indexes[var_name.lower()]
        else: return self.__gribname_indexes[var_name]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # pygrib : message attribute access 
    #
    #  grib.attr_name i.e. _getattr_(attr_name) # returns attribute value
    #                  _getattribute_(attr_name) # returns attribute value
    #  grib[key] i.e. _getitem_(key) # returns value associated with grib key
    #
    # pygrib : message functions
    #
    #   data(lat1=None,lat2=None,lon1=None,Lon2=None)
    #        # returns data, lats and lons for the bounding box
    #   has_key(key) # T/F whether grib has the specified key
    #   is_missing(key) # True if key is invalid or value is equal to
    #                   # the missing value for the message
    #   keys() # like Python dict keys function
    #   latlons() # return lats/lons as NumPy array
    #   str(grib) or repr(grib)
    #                i.e. repr(grib) # prints inventory of grib
    #   valid_key(key) # True only if the grib message has a specified key,
    #                  # it is not missing and it has a value that can be read
    #
    # pygrib : message instance variables
    #    analDate     !!! often "unknown" by pygrib
    #    validDate ... value is datetime.datetime
    #    fcstimeunits ... string ... usually "hrs"
    #    messagenumber ... int ... index of grib in file
    #    projparams ... proj4 representation of projection spec
    #    values ... return data values as a NumPy array
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
