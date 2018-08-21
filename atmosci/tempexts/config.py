
from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# take advantage of the default seasonal project configuration
# this helps keep common things consistent between projects
# which, in turn, means we can re-use scripts from the 
# atmosci.seasonal package without making changes 
from atmosci.seasonal.config import CFGBASE
CONFIG = CFGBASE.copy('config', None)
del CFGBASE


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.dirpaths.project = \
       os.sep.join(CONFIG.dirpaths.shared, 'grid')
CONFIG.modes.dev.dirpaths.project = \
       os.sep.join(CONFIG.modes.dev.dirpaths.shared, 'grid')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TempExt project datasets
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.datasets.maxt.dtype = int
CONFIG.datasets.maxt.dtype_packed ='<i2'
CONFIG.datasets.maxt.missing_packed = -32768
CONFIG.datasets.maxt.missing_data = -32768

CONFIG.datasets.mint.dtype = int
CONFIG.datasets.mint.dtype_packed ='<i2'
CONFIG.datasets.mint.missing_packed = -32768
CONFIG.datasets.mint.missing_data = -32768


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TempRxt project configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.project.compression = 'gzip'
CONFIG.project.end_day = (12,31)
CONFIG.project.forecast = 'ndfd'
CONFIG.project.forecast_days = 6
CONFIG.project.region = 'NE'
CONFIG.project.source = 'acis'
CONFIG.project.start_day = (1,1)
CONFIG.project.subdir_path = ('grid','%(region)s','%(source)s','temps')
CONFIG.project.subproject_by_region = True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# TempExt project file names and file types
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.filenames.source = '%(year)d-%(source)s-%(region)s-Daily.h5'
CONFIG.filenames.tempexts = '%(year)d-%(source)s-%(region)s-Daily.h5'

CONFIG.filetypes.tempexts = { 'scope':'year', 'period':'date', 
       'datasets':('lon','lat'), 'groups':('temps',),
       'description':'Temerature extremes downloaded from %(source)s',
       'start_day':(1,1), 'end_day':(12,31) }
# some old code uses 'source' as the file type
CONFIG.filetypes.tempexts.copy('source', CONFIG.filetypes)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# project data groups
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.groups.temps = { 'description':'Daily temperatures',
        'datasets':('maxt','mint','provenance:tempexts') }

