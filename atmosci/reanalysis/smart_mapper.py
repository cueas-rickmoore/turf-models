
import os
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N

from atmosci.units import convertUnits

from nrcc_viz.maps import hiResMap, addScatterToMap, drawFilledContours, \
                          drawColoredTextBar, finishMap, finishPlot
from atmosci.reanalysis.factory import ReanalysisGridFileFactory
from atmosci.reanalysis.smart_grid import SmartReanalysisDataMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

MAP_CONFIG = CONFIG.copy('map_config', None)

# templates for data maps
MAP_CONFIG.mapper = {
    'anim_filename':'%(year)s-%(analysis)s-%(variable)s-Maps-Animation.gif',
    'map_filename':'%(date)s-%(analysis)s-%(variable)s-Map.png',
    'subdir':('reanalysis','%(region)s','maps','%(year)d'),

    'options':{'map_type':'reanalysis',
               'area':'northeast',
               'area_template':'NortheastEmpty_template.png',
               'cbarfontweight':'bold',
               'cbarlabelsize':8,
               # cbar @ [left, bottom, width, height]
               'cbarsettings':[0.13, 0.08, .76, 0.04],
               'colorbar':True,
               'extend':'neither',
               'linewidths':0,
               'marker':'o',
               'marker_size':2,
               'mask_coastlines':False,
               'shape_resolution':None,
               'title_x':0.45,
               'title_y':0.78, 
               'title_va':'top',
               'title_box_alpha':0.0,
    },
    'NWS_PCPN':{ 'colors':( # NWS precipitation colors
                        '#04e9e7',  # 0.01 - 0.10 inches
                        '#019ff4',  # 0.10 - 0.25 inches
                        '#0300f4',  # 0.25 - 0.50 inches
                        '#02fd02',  # 0.50 - 0.75 inches
                        '#01c501',  # 0.75 - 1.00 inches
                        '#008e00',  # 1.00 - 1.50 inches
                        '#fdf802',  # 1.50 - 2.00 inches
                        '#e5bc00',  # 2.00 - 2.50 inches
                        '#fd9500',  # 2.50 - 3.00 inches
                        '#fd0000',  # 3.00 - 4.00 inches
                        '#d40000',  # 4.00 - 5.00 inches
                        '#bc0000',  # 5.00 - 6.00 inches
                        '#f800fd',  # 6.00 - 8.00 inches
                        '#9854c6',  # 8.00 - 10.00 inches
                        '#fdfdfd'   # 10.00+
             ),
             'contourbounds':(0., 0.01, 0.1, 0.25, 0.50, 0.75, 1.0, 1.5, 2.0,
                              2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10., 20.0),
             'title':'Accumulated Precip\n%(start)s thru %(end)s',
    },
    'PCPN':{ 'colors':( '#ffffff',  # zero - 0.10 inches
                        '#ccccff',  # 0.01 - 0.10 inches
                        '#9999ff',  # 0.10 - 0.25 inches
                        '#6666ff',  # 0.25 - 0.50 inches
                        '#3333ff',  # 0.50 - 0.75 inches
                        '#0000ff',  # 0.75 - 1.00 inches
                        '#0000cc',  # 1.00 - 1.50 inches
                        '#9933ff',  # 1.50 - 2.00 inches
                        '#8000ff',  # 2.00 - 2.50 inches
                        '#6600cc',  # 2.50 - 3.00 inches
                        '#ff6666',  # 3.00 - 4.00 inches
                        '#ff0000',  # > 4.00 inches
             ),
             'cbarlabelsize':9,
             'contourbounds':(0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0,
                              2.0, 3.0, 4.0, 20.0),
             'keylabels':('0', '.1', '.2', '.3', '.4', '.5', '.75',
                           '1', '2', '3', '4+'),
             'title':'%(summary)s Precip\n%(start)s thru %(end)s',
    },
    'RHUM': { 'colors': ( # reds - darkest to lightest 
                         '#a04000', '#d35400', '#dc7633', '#cb4335', '#e74c3c',
                         '#ec7063', '#f1948a', '#f5b7b1', '#fadbd8', '#fdedec',
                         # blues - lightest to darkest
                         '#ebf5fb', '#ddeaf8', '#aed6f1', '#85c1e9', '#5dade2',
                         '#3498db', '#2e86c1', '#2874a6', '#21618c', '#1b4f72',
             ),
             'contourbounds':(0.,40.,45.,50.,55.,60.,65.,70.,72.5,75.,77.5,
                              80.,82.5,85.,87.5,90.,92.5,95.,97.5,100.),
             'keylabels':('0','40','45','50','55','60','65','70','72.5','75',
                          '77.5','80','82.5','85','87.5','90','92.5','95',
                          '97.5','100'),
             'title':'%(summary)s Humidity\n%(start)s thru %(end)s',
    },
    'TMP': { 'colors': ( # blues - darkest to lightest 
                         '#1b4f72', '#21618c', '#2874a6', '#2e86c1', '#3498db',
                         '#5dade2', '#85c1e9', '#aed6f1', '#ddeaf8', '#ebf5fb',
                         # reds - lightest to darkest
                         '#fdedec', '#fadbd8', '#f5b7b1', '#f1948a', '#ec7063',
                         '#e74c3c', '#cb4335', '#dc7633', '#d35400', '#a04000'    
             ),
             'contourbounds':(0.,40.,45.,50.,55.,60.,65.,70.,72.5,75.,77.5,
                              80.,82.5,85.,87.5,90.,92.5,95.,97.5,100.),
             'keylabels':('0','40','45','50','55','60','65','70','72.5','75',
                          '77.5','80','82.5','85','87.5','90','92.5','95',
                          '97.5','100'),
             'title':'%(summary)s Temperature\n%(start)s thru %(end)s',
    },
}

