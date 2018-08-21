
import os
import datetime
import urllib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosct.rtma.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class RTMAFactoryMethods:
    """ Methods for downloading data from RTMA and generating directory
    and file paths.

    WARNING: Requires functionality contained in the base Seasonal Project
             Factory. So it MUST be included in a subclass based on the
             Seasonal Project Factory.
    """

    def initRTMA(self, server_url=RTMA_REMOTE_SERVER):
        self.setServerUrl(server_url)
        self.file_template = RTMA_FILE_TEMPLATE
        self.rtma_config = self.sourceConfig('rtma')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableTimeSpan(self, num_hours=3):
        latest_time = datetime.datetime.utcnow()
        if latest_time.minute < 30: previous_hour = 2
        else: previous_hour = 1
        latest_time.replace(minute=0, second=0, microsecond=0)
        latest_time -= datetime.timedelta(hours=previous_hour)
        return (latest_time-datetime.timedelta(hours=num_hours), lastest_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def downloadLatestFiles(self, verbose=False):
        target_date = self.timeOfLatestRTMA()
        filepaths = [ ]
        for temp_var in ('maxt','mint'):
            for time_span in ('001-003','004-007'):
                remote_uri = \
                    RTMA_FILE_TEMPLATE.format('conus', time_span, temp_var)
                if verbose:
                    print '\ndownloading :', remote_uri
                local_filepath = self.rtmaGribFilepath(self.rtma_config,
                                      target_date, time_span, temp_var)
                if verbose:
                    print 'to :', local_filepath
            
                url = self.server_url + remote_uri
                if verbose:
                    print 'url :', url
                urllib.urlretrieve(url, local_filepath)
                filepaths.append(local_filepath)

        return target_date, tuple(filepaths)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def destFileTemplate(self):
        return self.local_file_template

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def rtmaVariableNames(self):
        return self.variable_names

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # rtma directory & data file path
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def rtmaDownloadDir(self, fcast_date):
        root_dir = self.reanalysis.grib.root_dir
        # add subdirectory for rtma source
        download_dir = \
            os.path.join(root_dir, self.sourceToDirpath(self.rtma_config))
        # add subdirectory for rtma date
        download_dir = \
            os.path.join(download_dir, self.timeToDirpath(fcast_date))
        # make sure directory exists before return
        if not os.path.exists(download_dir): os.makedirs(download_dir)
        return download_dir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def rtmaGribFilename(self, fcast_date, time_span, variable, **kwargs):
        template = self.destFileTemplate()
        template_args = dict(kwargs)
        template_args['date'] = self.timeToDirpath(fcast_date)
        template_args['source'] = self.sourceToFilepath(self.rtma_config)
        template_args['timespan'] = time_span
        template_args['variable'] = variable
        return template % template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def rtmaGribFilepath(self, rtma_config, fcast_date, time_span,
                                   variable, **kwargs):
        fcast_dir = self.rtmaDownloadDir(fcast_date)
        filename = \
           self.rtmaGribFilename(fcast_date, time_span, variable, **kwargs)
        return os.path.join(fcast_dir, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setServerUrl(self, server_url):
        self.server_url = server_url

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeToDirpath(self, time_obj):
        if isinstance(time_obj, datetime.datetime):
            return time_obj.strftime('%Y%m%d%H%M')
        elif isinstance(time_obj, datetime.date):
            return time_obj.strftime('%Y%m%d')
        else: return time_obj


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class RTMADownloadFactory(RTMAFactoryMethods):

    def __init__(self, grib_dest_dir, rtma_variable_names, area='conus',
                       local_file_template=None,
                       rtma_file_template=RTMA_FILE_TEMPLATE,
                       server_url=RTMA_REMOTE_SERVER);
        self.rtma_file_template = rtma_file_template
        self.setGribDir(grib_dest_dir)
        self.setServerUrl(server_url)

        if local_file_template is None: 
            self.local_file_template = rtma_file_template
        else: self.local_file_template = local_file_template

