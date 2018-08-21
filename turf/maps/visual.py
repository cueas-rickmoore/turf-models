
import os
import numpy as N

from nrcc_viz.maps import hiResMap, finishMap
from nrcc_viz.maps import addScatterToMap #, addMapText, addFigureText

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def drawScatterMap(data, lats, lons, **map_options):

    # extract options required for plotting markers 
    marker_colors = map_options['markercolors']
    levels = map_options['contourbounds'][1:]
    del map_options['contourbounds']

    # create a map figure
    options, _map_, map_fig, axes, xy_extremes, x, y, _grid_ = \
        hiResMap(data, lats, lons, **map_options)
    del x, y, _grid_

    # flatten the datasets so basemap scatter can handle them
    map_lats = lats.flatten()
    map_lons = lons.flatten()
    map_data = data.flatten()

    for level in levels:
        indexes = N.where(map_data == level)
        if len(indexes[0]) > 0:
            color = marker_colors[level]
            fig = addScatterToMap(map_options, _map_, map_fig, 
                                  map_data[indexes], map_lats[indexes],
                                  map_lons[indexes], markercolor=color)
    if options.get('finish',True):
        finishMap(map_fig, axes, map_fig, **options)
    
    return options, _map_, map_fig, axes, fig, xy_extremes

