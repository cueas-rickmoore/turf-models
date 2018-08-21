
import numpy as N


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def setMissingToNan(data, missing):
    if data.dtype.kind == 'f' and missing is not None and not N.isnan(missing):
        data[N.where(data == missing)] = N.nan
    return data

def setNanToMissing(data, missing):
    if data.dtype.kind == 'f' and missing is not None and not N.isnan(missing):
        data[N.where(N.isnan(data))] = missing
    return data

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcTimespanAvg(data, timestep=24, timespan=24, start_indx=0,
                    missing=N.nan, dtype=float):
    """
    Calculate the average data value for each timespan in the data.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index to start
      missing: value representing missing data, default=N.nan
      dtype: NumPy data type to use for generated array
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
    
    Returns: NumPy array containing average value for each increment of
             timespan at each location

    NOTE: All calculations are done using N.nan as the missing value.
          However, returned arrays will have the same missing value as
          the input array (i.e. the value specified in the "mising" arg).
    """
    periods, data_avg = createTimePeriodArray(data.shape, dtype, timestep, 
                                              timespan, start_indx, N.nan)

    if data.ndim == 3:
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end,:,:]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_avg[n,:,:] = N.nanmean(period_data, axis=0)
            else: # return 2D result for a single time period
                data_avg = N.nanmean(period_data, axis=0)

    elif data.ndim == 2:
        for n, (start, end) in enumerate(periods):
            period_data = data[:,start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_avg[:,n] = N.nanmean(period_data, axis=1)
            else: # return 1D result for a single time period
                data_avg = N.nanmean(period_data, axis=1)

    else: # data.ndim == 1
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_avg[n] = N.nanmean(period_data)
            else: # return integer result for a single time period
                data_avg = N.nanmean(period_data)

    return setNanToMissing(data_avg, missing)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcTimespanMax(data, timestep=24, timespan=24, start_indx=0,
                    missing=N.nan):
    """
    Calculate the maximum data value for each timespan in the data.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index to start averaging
      missing: value representing missing data, default=N.nan
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
    
    Returns: NumPy array containing maximum value for each increment of
             timespan at each location

    NOTE: All calculations are done using N.nan as the missing value.
          However, returned arrays will have the same missing value as
          the input array (i.e. the value specified in the "mising" arg).
    """
    periods, data_max = createTimePeriodArray(data.shape, data.dtype,
                                  timestep, timespan, start_indx, N.nan)

    if data.ndim == 3:
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end,:,:]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_max[n,:,:] = N.nanmax(period_data, axis=0)
            else: # return 2D result for a single time period
                data_max = N.nanmax(period_data, axis=0)

    elif data.ndim == 2:
        for n, (start, end) in enumerate(periods):
            period_data = data[:,start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_max[:,n] = N.nanmax(period_data, axis=1)
            else: # return 1D result for a single time period
                data_max = N.nanmax(period_data, axis=1)
    
    else: # data.ndim == 1
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_max[n] = N.nanmax(period_data)
            else: # return 1D result for a single time period
                data_max = N.nanmax(period_data)

    return setNanToMissing(data_max, missing)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcTimespanMin(data, timestep=24, timespan=24, start_indx=0,
                    missing=N.nan):
    """
    Calculate the minimum data value for each timespan in the data.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index to start
      missing: value representing missing data, default=N.nan
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
    
    Returns: NumPy array containing minimum value for each increment of
             timespan at each location

    NOTE: All calculations are done using N.nan as the missing value.
          However, returned arrays will have the same missing value as
          the input array (i.e. the value specified in the "mising" arg).
    """
    periods, data_min = createTimePeriodArray(data.shape, data.dtype,
                                  timestep, timespan, start_indx, N.nan)

    if data.ndim == 3:
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end,:,:]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_min[n,:,:] = N.nanmin(period_data, axis=0)
            else: # return 2D result for a single time period
                data_min = N.nanmin(period_data, axis=0)

    elif data.ndim == 2:
        for n, (start, end) in enumerate(periods):
            period_data = data[:,start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_min[:,n] = N.nanmin(period_data, axis=1)
            else: # return 1D result for a single time period
                data_min = N.nanmin(period_data, axis=1)
    
    else: # data.ndim == 1
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_min[n] = N.nanmin(period_data)
            else: # return 1D result for a single time period
                data_min = N.nanmin(period_data)

    return setNanToMissing(data_min, missing)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcTimespanSum(data, timestep=24, timespan=24, start_indx=0,
                    missing=N.nan):
    """
    Calculate the sum of data values for each timespan in the data.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index to start
      missing: value representing missing data, default=N.nan
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
 
    Returns: NumPy array containing sum of data values for each increment
             of timespan at each location

    NOTE: All calculations are done using N.nan as the missing value.
          However, returned arrays will have the same missing value as
          the input array (i.e. the value specified in the "mising" arg).
    """
    periods, data_sum = createTimePeriodArray(data.shape, data.dtype,
                                  timestep, timespan, start_indx, N.nan)

    if data.ndim == 3:
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end,:,:]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_sum[n,:,:] = N.nansum(period_data, axis=0)
            else: # return 2D result for a single time period
                data_sum = N.nansum(period_data, axis=0)

    elif data.ndim == 2:
        for n, (start, end) in enumerate(periods):
            period_data = data[:,start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_sum[:,n] = N.nansum(period_data, axis=1)
            else: # return 1D result for a single time period
                data_sum = N.nansum(period_data, axis=1)
    
    else: # data.ndim == 1
        for n, (start, end) in enumerate(periods):
            period_data = data[start:end]
            period_data = setMissingToNan(period_data, missing)
            if periods > 1:
                data_sum[n] = N.nansum(data[start:end])
            else: # return integer result for a single time period
                return N.nansum(data[start:end])

    return setNanToMissing(data_sum, missing)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def countTimespanEQ(data, threshold, timestep=24, timespan=24, start_indx=0,
                    dtype='<i2'):
    """
    Count the number of timespans when values in data are equal to a
    threshold during the specified timespan.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      threshold : data value to use as delineator
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index where counting starts
      missing: value representing missing data, default=N.nan
      dtype: NumPy datatype for output array, default='<i2'
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
    
    Returns: NumPy array containing count for each increment of timespan
             at each location

    NOTE: All counts are done using N.nan as the missing data value.
    """
    periods, count = createTimePeriodArray(data.shape, dtype, timestep,
                                           timespan, start_indx, 0)

    if data.ndim == 3:
        shape = (timespan,) + data.shape[1:]
        data_counter = N.zeros(shape, dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end,:,:] == threshold)] = 1
            if periods > 1:
                count[n,:,:] = N.sum(data_counter, axis=0)
            else: # return 2D result for a single time period
                return N.sum(data_counter, axis=0)
            data_counter.fill(0)

    elif data.ndim == 2:
        shape = (timespan, data.shape[1])
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[:,start:end] == threshold)] = 1
            if periods > 1:
                count[:,n] = N.sum(data_counter, axis=1)
            else: # return 1D result for a single time period
                return N.sum(data_counter, axis=1)
            data_counter.fill(0)
    
    else: # data.ndim == 1
        data_counter = N.zeros(timespan,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end] == threshold)] = 1
            if periods > 1:
                count[n] = N.sum(data_counter)
            else: # return integer result for a single time period
                return N.sum(data_counter)
            data_counter.fill(0)

    return count

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def countTimespanGE(data, threshold, timestep=24, timespan=24, start_indx=0,
                    dtype='<i2'):
    """
    Count the number of timespans when values in data are greater than or
    equal to a threshold during the specified timespan. 

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      threshold : data value to use as delineator
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index where counting starts
      missing: value representing missing data, default=N.nan
      dtype: NumPy datatype for output array, default='<i2'
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
    
    Returns: NumPy array containing count for each increment of timespan
             at each location

    NOTE: All counts are done using N.nan as the missing data value.
    """
    periods, count = createTimePeriodArray(data.shape, dtype, timestep,
                                           timespan, start_indx, 0)

    if data.ndim == 3:
        shape = (timespan,) + data.shape[1:]
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end,:,:] >= threshold)] = 1
            if periods > 1:
                count[n,:,:] = N.sum(data_counter, axis=0)
            else: # return 2D result for a single time period
                return N.sum(data_counter, axis=0)
            data_counter.fill(0)

    elif data.ndim == 2:
        shape = (timespan, data.shape[1])
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[:,start:end] >= threshold)] = 1
            if periods > 1:
                count[:,n] = N.sum(data_counter, axis=1)
            else: # return 1D result for a single time period
                return N.sum(data_counter, axis=1)
            data_counter.fill(0)
    
    else: # data.ndim == 1
        data_counter = N.zeros(timespan,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end] >= threshold)] = 1
            if periods > 1:
                count[n] = N.sum(data_counter)
            else: # return integer result for a single time period
                return N.sum(data_counter)
            data_counter.fill(0)

    return count

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def countTimespanGT(data, threshold, timestep=24, timespan=24, start_indx=0,
                    dtype='<i2'):
    """
    Count the number of timespans when values in data are greater than a
    threshold during the specified timespan.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      threshold : data value to use as delineator
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index where counting starts
      missing: value representing missing data, default=N.nan
      dtype: NumPy datatype for output array, default='<i2'
     
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
   
    Returns: NumPy array containing count for each increment of timespan
             at each location

    NOTE: All counts are done using N.nan as the missing data value.
    """
    periods, count = createTimePeriodArray(data.shape, dtype, timestep,
                                           timespan, start_indx, 0)

    if data.ndim == 3:
        shape = (timespan,) + data.shape[1:]
        data_counter = N.zeros(shape, dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end,:,:] > threshold)] = 1
            if periods > 1:
                count[n,:,:] = N.sum(data_counter, axis=0)
            else: # return 2D result for a single time period
                return N.sum(data_counter, axis=0)
            data_counter.fill(0)

    elif data.ndim == 2:
        shape = (timespan, data.shape[1])
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[:,start:end] > threshold)] = 1
            if periods > 1:
                count[:,n] = N.sum(data_counter, axis=1)
            else: # return 1D result for a single time period
               return N.sum(data_counter, axis=1)
            data_counter.fill(0)
    
    else: # data.ndim == 1
        data_counter = N.zeros(timespan,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end] > threshold)] = 1
            if periods > 1:
                count[n] = N.sum(data_counter)
            else: # return integer result for a single time period
                return N.sum(data_counter)
            data_counter.fill(0)

    return count

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def countTimespanLE(data, threshold, timestep=24, timespan=24, start_indx=0,
                    dtype='<i2'):
    """
    Count the number of timespans when values in data are less than or
    equal to a threshold during the specified timespan. 

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      threshold : data value to use as delineator
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index where counting starts
      missing: value representing missing data, default=N.nan
      dtype: NumPy datatype for output array, default='<i2'
    
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array
    
    Returns: NumPy array containing count for each increment of timespan
             at each location

    NOTE: All counts are done using N.nan as the missing data value.
    """
    periods, count = createTimePeriodArray(data.shape, dtype, timestep,
                                           timespan, start_indx, 0)

    if data.ndim == 3:
        shape = (timespan,) + data.shape[1:]
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end,:,:] <= threshold)] = 1
            if periods > 1:
                count[n,:,:] = N.sum(data_counter, axis=0)
            else: # return 2D result for a single time period
                return N.sum(data_counter, axis=0)
            data_counter.fill(0)

    elif data.ndim == 2:
        shape = (timespan, data.shape[1])
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[:,start:end] <= threshold)] = 1
            if periods > 1:
                count[:,n] = N.sum(data_counter, axis=1)
            else: # return 1D result for a single time period
                return N.sum(data_counter, axis=1)
            data_counter.fill(0)
    
    else: # data.ndim == 1
        data_counter = N.zeros(timespan,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end] <= threshold)] = 1
            if periods > 1:
                count[n] = N.sum(data_counter)
            else: # return integer result for a single time period
                return N.sum(data_counter)
            data_counter.fill(0)

    return count

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def countTimespanLT(data, threshold, timestep=24, timespan=24, start_indx=0,
                    dtype='<i2'):
    """
    Count the number of timespans when values in data are less than a
    threshold during the specified timespan.

    Will loop through as many time spans as are present in the data.
    TIMESPANS DO NOT OVERLAP

    Arguments:
      data: hourly data of any type
            valid argument types:
                3D NumPy array : multiple times at multiple points
                                 [time, y, x] or [time, x, y]
                2D NumPy array : multiple times at multiple locationss
                                 [locations, times]
                1D NumPy array : multiple times at single point
      threshold : data value to use as delineator
      timestep: length of time interval between calculations 
      timespan: number of times to treat as a single time period
      start_indx: time index where counting starts
      missing: value representing missing data, default=N.nan
      dtype: NumPy datatype for output array, default='<i2'
    
    NOTE: if start_indx is not 0, start_indx times will be skipped
           at the beginning of the input array

    Returns: NumPy array containing count for each increment of timespan
             at each location

    NOTE: All counts are done using N.nan as the missing data value.
    """
    periods, count = createTimePeriodArray(data.shape, dtype, timestep,
                                           timespan, start_indx, 0)

    if data.ndim == 3:
        shape = (timespan,) + data.shape[1:]
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end,:,:] < threshold)] = 1
            if periods > 1:
                count[n,:,:] = N.sum(data_counter, axis=0)
            else: # return 2D result for a single time period
                return N.sum(data_counter, axis=0)
            data_counter.fill(0)

    elif data.ndim == 2:
        shape = (timespan, data.shape[1])
        data_counter = N.zeros(shape,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[:,start:end] < threshold)] = 1
            if periods > 1:
                count[:,n] = N.sum(data_counter, axis=1)
            else: # return 1D result for a single time period
               return N.sum(data_counter, axis=1)
            data_counter.fill(0)
    
    else: # data.ndim == 1
        data_counter = N.zeros(timespan,dtype=dtype)
        for n, (start, end) in enumerate(periods):
            data_counter[N.where(data[start:end] < threshold)] = 1
            if periods > 1:
                count[n] = N.sum(data_counter)
            else: # return integer result for a single time period
                return N.sum(data_counter)
            data_counter.fill(0)

    return count

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def createTimePeriodArray(data_shape, data_type, timestep, timespan,
                          start_indx, fill_value=None):
    """
    Create an array for the given shape, type and timespan. The first
    dimension of the created array will be the number of time periods
    of length timespan that are available,

    Arguments:
      data_shape: shape of the data array. The first dimension must be time.
      data_type: the NumPy data type for the generated array
      timestep: number of times to treat as a single time period
      start_indx: time index to use as start of first time period
      fill_value: the value to use to fill the generated array.
                  The default is None, which returns an empty array. 
    
    NOTE: if start_indx is not 0, average will be calculated for 
          a single timespan starting at that index into the array

    NOTE: Time must be first axis data_shape

    Returns: Numner of time periods and NumPy array containing zeros
             for each increment of timespan at each location
    """
    ndims = len(data_shape)
    if ndims == 3:
        num_times = data_shape[0]
    elif ndims == 2:
        num_times = data_shape[1]
    elif ndims == 1:
        num_times = data_shape[0]
    else:
        raise ValueError, '%d dimension arrays are not supported,' % ndims

    periods = [ ]
    start = start_indx
    while start < num_times:
          end = start + timespan
          if end <= num_times: 
              periods.append((start, end))
          start += timestep

    num_periods = len(periods)
    if num_periods > 0:
        if ndims == 3:
            array_shape = (num_periods, data_shape[1], data_shape[2])
        elif ndims == 2:
            array_shape = (data_shape[0], num_periods)
        elif ndims == 1:
            array_shape = (num_periods,)
        periods_array = N.empty(array_shape, dtype=data_type)
        if fill_value is not None: periods_array.fill(fill_value) 

        return periods, periods_array

    else:
        errmsg = 'Data shape (%s) does not cover even one timespan (%d)'
        raise ValueError, errmsg % (str(data_shape), timespan)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def matchObjectType(data, object_to_match):
    """
    Return an equivalent object where the type of "data" matches the
    type of "object_to_match".

    Supported types are : NumPy array, Python list and Python tuple
    """
    if type(data) == type(object_to_match): return data
    if isinstance(data, N.ndarray):
        if isinstance(object_to_match, list): return data.tolist()
        elif isinstance(object_to_match, tuple): return map(tuple, data)
    elif isinstance(data, list):
        if isinstance(object_to_match, N.ndarray): N.asarray(data)
        if isinstance(object_to_match, tuple): return tuple(data)
    elif isinstance(data, tuple):
        if isinstance(object_to_match, N.ndarray): N.asarray(data)
        if isinstance(object_to_match, list): return list(data)

    errmsg = ''
    if not type(data) in (N.ndarray, list, tuple):
        errmsg = '"data" argument is an unsupported type (%s)' % type(data)
    if not type(object_to_match) in (N.ndarray, list, tuple):
        msg = '"object_to_match" argument is an unsupported type (%s)'
        if errmsg.len() == 0: errmsg = msg % type(object_to_match)
        else: errmsg = "%s and %s" % (errmsg, msg % type(object_to_match))
    raise TypeError, errmsg

