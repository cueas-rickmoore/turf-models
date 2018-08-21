
import datetime

import numpy as N

from atmosci.units import convertUnits

from turf import common as funcs
from turf.threats.wetness import leafWetnessFromPrecip
from turf.threats.disease import BasicDisease


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DollarSpot(BasicDisease):
    """ Functions that model potential risk for outbreak of Anthracnose in
    turf grass.
    """
    def __init__(self, period, debug=False):
        BasicDisease.__init__(self, THREATS.dspot, period, debug)

        self.count_thresholds = self.config.count_thresholds
        self.offsets = self.config.offsets
        self.timespans = self.config.timespans
        self.timesteps = self.config.timesteps

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, temp, rhum, pcpn, tmp_units='C', pcpn_units='in'):
        """
        Dollar Spot utilizes 3-day and 2-day averages and counts in
        order to calculate threat index. Therefore, hourly data arrays
        must begin 72 hours before the expected first day in results.

        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
            temp: hourly temperatures
            rhum: hourly relative humidity
            pcpn: hourly precipitation
            tmp_units: units for temperature data. Default is 'C'.
                        Calculations require degrees 'C' (Celsius).
                        However, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will
                        be converted for use in the calculations. 
            pcpn_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                        However, input data in kilograms per square
                        meter ('kg m**-2' or 'kg^m**-2') may be passed
                        and will be converted to 'in' for use in the
                        calculations. 

        Data argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have missing value == N.nan

        Returns: NumPy array containing daily risk level at each node.
        """
        threat = \
            self.threatIndex(temp, rhum, pcpn, tmp_units, pcpn_units)
        return self.risk(threat)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def componentsToThreatIndex(self, rh_component, pcpn_component,
                                      leaf_wetness_component):
        """
        Dollar Spot utilizes 3-day averages. Therefore, hourly data arrays
        must begin 72 hours before the expected first day in results.

        NOTE: input arrays must be in  the same dimensions

        Arguments:
            rh_component: daily humidity component of threat index
                          calculated using rhumComponent function
            pcpn_component: daily precipition component of threat index
                            calculated using precipComponent function
            leaf_wetness_component: daily leaf wetness compnent
                            calculated using wetnessComponent function

        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        Returns: NumPy array containing threat index at each node.
        """
        if self.debug:
            print '\ncalculating average threat index ...'
            print '   rhum component shape :', rh_component.shape
            print ' precip component shape :', pcpn_component.shape
            print 'wetness component shape :', leaf_wetness_component.shape
        # threat index = sum of RH, wetness and consecutive precip factors
        threat_index = rh_component + pcpn_component + leaf_wetness_component

        # average threat index over consecutive days
        offset = self.offsets.threat # should be 0
        span = self.period.num_days # should be 3 or 7 days
        step = self.timesteps.threat # should be 1 day
        # get average threat over last 'span' days
        return funcs.calcTimespanAvg(threat_index, step, span, offset)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def precipComponent(self, consec_rain, consec_avgt, return_masks=False):
        """
        Calculate a the threat component contributed by the interaction
        of consecutive days of precipitation and corresponding
        temperature on those days.

        NOTE: input arrays must have the same dimensions

        Arguments:
            consec_rain: daily count of consecutive days with rain
            consec_avgt: temprature averaged over consecutive days
                         with rain (e.g., when 5 days of rain,
                         consec_avgt will be the average temp over
                         that 5 day time span).
 
        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        Returns :
            if return_masks == False:
                returns an int NumPy array containing precip component
                for each day at each node.
            else if return_masks == True:
                returns a tuple with three items
                [0] int NumPy array containing precip component for
                    each day at each node.
                [1] int 0/1 NumPy array where 1 indicates days where
                    consec_rain >= 2 and avg temp on those days > 20 
                [2] int 0/1 NumPy array where 1 indicates days where
                    consec_rain >= 3 and avg temp on those days > 15 
        """
        # Need to create separate rain and avgt factors because NumPy 
        # cannot handle N.where(consec_rain >= 2 & consec_avgt > 20)
        # and N.where(consec_rain >= 3 & consec_avgt > 15).
        # It often throws TypeError with message "ufunc 'bitwise_and' not 
        # supported for the input types" and/or "the inputs could not be
        # safely coerced to any supported types according to the casting
        # rule ''safe''"

        # initialize precip component arrays
        avgt_factor = N.zeros(consec_rain.shape, '<i2')
        rain_factor = N.zeros(consec_rain.shape, '<i2')
        precip_component = N.zeros(consec_rain.shape, dtype=float)
        precip_component[N.where(N.isnan(consec_avgt))] = N.nan

        # need N.where(consec_rain >= 2 and consec_avgt > 20)
        avgt_factor[N.where(consec_avgt > 20)] = 1
        rain_factor[N.where(consec_rain >= 2)] = 1
        # rain_avgt_2_20 is where here consec_rain >= 2 & consec_avgt > 20 
        rain_avgt_2_20 = rain_factor + avgt_factor
        where = N.where(rain_avgt_2_20 == 2)
        rain_avgt_2_20_count = len(where[0]) 
        precip_component[where] = 1

        avgt_factor.fill(0)
        rain_factor.fill(0)
        # need N.where(consec_rain >= 3 and consec_avgt > 15).
        avgt_factor[N.where(consec_avgt > 15)] = 1
        rain_factor[N.where(consec_rain >= 3)] = 1
        # rain_avgt_3_15 is where here consec_rain >= 3 & consec_avgt > 15 
        rain_avgt_3_15 = rain_factor + avgt_factor
        where = N.where(rain_avgt_3_15 == 2)
        precip_component[where] = 1
        if self.debug:
            print '\nin precipComponent ...'
            print '  where rain_avgt_2_20 == 2 :', rain_avgt_2_20_count
            print '  where rain_avgt_3_15 == 2 :', len(where[0])
            print '      precip component nans :', len(N.where(N.isnan(precip_component))[0])
            print '      precip component == 0 :', len(N.where(precip_component == 0)[0])
            print '      precip component == 1 :', len(N.where(precip_component == 1)[0])
            print '      precip component  > 1 :', len(N.where(precip_component > 1)[0])

        if return_masks:
            return precip_component, rain_avgt_2_20, rain_avgt_3_15
        return precip_component

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def precipFactors(self, pcpn, temp, pcpn_units='in', tmp_units='C',
                            return_count=False):
        """
        Calculate the individual threat factors contributed by the
        interaction of consecutive days of precipitation and the
        corresponding average temperature on those days.

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have missing value = numpy.nan

        Arguments:
            pcpn: hourly precipitation
            temp: houry temprature 
            pcpn_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                        However, input data in kilograms per square
                        meter ('kg m**-2' or 'kg^m**-2') may be passed
                        and will be converted to 'in' for use in the
                        calculations. 
            tmp_units: units for temperature data. Default is 'C'.
                        Calculations require degrees 'C' (Celsius).
                        However, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will
                        be converted for use in the calculations.
            return_count: boolean, whete to include daily counts
                           of hours with rain in results

        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        Returns : tuple containing the following items
            tuple[0] = int NumPy array containing number of consecutive
                       days of rain for each day at each node.
            tuple[1] float NumPy array containing the average temperature
                     over the consecutive days of rain for each day at
                     each node.
            tiple[2] units for average temperature data

            if return_count == Ture, tuple also includes:
               tuple[3] = int NumPy array containing the number of hours
                          of rain for each day at each node. This array
                          will contain 6 more days than the other arrays
        """
        if pcpn_units == 'in': precip = pcpn
        else: precip = convertUnits(pcpn, pcpn_units, 'in')
        # adjustment for minimum effective precipitation
        precip[N.where(precip < self.config.min_precip)] = 0

        if tmp_units == 'C': tmp = temp
        else: tmp = convertUnits(temp, tmp_units, 'C')
        if self.debug:
            print '\n  in precipFactors ...'
            print '           precip shape :', pcpn.shape
            print '             temp shape :', tmp.shape

        # offset, time span and time step for avg temp and rain counts
        offset = self.offsets.rain_count
        span = self.timespans.rain_count
        step = self.timesteps.rain_count
        threshold = self.count_thresholds.rain_count
        # calculate the daily average temps for the days needed
        avg_temp = funcs.calcTimespanAvg(tmp, step, span, offset)
        # rain_count = number of hours with rain on each day
        rain_count = \
            funcs.countTimespanGT(precip, threshold, step, span, offset)

        if self.debug:
            print '     average temp shape :', avg_temp.shape
            print '       rain count shape :', rain_count.shape

        # get a solver for consecutive days of rain and the average temp
        ndims = len(avg_temp.shape)
        if ndims == 3:
            solver = DollarSpot3D(self.period, self.debug)
        else:
            raise TypeError, '%dD arrays are not currently supported' % ndims

        # get counts of consecutive days of rain and the average temp
        # over those days
        consec_rain, consec_avgt = \
            solver.consecPcpnAvgt(rain_count, avg_temp, 'C')
        if self.debug:
            print '\n    solver results ...'
            print '      consec rain shape :', consec_rain.shape
            print '      consec avgt shape :', consec_avgt.shape

        results = [consec_rain, consec_avgt, 'C']
        if return_count: result.append(rain_count)
        return tuple(results)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def rhumComponent(self, max_rh, avg_temp, tmp_units='C'):
        """
        Calculate a the threat factor contributed by the interaction
        of relative humidity and temperature.

        Arguments:
            rhum: daily maximum relative humidity
            avg_temp: daily average temprature for each day in max_rh.
            tmp_units: units for average temperature data. Default is
                       'C'.  Calculations require degrees 'C' (Celsius).
                       However, input data in degrees 'K' (Kelvin)
                       or 'F' (Fahrenheit) may be passed and will
                       be converted for use in the calculations. 

        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        NOTE: input arrays must :
              1) be dtype=float
              2) have missing value == NaN

        Returns :
            int NumPy array containing rh/temp component
                    at each node.
                
            else: returns tuple = (rh_factor, avg_temp) 
                [0] int NumPy array containing rh/temp factor at each node.
                [1] float NumPy array average temperature array used to
                    calculate the rh factor (in degress C).
        """
        if self.debug:
            print '\n  in rhumComponent ...'
            print '           max_rh shape :', max_rh.shape
            print '             avgt shape :', avg_temp.shape

        if tmp_units == 'C': avgt = avg_temp
        else: avgt = convertUnits(avg_temp, tmp_units, 'C')

        # Need to create separate avg temp and max_rh components because
        # NumPy cannot handle N.where(max_rh > 90 & avg_temp > 25). It often
        # throws TypeError with message "ufunc 'bitwise_and' not supported
        # for the input types, and the inputs could not be safely coerced
        # to any supported types according to the casting rule ''safe''"
        #
        # daily average temp factor - 1 means condition was met
        avgt_factor = N.zeros(avgt.shape, '<i2')
        avgt_factor[N.where(avgt > 25)] = 1
        # daily max_rh factor - 1 means condition was met
        maxrh_factor = N.zeros(max_rh.shape, '<i2')
        maxrh_factor[N.where(max_rh > 90)] = 1

        # daily composite of max_rh and avg_temp factors
        # maxrh_avgt == 2 is where here max_rh > 90 & avg_temp > 25
        maxrh_avgt = avgt_factor + maxrh_factor
        if self.debug:
            print '     maxrh & avgt shape :', maxrh_avgt.shape

        # RH componet is number of days that maxrh_avgt has value of 2
        offset = self.offsets.maxrh_avgt_count # should be 0
        span = self.timespans.maxrh_avgt_count # should be 7 days
        step = self.timesteps.maxrh_avgt_count # should be 1
        # maxrh_avgt == 2 is where here max_rh > 90 & avg_temp > 25
        maxrh_avgt_count = funcs.countTimespanEQ(maxrh_avgt, 2, step, span,
                                                 offset, '<i2')
        if self.debug:
            print ' maxrh avgt count shape :', maxrh_avgt_count.shape
            num_nans = len(N.where(N.isnan(avgt))[0])
            print '    maxrh_avgt_count NaN :', num_nans
            num_nodes = len(N.where(maxrh_avgt_count == 0)[0]) - num_nans
            print '    maxrh_avgt_count = 0 :', num_nodes
            for n in range(1,N.max(maxrh_avgt_count)+1):
                num_nodes = len(N.where(maxrh_avgt_count == n)[0])
                print '    maxrh_avgt_count = %d : %d' % (n, num_nodes)

        # RH componet is 1 where maxrh_avgt_count >= threshold
        threshold = self.count_thresholds.rh_component
        rh_component = N.zeros(maxrh_avgt_count.shape, dtype=float)
        # account for NaN in the original data
        # assumes all days have NaN at the same nodes
        nans = N.where(N.isnan(avgt[0,:,:]))
        for day in range(rh_component.shape[0]):
            rh_component[day][nans] = N.nan

        rh_component[N.where(maxrh_avgt_count >= threshold)] = 1
        if self.debug:
            print '     rh_component shape :', maxrh_avgt_count.shape

        return rh_component

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def rhumFactors(self, rhum, temp, tmp_units='C'):
        """
        Calculate the threat factors contributed by the interaction
        of relative humidity and temperature.

        NOTE: input arrays must be dtype=float with missing value=NaN

        Arguments:
            rhum: hourly relative humidity
            temp: hourly temperature 
            tmp_units: units for temperature data. Default is 'C'.
                        Calculations require degrees 'C' (Celsius).
                        However, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will
                        be converted for use in the calculations. 

        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        Returns : tuple
            tuple[0] 
            tupke[1]
        """
        if self.debug: print '\n  in rhumFactors ...'

        # offset for humidity factors
        offset = self.offsets.rh_factors # should be 0
        span = self.timespans.rh_factors # should be 24 hours
        step = self.timesteps.rh_factors # should be 24 hours

        # calculate daily avg temp for use in max_rh factor
        if tmp_units == 'C': tmp = temp
        else: tmp = convertUnits(temp, tmp_units, 'C')
        avgt = funcs.calcTimespanAvg(tmp, step, span, offset)
        if self.debug:
            print '         avg temp shape :', avgt.shape

        max_rh = funcs.calcTimespanMax(rhum, step, span, offset)
        if self.debug:
            print '           max rh shape :', max_rh.shape

        return max_rh, avgt, 'C' # avgt units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatIndex(self, temp, rhum, precip, tmp_units='C', pcpn_units='in'):
        """
        Dollar Spot utilizes 3-day and 2-day averages and counts in
        order to calculate threat index. Therefore, hourly data arrays
        must begin 72 hours before the expected first day in results.

        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
            temp: hourly temperatures
            rhum: hourly relative humidity
            precip: hourly precipitation
            tmp_units: units for temperature data. Default is 'C'.
                        Calculations require degrees 'C' (Celsius).
                        However, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will
                        be converted for use in the calculations. 
            pcpn_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                        However, input data in kilograms per square
                        meter ('kg m**-2' or 'kg^m**-2') may be passed
                        and will be converted to 'in' for use in the
                        calculations. 

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : same day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have missing value == numpy.nan

        Returns: NumPy array containing threat index at each node.
        """
        if tmp_units == 'C': tmp = temp
        else: tmp = convertUnits(temp, tmp_units, 'C')
        if self.debug:
            print '\n\nDollarSpot.threatIndex ...'
            print '      hourly temp shape :', tmp.shape
            print '      hourly rhum shape :', rhum.shape
            print '    hourly precip shape :', precip.shape

        if pcpn_units == 'in': pcpn = precip 
        else: pcpn = convertUnits(pcpn, pcpn_units, 'in')

        # calulate RH component of threat index
        rhum_component = self.rhumComponent(*self.rhumFactors(rhum, tmp, 'C'))

        # calculate component due to interaction of precip and avg temp 
        precip_factors = self.precipFactors(pcpn, tmp, 'in', 'C')
        precip_component = self.precipComponent(*precip_factors[:-1])

        # calculate wet_count factor of threat index
        wetness_component = \
            self.wetnessComponent(*self.wetnessFactors(precip, tmp, 'in', 'C'))

        return self.componentsToThreatIndex(rhum_component, precip_component,
                                            wetness_component)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def wetnessComponent(self, wet_count, wet_avgt):
        """
        Calculate a the threat factor contributed by the interaction
        of leaf wetness and temperature.

        Arguments:
            wet_count: daily count of hours of leaf wetness
            wet_agt: daily average temprature 

        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point
        """
        if self.debug:
            print '\n  in wetnessComponent ...'
            print '        wet_count shape :', wet_count.shape
            print '         wet_avgt shape :', wet_avgt.shape

        # Need to create separate avg temp and wet count components because
        # NumPy cannot handle N.where(wet_count > 90 & avg_temp > 15). It
        # often throws TypeError with message "ufunc 'bitwise_and' not 
        # supported for the input types" and/or "the inputs could not be
        # safely coerced to any supported types according to the casting
        # rule ''safe''"
        avgt_factor = N.zeros(wet_avgt.shape, '<i2')
        avgt_factor[N.where(wet_avgt > 15)] = 1

        wet_factor = N.zeros(wet_count.shape, '<i2')
        wet_factor[N.where(wet_count > 8)] = 1

        # wet_avgt_factor == 2 is where here wet_count > 8 and wet_avgt > 15
        wet_avgt_factor = avgt_factor + wet_factor
        if self.debug:
            print '   wetness + avgt shape :', wet_avgt_factor.shape

        wetness_component = N.zeros(wet_count.shape, dtype=float)
        wetness_component[N.where(N.isnan(wet_avgt))] = N.nan
        wetness_component[N.where(wet_avgt_factor == 2)] = 1
        if self.debug:
            print 'wetness component shape :', wetness_component.shape

        return wetness_component

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def wetnessFactors(self, precip, temp, pcpn_units='in', tmp_units='C'):
        """
        Calculate a the threat factor contributed by the interaction
        of leaf wetness and temperature.

        NOTE: inputs must be NumPy float arrays with the same dimensions
              and missing value = nan

        Arguments:
            precip: hourly precipitation
            temp: hourly temprature for same hours as precip
            tmp_units: units for temperature data. Default is 'C'.
                       Calculations require degrees 'C' (Celsius).
                       However, input data in degrees 'K' (Kelvin)
                       or 'F' (Fahrenheit) may be passed and will
                       be converted for use in the calculations. 
            pcpn_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                        However, input data in kilograms per square
                        meter ('kg m**-2' or 'kg^m**-2') may be passed
                        and will be converted to 'in' for use in the
                        calculations. 

        Argument types:
            3D NumPy array : multiple hours for multiple grid nodes
            2D NumPy array : multiple hours at multple points
            1D NumPy array : multiple hours at single point

        Returns : tuple of arrays
            tuple[0] = int NumPy array 
                       daily count of hours with leaf wetness at each node.
            tuple[1] = float NumPy array
                       average daily temp for each day in leaf wetnes array
        """
        if self.debug: print '\n  in wetnessFactors ...'
        # make sure that input precip is in the correct units
        if pcpn_units == 'in': pcpn = precip
        else: pcpn = convertUnits(precip, pcpn_units, 'C')
        if self.debug: print '             pcpn shape :', pcpn.shape

        # make sure that input temps are in the correct units
        if tmp_units == 'C': tmp = temp
        else: tmp = convertUnits(temp, tmp_units, 'C')
        if self.debug: print '             temp shape :', tmp.shape

        # get mask-like array with 1 in each hour with wetness
        leaf_wetness = leafWetnessFromPrecip(pcpn, 'in')
        if self.debug: print '     leaf wetness shape :', leaf_wetness.shape

        # offset, span, step for wet_count
        offset = self.offsets.wet_count # should skip first 4 days (96 hours)
        span = self.timespans.wet_count # should 3 days (72 hours)
        step = self.timesteps.wet_count # 24 hours
        threshold = self.count_thresholds.wet_count
        # count number of hours of leaf wetness per day
        wet_count = funcs.countTimespanEQ(leaf_wetness, threshold, step,
                                          span, offset, '<i2')
        if self.debug: print '    wetness count shape :', wet_count.shape

        span = 24
        step = 24

        wet_avgt = funcs.calcTimespanAvg(tmp, step, span, offset)
        if self.debug: print '     wetness avgt shape :', wet_avgt.shape

        if wet_count.shape[0] < wet_avgt.shape[0]:
            diff = wet_avgt.shape[0] - wet_count.shape[0]
            wet_avgt = wet_avgt[diff:,:,:]
            if self.debug:
                print '\n wetness avgt adjust to match wetness count'
                print '     new wetness avgt shape :', wet_avgt.shape

        return wet_count, wet_avgt


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DollarSpot3D(BasicDisease):
    """ Functions that model potential risk for outbreak of Anthracnose in
    turf grass.
    """
    def __init__(self, period, debug=False):
        BasicDisease.__init__(self, THREATS.dspot, period, debug)
        self.count_thresholds = self.config.count_thresholds
        self.offsets = self.config.offsets
        self.timespans = self.config.timespans
        self.timesteps = self.config.timesteps

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def consecPcpnAvgt(self, rain_count, avg_temp, tmp_units='C'):
        """
        Utilizes daily rain counts to determine the number of
        consecutive days with precipitation. Input data must contain
        hourly precipitation for a minimum of 5 days before data 
        reduction can begin. For example, 120 hours of data will
        return number of consectuive days with precip for 1 day,
        144 hours will return results for 2 days, etc.

        Arguments:
            rain_count: daily count of hours with precipitation
            avg_temp: daily average temprature for same days as 
                      rain_count
            tmp_units: units for temperature data. Default is 'C'.
                       Calculations require degrees 'C' (Celsius).
                       However, input data in degrees 'K' (Kelvin)
                       or 'F' (Fahrenheit) may be passed and will
                       be converted for use in the calculations.

        Data argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : same day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have missing value == N.nan

        Returns: 
              1) NumPy array containing counts of consecutive days of
                 precipitation for each day at each node.
              2) NumPy array containing average temperatures on days
                 with precipitaton
        """
        # capture avg_tmp for each consecutive day of rain
        if tmp_units == 'C': avgt = avg_temp
        else: avgt = convertUnits(avg_temp, tmp_units, 'C')
        if self.debug:
            print '\n  in consecPcpnAvgt ...'
            print '             avgt shape :', avgt.shape

        # determine number of consecutive previous days with rain
        offset = self.offsets.consec_rain
        span = self.timespans.consec_rain
        step = self.timesteps.consec_rain
        threshold = self.count_thresholds.wet_count
        consec_rain = funcs.countTimespanGE(rain_count, threshold, step, 
                                            span, offset, '<i2')
        if self.debug:
            print '\n  in consecPcpnAvgt ...'
            print '      consec rain shape :', consec_rain.shape
            for day in range(consec_rain.shape[0]):
                print '    day :', day
                for n in range(threshold,span+1):
                    num_nodes = len(N.where(consec_rain[day,:,:] == n)[0])
                    print '      %d consec days rain : %d' % (n, num_nodes)

        # because consecutive rain is for the 5 previous days,
        # the result in consec_rain is 1 day too long
        consec_rain = consec_rain[1:,:,:]
        consec_avgt = N.zeros(consec_rain.shape, dtype=float)
        consec_avgt[N.where(N.isnan(consec_rain))] = N.nan
        avg_tmp_sum = N.zeros(consec_rain.shape[1:], dtype=float)

        for rain_day in range(offset, consec_rain.shape[0]):
            consec_days = 0
            avg_tmp_sum.fill(0)
            avg_tmp_sum[N.where(N.isnan(consec_rain[rain_day,:,:]))] = N.nan

            # loop thru max previous days with rain
            for day_num in range(span):
                day = rain_day - day_num
                if day < 0: break
                count = day_num + 1
                # look for nodes with rain
                where = N.where(consec_rain[day,:,:] >= count)
                if len(where[0]) > 0: # rain_found
                    consec_days += 1
                    avg_tmp_sum[where] += avgt[day][where]
                    # must have a least 2 consecutive days of rain
                    if consec_days > 1:
                        consec_avgt[rain_day][where] = \
                                    avg_tmp_sum[where] / consec_days

        return consec_rain, consec_avgt

