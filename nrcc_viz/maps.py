
import os, sys
import warnings

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N
import PIL.Image

# ignore matplotlib loading fonts warning
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot
from matplotlib import cm
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle, PathPatch
from matplotlib.path import Path


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

RESOURCE_DIR = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'resources')

AREA_BBOX = { 'northeast':          [-82.70, 37.20, -66.90, 47.60],
              'westny':             [-80.00, 41.95, -74.75, 45.00],
              'eastny':             [-77.00, 40.45, -71.80, 43.45],
              'midatlantic':        [-79.75, 37.25, -73.00, 41.75],
              'newengland':         [-73.80, 40.95, -66.85, 47.60],
              'easternregion':      [-85.10, 31.90, -66.80, 47.60],
              'gulfmaine_masked':   [-77.00, 41.20, -59.00, 49.50],
              'gulfmaine_unmasked': [-77.00, 41.20, -59.00, 49.50],
              'greatlakes_unmasked':[-94.30, 40.00, -74.00, 51.50],
              'ct':                 [-73.75, 40.75, -71.25, 42.25], 
              'ma':                 [-73.75, 41.25, -69.75, 43.00],
              'md':                 [-80.00, 37.50, -74.75, 40.00],
              'me':                 [-72.00, 42.75, -66.85, 47.60],
              'ne':                 [-82.70, 37.20, -66.90, 47.60],
              'nh':                 [-72.75, 42.50, -70.25, 45.50],
              'nj':                 [-76.00, 38.75, -73.50, 41.75],
              'ny':                 [-79.90, 40.45, -71.80, 45.05],
              'pa':                 [-80.75, 39.50, -74.25, 42.25],
              'ri':                 [-72.50, 41.00, -70.50, 42.25],
              'vt':                 [-74.00, 42.50, -71.20, 45.25],
              'wv':                 [-83.00, 37.00, -77.50, 40.80],
              'wv_state':           [-83.00, 37.00, -77.50, 40.80],
            }

MAP_OPTIONS = { 'area': 'northeast',       # northeast, westny, eastny, ny, etc.
                'bbox': [-82.70, 37.20, -66.90, 47.60],  # plot coordinate bounding box
                'maptype': 'contourf',     # contourf, interpf or dotmap
                'size_tup': (6.8, 6.55),   # new standard size is (6.8, 6.55), thumbnail is (2.3, 2.3), original standard is (4.7, 4.55), large is (12,8.3)
                'dpi': 100,
                'titlefontsize': 12,       # standard is 12, original is 10, large is 15, (none for thumbnail)
                'titlexoffset': 0.05,      # 0.05 for all but those specified below
                'titleyoffset': 0.10,      # 0.10 for all but those specified below
                'pltshow': False,          # boolean
                'datesfromfile': False,    # boonean
                'inputfile': None,                                                      # tab-delimited input file for dotmap or interpf
                'grid': 3,
                'numlevels': 8,            # number of contour levels
                'autolevels':None,
                'levelmult': None,         # contour bounds are multiples of this value (None = pick based on data)
                #
                'cmap': 'RdYlGn',
                'colorbar': False,          # whether or not to plot a colorbar
                'cbarlabelsize': 8,                             # small is 8, large is 10
                'cbarsettings': [0.25, 0.11, 0.5, 0.02],        # small is [0.25, 0.11, 0.5, 0.02], large is [0.25, 0.06, 0.5, 0.03] -- [left, bottom, width, height]
                #
                'logo': '%s/PoweredbyACIS-rev2010-08.png' % RESOURCE_DIR,  # also available ...PoweredbyACIS_NRCC.jpg (False for no logo)
                'metalocation': RESOURCE_DIR, 
                'shapelocation': RESOURCE_DIR, # location of template or shapefiles (old basemap)
                'shape_resolution':'i',
                }

