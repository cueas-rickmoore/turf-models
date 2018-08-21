
import os, sys

import numpy as N
import json

from turf.threats.factory import TurfThreatGridFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class JsonFileGenerator(object):

    def __init__(self, factory, source, region, sub_region=None):
        self.factory = factory

        # get the indexes of all valid grid nodes from region's static file 
        source = factory.sourceConfig(factory.config.project.source)
        static_reader = factory.staticFileReader(source, region)
        if sub_region is not None:
            region_config = factory.regionConfig(sub_region)
            static_reader.setCoordinateBounds(region_config.data)
            cus_mask = static_reader.getDataInBounds('cus_mask')
        else:
            cus_mask = static_reader.getData('cus_mask')
            indexes = N.where(cus_mask == False)
        self.region_indexes = zip(indexes[0], indexes[1])
        del cus_mask, indexes, source
        static_reader.close()
        del static_reader

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def jsonPathTemplates(self, threat, target_year):
        factory = self.factory
        # create templates for constructing json data file paths 
        path_key = 'threats.%s' % threat
        dirpath = factory.threatJsonDirpath(path_key, target_year)
        if not os.path.isdir(dirpath): os.makedirs(dirpath)
        filename = factory.threatJsonFilename(path_key, '%(node)s', target_year)
        return dirpath, filename


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class CommonRiskJsonFileGenerator(JsonFileGenerator):

    def __init__(self, factory, source, region, sub_region=None):
        JsonFileGenerator.__init__(self, factory, source, region, sub_region)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, threat, target_year, debug=False):
        self.target_year = target_year
        self.threat = threat

        self.avg_reader = \
            self.factory.threatFileReader(threat, 'average', target_year)
        avg_dates = self.avg_reader.dateAttributes('risk', True)
        self.avg_reader.close()
        if debug:
            print '\nCommonRiskJsonFileGenerator'
            print '%s average risk dates:' % threat
            for key, value in avg_dates.items():
                print '    %s : %s' % (key,value)

        self.daily_reader = \
            self.factory.threatFileReader(threat, 'daily', target_year)
        daily_dates = self.daily_reader.dateAttributes('risk', True)
        self.daily_reader.close()
        if debug:
            print '%s daily risk dates:' % threat
            for key, value in daily_dates.items():
                print '    %s : %s' % (key,value)

        return self.generateJsonFiles(avg_dates, daily_dates, debug)
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def generateJsonFiles(self, avg_dates, daily_dates, debug):
        factory = self.factory
        region_indexes = self.region_indexes
        threat = self.threat
        
        data_start, data_end, json_datestr = \
            self.threatDates(avg_dates, daily_dates)
        if debug:
            info = (threat, str(data_start), str(data_end))
            print 'generating %s JSON files for %s thru %s' % info
        # no data available
        if json_datestr is None: return 0

        # create JSON content template
        params = { 'name':threat, 'lat':'%(lat)s', 'lon':'%(lon)s', 
                   'dates':json_datestr,
                   'data':'{"average":[%(avg)s],"daily":[%(daily)s]}' }
        json_template = factory.threats.json_template % params

        # JSON file path templates
        json_dirpath, json_filename = \
            self.jsonPathTemplates(threat, self.target_year)

        # get risk data for both periods
        avg_risk, daily_risk, lats, lons = self.threatRisk(data_start, data_end, debug)

        num_files = 0

        for y, x in region_indexes:
            avg = avg_risk[:,y,x]
            daily = daily_risk[:,y,x]


            if len(N.where(N.isnan(avg))[0]) == 0 and len(N.where(N.isnan(daily))[0]) == 0:
                lat = N.round(lats[y,x],3)
                lon = N.round(lons[y,x],3)
                params = { 'lat':lat, 'lon':lon }
                params['avg'] = ','.join(['%d' % value for value in avg])
                params['daily'] = ','.join(['%d' % value for value in daily])

                filename = json_filename % {'node':factory.gridNodeToFilename((lon,lat)),}
                filepath = os.path.join(json_dirpath, filename)
        
                with open(filepath, 'w') as writer:
                    writer.write(json_template % params)

                num_files += 1

            else:
                threat_name = factory.threatName(threat)
                if num_nans == avg.size:
                    location = (threat_name, y, x, lons[y,x], lats[y,x])
                    msg ='%s : all NAN Average risk @ node[%s,%d] (%.5f,%.5f)'
                    print msg % info 
                else:
                    info = (threat_name, len(N.where(N.isnan(avg))[0]), y, x,
                                lons[y,x], lats[y,x])
                    msg = '%s : %d NANs in Average risk @ node[%s,%d] (%.5f %.5f)'
                    print msg % info 

                if num_nans == daily.size:
                    info = (threat_name, y, x, lons[y,x], lats[y,x])
                    msg = '%s : all NAN Daily risk @ node[%s,%d] (%.5f,%.5f)'
                    print msg % info 
                else:
                    info = (threat_name, len(N.where(N.isnan(daily))[0]), y, x,
                            lons[y,x], lats[y,x])
                    msg = '%s : %d NANs in Daily risk @ node[%s,%d] (%.5f,%.5f)'
                    print msg % info 

        return num_files

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatDates(self, avg_dates, daily_dates):
        # key common dates that better be the same between files
        dates = { 'seasonEnd': daily_dates['end_date'].timetuple()[:3],
                  'seasonStart': daily_dates['start_date'].timetuple()[:3],
                }

        # get latest first valid date
        avg_first_valid = avg_dates.get('first_valid_date', avg_dates['start_date'])
        daily_first_valid = daily_dates.get('first_valid_date', daily_dates['start_date'])
        first_valid = max(avg_first_valid, daily_first_valid)
        dates['firstValid'] = first_valid.timetuple()[:3]

        # get the earliest last_valid_date
        avg_last_valid = avg_dates.get('last_valid_date', None)
        daily_last_valid = daily_dates.get('last_valid_date', None)
        if avg_last_valid is None or daily_last_valid is None:
            return None, None, None
        else:
            last_valid = min(avg_last_valid, daily_last_valid)
            dates['lastValid'] = last_valid.timetuple()[:3]

        # forecast dates
        fcast_start = daily_dates.get('fcast_start_date', None)
        if fcast_start is not None:
            dates['fcastStart'] = fcast_start.timetuple()[:3]
            fcast_end = min(daily_dates['fcast_end_date'],last_valid)
            dates['fcastEnd'] = fcast_end.timetuple()[:3]

        # generate the json string for the dates
        json_dates = json.dumps(dates,separators=(',',':'))
        json_dates = json_dates.replace('(','[').replace(')',']')
        return first_valid, last_valid, json_dates

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatRisk(self, data_start, data_end, debug):
        if debug: print 'extracting risk data for', data_start, data_end

        self.avg_reader.open()
        avg_risk = self.avg_reader.timeSlice('risk', data_start, data_end)
        self.avg_reader.close()
        if debug:
            nans = N.where(N.isnan(avg_risk))
            info = (sys.getsizeof(avg_risk), len(nans[0]), N.product(avg_risk.shape))
            print '    average risk dataset : %d bytes : %d NaN of %d elemnts in array' % info

        self.daily_reader.open()
        daily_risk = self.daily_reader.timeSlice('risk', data_start, data_end)
        lats = self.daily_reader.lats
        lons = self.daily_reader.lons
        self.daily_reader.close()
        if debug:
            nans = N.where(N.isnan(daily_risk))
            info = (sys.getsizeof(daily_risk), len(nans[0]), N.product(daily_risk.shape))
            print '    daily risk dataset : %d bytes : %d NaN of %d elemnts in array' % info

        return (avg_risk, daily_risk, lats, lons)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PeriodRiskJsonGenerator(JsonFileGenerator):

    def __init__(self, factory, period, source, region, sub_region=None):
        JsonFileGenerator.__init__(self, factory, source, region, sub_region)
        self.period = period

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, threat, period, target_year, debug=False):
        if debug: print '\nPeriodRiskJsonGenerator'
        self.target_year = target_year
        self.threat = threat

        self.reader = \
            self.factory.threatFileReader(threat, self.period, target_year)
        date_dict = self.reader.dateAttributes('risk', True)
        self.reader.close()
        if debug:
            print '%s %s risk dates:' % (threat, self.period)
            for key, value in date_dict.items():
                print '    %s : %s' % (key,value)

        return self.generateJsonFiles(date_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def generateJsonFiles(self, date_dict):
        factory = self.factory
        region_indexes = self.region_indexes
        threat = self.threat
        
        data_start, data_end, json_datestr = self.threatDates(date_dict)
        # no data available
        if json_datestr is None: return 0

        period = '"%s"' % self.period
        data_template = '{' + period + ":[%(data)s]}"
        params = { 'name':threat, 'lat':'%(lat)s', 'lon':'%(lon)s',
                   'dates':json_datestr, 'data':data_template }
        json_template = factory.threats.json_template % params

        # JSON file path templates
        json_dirpath, json_filename = \
            self.jsonPathTemplates(threat, self.target_year)
        
        # get risk data for period
        risk_data, lats, lons = self.threatRisk(data_start, data_end)

        num_files = 0

        for y, x in region_indexes:
            risk = risk_data[:,y,x]

            if len(N.where(N.isnan(risk))[0]) == 0:
                lat = N.round(lats[y,x],3)
                lon = N.round(lons[y,x],3)
                params = { 'lat':lat, 'lon':lon }
                params['data'] = ','.join(['%d' % value for value in risk])
    
                node_str = factory.gridNodeToFilename((lon,lat))
                filename = json_filename % {'node': node_str,}
                filepath = os.path.join(json_dirpath, filename)
        
                with open(filepath, 'w') as writer:
                    writer.write(json_template % params)

                num_files += 1

            else:
                threat_name = factory.threatName(threat)
                num_nans = len(N.where(N.isnan(risk))[0])
                period = self.period.title()
                if num_nans == risk.size:
                    info = (threat_name, period, y, x, lons[y,x], lats[y,x])
                    msg = '%s : all NAN %s risk @ node[%s,%d] (%.5f, %.5f)'
                else:
                    missing = len(N.where(N.isnan(risk))[0])
                    info = (threat_name, period, missing, y, x,
                            lons[y,x], lats[y,x])
                    msg = '%s : %d NANs in %s risk @ node[%s,%d] (%.5f, %.5f)' 
                print msg % info

        return num_files

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatDates(self, date_dict):
        # key common dates that better be the same between files
        dates = { 'seasonEnd': date_dict['end_date'].timetuple()[:3],
                  'seasonStart': date_dict['start_date'].timetuple()[:3],
                }

        # get the earliest last_valid_date
        last_valid = date_dict.get('last_valid_date', None)
        if last_valid is None: return None, None, None
        else: dates['lastValid'] = last_valid.timetuple()[:3]

        # get latest first valid date
        first_valid = date_dict.get('first_valid_date', date_dict['start_date'])
        dates['firstValid'] = first_valid.timetuple()[:3]

        # forecast dates
        fcast_start = date_dict.get('fcast_start_date', None)
        if fcast_start is not None:
            dates['fcastStart'] = fcast_start.timetuple()[:3]
            fcast_end = min(date_dict['fcast_end_date'],last_valid)
            dates['fcastEnd'] = fcast_end.timetuple()[:3]

        # generate the json string for the dates
        json_dates = json.dumps(dates,separators=(',',':'))
        json_dates = json_dates.replace('(','[').replace(')',']')
        return first_valid, last_valid, json_dates

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def threatRisk(self, data_start, data_end):
        self.reader.open()
        risk = self.reader.timeSlice('risk', data_start, data_end)
        lats = self.reader.lats
        lons = self.reader.lons
        self.reader.close()
        return (risk, lats, lons)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TurfThreatJsonGeneratorFactory(TurfThreatGridFileFactory):

    def riskFileGenerator(self, period, source, region, sub_region=None):
        if period in ('avg,daily','daily,avg'):
            return CommonRiskJsonFileGenerator(self, source, region, sub_region)
        else:
            return PeriodRiskJsonGenerator(self, period, source, region,
                                           sub_region)

