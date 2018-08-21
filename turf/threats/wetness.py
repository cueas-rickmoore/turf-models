
import numpy as N

from atmosci.units import convertUnits

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def leafWetness(precip, temp, dewpt, pcpn_units='in', temp_units='F'):
    if pcpn_units == 'in': pcpn = precip
    else: pcpn = convertUnits(precip, pcpn_units, 'in')

    # use dewpoint depression as a prozy for leaf wetness
    if temp_units == 'F':
        tdd = temp - dewpt
    else: 
        tmp = convertUnits(temp, temp_units, 'F')
        dpt = convertUnits(dewpt, temp_units, 'F')
        tdd = tmp - dpt

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def leafWetnessFromTemps(temp, dewpt, temp_units='F'):
    # use dewpoint depression as a prozy for leaf wetness
    if temp_units == 'F':
        tdd = temp - dewpt
    else: 
        tmp = convertUnits(temp, temp_units, 'F')
        dpt = convertUnits(dewpt, temp_units, 'F')
        tdd = tmp - dpt

    # need a wetness array filled with zeros for the entire time span
    wetness = N.zeros(tdd.shape, dtype='<i2')
    # array for track whether leaves were wet in a previous iteration
    last_wet = N.zeros(tdd.shape[1:], dtype='<i2')

    # need to process one time period per iteration
    for i in range(tdd.shape[0]):
        # leaves are wet at nodes with dew point depression less than 3 degrees
        where = N.where(tdd[i,:,:] < 3)
        wetness[i][where] = 1

        # add nodes where leaves were wet on previous day
        wetness[i][N.where(last_wet == 1)] = 1

        # track only where dewpoint criteria were met on this day
        last_wet.fill(0) # reset last_wet array to zeros first
        last_wet[where] = 1

    return wetness

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def leafWetnessFromPrecip(precip, pcpn_units='in'):
    if pcpn_units == 'in': pcpn = precip
    else: pcpn = convertUnits(precip, pcpn_units, 'in')

    # need empty wetness array for entire time span
    wetness = N.zeros(pcpn.shape, dtype='<i2')
    # track whether leaves were wet in an iteration
    last_wet = N.zeros(pcpn.shape[1:], dtype='<i2')

    # need to process one time period per iteration
    for i in range(pcpn.shape[0]):
        # leaves are wet wherever precip greater than zero
        where = N.where(pcpn[i,:,:] > 0)
        wetness[i][where] = 1

        # add nodes whereever leaves were wet on the previous day
        wetness[i][N.where(last_wet == 1)] = 1

        # track only where precip criteria were met on this day
        last_wet.fill(0)  # reset last_wet array to zeros first
        last_wet[where] = 1

    return wetness

