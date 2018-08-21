
import datetime
import numpy as N

from atmosci.units import convertUnits 

from turf import common as funcs
from turf.threats.disease import BasicDisease


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PythiumBlight(BasicDisease):
    """ Functions that model potential risk for outbreak of Pithium
    Blight disease in turf grass.
    """

    def __init__(self, period, debug=False):
        BasicDisease.__init__(self, THREATS.pblight, period, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, temp, rhum, temp_units='F'):
        """
        Pithium Blight utilizes 2-day averages and counts in order to
        calculate threat index. Therefore, hourly data arrays must
        begin at least 48 hours before the first day in results.

        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
          temp: hourly temperatures
          rhum: hourly relative humidity
          temp_units: units for temperature array. Default is 'F'.
                      Calculations require degrees 'F' (Fahrenheit).
                      However, input data in degrees 'C' (Celsius)
                      or 'K' (Kelvin) may be passed and will be
                      converted to'F' for use in the calculations. 

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : snme day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: temp and rhum arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy array containing daily risk level at each node.
        """
        return self.riskLevel(self.threatIndex(temp, rhum, temp_units))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatIndex(self, temp, rhum, temp_units='F'):
        """
        Pithium Blight utilizes 2-day averages and counts in order to
        calculate threat index. Therefore, hourly data arrays must
        begin at least 48 hours before the first day in results.

        NOTE: One day is 24 hours ending at 7AM.

        Arguments:
          temp: hourly temperatures
          rhum: hourly relative humidity
          temp_units: units for temperature array. Default is 'F'.
                      Calculations require degrees 'F' (Fahrenheit).
                      However, input data in degrees 'C' (Celsius)
                      or 'K' (Kelvin) may be passed and will be
                      converted to'F' for use in calculations. 

        Supported types for temp and rhum data:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : snme day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: temp and rhum arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have mssing value == N.nan

        Returns: NumPy array containing daily threat index at each node.
        """
        span = self.config.timespan # number of hours to evaluate per iteration
        step = self.config.timestep # number of hours to increment b/w interations

        if temp_units == 'F': tmp = temp
        else: tmp = convertUnits(temp, temp_units, 'F')

        maxt = funcs.calcTimespanMax(tmp, step, span)
        mint = funcs.calcTimespanMin(tmp, step, span)
        rh89 = funcs.countTimespanGT(rhum, 89, step, span)

        index = (maxt - 86) + (mint - 68) + (0.5 * (rh89 - 6))

        # average threat index over consecutive days
        span = self.period.num_days # should be 3 or 7 days
        # get average threat over last 'span' days
        return funcs.calcTimespanAvg(index, 1, span, 0)

