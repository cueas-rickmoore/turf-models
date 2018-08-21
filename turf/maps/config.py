
import os

from atmosci.utils.config import ConfigObject


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

MAP_CONFIG = ConfigObject('maps', None, 'groups')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

MAP_CONFIG.animate_command = '/opt/local/bin/convert -delay %d %s -loop 0 %s'
MAP_CONFIG.subdirs = {
    'anim': ('%(region)s','%(year)s','animations'),
    'map': ('%(region)s','%(year)s','maps'),
    'thumb': ('%(region)s','%(year)s','thumbs'),
}
MAP_CONFIG.thumbnail_shape = (125, 125)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  config for map generation
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

MAP_CONFIG.default = {
    'map_options':{
        'map_type':'risk',
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
        'pltshow':False,
        'shape_resolution':None,
        'title_x':0.45,
        'title_y':0.78, 
        'title_va':'top',
        'title_box_alpha':0.0,
    },
}

MAP_CONFIG.groups.controls = {
    'anim_filename':'%(year)s-%(treatment)s-%(threat)s-Maps-Animation.gif',
    'map_filename':'%(date)s-%(treatment)s-%(threat)s-Control-Map.png',
    'subdirs':('%(threat)s','%(treatment)s'),
    'threats':{
        'dandelion':{
            'fullname':'Dandelion',
            'gdd_threshold':50,
            'map_options':{
                'colors':('#ff0000','#ffd700','#00aa00'),
                'contourbounds':(-1,0,1,2), # no risk, moderate, high
                'keylabels':('Early','Marginal','Favorable'),
                'markercolors':('#ff0000','#ffd700','#00aa00'),
                'title':'%(treatment)s Dandelion Control Recommendation',
            },
            'treatments':{
                'amine':{'fullname':'Amine', 'thresholds':(0,150,180),
                         'title':'Amine Dandelion Control' },
                'ester':{'fullname':'Ester', 'thresholds':(0,130,145),
                         'title':'Ester Dandelion Control' },
            },
        },
        'seedhead':{
            'fullname':'Seedhead',
            'gdd_threshold':32,
            'map_options':{
               'colors':('#ff0000','#00aa00','#ffd700','#aaaaaa'),
               'contourbounds':(-1,0,1,2,3), # no risk, moderate, high
               'keylabels':('Early','Ideal','Marginal','Late'),
               'markercolors':('#ff0000','#00aa00','#ffd700','#aaaaaa'),
               'title':'%(treatment)s Seedhead Control Recommendation'
            },
            'treatments':{
                'embark':{'fullname':'Embark', 'thresholds':(0,350,450,650),
                          'title':'Embark Seedhead Control' },
                'proxy':{'fullname':'Proxy', 'thresholds':(0,200,300,500),
                         'title':'Proxy Seedhead Control' },
            },
        },
    },
    'thumb_filename':'%(date)s-%(treatment)s-%(threat)s-Control-Thumbnail.png',
}

MAP_CONFIG.groups.diseases = {
    'anim_filename':'%(year)s-%(threat)s-Risk-Maps-Animation.gif',
    'map_filename':'%(date)s-%(threat)s-Risk-Map.png',
    'map_options':{
        'colors':('#00aa00','#ffd700','#ff0000'),
        'contourbounds':(-1,0,1,2), # no risk, moderate, high
        'keylabels':('No Risk','Moderate','High'),
        'markercolors':('#00aa00','#ffd700','#ff0000'),
        'title':'%(threat)s Risk Level'
    },
    'subdirs':('%(threat)s',),
    'threats':{
        'anthrac':{'fullname':'Anthracnose', 'title':'Anthracnose Risk Level'},
        'bpatch':{'fullname':'Brown Patch', 'title':'Brown Patch Risk Level'},
        'dspot':{'fullname':'Dollarspot', 'title':'Dollarspot Risk Level'},
        'pblight':{'fullname':'Pythium Blight', 'title':'Pythiun Blight Risk Level'},
    },
    'thumb_filename':'%(date)s-%(threat)s-Risk-Thumbnail.png',
}

MAP_CONFIG.groups.hstress = {
    'map_filename':'%(date)s-Heat-Stress-Risk-Map.png',
    'map_options':{
        'colors':('#00aa00','#ffd700','#ff0000'),
        'contourbounds':(-1,0,1,2), # no risk, moderate, high
        'keylabels':('No Risk','Moderate','High'),
        'markercolors':('#00aa00','#ffd700','#ff0000'),
        'title':'Heat Stress Risk Level',
    },
    'subdirs':('Heat-Stress',),
    'threats':{'hstress':{'fullname':'Heat Stress',
               'title':'Heat Stress Risk Level'}, },
    'thumb_filename':'%(date)s-Heat-Stress-Risk-Thumbnail.png',
}

MAP_CONFIG.no_threat = {
       'area_template':'NortheastNoData_template.png',
       'create_with':'NortheastNoData_template.png',
       'mask_coastlines':False,
       'shape_resolution':None,
       'title_x':0.45, 'title_y':0.78,
       'title_va':'top', 'title_box_alpha':0.0,
       'title_box_alpha':0.0,
}

