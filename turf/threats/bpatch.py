
import datetime
ONE_DAY = datetime.timedelta(days=1)

import numpy as N

from atmosci.units import convertUnits

from turf import common as funcs
from turf.threats.disease import BasicDisease


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BrownPatch(BasicDisease):
    """ Functions that model potential risk for outbreak of Brown
    Patch disease in turf grass.
    """

    def __init__(self, season, period, debug=False):
        BasicDisease.__init__(self, THREATS.bpatch, period, debug)
        # needed for handling seasonal exceptions
        self.season_start = datetime.date(season,*self.config.season.start_day)
        self.season_end = datetime.date(season,*self.config.season.end_day)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, first_hour, temp, dewpt, rhum, pcpn, temp_units,
                       pcpn_units):
        """
        Brown Patch utilizes 24 hour averages and counts in order to
        calculate threat index. Therefore, your hourly data arrays
        must begin at least 24 hours before the first day you want
        results for.

        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
            first_hour: first hour in data arrays (datetime.datetime)
            temp: hourly temperatures.
            dewpt: hourly dewpoint temperatures.
            rhum: hourly relative humidity
            pcpn: hourly precipitation.
            temp_units: units for temperature and dew point arrays.
                        Calculations require degrees 'C' (Celsius),
                        however, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will be
                        converted to 'C' for use in the calculations. 
            pcpn_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                        Data in other units may be passed and will be 
                        converted to 'in' for use in the calculations. 

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : snme day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy array containing daily risk level at each node.
        """
        threat = \
            self.threatIndex(temp, dewpt, rhum, pcpn, temp_units, pcpn_units)
        return self.riskLevel(threat)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dailyReductions(self, temp, dewpt, rhum, pcpn, temp_units,
                              pcpn_units):
        """
        Brown Patch utilizes 24 hour data reductions to calculate 
        threat index. Therefore, hourly data arrays must begin 48
        hours before the expected first day in results.
        
        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
            temp: hourly temperatures.
            dewpt: hourly dewpoint temperatures.
            rhum: hourly relative humidity
            pcpn: hourly precipitation.
            temp_units: units for temperature and dew point arrays.
                        Calculations require degrees 'C' (Celsius),
                        however, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will be
                        converted to 'C' for use in the calculations. 
            pcpn_units: units for precipitation data.
                        Calculations require 'in' (inches of rainfall).
                        Data in other units may be passed and will be 
                        converted to 'in' for use in the calculations. 

        Argument types:ple days at multiple points
            2D NumPy array : snme day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy arrays for the following daily reductions:
                 1) minimum temp
                 2) average rhum
                 3) num hours of leaf wetness 
        """
        # number of hours to skip before starting iteration
        offset = self.config.offset
        # number of hours to evaluate per iteration
        span = self.config.timespan
        # number of hours to increment b/w interations 
        step = self.config.timestep

        # make sure that temperature and dew point units are correct
        tmp_units = self.config.units.tmp
        if temp_units == tmp_units:
            tmp = temp
            dpt = dewpt
        else:
            tmp = convertUnits(temp, temp_units, tmp_units)
            dpt = convertUnits(dewpt, temp_units, tmp_units)

        # calculate minimum daily temp
        mint = funcs.calcTimespanMin(tmp, step, span, offset, N.nan)
        if self.debug:
            print '\n  in dailyReductions ...'
            print '             temp shape :', tmp.shape
            print '         min temp shape :', mint.shape

        # calculate average daily humidity
        avgrh = funcs.calcTimespanAvg(rhum, step, span, offset, N.nan)
        if self.debug:
            print '     avg humidity shape :', avgrh.shape

        # count daily rhum > threshold
        threshold = self.config.rh_threshold
        rh_count = funcs.countTimespanGT(rhum, threshold, step, span, offset)
        if self.debug:
            print '           rh threshold :', threshold
            print '         rh count shape :', rh_count.shape

        # get hourly leaf wetness
        leaf_wet = self.leafWetness(tmp, dpt, pcpn, tmp_units, pcpn_units)
        if self.debug:
            stats = (N.nanmin(leaf_wet), N.nanmean(leaf_wet),
                     N.nanmedian(leaf_wet), N.nanmax(leaf_wet))
            print '         leaf wet stats :', stats
        # count number of hours with leaf wetness
        wet_count = funcs.countTimespanGT(leaf_wet, 0, step, span, offset)
        if self.debug:
            print '              wet count :', wet_count.shape

        return mint, avgrh, rh_count, wet_count

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatIndex(self, first_hour, temp, dewpt, rhum, pcpn, temp_units,
                          pcpn_units):
        """
        Brown Patch utilizes 24 hour averages and counts in order to
        calculate threat index. Therefore, your hourly data arrays
        must begin 24 hours before the expected first day in results.
        
        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
            first_hour: first hour in data arrays (datetime.datetime)
            temp: hourly temperatures
            dewpt: hourly dewpoint temperatures.
            rhum: hourly relative humidity
            pcpn: hourly precipitation.
            temp_units: units for temperature and dew point arrays.
                        Calculations require degrees 'C' (Celsius),
                        however, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will be
                        converted to 'C' for use in the calculations. 
            pcpn_units: units for precipitation data.
                        Calculations require 'in' (inches of rainfall).
                        Data in other units may be passed and will be 
                        converted to 'in' for use in the calculations. 

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : snme day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy array with threat index for each node on each day
        """
        mint, avgrh, rh95, wet_count = \
        self.dailyReductions(temp, dewpt, rhum, pcpn, temp_units, pcpn_units)

        # convert avg daily rhum to an index (0,1)
        avgrh_factor = N.zeros(avgrh.shape, '<i2')
        avgrh_factor[N.where(avgrh >= 80)] = 1

        # convert rhum > 95 count to index (0,1,2)
        rh95_factor = N.zeros(rh95.shape, '<i2')
        rh95_factor[N.where(rh95 > 4)] = 1
        rh95_factor[N.where(rh95 >= 8)] = 2

        # convert leaf wetness counts to an index (0,1)
        lwet_factor = N.zeros(wet_count.shape, '<i2')
        lwet_factor[N.where(wet_count >= 10)] = 1
        
        # convert min temperature to an index (-4, -2, 1)
        mint_factor = N.empty(mint.shape, '<i2')
        mint_factor.fill(-2) # covers effect of low min temps in season
        # mint_factor = N.zeros(mint.shape, '<i2')
        # always count temps above 16 degrees C whether in season or not
        mint_factor[N.where(mint >= 16)] = 1

        # adjust mint factor using season time span restrictions
        # first/last data day are used filter low min temps out of season
        # do this by filtering temps out of mint by setting them to -4
        # but always count min temps above 16 degrees C (factor == 1) 
        first_date = first_hour.date()
        last_date = first_date + datetime.timedelta(days=mint.shape[0]-1)
        if first_date < self.season_start:
            if last_date < self.season_start:
                mint_factor[N.where(mint_factor != 1)] = -4
            else:
                the_date = first_date
                index = 0
                while the_date < self.season_start:
                    index += 1
                    the_date += ONE_DAY
                # index is for season start
                mint_factor[N.where(mint_factor[:index,:,:] != 1)] = -4

        elif last_date > self.season_end:
            if first_date > self.season_start:
                mint_factor[N.where(mint_factor != 1)] = -4
            else:
                index = 0
                the_date = last_date
                while the_date < self.season_start:
                    the_date += ONE_DAY
                    index += 1
                # index is for  season end
                mint_factor[N.where(mint_factor[index:,:,:] != 1)] = -4

        # threat index is sum of avgrh, rh92, lwet and mint factors
        index = avgrh_factor + rh95_factor + lwet_factor + mint_factor

        # average threat index over consecutive days
        span = self.period.num_days # should be 3 or 7 days
        # get average threat over last 'span' days
        return funcs.calcTimespanAvg(index, 1, span, 0, 0)

