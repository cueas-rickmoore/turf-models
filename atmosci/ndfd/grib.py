# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import os, sys
import warnings

import datetime
from dateutil.relativedelta import relativedelta

import numpy as N
import pygrib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.ndfd.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NdfdGribFileIterator(object):
    """
    An iterator to sequentially return messages from  a grib file
    """

    def __init__(self, grib_filepath):
        self.gribs = pygrib.open(grib_filepath)
        self.messages = self.gribs.select()
        self.next_message = 0
        self.num_messages = len(self.messages)

    def __iter__(self):
        return self

    def close(self):
        self.gribs == None

    @property
    def first_message(self):
        return self.messages[0]

    @property
    def last_message(self):
        return self.messages[-1]

    def next(self):
        if self.next_message < self.num_messages:
            index = self.next_message
            self.next_message += 1
            return index, self.messages[index]

        self.gribs.close()
        self.messages == [ ]
        raise StopIteration


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NdfdGribFileReader(object):
    """
    VERY SIMPLISTIC NDFD grib file reader
    """

    def __init__(self, grib_filepath, timespan=None, **kwargs):
        config = kwargs.get('config', CONFIG).copy()
        self.__config = config.copy()
        self.__grib_filepath = grib_filepath
        self.__gribs = None
        self.__ndfd_config = ndfd = config.sources.ndfd
        self.__grib_source = ndfd[kwargs.get('source', ndfd.default_source)]
        if timespan is None: self.timespan = self.grib_source.timepsans[0]
        else: self.timespan = timepsan
        self.variable_map = self.grib_source.variable_maps[timespan] 

    @property
    def conifg(self):
        return self.__config

    @property
    def gribs(self):
        return self.__gribs

    @property
    def filepath(self):
        return self.__grib_filepath

    @property
    def ndfd_config(self):
        return self.__ndfd_config

    @property
    def grib_source(self):
        return self.__grib_source

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def close(self):
        pygrib.close(self.__gribs)
        self.__gribs == None

    def open(self):
        self.__gribs = pygrib.open(self.__grib_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def explore(self):
        info = [ ]
        for index, grib in enumerate(self.gribs.select()):
            info.append( (index, grib.name, grib.shortName, grib.forecastTime,
                          grib.validDate) )
        return info

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def exploreInDetail(self):
        info = [ ]
        for index, grib in enumerate(self.gribs.select()):
            info.append( (index, grib.name, grib.shortName, grib.forecastTime,
                          grib.validDate, grib.dataDate, grib.dataTime,
                          grib.missingValue, grib.units, grib.values.shape) )
        return info

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

