#! /usr/bin/env python

import datetime
SCRIPT_START_TIME = datetime.datetime.now()

import warnings

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime, lastDayOfMonth

from turf.threats.smart_models import SmartThreatModelFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

HOURS_IN_DAY = datetime.timedelta(hours=24)
HOURS_TO_START = datetime.timedelta(hours=23)
ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(days=1)
TODAY = datetime.date.today()
YESTERDAY = TODAY - ONE_DAY

LAST_DAY_OF_MONTH = datetime.date(TODAY.year, TODAY.month, lastDayOfMonth(TODAY.year, TODAY.month))
FIRST_DAY_NEXT_MONTH = LAST_DAY_OF_MONTH + ONE_DAY


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

usage = '%prog [date] [options]'
usage += '\n    When passing dates without year :'
usage += '\n       %prog [day_in_current_month] [options]'
usage += '\n       %prog [month day] [options]'
usage += '\n       %prog [month 1st_day last_day] [options]'
usage += '\n       %prog [1st_month day last_month day] [options]'
usage += '\n    When passing dates with year :'
usage += '\n       %prog [year month day] [options]'
usage += '\n       %prog [year month 1st_day last_day] [options]'
usage += '\n       %prog [year 1st_month day last_month day] [options]'
usage += '\n\nno date args passed : update all days since perevious analysis.'

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-f', action='store', type=int, dest='fcast_days', default=7,
       help='Number of days in the forecast(default=7)')

parser.add_option('-m', action='store', dest='models', default='anthrac,bpatch,dspot,hstress,pblight',
       help='list of models to run (default="anthrac,bpatch,dspot,hstress,pblight")')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False,
       help='boolean: use development data paths (default=False)')

parser.add_option('-r', action='store_true', dest='replace_prev', default=False,
       help='boolean: replace previous analysis/forecast day (default=False)')

parser.add_option('-v', action='store_true', dest='verbose', default=False,
       help='boolean: print verbose output (default=False)')

parser.add_option('-z', action='store_true', dest='debug', default=False,
       help='boolean: print debug output (default=False)')

options, args = parser.parse_args()

