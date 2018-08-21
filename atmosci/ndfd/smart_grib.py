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

import numpy as N
import pygrib

from atmosci.utils.tzutils import asUTCTime

from atmosci.ndfd.factory import NdfdGribFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.ndfd.config import CONFIG
VALID_TIMESPANS = tuple(CONFIG.sources.ndfd.variables.keys())

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

BAD_FILL_METHOD = '"%s" fill method is not supported. Must be one of\n'
BAD_FILL_METHOD += '"avg", "constant", "copy", "scaled".'
BAD_TIMESPAN = '"%s" is not a valid timespan. Must be one of '
BAD_TIMESPAN += ','.join(['"%s"' % span for span in VALID_TIMESPANS])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def fillWithAverage(fcast1, fcast2, varconfig, decimals=2):
    if fcast2 is None: return [ ]

    # make sure forecasts are in the correct order
    if fcast2 > fcast1:
        source, base_time, base_grid = fcast1
        end_grid = fcast2[-1]
        end_time = fcast2[1]
    else: # just in case the rules are not followed
        source, base_time, base_grid = fcast2
        end_grid = fcast1[-1]
        end_time = fcast1[1]
    source = '%s avg' % source

    # number of hours in the gap
    gap = hoursInTimespan(end_time, base_time, inclusive=False)
    grid = N.around(base_grid / gap, decimals)
               
    filled = [(source, base_time, grid),]
    for hr in range(1, gap):
        fcast_time = base_time+datetime.timedelta(hours=hr)
        filled.append((source, fcast_time, grid))

    return filled

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def fillWithConstant(fcast, dummy, varconfig, decimals=2):
    # data for each missing hour set to same numeric value
    source, base_time, base_grid = fcast
    source = '%s constant' % source

    grid = N.empty(base_grid.shape, base_grid.dtype)
    grid.fill(varconfig.fill_value)

    filled = [ fcast, ]
    for hr in range(1, varconfig.span):
        fcast_time = base_time+datetime.timedelta(hours=hr)
        filled.append((source, fcast_time, grid))

    return filled

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def fillWithCopy(fcast, dummy, varconfig, decimals=2):
    # constant : all hours in gap have same values as the fcast
    # dummy only exists for compatability
    source, base_time, grid = fcast
    filled = [(source, base_time, grid),]
    source = '%s copy' % source
    for hr in range(1, varconfig.span):
        fcast_time = base_time+datetime.timedelta(hours=hr)
        filled.append((source, fcast_time, grid))

    return filled

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def scaledFill(fcast1, fcast2, varconfig, decimals=2):
    # scale : increment each hour in the gap by the average
    #         difference b/w end time and base time data values
    if fcast2 is None: return [ ]

    # make sure forecasts are in the correct order
    if fcast2 > fcast1:
        source, base_time, base_grid = fcast1
        end_grid = fcast2[-1]
        end_time = fcast2[1]
    else: # just in case the rules are not followed
        source, base_time, base_grid = fcast2
        end_grid = fcast1[-1]
        end_time = fcast1[1]

    # number of hours in the gap
    gap = hoursInTimespan(end_time, base_time, inclusive=False)
    avg_grid = N.around((end_grid-base_grid) / gap, decimals)

    source = fcast1[0]
    filled = [ (source, base_time, base_grid) ]

    source = '%s scaled' % source
    for hr in range(1, gap):
        fcast_time = base_time+datetime.timedelta(hours=hr)
        grid = base_grid + (avg_grid * hr)
        filled.append((source, fcast_time, grid))

    return filled

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

def spreadFill(fcast1, dummy, varconfig, decimals=2):
    # spread : divide incoming by num hours in span  
    source, base_time, base_grid = fcast1
    source = '%s spread' % source

    # number of hours in the gap
    hours = varconfig.span
    zeros = N.where(base_grid < 0.01)
    grid = N.around((base_grid) / hours, decimals)
    grid[zeros] = 0;

    filled = [ (source, base_time, grid) ]

    for hr in range(1, hours):
        fcast_time = base_time+datetime.timedelta(hours=hr)
        filled.append((source, fcast_time, grid))

    return filled

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

