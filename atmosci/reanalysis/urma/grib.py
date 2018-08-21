
import pygrib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAGribFileReader(object):

    def __init__(self, grib_filepath, grib_source):
        self.__gribs = None
        self.__grib_filepath = None
        self.__grib_source = grib_source
        self.__source_variables = self.__grib_source.variables
        self.open(grib_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @property
    def gribs(self): return self.__gribs

    @property
    def grib_source(self): return self.__grib_source

    @property
    def filepath(self): return self.__grib_filepath

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
        print 'opened grib file :\n    ', self.__grib_filepath

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
    #   str(grib) or repr(grib) i.e. __repr__() # prints inventory of grib
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
