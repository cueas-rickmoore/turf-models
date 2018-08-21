
import datetime
import warnings
import numpy as N

from atmosci.units import convertUnits

from turf.common import countTimespanEQ


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from turf.threats.config import THREATS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HeatStress(object):
    """ Functions that model potential risk for heat stress in turf grass.
    """
    def __init__(self, debug=False):
        self.config = THREATS.hstress
        self.debug = debug

    @property # stress thresholds
    def thresholds(self): return self.config.stress_thresholds

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, temp, rhum, temp_units='F'):
        """
        Heat Stress utilizes 12 hour data summaries to calculate
        daily stress indices. A "day" is 12 hours ending at 7AM.

        NOTE: Hourly data arrays must contain full 24 hour sequences
        beginning 12 hours before the expected first day of results.

        Arguments:
            temp: hourly temperatures
            rhum: hourly relative humidity
            temp_units: units for temperature data. Default is 'F'.
                        Calculations require degrees 'F' (Fahrenheit)
                        However, input data in degrees 'C' (Celsius).
                        or 'K' (Kelvin) may be passed and will
                        be converted for use in the calculations. 

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
        return self.riskLevel(self.stressHours(temps, rhum, temp_units))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataStartTimeForTarget(self, target_date):
        """
        Heat Stress utilizes 12 hour data summaries to calculate
        daily stress indices. A "day" is 12 hours ending at 7AM.
        This routine determines the time that input data must start 
        in order to return daily results beginning on the day in
        the target hour.

        NOTE: Hourly data arrays must contain full 24 hour days
        beginning 12 hours before the expected first day in results.

        Arguments:
            target_date: datetime.date object for the first date

        Returns:
        datetime.datetime object with the time of the first hour that
        data must contain in order to return results beginning on the
        day in the target hour.
        """
        end_hour = datetime.time(hour=self.config.day_begins-1)
        end_date = target_date + datetime.timedelta(days=1)
        end_time = datetime.datetime.combine(end_date, end_hour) 
        return end_time - datetime.timedelta(hours=self.config.padding)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def stressHours(self, temp, rhum, temp_units='F'):
        """
        Heat Stress utilizes 12 hour data summaries to calculate
        daily stress hours. A "day" is 12 hours ending at 7AM.

        NOTE: Hourly data arrays must contain full 24 hour sequences
        beginning 12 hours before the expected first day in results.

        Arguments:
            temp: hourly temperatures for 24 hours
            rhum: hourly relative humidity 24 hours
            temp_units: units for temperature data. Default is 'F'.
                        Calculations require degrees 'F' (Fahrenheit)
                        However, input data in degrees 'C' (Celsius).
                        or 'K' (Kelvin) may be passed and will
                        be converted for use in the calculations. 

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : same day at multiple points
            1D NumPy array : multiple days at single point

        NOTE: all arguments must be the same type and have the same dimensions

        Returns: NumPy array containing daily stress hours at each node.
        """
        # number of hours to skip before starting iteration
        offset = self.config.offset
        # number of hours to evaluate per iteration
        span = self.config.timespan
        # number of hours to increment b/w interations 
        step = self.config.timestep
        
        if temp_units == 'F': tmp = temp
        else: tmp = convertUnits(temp, temp_units, 'F')

        # need sum of temp and rhum for 2nd part of index
        trh = tmp + rhum

        # need to know the number of hours where tmp >= 70 & trh > 150
        # so create a count array that is the same size as tmp & trh
        stress_hours = N.zeros(tmp.shape, dtype='<i2')

        # Need to create separate tmp stress and trh stress conditions
        # because NumPy cannot handle N.where(tmp >= 70 & trh > 150).
        # It often throws TypeError with message "truth value of an 
        # array with more than one element is ambiguous"
        thresholds = self.config.stress_thresholds

        # filter annoying NumPy/SciPy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',
                                "invalid value encountered in greater")
        warnings.filterwarnings('ignore',
                                "invalid value encountered in greater_equal")

        # set nodes where temp threshold is met
        stress_hours[N.where(tmp >= thresholds.temp)] = 1
        # now add nodes where trh threshold is met so that
        stress_hours[N.where(trh > thresholds.rhum)] += 1

        # turn annoying NumPy/SciPy warnings back on
        warnings.resetwarnings()

        # stress_hours == 2 when N.where(tmp >= 70 & trh > 150)
        return countTimespanEQ(stress_hours, 2, step, span, offset)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def riskLevel(self, stress_hours):
        """
        Calculates Heat Stress risk level in range 0 to 2 (no risk,
        moderate risk, high risk).
        
        NOTE: risk level will be set to -999 whereever threat_index
              is missing.

        Arguments:
          threat_index: daily Heat Stress threat index.
                        The missing data value must be N.nan

        Argument types:
            3D NumPy array : multiple days at multiple points
            2D NumPy array : same day at multiple points
            1D NumPy array : multiple days at single point

        Returns: NumPy array with risk level at each node
        """
        risk = N.zeros(stress_hours.shape, dtype='<i2')
        for level, threshold in enumerate(self.config.risk_thresholds):
            if threshold > 0:
                risk[N.where(stress_hours > threshold)] = level
        return risk

