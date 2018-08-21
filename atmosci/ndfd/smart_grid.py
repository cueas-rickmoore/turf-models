# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import os
import datetime
ONE_HOUR = datetime.timedelta(hours=1)
import warnings

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth, nextMonth

from atmosci.ndfd.factory import NdfdGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartNdfdDataMethods:

    def latestAvailableForecast(self, variable, date_or_time=None):
        errmsg = 'No "%s" data available for %%s' % variable
        if date_or_time is None:
            today = datetime.date.today()
            next_month = nextMonth(today)
            filepath = self.ndfdGridFilepath(next_month, variable, self.region)
            if not os.path.exists(filepath):
                filepath = self.ndfdGridFilepath(today, variable, self.region)
                if not os.path.exists(filepath):
                    when = '%s or %s' % (today.strftime('%M,%Y'),
                                         next_month.strftime('%M,%Y'))
                    raise IOError, errmsg % when
        else:
            filepath = \
                self.ndfdGridFilepath(date_or_time, variable, self.region)
            if not os.path.exists(filepath):
                raise IOError, errmsg % date_or_time.strftime('%M,%Y')

        Class = self.fileAccessorClass('ndfd_grid', 'read')
        reader = Class(filepath)
        last_valid = reader.timeAttribute(variable, 'last_valid_time', None)
        reader.close()
        return last_valid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def slices(self, slice_start_time, slice_end_time):

        slices = [ ]
        start_time = tzutils.tzaDatetime(slice_start_time, 'UTC')
        end_time = tzutils.tzaDatetime(slice_end_time, 'UTC')

        if start_time.month == end_time.month:
            slices.append((start_time, end_time))
        else:
            last_day = lastDayOfMonth(start_time)
            month_end = start_time.replace(day=last_day, hour=23)
            slices.append((start_time, month_end))
            
            month = start_time.month + 1
            while month < end_time.month:
                month_start = start_time.replace(month=month, day=1, hour=0)
                last_day = lastDayOfMonth(month_start)
                month_end = month_start.replace(day=last_day, hour=23)
                slices.append((month_start, month_end))
            
            slices.append((end_time.replace(day=1, hour=0), end_time))

        return tuple(slices)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeSlice(self, variable, slice_start_time, slice_end_time, **kwargs):
        region = kwargs.get('region', self.region)

        # find
        time_slices = self.slices(slice_start_time, slice_end_time)

        # filter annoying numpy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',"invalid value encountered in greater")
        warnings.filterwarnings('ignore',"invalid value encountered in less")
        warnings.filterwarnings('ignore',"Mean of empty slice")
        # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

        data_slices = [ ]
        for first_hour, last_hour in time_slices:
            reader = \
                self.ndfdGridFileReader(first_hour, variable, region, **kwargs)
            data = \
                reader.timeSlice(variable, first_hour, last_hour, **kwargs)
            units = reader.datasetAttribute(variable, 'units')
            prev_indx = eindx
            data_slices.append((units,first_hour,data))

        # turn annoying numpy warnings back on
        warnings.resetwarnings()

        if kwargs.get('lonlat', False):
            lats = reader.lats
            lons = reader.lons
            reader.close()
            return lons, lats, data_slices
        else:
            reader.close()
            return data_slices


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartNdfdGridReader(SmartNdfdDataMethods, NdfdGridFileFactory):

    def __init__(self, region, **kwargs):
        NdfdGridFileFactory.__init__(self, **kwargs)
        self.region = region
        source = kwargs.get('source','acis')
        self.source = self.config.sources[source]
        dims = self.source.grid_dimensions[region]
        self.grid_dimensions = (dims.lat, dims.lon)