MAP_TITLE_OFFSETS = { 'default':       (0.05, 0.10),
                      'northeast':     (0.05, 0.10),
                      'easternregion': (0.25, 0.10),
                      'midatlantic':   (0.25, 0.10),
                      'ne':            (0.05, 0.10),
                      'newengland':    (0.15, 0.10),
                      'ny':            (0.01, 0.10),
                      'eastny':        (0.23, 0.10),
                      'gulfmaine':     (0.65, 0.90), # not tested
                      'greatlakes':    (0.55, 0.15), # not tested
                      'wv':            (0.48, 0.09),
                      'wv_state':      (0.48, 0.09),
                    }


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def resolveColorMapOptions(**map_options):
    cmap_options = { }
    colors = map_options.get('colors', None)
    if colors is not None: 
        cmap = matplotlib.colors.ListedColormap(colors)
    else: cmap = cm.get_cmap(map_options['cmap'])
    if 'under_color' in map_options: cmap.set_under(map_options['under_color'])
    if 'over_color' in map_options: cmap.set_over(map_options['over_color'])
    cmap_options['cmap'] = cmap
    cmap_options['extend'] = map_options.get('extend','both')
    return cmap_options

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def resolveMapOptions(**options):
    map_options = MAP_OPTIONS.copy()
    map_options.update(options)
    return map_options

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# contour levels (from options, if available)
def getContourIntervals(data, **options):
    bounds = options.get("contourbounds", options.get("autobounds", None))
    if bounds is None:
        bounds = contourBounds(data, options["numlevels"], options["levelmult"])
    return bounds

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# reasonable contour intervals
def contourBounds(data, num_bins, mult=None, missing=None):
    if data.dtype.kind == 'f':
        _array_ = data[N.where(N.isfinite(data))]
        if missing is not None:
            _array_ = _array_[N.where(_array_ != missing)]
        #_array_ = _array_.astype(int)
    elif data.dtype.kind == 'i':
        if missing is None: missing = -999
        _array_ = data[N.where(data != missing) & (data > -9000000000000000000)]
    _array_ = _array_.flatten()

    # added 4/28/2014 -kle
    if mult is None:
        array_max = N.max(_array_)
        array_min = N.min(_array_)
        array_size = _array_.size
        data_intvl = (array_max-array_min)/num_bins
        mult = 1
        for i in [500,100,50,10,5]:
            if data_intvl > i:
                mult = i
                break

    _array_ /= mult
    array_size = float(len(_array_))

    array_min = N.min(_array_)
    bin_mid = N.histogram(_array_, bins=num_bins)
    bin_minimum = bin_mid[1][0]
    bin_maximum = bin_mid[1][-1]
    bin_converge = 0

    while bin_converge == 0:
        bin_tot_low = 0
        bin_tot_hi = 0
        bin_start = bin_mid[1][1]
        bin_end = bin_mid[1][num_bins]

        for val in range(len(bin_mid[0])):
            bin_tot_low=bin_tot_low+bin_mid[0][val]
            if bin_tot_low/array_size < 0.01:
                bin_start =bin_mid[1][val+1]
            else: break

        for val in range(len(bin_mid[0])-1,-1,-1):
            bin_tot_hi=bin_tot_hi+bin_mid[0][val]
            if bin_tot_hi/array_size < 0.01:
                bin_end = bin_mid[1][val] ###changed to val from val -1 atd 2/14
            else: break
                                
        if bin_start > bin_end: bin_start = bin_end
        bin_final = N.histogram(_array_, bins=num_bins,
                                range=(bin_start,bin_end))
        bin_range = abs(bin_mid[0][1]-bin_mid[0][0])
        if (bin_final[0][0]/array_size >= 0.01) or (abs(bin_final[1][0] - bin_final[1][-1]) < 1):
            bin_converge = 1
        else: bin_mid = bin_final

        # round bin contours, omitting the first and last bins as these will be extended to all values less and greater
        bin_contours=[]
        for vals in range(1,len(bin_final[1])-1):
            bin_contours.append(round(bin_final[1][vals],0))
        
        # create bins of equal integer width
        crange = bin_contours[-1]-bin_contours[0]
        resid = crange%num_bins
        factor = 1
        if resid < num_bins/2. and resid <> 0:
            ### shorten end bins
            b_change = round(resid/2.)
            low_change = b_change
            hi_change=-1*b_change 
            if b_change>resid/2.:
                hi_change = -1*(b_change -1)
        if resid <> 0:
            ### length end bins
            b_change = round((num_bins-resid)/2.)
            low_change = -1*b_change
            hi_change = b_change
            if b_change>(num_bins-resid)/2.:
                hi_change = b_change -1 
        else:
            b_change=0
            low_change=0
            hi_change=0
                
        binw = (crange+abs(low_change)+abs(hi_change))/num_bins
        bin_contours_new = [bin_contours[0]+low_change]
        for bin in range(len(bin_contours)):
             if bin_contours_new[bin]+binw <= bin_contours[-1]+hi_change:
                 bin_contours_new.append(bin_contours_new[bin]+binw)
             else: break   

        # remove duplicates and contours less than the min value of the array
        for i in range(len(bin_contours_new)-1,0,-1):
            if bin_contours_new[i] == bin_contours_new[i-1] or bin_contours_new[i] < array_min:
                del bin_contours_new[i]
        if bin_contours_new[0] < array_min:
            del bin_contours_new[0]

        # need to have at least two levels for contouring
        if len(bin_contours_new) == 1:
            bin_contours_new.append(N.max(_array_) + 1)

        # convert back to non-scaled values
        return tuple(N.array(bin_contours_new,dtype=float) * mult)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def basemapSetup(lats, lons, **map_options):
    # setup plot figure
    fig = pyplot.figure(figsize=(map_options['size_tup']))
    axes = fig.gca()

    # initialize basmap
    if map_options['area'].find("gulfmaine") < 0:
        lon_min = N.nanmin(lons)
        lat_min = N.nanmin(lats)
        lat_max = N.nanmax(lats)
        lon_max = N.nanmax(lons)
    else:
        lon_min = -77.0
        lat_min = 41.2
        lat_max = 49.5
        lon_max = -59.0

    _base_map_ = Basemap(llcrnrlon=lon_min, llcrnrlat=lat_min, 
                         urcrnrlon=lon_max, urcrnrlat=lat_max,
                         projection='merc',
                         resolution=map_options['shape_resolution'],
                         lat_ts=(lat_max+lat_min)/2.0)
    x_max, y_max = _base_map_(lon_max,lat_max)
    x_min, y_min = _base_map_(lon_min,lat_min)
    xy_extremes = (x_min, x_max, y_min, y_max)

    return _base_map_, fig, axes, xy_extremes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def finishMap(fig, axes, fig1, **map_options):
    if map_options.get("keylabels",None) is not None:
        if map_options['colorbar']:
           drawLabeledColorBar(fig, fig1, **map_options)
        else: drawColoredTextBar(fig, fig1, **map_options)
    elif map_options['colorbar']: drawColorBar(fig, fig1, **map_options)

    finishPlot(**map_options)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def finishPlot(**options):
    pyplot.savefig(options['outputfile'], bbox_inches='tight', pad_inches=0.02)
    if options['pltshow']: pyplot.show()
    else: pyplot.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def hiResMap(grid, lats, lons, **options):
    map_options, _basemap_, fig, axes, xy_extremes = \
    mapSetup(options, lats, lons)

    _lons_, _lats_, _grid_ = highResolutionGrid(lats, lons, grid, **options)
    x, y = _basemap_(_lons_, _lats_)

    return map_options, _basemap_, fig, axes, xy_extremes, x, y, _grid_

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def highResolutionGrid(lats, lons, grid, **options):
    from mpl_toolkits.basemap import interp
    from mpl_toolkits.basemap import maskoceans
    # interpolate data to higher resolution grid in order to better match
    # the builtin land/sea mask. Output looks less 'blocky' near coastlines.
    ##      rbf = Rbf(lons[0], lats[:,0], map_val, epsilon=2)       ##
    nlats = 5 * lats.shape[0]
    nlons = 5 * lats.shape[1]
    interp_lons = N.linspace(N.min(lons), N.max(lons),nlons)
    interp_lats = N.linspace(N.min(lats), N.max(lats),nlats)
    interp_lons, interp_lats = N.meshgrid(interp_lons, interp_lats)

    # interpolated high resolution data grid
    interp_grid = interp(grid, lons[0], lats[:,0], interp_lons, interp_lats)
    ##map_val to rbf

    # interpolate land/sea mask to data grid, then mask nodes in ocean
    if options.get('mask_coastlines', True):
        interp_grid = maskoceans(interp_lons, interp_lats, interp_grid,
                                 resolution=options['shape_resolution'],
                                 grid=1.25, inlands=False)
        interp_grid[interp_grid == -999] = N.nan

    return interp_lons, interp_lats, interp_grid

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def mapInit(lats, lons, **map_options):
    _base_map_, fig, axes, xy_extremes = basemapSetup(lats, lons, **map_options)
    x_min, x_max, y_min, y_max = xy_extremes

    # add logo
    logo = map_options.get('logo', None)
    if logo is not None:
        zorder = map_options.get('logo_zorder', 10)
        extent = map_options.get('logo_extent', None)
        if extent is None:
            xdiff = x_max-x_min
            ydiff = y_max-y_min
            extent = (x_max-0.30*xdiff, x_max-0.01*xdiff,
                      y_min+0.01*ydiff, y_min+0.15*ydiff)
        
        img = PIL.Image.open(logo)
        pyplot.imshow(img, extent=extent, zorder=zorder)

    # add title
    if 'title' in map_options:
        addMapTitle(fig, xy_extremes=xy_extremes, **map_options)

    # add area template image
    area_template = map_options.get('area_template',None)
    if area_template is None:
        area = map_options.get('area', map_options.get('region',None))
        if area is not None:
            filename = "%s_template.png" % area
            path = os.path.join(map_options['shapelocation'], filename)
        else: path = None
    else: path = os.path.join(map_options['shapelocation'], area_template)
    if path is not None:
        img = PIL.Image.open(path)
        pyplot.imshow(img, extent=(x_min+.0015*(x_max-x_min),x_max,y_min,y_max),
                      zorder=3)

    # add box around the map
    if map_options.get('draw_map_border', True):
        _base_map_.drawmapboundary(linewidth=1.0, color="black", zorder=15)

    return _base_map_, fig, axes, xy_extremes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def mapSetup(options, lats=None, lons=None):
    map_options = resolveMapOptions(**options)

    if 'area' in options and 'bbox' not in options:
        area = options['area']
        map_options['bbox'] = AREA_BBOX[area]

    if lons is not None:
        _basemap_, fig, axes, xy_extremes = mapInit(lats, lons, **map_options)

    if lons is None: return map_options
    else: return map_options, _basemap_, fig, axes, xy_extremes

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def addAxisText(axis, text, **text_options):
    bbox_alpha = text_options.get('bbox_alpha', 0)
    options = { 'backgroundcolor':text_options.get('bgcolor','white'),
                'color':text_options.get('fgcolor','black'),
                'fontsize':text_options.get('fontsize',10),
                'ha':text_options.get('ha','center'),
                'va':text_options.get('va','center'),
                'zorder':text_options.get('zorder',20),
              }

    ax_pos = axis.get_position()
    x0, y0, width, height = ax_pos.bounds

    if 'x' in text_config: x = text_options['x']
    else: x = x0 + width * text_options['x_offset']

    if 'y' in text_config: y = text_options['y']
    else: y = y0 + height * text_options['y_offset']

    axis_text = axis.text(x, y, text, **options)
    if bbox_alpha is not None:
        axis_text.set_bbox({'alpha':bbox_alpha})

    return axis_text

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def addFigureText(fig, text, x, y, **text_options):
    bbox_alpha = text_options.get('bbox_alpha', 0)
    options = { 'backgroundcolor':text_options.get('bgcolor','white'),
                'color':text_options.get('fgcolor','black'),
                'fontsize':text_options.get('fontsize',10),
                'ha':text_options.get('ha','center'),
                'va':text_options.get('va','center'),
                'zorder':text_options.get('zorder',20),
              }

    #origin = text_options.get('origin','ll')
    #x0, y0, width, height = tuple(axes.bbox.bounds)
    #if origin == 'll':
    #    x = width * x_offset 
    #    y = height * y_offset 
    #else:
    #    x_range = width - x0
    #    x = x0 + x_offset * x_range
    #    x = x_offset * width
    #    y_range = height - y0
    #    y = y0 + y_offset * y_range
    #    y = y0
    #    y = y_offset * height

    #axes = fig.add_axes((0.,0.,1.,1.))
    #axes.xaxis.set_visible(False)
    #axes.yaxis.set_visible(False)
    fig_text = fig.text(x, y, text, **options)

    if bbox_alpha is not None:
        fig_text.set_bbox({'alpha':bbox_alpha})
    return fig_text

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def addMapText(text, x_offset, y_offset, xy_extremes, **text_options):
    bbox_alpha = text_options.get('bbox_alpha', 0)
    options = { 'backgroundcolor':text_options.get('bgcolor','white'),
                'color':text_options.get('fgcolor','black'),
                'fontsize':text_options['fontsize'],
                'zorder':text_options.get('zorder', 10),
                'ha':text_options.get('ha','center'),
                'va':text_options.get('va','center'),
              }

    origin = text_options.get('origin','ul')
    x_min, x_max, y_min, y_max = xy_extremes
    if origin == 'ul': # upper left corner
        x = x_min + x_offset * (x_max-x_min)
        y = y_max - y_offset * (y_max-y_min)
    elif origin == 'll': # lower left corner
        x = x_min + x_offset * (x_max-x_min)
        y = y_min + y_offset * (y_max-y_min)
    elif origin == 'lr': # lower right corner
        x = x_max - x_offset * (x_max-x_min)
        y = y_min + y_offset * (y_max-y_min)
    else: # upper right corner
        x = x_max - x_offset * (x_max-x_min)
        y = y_max - y_offset * (y_max-y_min)

    fig_text = pyplot.text(x, y, text, **options)
    if bbox_alpha is not None:
        fig_text.set_bbox({'alpha':bbox_alpha})
    return fig_text

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def addMapTitle(fig, **map_options):
    title = map_options.get('title',None)
    title2 = map_options.get('title2',None)
    if title2 is not None: title += '\n%s' % title2
    date = map_options.get('date', None)
    if date is not None:
        if isinstance(date, basestring): title += '\n%s' % date
        else: title += '\n%s' % date.strftime('%B %d, %Y')

    fontsize = map_options.get('title_fontsize', map_options['titlefontsize'])
    options = { 'bgcolor':map_options.get('title_bgcolor','white'),
                'fgcolor':map_options.get('title_fgcolor','black'),
                'fontsize':fontsize,
                'bbox_alpha': map_options.get('title_box_alpha', None),
                'zorder':map_options.get('title_zorder', 10),
                'ha':map_options.get('title_ha','center'),
                'va':map_options.get('titke_va','center'),
              }
    if 'title_x' in map_options:
        addFigureText(fig, title, map_options['title_x'], 
                      map_options['title_y'], **options)
    else:
        addMapText(title, map_options['titlexoffset'], 
                   map_options['titleyoffset'],
                   map_options['xy_extremes'], **options)                       

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawColorBar(fig, fig1, **map_options):
    axis1 = fig.add_axes(map_options['cbarsettings'])
    ticks = map_options.get('ticks', None)
    if ticks is not None:
        cbar = fig.colorbar(fig1, axis1, ticks=ticks, orientation='horizontal')
    else: cbar = fig.colorbar(fig1, axis1, orientation='horizontal')
    label_size = map_options.get("cbarlabelsize",None)
    if label_size is not None:
        cbar.ax.tick_params(labelsize=label_size)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawColoredTextBar(fig, fig1, **map_options):
    labels = map_options["keylabels"]
    num_labels = len(labels)
    label_size = map_options['cbarlabelsize']
    colors = map_options['colors']
    ypos = map_options['cbarsettings'][1]
    for indx, label in enumerate(labels):
        xpos = 0.16 + ( ((2.*indx) + 1.) * (1. / (num_labels*2.)) ) * 0.5
        fig.text(xpos, ypos, label, color=colors[indx],
                 fontsize=label_size, horizontalalignment="center")       

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawLabeledColorBar(fig, fig1, **map_options):
    colors = map_options['colors']
    cbar_alpha = map_options.get('cbar_alpha',None)
    cbar_specs = map_options['cbarsettings']
    labels = map_options["keylabels"]
    num_labels = len(labels)
    label_colors = map_options.get('label_colors', # else set to black
                                   ['k' for l in range(num_labels)])
    font_style = { 'horizontalalignment':'center',
                   'verticalalignment':'center',
                   'fontsize':map_options['cbarlabelsize'],
                   'fontweight':map_options.get('cbarfontweight','normal'),
                   'fontstyle':map_options.get('cbarfontstyle','normal'),
                 }

    rect_width = 1. / num_labels
    rect_half = rect_width / 2.
    x_left = 0.
    y_bottom = 0.
    y_mid = 0.5
    y_top = 1.

    moves = \
    [ Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY ]

    axis = \
    fig.add_axes(cbar_specs, xticks=[], yticks=[], xlim=(0.,1.), ylim=(0.,1.))

    for indx, label in enumerate(labels):
        x_right = x_left + rect_width
        corners = [ (x_left, y_bottom), (x_left, y_top), (x_right, y_top),
                    (x_right, y_bottom), (x_left, y_bottom) ]
        if cbar_alpha is not None:
            rectangle = PathPatch(Path(corners, moves), facecolor=colors[indx],
                                  lw=0, alpha=cbar_alpha, zorder=1)
        else:
            rectangle = PathPatch(Path(corners, moves), facecolor=colors[indx],
                                  lw=0, zorder=1)
        axis.add_patch(rectangle)
        axis.text(x_left+rect_half, y_mid, label, color=label_colors[indx], 
                  zorder=2, **font_style)
        x_left = x_right

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawBlankMap(lats, lons, **options):
    map_options, _basemap_, fig, axes, xy_extremes = \
    mapSetup(options, lats, lons)
    finishMap(fig, axes, fig1, **options)
    print 'completed', map_options['outputfile']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawContours(grid, lats, lons, **map_options):
    options, _basemap_, fig, axes, xy_extremes, x, y, _grid_ = \
    hiResMap(grid, lats, lons, **map_options)

    # draw filled contours
    cmap_options = resolveColorMapOptions(**options)
    color_bounds = getContourIntervals(grid, **options)
    fig1 = _basemap_.contour(x, y, _grid_, color_bounds, **cmap_options)

    options.update(cmap_options)
    if options.get('finish',True): finishMap(fig, axes, fig1, **options)
    else: return options, _basemap_, fig, axes, fig1, xy_extremes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawFilledContours(grid, lats, lons, **map_options):
    options, _basemap_, fig, axes, xy_extremes, x, y, _grid_ = \
    hiResMap(grid, lats, lons, **map_options)
    # get color mapcontours
    cmap_options = resolveColorMapOptions(**options)
    
    # draw filled contours
    color_bounds = getContourIntervals(grid, **options)
    if color_bounds == True:
        fig1 = _basemap_.contourf(x, y, _grid_, **cmap_options)
    else: fig1 = _basemap_.contourf(x, y, _grid_, color_bounds, **cmap_options)

    options.update(cmap_options)
    if options.get('finish',True): finishMap(fig, axes, fig1, **options)
    else: return options, _basemap_, fig, axes, fig1, xy_extremes

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def addScatterToMap(map_options, _basemap_, fig, data, lats=None, lons=None,
                    x=None, y=None, markercolor=None):
    marker_size = map_options.get('marker_size', 10)
    if markercolor is None:
        if markercolors is None:
            cmap = map_options.get('cmap','jet')
        else: cmap = matplotlib.colors.ListedColormap(markercolors)
    else: cmap = matplotlib.colors.ListedColormap(markercolor)
    plot_args = { 'cmap':cmap, 'linewidths':map_options.get('linewidths', 0),
                  'edgecolors':map_options.get('edgecolors',None),
                  'marker':map_options.get('marker','^') }

    if x is None: x ,y = _basemap_(lons, lats)
    fig1 = _basemap_.scatter(x, y, s=marker_size, c=data, **plot_args)
    return fig1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawScatterMap(grid, lats, lons, **map_options):
    options, _basemap_, fig, axes, xy_extremes, x, y, _grid_ = \
    hiResMap(grid, lats, lons, **map_options)

    cmap_options = resolveColorMapOptions(**options)
    options.update(cmap_options)

    fig1 = addToScatterMap(options, _basemap_, fig, _grid_, x=x, y=y)

    if options.get('finish',True): finishMap(fig, axes, fig1, **map_options)
    else: return options, _basemap_, fig, axes, fig1, xy_extremes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def drawNoDataMap(lons, lats, **options):
    map_options = resolveMapOptions(**options)

    no_data_config = options.get('config', None)
    if no_data_config is not None: map_options.update(no_data_config)
    _basemap_, map_fig, axes, xy_extremes = mapInit(lats, lons, **map_options)

    if 'contourbounds' in map_options:
        x_min = xy_extremes[0]
        x = N.array( [ [x_min, x_min+1.0], [x_min, x_min+1.0 ] ] )
        y_min = xy_extremes[2]
        y = N.array( [ [y_min, y_min], [y_min+1.0, y_min+1.0 ] ] )
        zero = N.array( [ [0.0, 0.0], [0.0, 0.0] ] )
        cmap_options = resolveColorMapOptions(**map_options)
        fig1 = _basemap_.contourf(x, y, zero, options['contourbounds'],
                                 **cmap_options)
    else: fig1 = map_fig

    if options.get('finish',True):
        finishMap(map_fig, axes, fig1, **map_options)
    else: return options, _basemap_, fig, axes, fig1, xy_extremes