debug = options.debug
dev_mode = options.dev_mode
fcast_days = datetime.timedelta(options.fcast_days-1)
replace_prev = options.replace_prev
threat_models = options.models.split(',')
verbose = options.verbose or debug


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def endTimeForDate(factory, threat_key, date):
    day_ends = datetime.datetime.combine(date+ONE_DAY, factory.threatDayEnds(threat_key))
    return tzutils.asUTCTime(day_ends, 'US/Eastern')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def maxForecastEndTime(factory, threat_key):
    end_date = TODAY + datetime.timedelta(days=factory.project.fcast_days-1)
    return endTimeForDate(factory, threat_key, end_date)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def maxReanalysisEndTime(factory, threat_key):
    now_utc = tzutils.asUTCTime(datetime.datetime.now(), 'US/Eastern')
    day_ends = endTimeForDate(factory, threat_key, YESTERDAY)
    if now_utc >= day_ends: return day_ends
    return day_ends - HOURS_IN_DAY

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def modelDataStartTime(factory, threat_key, period_key, date):
    day_starts = startTimeForDate(factory, threat_key, date)
    padding_hours = factory.threatPaddingHours(threat_key, period_key)
    if padding_hours > 0: day_starts -= datetime.timedelta(hours=padding_hours)
    return day_starts

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def startTimeForDate(factory, threat_key, date):
    day_starts = datetime.datetime.combine(date, factory.threatDayEnds(threat_key)) + ONE_HOUR
    return tzutils.asUTCTime(day_starts, 'US/Eastern')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def reportUpdate(source, threat_fullname, period_name, start_date, index_end, risk_end):
    info = (threat_fullname, period_name, source)
    print '    Completed update of %s %s %s risk.' % info
    info = (start_date.strftime('%Y-%m-%d'), index_end.strftime('%Y-%m-%d'))
    print '        Threat index dataset time span : %s thru %s' % info
    info = (start_date.strftime('%Y-%m-%d'), risk_end.strftime('%Y-%m-%d'))
    print '        Risk dataset time span : %s thru %s' % info

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def timeString(time_obj): return time_obj.strftime('%Y-%m-%d:%H')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def runThreatModel(factory, threat_key, period_key, start_date, model_start_time,
                   model_end_time, is_analysis, debug):
    # get the appropriate threat model
    model = factory.riskModel(threat_key, model_start_time.date(), period_key, debug)

    # get all data for model
    model_data = factory.getModelWeatherData(threat_key, model_start_time, model_end_time)

    # filter annoying numpy warnings
    warnings.filterwarnings('ignore',"All-NaN axis encountered")
    warnings.filterwarnings('ignore',"All-NaN slice encountered")
    warnings.filterwarnings('ignore',"invalid value encountered in greater")
    warnings.filterwarnings('ignore',"invalid value encountered in less")
    warnings.filterwarnings('ignore',"Mean of empty slice")
    # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

    # run the model's threat index calculator
    if threat_key == 'hstress':
        index_dataset = 'stress'
        index = model.stressHours(*model_data)
    else:
        index_dataset = 'threat'
        index = model.threatIndex(*model_data)

    if debug:
        print '   index grid shape :', index.shape
        print '\nThreat index summary :'
        risk_thresholds = list(factory.riskThresholds(threat_key, period_key))
        risk_thresholds.reverse()
        prev_threshold = risk_thresholds[0]
        prev_count = len(N.where(index > prev_threshold)[0])
        print '    %6d nodes with index > %.1f' % (prev_count, prev_threshold)

        for threshold in risk_thresholds[1:]:
            count = len(N.where(index > threshold)[0]) - prev_count
            print '    %6d nodes with %.1f <= index > %.1f' % (count, prev_threshold, threshold)
            prev_count = count
            prev_threshold = threshold

        count = len(N.where(index < 0.)[0])
        print '    %6d nodes with index < 0.' % count

    # update the threat index dataset
    manager = factory.threatFileManager(threat_key, period_key, start_date.year)
    if is_analysis:
        index_end_date = manager.updateReanalysis(index_dataset, start_date, index)
    else: index_end_date = manager.updateForecast(index_dataset, start_date, index)
    manager.close()

    # run the model's risk calculator
    risk_level = model.riskLevel(index)
    
    if debug:
        print '\nRisk level summary :'
        risk_thresholds = list(factory.riskThresholds(threat_key, period_key))
        for level in range(len(risk_thresholds)):
            count = len(N.where(risk_level == level)[0])
            print '    %6d nodes with risk level == %d' % (count, level)
        print ' '

    # update the threat risk dateset
    manager.open('a')
    if is_analysis:
        risk_end_date = manager.updateReanalysis('risk', start_date, risk_level)
    else: risk_end_date = manager.updateForecast('risk', start_date, risk_level)
    manager.close()

    # turn annoying numpy warnings back on
    warnings.resetwarnings()

    return index_end_date, risk_end_date


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateReanalysis(factory, threat_key, period_key, start_date, end_date, verbose, debug):
    start_time = modelDataStartTime(factory, threat_key, period_key, start_date)
    end_time = endTimeForDate(factory, threat_key, end_date)
    num_hours = tzutils.hoursInTimespan(start_time, end_time)
    threat_fullname = factory.threatName(threat_key)

    if debug:
        details = (threat_fullname, period_key.title())
        print '\nEstimated time period required to update %s %s reanalysis :' % details
        print '      weather start :', start_time
        print '        weather end :', end_time
        print '  num weather hours :', num_hours
        print '   num weather days :', num_hours / 24
        print 'num reanalysis days :', (end_date - start_date).days + 1

    # run the model and save the results
    index_end, risk_end = runThreatModel(factory, threat_key, period_key, start_date, start_time, end_time, True, debug)
    reportUpdate('reanalysis', threat_fullname, period_key, start_date, index_end, risk_end)
    if debug:
        info = (num_hours, start_time.strftime('%Y-%m-%d:%H'), end_time.strftime('%Y-%m-%d:%H'))
        print 'Updated %d reanalysis data hours : %s thru %s' % info

    return start_date, risk_end


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateTurfModelFiles(factory, threat_key, replace_prev, verbose, debug):
    threat_fullname = factory.threatName(threat_key)

    if threat_key == 'hstress': periods = ('daily',)
    else: periods = ('daily', 'average')
    num_periods = len(periods)

    MODEL_START_TIME = datetime.datetime.now()

    common_obs_end = factory.commonObsEnd(threat_key, TODAY)
    max_obs_end = maxReanalysisEndTime(factory, threat_key)
    while max_obs_end > common_obs_end: # most common case
        max_obs_end -= HOURS_IN_DAY
    max_obs_start = max_obs_end - HOURS_TO_START
    max_obs_date = max_obs_start.date()

    if debug:
        print '\nupdateTurfModelFiles debug info >>'
        print '     commonObsEnd :', common_obs_end
        print '      max_obs_end :', max_obs_end
        print '    max_obs_start :', max_obs_start
        print '     max_obs_date :', max_obs_date

    max_fcast_time = maxForecastEndTime(factory, threat_key)
    common_fcast_end = factory.commonFcastEnd(threat_key, max_fcast_time)

    if debug:
        print '   max_fcast_time :', max_fcast_time
        print '   commonFcastEnd :', common_fcast_end

    print '\nProcessing %s risk :' % threat_fullname

    period_count = 0
    for period_key in periods:
        PERIOD_START_TIME = datetime.datetime.now()

        key_dates = updateTurfModelPeriod(threat_key, period_key, max_obs_date, common_fcast_end, max_fcast_time, verbose, debug)
        # period_start, fcast_start, period_end = key_dates

        elapsed_time = elapsedTime(PERIOD_START_TIME, True)
        print '    Completed %s %s grid file update in %s' % (threat_fullname, period_key.title(), elapsed_time)
        if verbose:
            print '        data start = %s : fcast start = %s : data end = %s' % key_dates

        period_count += 1
        if period_count < num_periods: print ' '


    elapsed_time = elapsedTime(MODEL_START_TIME, True)
    print '\nCompleted %s grid updates in %s' % (threat_fullname, elapsed_time)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateTurfModelPeriod(threat_key, period_key, max_obs_date, common_fcast_end, max_fcast_time, verbose, debug):
    threat_fullname = factory.threatName(threat_key)
    period_name = period_key.title()

    if not factory.threatFileExists(threat_key, period_key, TODAY.year):
        factory.buildThreatGridFile(threat_key, period_key, TODAY, 'acis')

    if replace_prev:
        start_date = end_date = factory.threatDateAttribute(threat_key, period_key, TODAY.year, 'last_obs_date', 'risk')
        print '   replacing previous %s %s reanalysis for %s' % (threat_fullname, period_name, str(start_date))
        risk_start, risk_end = updateReanalysis(factory, threat_key, period_key, start_date, end_date, verbose, debug)
        reportUpdate('forecast', threat_fullname, period_name, risk_start, index_end, risk_end)

    else:
        last_obs_date = factory.threatDateAttribute(threat_key, period_key, TODAY.year, 'last_obs_date', 'risk')
        if debug:
            print '\nupdateTurfModelPeriod debug info >>'
            print '           threat :', threat_key
            print '           period :', period_key
            print '    last_obs_date :', last_obs_date
            print ' '

        if last_obs_date < max_obs_date:
            end_date = max_obs_date
            start_date = min(end_date, last_obs_date + ONE_DAY)
            if debug: print '    updating reanalysis for %s thru %s' % (start_date, end_date)
            risk_start, risk_end = updateReanalysis(factory, threat_key, period_key, start_date, end_date, verbose, debug)
        else:
            print '%s %s reanalsysis data is already up to date' % (threat_fullname, period_name)
            risk_end = last_obs_date
            start_date = risk_end + ONE_DAY

    # run the model with a forecast
    fcast_start = risk_end + ONE_DAY
    fcast_start_time = modelDataStartTime(factory, threat_key, period_key, fcast_start)

    fcast_end_time = max_fcast_time
    while fcast_end_time > common_fcast_end: # most common case
        fcast_end_time -= HOURS_IN_DAY
    num_hours = tzutils.hoursInTimespan(fcast_start_time, fcast_end_time)

    if verbose:
        print '\n Updating %s %s risk forecast :' % (threat_fullname, period_name)
        print ' forecast start date :', fcast_start
        print '       weather start :', fcast_start_time
        print '         weather end :', fcast_end_time
        print '   num weather hours :', num_hours
        print '    num weather days :', num_hours / 24
        fcast_end = fcast_end_time.date() - ONE_DAY
        print '   num forecast days :', (fcast_end - fcast_start).days + 1
        print ' '

    # run the model and save the results
    index_end, risk_end = runThreatModel(factory, threat_key, period_key, fcast_start, fcast_start_time, fcast_end_time, False, debug)
    reportUpdate('forecast', threat_fullname, period_name, fcast_start, index_end, risk_end)
    if debug:
        info = (num_hours, fcast_start_time.strftime('%Y-%m-%d:%H'), fcast_end_time.strftime('%Y-%m-%d:%H'))
        print '        Processed %d raw forecast hours: %s thru %s' % info

    return start_date, fcast_start, risk_end


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# MAIN PROGRAM
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# create a factory for access to the threat file
factory = SmartThreatModelFactory()
if dev_mode: factory.useDirpathsForMode('dev')

for threat_key in threat_models:
    updateTurfModelFiles(factory, threat_key, replace_prev, verbose, debug)

elapsed_time = elapsedTime(SCRIPT_START_TIME, True)
print '\nCompleted turf model updates in %s' % elapsed_time

