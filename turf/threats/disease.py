
import datetime
import numpy as N

from atmosci.units import convertUnits

from turf import common as funcs
from turf.threats import wetness


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BasicDisease(object):
    """ Functions that model potential risk for outbreak of Brown
    Patch disease in turf grass.
    """

    def __init__(self, threat_config, period, debug=False):
        self.debug = debug
        self.config = threat_config

        # criteria for threat avaraging over the specified periods
        if isinstance(period, basestring):
            self.period = self.config.periods[period]
        else: self.period = period
        self.risk_thresholds = self.period.risk_thresholds

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataStartTimeForTarget(self, target_date):
        """
        This routine determines the time that input data must start in 
        order to return daily results for the target_date.
        
        It is important to understand that data for any date typically
        begins in the morning (usually 8AM) of the target_date but ends
        on the morning of the next day (usually 7AM)

        Arguments:
            target_date: datetime.date object for the first date
                         desired in threat and risk results.

        Returns:
            datetime.datetime object with the time of the first hour that
            data must contain in order to return results beginning on the
            target_date.
        """
        end_hour = datetime.time(hour=self.config.day_begins-1)
        end_date = target_date + datetime.timedelta(days=1)
        end_time = datetime.datetime.combine(end_date, end_hour) 
        return end_time - datetime.timedelta(hours=self.period.padding)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def leafWetHours(self, temp, dewpt, pcpn, temp_units, pcpn_units):
        """
        estimate hourly probablilty ofleaf wetness
        
        Arguments:
            temp: hourly temperatures.
            dewpt: hourly dewpoint temperatures.
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
            3D NumPy array : multiple days at points on a 2D grid.
                             shape = (days, y, x)
            2D NumPy array : multiple days at multiple points
                             shape = (days, points)
            1D NumPy array : multiple days at single point
                             shape = (days,)

        NOTE: input arrays must :
              1) have the same dimensions
              2) be dtype=float
              3) have missing value == N.nan

        Returns:
            NumPy array the number of hours of leaf wetness per day
            at each node in the input arrays.
        """
        # number of hours to skip before starting iteration
        offset = self.config.offset
        # number of hours to evaluate per iteration
        span = self.config.timespan
        # number of hours to increment b/w interations 
        step = self.config.timestep

        # get hourly leaf wetness
        leaf_wet = self.leafWetness(tmp, dpt, precip)
        if self.debug:
            stats = (N.nanmin(leaf_wet), N.nanmean(leaf_wet),
                     N.nanmedian(leaf_wet), N.nanmax(leaf_wet))
            print '         leaf wet stats :', stats

        # count number of hours with leaf wetness
        wet_count = funcs.countTimespanGT(leaf_wet, 0, step, span, offset)
        if self.debug:
            print '              wet count :', wet_count.shape

        return wet_count

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def leafWetness(self, temp, dewpt, pcpn, temp_units, pcpn_units):

        # make sure that temperature and dew point units are correct
        tmp_units = self.config.units.tmp
        if temp_units == tmp_units:
            tmp = temp
            dpt = dewpt
        else:
            tmp = convertUnits(temp, temp_units, tmp_units)
            dpt = convertUnits(dewpt, temp_units, tmp_units)

        # dew point depression is one proxy for leaf wetness
        tdd = temp - dewpt

        # make sure that precip units are correct
        precip_units = self.config.units.pcpn
        if pcpn_units == precip_units: precip = pcpn
        else: precip = convertUnits(pcpn, pcpn_units, precip_units)
        # adjustment for minimum effective precipitation
        precip[N.where(precip < self.config.min_precip)] = 0

        # precipitation is the other proxy
        # need a wetness array filled with zeros for the entire time span
        wetness = N.zeros(pcpn.shape, dtype='<i2')
        # array to track whether leaves were wet in a previous iteration
        last_wet = N.zeros(pcpn.shape[1:], dtype='<i2')

        # need to process one time period per iteration
        for i in range(tdd.shape[0]):
            # leaves are wet wherever precip is greater than zero
            pcpn_where = N.where(pcpn[i,:,:] > 0)
            wetness[i][pcpn_where] = 1

            # also include nodes with dew point depression less than 3 degrees
            tdd_where = N.where(tdd[i,:,:] < 3)
            wetness[i][tdd_where] = 1
        
            # add nodes whereever leaves were wet on the previous day
            wetness[i][N.where(last_wet == 1)] = 1

            # track where only where wetness criteria wre met on this day
            last_wet.fill(0) # reset last_wet array to zeros first
            # track where precip criteria were met on this day
            last_wet[pcpn_where] = 1
            # track where dewpoint criteria were met on this day
            last_wet[tdd_where] = 1

        return wetness

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def riskLevel(self, threat_index):
        """
        Estimates the risk level for each day at each location.

        Arguments:
          threat_index: daily threat index.

        Supported types for threat_index data:
            3D NumPy array : multiple days at points on a 2D grid.
                             shape = (days, y, x)
            2D NumPy array : multiple days at multiple points
                             shape = (days, points)
            1D NumPy array : multiple days at single point
                             shape = (days,)

        Returns: NumPy array with daily risk level at each node
        """
        risk = N.zeros(threat_index.shape, dtype='<i2')
        for index, threshold in enumerate(self.risk_thresholds):
            risk[N.where(threat_index > threshold)] = index + 1
        return risk