GridFillMethods = {
    'avg': fillWithAverage,
    'constant': fillWithConstant,
    'copy': fillWithCopy,
    'scaled': scaledFill,
    'spread': spreadFill,
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def hoursInTimespan(time1, time2, inclusive=True):
    if time1 > time2: diff = (time1 - time2)
    else: diff = (time2 - time1)
    if inclusive: return (diff.days * 24) + (diff.seconds/3600) + 1
    else: return (diff.days * 24) + (diff.seconds/3600)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def reshapeGrid(grib_msg, missing_value, grib_indexes, grid_shape_2D,
                grid_mask, decimals=2):
    values = grib_msg.values[grib_indexes].reshape(grid_shape_2D)
    if N.ma.is_masked(values): values = values.data
    values[N.where(values >= missing_value)] = N.nan
    values[N.where(grid_mask == True)] = N.nan
    return N.around(values,decimals)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartNdfdGribFileReader(NdfdGribFileFactory):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def completeInitialization(self, **kwargs):
        # initialize additonal factory/reader attributes  
        self.grib_region = kwargs.get('grib_region', self.ndfd.default_region)
        self.grib_source = \
             self.ndfd[kwargs.get('grib_source', self.ndfd.default_source)]
        self.gribs = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataForRegion(self, fcast_date, variable, timespan, grib_region,
                            grid_region, grid_source, fill_gaps=False,
                            graceful_fail=False, debug=False):
        """
        Returns a sequence containing (relative hour, full forecast date,
        numpy array) tuples for each message in the grib files for each
        timezone in the list. Arrays are cleaned so that both masked and
        missing values are set to N.nan. The shape of each returned array
        is the same (num_lons x num_lats)

        Assumes file contains a range of times for a single variable.
        """
        data_records = [ ]

        # parameters for reshaping the grib arrays
        grid_shape_2D, grib_indexes, grid_mask = \
            self.gribToGridParameters(grid_source, grid_region)

        # check whether varible supports filling gaps between records
        varconfig = self.variableConfig(variable, timespan)
        fill_method = varconfig.get('fill_method',None)

        # code for filling gaps between records
        if fill_gaps and fill_method is not None:
            prev_record = None
            if debug:
                info = (timespan, variable, str(fcast_date))
                print '\nReading %s %s grib file for %s' % info

            # retrieve pointers to all messages in the file
            self.openGribFile(fcast_date, variable, timespan, grib_region)
            messages = self.gribs.select()
            first_msg = messages[0]
            missing = float(first_msg.missingValue)
            units = first_msg.units

            # fill the gap between this timespan and the previous one
            if not prev_record is None:
                grid = reshapeGrid(first_msg, missing, grib_indexes,
                                   grid_shape_2D, grid_mask)
                next_record = ('ndfd',asUTCTime(first_msg.validDate),grid)
                data_records.extend(self.fillTimeGap(prev_record,
                                         next_record, varconfig))

            # update with records for the current timespan
            data = self.dataWithoutGaps(messages, varconfig, grib_indexes,
                                        grid_shape_2D, grid_mask, debug)
            data_records.extend(data)

            # track last record in previous timespan
            msg = messages[-1]
            grid = reshapeGrid(msg, missing, grib_indexes, grid_shape_2D,
                               grid_mask)
            prev_record = ('ndfd', asUTCTime(msg.validDate), grid)

            self.closeGribfile()
        
        # code that preserves gaps between records
        else:
            if debug:
                info = (variable, timespan, str(fcast_date))
                print '\nReading %s %s grib file for %s' % info

            # retrieve pointers to all messages in the file
            self.openGribFile(fcast_date, variable, timespan, grib_region)
            messages = self.gribs.select()
            first_msg = messages[0]
            missing = float(first_msg.missingValue)
            units = first_msg.units

            for msg in messages:
                grid = reshapeGrid(msg, missing, grib_indexes,
                                   grid_shape_2D, grid_mask)
                this_time =  asUTCTime(msg.validDate)
                data_records.append(('ndfd', this_time, grid))
                if debug:
                    stats = (N.nanmin(grid), N.nanmax(grid))
                    print 'value stats :', msg.validDate, stats
            self.closeGribfile()

        return units, data_records

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataWithoutGaps(self, messages, varconfig, grib_indexes,
                              grid_shape_2D, grid_mask, debug=False):
        data_records = [ ]

        first_msg = messages[0]
        missing = float(first_msg.missingValue)

        prev_grid = reshapeGrid(first_msg, missing, grib_indexes,
                                grid_shape_2D, grid_mask)
        prev_time = asUTCTime(first_msg.validDate)
        prev_record = ('ndfd', prev_time, prev_grid)
        if debug:
            print 'processing %d grib messages :' % len(messages)
            stats = (N.nanmin(prev_grid), N.nanmax(prev_grid))
            print '    stats :', first_msg.validDate, stats

        open_gap = False
        for msg in messages[1:]:
            grid = reshapeGrid(msg, missing, grib_indexes, grid_shape_2D,
                               grid_mask)
            this_time =  asUTCTime(msg.validDate)
            this_record = ('ndfd', this_time, grid)
            if debug:
                stats = (N.nanmin(grid), N.nanmax(grid))
                print '    stats :', msg.validDate, stats

            gap = hoursInTimespan(prev_time, this_time, inclusive=False)
            if gap > 1:
                records = \
                    self.fillTimeGap(prev_record, this_record, varconfig)
                # add the gap records
                data_records.extend(records)
            else: # no gap, add previous record
                data_records.append(prev_record)

            prev_record = this_record
            prev_time = this_time

        # at this point prev_record == last this_record
        records = self.fillTimeGap(prev_record, None, varconfig)
        if len(records) > 0: data_records.extend(records)
        else: data_records.append(prev_record)

        return data_records

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fillTimeGap(self, fcast1, fcast2, varconfig, decimals=2):
        fill = GridFillMethods.get(varconfig.fill_method, None)
        if fill is None: return [fcast1, fcast2]

        if fcast2 is None: # don't have the next forcast
            # fill method might allow extrapolation
            # otherwise it will return an empty record set
            return fill(fcast1, fcast2, varconfig, decimals)

        # number of hours in the gap
        gap = hoursInTimespan(fcast1[1], fcast2[1], inclusive=False)
        if gap > 1:
            return fill(fcast1, fcast2, varconfig, decimals)
        return [fcast1, fcast2]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribToGridParameters(self, grid_source, grid_region):
        reader = self.staticFileReader(grid_source, grid_region)
        grid_shape_2D, grib_indexes = reader.gribSourceIndexes('ndfd')
        grid_mask = reader.getData('cus_mask')
        reader.close()
        del reader
        return grid_shape_2D, grib_indexes, grid_mask

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridForRegion(self, fcast_date, variable, timespan, grib_region,
                            grid_region, grid_source, fill_gaps=False,
                            graceful_fail=False, debug=False):
        """
        Returns a 3D NumPy grid containing data at all nodes in the grid
        region for all messages in file.
        
        Shape of returned grid is [num_hours, num_lons, num_lats]

        Assumes file contains a range of time periods for a single variable.
        """
        varconfig = self.variableConfig(variable, timespan)

        records = self.dataForRegion(fcast_date, variable, timespans,
                       grib_region, grid_region, grid_source, fill_gaps,
                       graceful_fail, debug)

        first_hour = records[0][1]
        last_hour = records[-1][1]
        num_hours = hoursInTimespan(last_hour, first_hour, inclusive=True)

        grid_shape_2d = records[0][-1].shape
        grid = N.empty((num_hours,)+grid_shape_2D, dtype=float)
        grid.fill(N.nan)

        for index, record in enumerate(records):
            grid[index,:,:] = record[-1]
        
        return first_hour, varconfig.units, grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def closeGribfile(self):
        if self.gribs is not None:
            self.gribs.close()
            self.gribs = None

    def openGribFile(self, fcast_date, variable, timespan, region, **kwargs):
        if self.gribs != None: self.closeGribfile()
        grib_filepath = self.ndfdGribFilepath(fcast_date, variable, timespan,
                                              region, **kwargs)
        if not os.path.exists(grib_filepath):
            info = (timespan, variable, str(fcast_date), grib_filepath)
            errmsg = '%s %s grib file for %s was not found\n %s'
            print errmsg % info
            raise ValueError, 'file not found'

        if kwargs.get('debug',False):
            print '\nReading gribs from :\n', grib_filepath
        try:
            self.gribs = pygrib.open(grib_filepath)
        except e:
            print 'Error reading gribs from file :\n    ', grib_filepath
            raise e

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

    def scanGridFile(self, fcast_date, variable, timespan):
        self.openGribFile(fcast_date, variable, timespan, 'conus')
        for message in self.gribs.select():
            print '\n    grib name :', message.name
            print '    anal date :', message.analDate
            print 'forecast hour :', message.forecastTime
            print 'forecast time :', message.validDate