MAP_CONFIG.mapper.TMP.copy('DPT', MAP_CONFIG.mapper)
MAP_CONFIG.mapper.DPT.title = '%(summary)s Dew Point\n%(start)s thru %(end)s'


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartReanalysisDataMapper(SmartReanalysisDataMethods,
                                ReanalysisGridFileFactory):

    def __init__(self, region, **kwargs):
        ReanalysisGridFileFactory.__init__(self, MAP_CONFIG, **kwargs)
        self.region = region
        dims = self.source.dimensions[region]
        self.grid_dimensions = (dims.lat, dims.lon)
        self.map_config = self.config.mapper
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def mapDirpath(self, date, variable, region, **kwargs):
        if self.project.get('shared_grid_dir', False):
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.config.dirpaths.get('reanalysis',
                                                self.projectRootDir())
        subdir_path = self.mapSubdirPath(date, region, **kwargs)
        map_dirpath = os.path.join(root_dir, subdir_path)
        if not os.path.exists(map_dirpath): os.makedirs(map_dirpath)

        return map_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapFilename(self, date, variable, region, **kwargs):
        analysis = kwargs.get('analysis', 'Reanalysis')
        if len(analysis) == 4: analysis = analysis.upper()
        filename_args = { 'analysis':analysis,
                          'region':region }
        summary = kwargs.get('summary', None)
        if summary is None: var_arg = variable.upper()
        else: var_arg = "%s-%s" % (summary.title(), variable.upper())
        filename_args['variable'] = var_arg

        if isinstance(date, (datetime.date, datetime.datetime)):
            filename_args['date'] = date.strftime('%Y%m%d')
        else: filename_args['date'] = date

        return self.map_config.map_filename % filename_args
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapFilepath(self, date, variable, region, **kwargs):
        print '\nmapFilepath kwargs : %s\n' % str(kwargs)
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            root_dir = self.mapDirpath(date, variable, region, **kwargs)
            filename = self.mapFilename(date, variable, region, **kwargs)
            filepath = os.path.join(root_dir, filename)
        return filepath
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapOptions(self, variable, start_time, end_time, region, **kwargs):
        map_options = self.map_config.options.attrs
        map_options.update(self.map_config[variable].attrs)
        map_options['finish'] = kwargs.get('finish',True)

        map_title_template = map_options['title']
        title_args = { 'start':start_time.strftime('%Y%m%d:%H'),
                       'end':(end_time-ONE_HOUR).strftime('%Y%m%d:%H'),
                     }
        if '%(summary)s' in map_title_template:
            title_args['summary'] = kwargs.get('summary','%(summary)s')
        map_options['title'] = map_title_template % title_args

        return map_options

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapSubdirPath(self, target_date_or_year, region, **kwargs):
        subdir = self.map_config.subdir
        if isinstance(subdir, tuple):
            subdir_path = os.path.join(*subdir)
        else: subdir_path = subdir

        subdir_args = dict(kwargs)
        if isinstance(target_date_or_year, (datetime.date, datetime.datetime)):
            subdir_args['year'] = target_date_or_year.year
        else: subdir_args['year'] = target_date_or_year
        subdir_args['region'] = self.regionToDirpath(region)

        return subdir_path % subdir_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapData(self, variable, start_time, end_time):
        lons, lats, units, data = \
            self.timeSlice(variable, start_time, end_time, lonlat=True)
        return lons, lats, units, N.nansum(data, axis=0)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawContourMap(self, variable, start_time, end_time, region):
        map_filepath = self.mapFilepath(end_time, variable, region)

        options = self.mapOptions(variable, start_time, end_time, region)
        options['outputfile'] = map_filepath

        lons, lats, units, data = self.mapData(variable, start_time, end_time)
        drawFilledContours(N.nansum(data, axis=0), lats, lons, **options)

        return options

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawScatterMap(self, lons, lats, data, start_time, end_time,
                             map_options, debug):

        # extract options required for plotting markers 
        marker_colors = map_options['colors']
        levels = map_options['contourbounds'][1:]
        #map_options['keylabels'] = levels
        #map_options['colorbar'] = False

        # create a map figure
        options, _map_, map_fig, axes, xy_extremes, x, y, _grid_ = \
            hiResMap(data, lats, lons, **map_options)
        del x, y, _grid_

        # flatten the datasets so basemap scatter can handle them
        map_lats = lats.flatten()
        map_lons = lons.flatten()
        map_data = data.flatten()

        # plot data for each level
        if debug: print '\nbuilding scatter map :'
        level_msg = '   contour interval %.2f < z <= %.2f has %d nodes'
        prev_value = float(options.get('min_value', 0))
        for level, value in enumerate(levels):
            indexes = N.where((map_data > prev_value) & (map_data <= value))
            if debug: print level_msg % (prev_value, value, len(indexes[0]))
            if len(indexes[0]) > 0:
                color = marker_colors[level]
                fig = addScatterToMap(options, _map_, map_fig, 
                                      map_data[indexes], map_lats[indexes],
                                      map_lons[indexes], markercolor=color)
            prev_value = value

        finishMap(map_fig, axes, map_fig, **options)
        #drawColoredTextBar(map_fig, map_fig, **options)
        #finishPlot(**options)

        return options['outputfile']

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapDataExtremes(self, variable, start_time, end_time, region, debug,
                              **kwargs):
        lons, lats, data_units, data = \
            self.timeSlice(variable, start_time, end_time, lonlat=True)
        map_units = kwargs.get('units', data_units)
        if map_units != data_units:
            data = convertUnits(data, data_units, map_units)

        options = self.mapOptions(variable, start_time, end_time, region)
        title_template = options['title']

        arg_dict = { 'summary':'Min', }
        options['title'] = title_template % arg_dict
        options['outputfile'] = \
            self.mapFilepath(end_time, variable, region, **arg_dict)
        min_filepath = self.drawScatterMap(lons, lats, N.nanmin(data, axis=0),
                                       start_time, end_time, options, debug)

        arg_dict = { 'summary':'Max', }
        options['title'] = title_template % arg_dict
        options['outputfile'] = \
            self.mapFilepath(end_time, variable, region, **arg_dict)
        max_filepath = self.drawScatterMap(lons, lats, N.nanmax(data, axis=0),
                                       start_time, end_time, options, debug)

        return min_filepath, max_filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapDataMeans(self, variable, start_time, end_time, region, debug,
                           **kwargs):
        lons, lats, data_units, data = \
            self.timeSlice(variable, start_time, end_time, lonlat=True)
        map_units = kwargs.get('units', data_units)
        if map_units != data_units:
            data = convertUnits(data, data_units, map_units)

        options = self.mapOptions(variable, start_time, end_time, region)
        title_template = options['title']
        
        arg_dict = { 'summary':'Average', }
        options['title'] = title_template % arg_dict
        options['outputfile'] = \
            self.mapFilepath(end_time, variable, region=region, **arg_dict)

        return self.drawScatterMap(lons, lats, N.nanmean(data, axis=0), 
                                   start_time, end_time, options, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapDataTotals(self, variable, start_time, end_time, region, debug,
                            **kwargs):
        lons, lats, data_units, data = \
            self.timeSlice(variable, start_time, end_time, lonlat=True)
        map_units = kwargs.get('units', data_units)
        if map_units != data_units:
            data = convertUnits(data, data_units, map_units)

        options = self.mapOptions(variable, start_time, end_time, region)
        title_template = options['title']

        if variable in ('pcpn','PCPN'):
            arg_dict = { 'summary':'Accumulated', }
        else: arg_dict = { 'summary':'Total', }
        options['title'] = title_template % arg_dict
        options['outputfile'] = \
            self.mapFilepath(end_time, variable, region, **arg_dict)

        return self.drawScatterMap(lons, lats, N.nansum(data, axis=0),
                                   start_time, end_time, options, debug)

