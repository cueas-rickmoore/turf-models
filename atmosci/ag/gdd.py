
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def accumulateGDD(gdd, axis=0):
    """ Calculate accumulated GDD from a NumPy array of daily GDD values.

    Arguments
    --------------------------------------------------------------------
    gdd  : NumPy float array of daily GDD
    axis : array axis along whihc to calculate average. Not used for 1D
           arrays. Defaults to 0 for 2D and 3D arrays. 

    Returns
    --------------------------------------------------------------------
    NumPy array af the same dimensions as the input gdd array.
    """
    if gdd.ndim > 1: 
        return N.cumsum(gdd, axis=axis)
    else: return N.cumsum(gdd, axis=None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcAvgGDD(gdd, axis=0):
    """ Calculate the average for a NumPy array of GDD values.

    Arguments
    --------------------------------------------------------------------
    gdd  : NumPy float array
    axis : array axis along which to calculate average. Not used for 1D
           arrays. Defaults to 0 for 2D and 3D arrays. 

    Returns
    --------------------------------------------------------------------
    float value for 1D input
    OR
    NumPy array with 1 fewer dimensions than the input gdd array.
    """
    if not isinstance(gdd, N.ndarray):
        raise TypeError, 'gdd argument must be a NumPy array'
    if gdd.ndim > 1:
        return N.round(N.nanmean(gdd, axis=axis) + .01)
    else:
        return N.round(N.nanmean(gdd) + .01)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcAvgTemp(mint, maxt, threshold):
    """ Calculate the average temperature based on commonly accepted GDD
    threshold rules.

    Arguments
    --------------------------------------------------------------------
    mint      : minimum temperature
    maxt      : maximum temperature
    threshold : GDD threshold specification. Pass a single int for 
                caculatations using only a low temperature threshold.
                Pass a tuple/list for calculations using both upper and
                lower GDD thresholds.

    NOTE: mint and maxt arguments may be either a single float or int or
          a NumPy array of floats. 

    Returns
    --------------------------------------------------------------------
    calculated average temperature of same type and size as input temps
    """
    if isinstance(maxt, N.ndarray):
        nans = N.where(N.isnan(mint))
        _mint = mint.copy()
        _mint[nans] = 0
        _maxt = maxt.copy()
        _maxt[nans] = 0

    if isinstance(threshold, (list,tuple)):
        if threshold[0] > threshold[1]:
            hi_thold, lo_thold = threshold
        else: lo_thold, hi_thold = threshold
        if isinstance(maxt, N.ndarray):
            nans = N.where(N.isnan(mint))
            _mint[N.where(_mint < lo_thold)] = lo_thold 
            _mint[N.where(_mint > hi_thold)] = hi_thold
            _mint[nans] = N.nan

            _maxt[N.where(_maxt < lo_thold)] = lo_thold
            _maxt[N.where(_maxt > hi_thold)] = hi_thold
            _maxt[nans] = N.nan
        else:
            if mint < lo_thold: _mint = lo_thold 
            elif mint > hi_thold: _mint = hi_thold
            else: _mint = mint
            if maxt < lo_thold: _maxt = lo_thold 
            elif maxt > hi_thold: _maxt = hi_thold
            else: _maxt = maxt
    else:
        if isinstance(maxt, N.ndarray):
            _mint[nans] = N.nan
            _maxt[nans] = N.nan
        else:
            _mint = mint
            _maxt = maxt
    
    return N.round(((_maxt + _mint) * 0.5) + .01)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcGDD(temps, threshold):
    """ Calculate the GDD using average temperature based on commonly accepted
    GDD threshold rules.

    Arguments
    --------------------------------------------------------------------
    temps     : tuple (mint array, maxt array) or average temp arrays
    threshold : GDD threshold specification. Pass a single int for 
                caclutations using only a low temperature threshold.
                Pass a tuple/list for calculations using both upper and
                lower GDD thresholds.

    NOTE: avgt argument may be float, int or a NumPy array of floats.

    Returns
    --------------------------------------------------------------------
    calculated GDD
    """
    if isinstance(temps, (list,tuple)):
        avgt = calcAvgTemp(temps[0], temps[1], threshold)
    else: avgt = temps

    if isinstance(threshold, (list,tuple)):
        if threshold[0] > threshold[1]:
            lo_thold = threshold[1]
        else: lo_thold = threshold[0]
    else: lo_thold = threshold

    # numpy array
    if isinstance(avgt, N.ndarray):
        nans = N.where(N.isnan(avgt))
        gdd = avgt - lo_thold
        gdd[nans] = 0
        gdd[N.where(gdd < 0)] = 0
        gdd[nans] = N.nan
        return gdd

    # scalar value
    else:
        gdd = type(avgt)(avgt - lo_thold)
        if gdd > 0: return gdd
        return 0

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def roundGDD(gdd):
    return N.round(gdd + .01)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDFunctionsMixin:

    def accumulateGDD(self, gdd, axis=0):
        """ Calculate accumulated GDD from a NumPy array of daily GDD values.

        Arguments
        --------------------------------------------------------------------
        gdd  : NumPy float array of daily GDD
        axis : array axis along whihc to calculate average. Not used for 1D
               arrays. Defaults to 0 for 2D and 3D arrays. 

        Returns
        --------------------------------------------------------------------
        NumPy array af the same dimensions as the input gdd array.
            return accumulateGDD(gdd, axis)
        """
        return accumulateGDD(gdd, axis)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcAvgGDD(self, gdd, axis=None):
        """ Calculate average GDD from a NumPy array of GDD values.

        Arguments
        --------------------------------------------------------------------
        gdd  : NumPy float array
        axis : array axis along whihc to calculate average. Not used for 1D
               arrray. Defaults to 0 for 2D and 3D arrays. 

        Returns
        --------------------------------------------------------------------
        float value for 1D input
        OR
        NumPy array with 1 fewer dimensions than the input gdd array.
        """
        return calcAvgGDD(gdd, axis)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcAvgTemp(self, mint, maxt, threshold):
        """ Calculate the average temperature based on commonly accepted GDD
        threshold rules.

        Arguments
        --------------------------------------------------------------------
        mint      : minimum temperature
        maxt      : maximum temperature
        threshold : GDD threshold specification. Pass a single int for 
                    caculatations using only a low temperature threshold.
                    Pass a tuple/list for calculations using both upper and
                    lower GDD thresholds.

        NOTE: mint and maxt arguments may be either a single float or int or
              a NumPy array of floats. 

        Returns
        --------------------------------------------------------------------
        calculated average temperature of same type and size as input temps
        """
        return calcAvgTemp(mint, maxt, threshold)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcGDD(self, temps, threshold):
        """ Calculate the GDD using average temperature based on commonly accepted
        GDD threshold rules.

        Arguments
        --------------------------------------------------------------------
        temps     : tuple (mint array, maxt array) or average temp arrays
        threshold : GDD threshold specification. Pass a single int for 
                    caclutations using only a low temperature threshold.
                    Pass a tuple/list for calculations using both upper and
                    lower GDD thresholds.

        NOTE: temperature arguments may be float, int or a NumPy array
              of floats.

        Returns
        --------------------------------------------------------------------
        calculated GDD of corresponding type to temparatue inputs
        """
        return calcGDD(temps, threshold)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDCalculator(GDDFunctionsMixin, object):

    def __init__(self, low_threshold, high_threshold=None):
        if high_threshold is None:
            self.threshold = low_threshold
        else: self.threshold = (low_threshold, high_threshold)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt):
        return calcGDD((mint, maxt), self.threshold)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDAccumulator(GDDFunctionsMixin, object):

    def __init__(self, low_threshold, high_threshold=None,
                       previously_accumulated_gdd=None):
        self.daily_gdd = None
        if high_threshold is None:
            self.threshold = low_threshold
        else: self.threshold = (low_threshold, high_threshold)
        self.accumulated_gdd = previously_accumulated_gdd

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt, axis=0):
        daily_gdd = calcGDD((mint, maxt), self.threshold)
        if self.daily_gdd is None:
            self.daily_gdd = daily_gdd
        else: 
            self.daily_gdd = N.vstack((self.daily_gdd, daily_gdd))

        accumulated = self.accumulate(daily_gdd, axis)
        if self.accumulated_gdd is None:
            self.accumulated_gdd = accumulated
        else:
            self.accumulated_gdd = N.vstack((self.accumulated_gdd, accumulated))

        return daily_gdd, accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_gdd, axis=0):
        if self.accumulated_gdd is None:
            return accumulateGDD(daily_gdd, axis)
        else: 
            return accumulateGDD(daily_gdd, axis) + \
                   self._previouslyAccumulated(daily_gdd.shape)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self, grid_shape):
        if self.accumulated_gdd is None:
            return N.zeros(grid_shape[1:], dtype=float)
        else:
            if self.accumulated_gdd.ndim == 2:
                return self.accumulated_gdd
            else: return self.accumulated_gdd[-1,:,:]

