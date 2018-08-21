# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import numpy as N

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PROVENANCE = ConfigObject('provenance', None, 'generators', 'types')

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record generator for pcpn/pop
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def pcpnpopProvenanceGenerator(fcast_time, timestamp, pcpn, pop, source):
    return (fcast_time.strftime('%Y%m%d:%H'), N.nanmin(pcpn),
            N.nanmax(pcpn), N.nanmedian(pcpn,axis=None),
            N.nanmin(pop), N.nanmax(pop), N.nanmedian(pop,axis=None),
            timestamp, source )
PROVENANCE.generators.pcpnpop = pcpnpopProvenanceGenerator

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record type definition for pcpn/pop
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PROVENANCE.provenance.types.pcpnpop = {
    'empty':('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,'',''),
    'formats':['|S10','f4','f4','f4','f4','f4','f4','|S20','|S10'],
    'names':['time','pcpn min','pcpn max','pcpn median','pop min','pop max',
             'pop median','processed', 'source'],
    'period':'hour',
    'scope':'time',
    'type':'pcpnpop'
}

