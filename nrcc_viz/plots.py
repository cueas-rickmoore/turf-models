
import os, sys

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N
import PIL.Image

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot
from matplotlib import cm
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle, PathPatch
from matplotlib.path import Path

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PLOT_OPTIONS = { "bbox": [-82.70, 37.20, -66.90, 47.60],  # plot coordinate bounding box
                 "size_tup" : (6.8, 6.55),   # new standard size is (6.8, 6.55), thumbnail is (2.3, 2.3), original standard is (4.7, 4.55), large is (12,8.3)
                 "dpi": 100,
                 "axis_grid": True,
                 "pltshow": False,          # boolean

                 "cmap": 'RdYlGn',
                 "marker":'s',
                 "marker_color":'g',
                 "marker_size":10,

                 "titlefontsize": 12,       # standard is 12, original is 10, large is 15, (none for thumbnail)
                 "titlexoffset": 0.05,      # 0.05 for all but those specified below
                 "titleyoffset": 0.10,      # 0.10 for all but those specified below

                 "numlevels": 8,            # number of contour levels
                 "autolevels":None,
                 "levelmult": None,         # contour bounds are multiples of this value (None = pick based on data)

                 "colorbar": False,          # whether or not to plot a colorbar
                 "cbarlabelsize": 8,                      # small is 8, large is 10
                 "cbarsettings": [0.25, 0.11, 0.5, 0.02], # small is [0.25, 0.11, 0.5, 0.02], large is [0.25, 0.06, 0.5, 0.03] -- [left, bottom, width, height]
                 #
                 "logo": "%s/PoweredbyACIS-rev2010-08.png" % MAPS_DIR,  # also available ...PoweredbyACIS_NRCC.jpg (False for no logo)
               }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def resolvePlotOptions(options):
    plot_options = PLOT_OPTIONS.copy()
    plot_options.update(options)
    return plot_options

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def resolveColorMapOptions(plot_options):
    cmap_options = { }
    colors = plot_options.get('colors', None)
    if colors is not None: 
        cmap = matplotlib.colors.ListedColormap(colors)
    else: cmap = cm.get_cmap(plot_options['cmap'])

    under_color = plot_options.get('under_color',None)
    if under_color is not None: cmap.set_under(under_color)
    over_color = plot_options.get('over_color',None)
    if over_color is not None: cmap.set_under(over_color)

    cmap_options['cmap'] = cmap
    cmap_options['extend'] = plot_options.get('extend','both')
    return cmap_options

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def finishPlot(plot_options):
    if plot_options.get("keylabels",None) is not None:
        if plot_options['colorbar']:
            drawLabeledColorBar(fig, fig1, plot_options)
        else: drawColoredTextBar(fig, fig1, plot_options)
    elif plot_options['colorbar']: drawColorBar(fig, fig1, plot_options)

    pyplot.savefig(options['outputfile'], bbox_inches='tight', pad_inches=0.02)
    if options['pltshow']: pyplot.show()
    else: pyplot.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def plotInit(x, y, plot_options):
    xy_extremes = (x.nanmin(), x.nanmax(), y.nanmin(), y.nanmax())
    x_min, x_max, y_min, y_max = xy_extremes

    # add logo
    logo = plot_options.get('logo', None)
    if logo is not None:
        zorder = plot_options.get('logo_zorder', 10)
        extent = plot_options.get('logo_extent', None)
        if extent is None:
            xdiff = x_max-x_min
            ydiff = y_max-y_min
            extent = (x_max-0.30*xdiff, x_max-0.01*xdiff,
                      y_min+0.01*ydiff, y_min+0.15*ydiff)
        
        img = PIL.Image.open(logo)
        pyplot.imshow(img, extent=extent, zorder=zorder)

    # add title
    title = plot_options.get('title',None)
    if title is not None:
        addPlotTitle(title, xy_extremes=xy_extremes, **plot_options)

    # add area template image
    area_template = plot_options.get('area_template',None)
    if area_template is None:
        area = plot_options.get('area',None)
        if area is not None:
            filename = "%s_template.png" % area
            path = os.path.join(map_options['shapelocation'], filename)
        else: path = None
    else: path = os.path.join(map_options['shapelocation'], area_template)
    if path is not None:
        img = PIL.Image.open(path)
        pyplot.imshow(img, extent=(x_min+.0015*(x_max-x_min),x_max,y_min,y_max),
                      zorder=3)

    # add box around the plor
    #if plot_options.get('draw_border', True):
    #    _base_map_.drawmapboundary(linewidth=1.0, color="black", zorder=15)

    return fig, axes, xy_extremes

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def addAxisText(axis, text, **text_options):
    bbox_alpha = text_options.get('bbox_alpha', 0)
    options = { 'bgcolor':text_options.get('bgcolor','white'),
                'fgcolor':text_options.get('fgcolor','black'),
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
    options = { 'bgcolor':text_options.get('bgcolor','white'),
                'fgcolor':text_options.get('fgcolor','black'),
                'fontsize':text_options.get('fontsize',12),
                'ha':text_options.get('ha','center'),
                'va':text_options.get('va','center'),
                'zorder':text_options.get('zorder',20),
              }

    fig_text = fig.text(x, y, text, **options)
    if bbox_alpha is not None:
        fig_text.set_bbox({'alpha':bbox_alpha})
    return fig_text

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def addPlotText(text, x_offset, y_offset, xy_extremes, **text_options):
    bbox_alpha = text_options.get('bbox_alpha', 0)
    options = { 'bgcolor':text_options.get('bgcolor','white'),
                'fgcolor':text_options.get('fgcolor','black'),
                'fontsize':text_options.get('fontsize',12),
                'ha':text_options.get('ha','center'),
                'va':text_options.get('va','center'),
                'zorder':text_options.get('zorder',20),
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

    fig_text = pyplot.text(x, y, text, **text_options)
    if bbox_alpha is not None:
        fig_text.set_bbox({'alpha':bbox_alpha})
    return fig_text

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def addPlotTitle(title, **plot_options):
    title2 = plot_options.get('title2',None)
    if title2 is not None: title += '\n%s' % title2
    date = plot_options.get('date', None)
    if date is not None:
        if isinstance(date, basestring): title += '\n%s' % date
        else: title += '\n%s' % date.strftime('%B %d, %Y')

    options = { }
    options['bgcolor'] = plot_options.get('title_bgcolor','white')
    options['fgcolor'] = plot_options.get('title_fgcolor','black')
    options['fontsize'] = plot_options['titlefontsize']
    options['bbox_alpha'] = plot_options.get('title_box_alpha', None)
    options['zorder'] = plot_options.get('title_zorder', 10)
    options['ha'] = plot_options.get('title_ha','center')
    options['va'] = plot_options.get('titke_va','center')
    if 'title_x' in plot_options:
        addFigureText(fig, title, plot_options['title_x'], 
                      plot_options['title_y'], **options)
    else:
        addPlotText(title, plot_options['titlexoffset'], 
                   plot_options['titleyoffset'],
                   plot_options['xy_extremes'], **options)                       

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawColorBar(fig, fig1, plot_options):
    axis1 = fig.add_axes(map_options['cbarsettings'])
    cbar = fig.colorbar(fig1, axis1, orientation='horizontal')
    label_size = plot_options.get("cbarlabelsize",None)
    if label_size is not None:
        cbar.ax.tick_params(labelsize=label_size)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawColoredTextBar(fig, fig1, plot_options):
    labels = plot_options["keylabels"]
    num_labels = len(labels)
    label_size = plot_options['cbarlabelsize']
    colors = plot_options['colors']
    ypos = plot_options['cbarsettings'][1]
    for indx, label in enumerate(labels):
        xpos = 0.16 + ( ((2.*indx) + 1.) * (1. / (num_labels*2.)) ) * 0.5
        fig.text(xpos, ypos, label, color=colors[indx],
                 fontsize=label_size, horizontalalignment="center")       

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawLabeledColorBar(fig, fig1, plot_options):
    colors = plot_options['colors']
    cbar_specs = plot_options['cbarsettings']
    labels = plot_options["keylabels"]
    num_labels = len(labels)
    label_colors = plot_options.get('label_colors', # else set to black
                                   ['k' for l in range(num_labels)])
    font_style = { 'ha':'center', 'va':'center',
                   'fontsize':plot_options['cbarlabelsize'],
                   'fontweight':plot_options.get('cbarfontweight','normal'),
                   'fontstyle':plot_options.get('cbarfontstyle','normal'),
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
        rectangle = PathPatch(Path(corners, moves), facecolor=colors[indx],
                              lw=0, zorder=1)
        axis.add_patch(rectangle)
        axis.text(x_left+rect_half, y_mid, label, color=label_colors[indx], 
                  zorder=2, **font_style)
        x_left = x_right

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawScatterPlot(data, x, y, **plot_options):
    options = resolvePlotOptions(plot_options)
    figsize = options.get('figsize', options['size_tup'])
    fig = pyplot.figure(figsize=figsize, dpi=options['dpi'])

    pyplot.xlim(N.nanmin(x),N.nanmax(x))
    pyplot.ylim(N.nanmin(y),N.nanmax(y))
    axis = pyplot.gca()
    scatter = axis.scatter(x, y, c=data, marker=options['marker'],
                           s=options['marker_size'], mew=0)
    axis.grid(options['axis_grid'])

    #if options['colorbar']:
    #    ax_pos = axis.get_position()
    #    l,b,w,h = ax_pos.bounds
    #    color_axis = pyplot.axes([l+w, b, 0.025, h])
    #    pyplot.colorbar(scatter, cax=color_axis, ticks=ticks)

    #pyplot.axes(axis)

    #pyplot.suptitle(title, fontsize=16)
    #pyplot.title(subtitle, fontsize=12)
    figure.savefig('test_plot.png')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

