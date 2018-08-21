
import datetime
import numpy as N

from atmosci.units import convertUnits

from turf import common as funcs
from turf.threats.disease import BasicDisease


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Anthracnose(BasicDisease):
    """ Functions that model potential risk for outbreak of
    Anthracnose disease in turf grass.
    """
    def __init__(self, period, debug=False):
        BasicDisease.__init__(self, THREATS.anthrac, period, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, temp, dewpt, pcpn, temp_units, pcpn_units):
        """
        Anhtracnose utilizes 3-day averages and counts in order to
        calculate threat index. Therefore, hourly data arrays must
        begin 72 hours before the expected first day in results.

        NOTE: one day is 24 hours ending at 7AM.

        Arguments:
            temp: hourly temperatures
            precip: hourly precipitation. Default is None
            dewpt: hourly dewpoint temperatures. Default is None
            temp_units: units for temperature data. Default is 'C'.
                        Calculations require degrees 'C' (Celsius).
                        However, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will
                        be converted for use in the calculations. 
            precip_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                       However, input data in kilograms per square
                        meter ('kg m**-2' or 'kg^m**-2') may be passed
                        and will be converted to 'in' for use in the
                        calculations. 

        Note: Must pass valid array for precip OR dewpt (not both).
              Either may be used estimate the leaf wetness variable
              that is required to calulate Anthracnose threat index.

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : same day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy array containing daily risk level at each node.
        """
        index = self.threatIndex(temp, dewpt, pcpn, temp_units, precip_units)
        return self.riskLevel(index)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatIndex(self, temp, dewpt, pcpn, temp_units, pcpn_units):
        """
        Anhtracnose utilizes 3-day averages and counts in order to
        calculate threat index. Therefore, hourly data arrays must
        begin 72 hours before the expected first day in results.

        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
            temp: hourly temperatures
            precip: hourly precipitation. Default is None
            dewpt: hourly dewpoint temperatures. Default is None
            temp_units: units for temperature data. Default is 'C'.
                        Calculations require degrees 'C' (Celsius).
                        However, input data in degrees 'K' (Kelvin)
                        or 'F' (Fahrenheit) may be passed and will
                        be converted for use in the calculations. 
            precip_units: units for precipitation data. Default is 'in'.
                        Calculations require 'in' (inches of rainfall).
                       However, input data in kilograms per square
                        meter ('kg m**-2' or 'kg^m**-2') may be passed
                        and will be converted to 'in' for use in the
                        calculations. 

        Note: Must pass valid array for precip OR dewpt (not both).
              Either may be used estimate the leaf wetness variable
              that is required to calulate Anthracnose threat index.

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : same day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy array contining daily threat index at each node.
        """
        offset = self.config.offset # index of first iteration
        # number of hours to evaluate per iteration
        span = self.config.timespan
        # number of hours to increment b/w interations 
        step = self.config.timestep

        if self.debug:
            print '\nAnthracnose.threatIndex :'
            print '         offset :', offset
            print '           span :', span
            print '           step :', step
            print '    temperature :', temp.shape, temp_units
            print '      dew point :', dewpt.shape
            print '         precip :', pcpn.shape, pcpn_units

        if temp.shape[0] < span:
            errmsg = 'Input arrays must contain at least %d hours of data.'
            raise ValueError, errmsg % span

        tmp_units = self.config.units.tmp
        if temp_units == tmp_units: tmp = temp
        else: tmp = convertUnits(temp, temp_units, tmp_units)

        # each day of interest needs average temp for previous 3 days
        avgt = funcs.calcTimespanAvg(tmp, step, span, offset, N.nan)
        if self.debug: print '     avgt shape :', avgt.shape
        avgt_nans = N.where(N.isnan(avgt))

        # each day of interest needs average leaf wetness for previous 3 days
        leaf_wet = self.leafWetness(temp, dewpt, pcpn, tmp_units, pcpn_units)
        wet_count = funcs.countTimespanGT(leaf_wet, 0, step, span, offset) / 3.
        if self.debug:
            print 'wet_count shape :', wet_count.shape
            print '  wet_count min :', N.min(wet_count)
            print '  wet_count max :', N.max(wet_count)

        index = 4.0233 - (wet_count * 0.2283) - (avgt * 0.5308) - \
                         (wet_count**2 * 0.0013) + (avgt**2 * 0.0197) + \
                         (avgt * wet_count * 0.0155 )
        # avoid issues with NimPy runtime warnings
        index[avgt_nans] = -99999. 
        if self.debug: print '    index shape :', index.shape

        index[N.where(avgt < 0)] = -1 # prevent positive index @ temp < 0C
        if self.debug: print '      index < 0 :', len(N.where(index < 0)[0])

        index[avgt_nans] = N.nan
        too_low = N.where(wet_count < 8)
        index[too_low] -= 3
        if self.debug:
            print '      index < 8 :', len(too_low[0])
            print '      index min :', N.nanmin(index)
            print '      index max :', N.nanmax(index)

        span = self.period.num_days
        if self.debug: print 'period.num_days :', span
        if span == 1: return index
        else:
            # get average threat over last 'span' consecutive days
            return funcs.calcTimespanAvg(index, 1, span, 0)

