#! /usr/bin/env python

import os, sys
from copy import copy
import subprocess, shlex

import datetime
UPDATE_START_TIME = datetime.datetime.now()

#from atmosci.utils.report import Reporter
from atmosci.utils.timeutils import elapsedTime

from turf.threats.config import THREATS
from turf.controls.config import CONFIG as CONTROLS


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#CRON_SCRIPT_DIR = '/Users/rrem63/venvs/frost/cron'
CRON_SCRIPT_DIR = os.path.split(os.path.abspath(sys.argv[0]))[0]
PYTHON_EXECUTABLE = sys.executable


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

AS_MSG = 'ACTIVE SCRIPT : %s %s'
CALL_MSG = 'called %s for %s'
FAILURE = '%s for %s failed with return code %d'
IP_MSG = 'INITIATE PROCESS : %s %s for %s'
SUCCESS = 'COMPLETED : %s'


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DummyProcess(object):

    def __init__(self):
        self.returncode = 0

    def poll(self): pass


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ProcessServer(object):

    PROCESS_INIT_METHODS = {}

    def __init__(self, model, dev_mode, debug, test_run):
        self.active_script = None
        self.debug = debug
        self.dev_mode = dev_mode
        #self.reporter = reporter
        self.test_run = test_run

        scripts = [ ]
        if model in THREATS.keys():
            scripts.append( ('json', ('threat', model)) )
            scripts.append( ('threat_maps', (model, 'daily')) )
            scripts.append( ('threat', (model,)) )
        else:
            scripts.append( ('json', ('control', model)) )
            for treatment in CONTROLS.controls[model].treatments.keys():
                scripts.append( ('ctrl_maps', (model, treatment)) )

        self.all_scripts = tuple(scripts)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run(self):
        debug = self.debug
        self.process_queue = list(self.all_scripts)
        if debug:
            print '\nrun process queue'
            print self.process_queue

        keep_on_trucking = True
        active_process = None

        while keep_on_trucking:
            # service active process
            if active_process is not None:
                active_process.poll()
                retcode = active_process.returncode
                if retcode is not None:
                    active_process =\
                        self.completeProcess(active_process, retcode)
                    if active_process is None:
                        print 'Completed update of', str(active_process)
                        keep_on_trucking = False
            else:
                process = self.nextProcess()
                if debug: print 'next script :', process
                active_process = self.initiateProcess(process)

        #self.reporter.logEvent('MODEL PROCESS SERVER EXITING')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def completeProcess(self, active_process, retcode):
        # reporter = self.reporter
        if retcode <= 0:
            print SUCCESS % str(self.active_script)
            #reporter.logEvent(SUCCESS % self.active_script)
        else:
            #errmsg = FAILURE % (self.active_script, retcode)
            #reporter.logError(errmsg)
            #reporter.reportError(errmsg)
            exit()

        next_process = self.nextProcess()
        if next_process is not None:
            return self.initiateProcess(next_process)
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initiateProcess(self, process):
        if process is not None:
            self.active_process = process
            initProcess = self.PROCESS_INIT_METHODS[process[0]]
            args = process[1]
            if args: return initProcess(self, *args)
            else: return initProcess(self)
        else: return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def nextProcess(self):
        if self.process_queue:
            return self.process_queue.pop()
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def runSubprocess(self, script, args):
        #self.reporter.logEvent(AS_MSG % (script,args))
        command = [PYTHON_EXECUTABLE, os.path.join(CRON_SCRIPT_DIR, script)]
        command.extend(args.split())
        if self.debug: print 'command :', command
        self.active_script = script
        return subprocess.Popen(command, shell=False, env=os.environ)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initiateThreatModelUpdate(self, model):
        if self.debug:
            print '\ninitiateThreatModelUpdate', model
            #self.reporter.logInfo(CALL_MSG % ('initiateThreatModelUpdate', model))
        if self.test_run: return DummyProcess()
        script = 'update_turf_threat_files.py'
        args = '%s' %  model
        if self.dev_mode: args += ' -d'
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['threat'] = initiateThreatModelUpdate

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initiateDrawControlMaps(self, model, treatment):
        if self.debug:
            info = '%s %s' % (model, treatment)
            print '\initiateDrawControlMaps', info
            #self.reporter.logInfo(CALL_MSG % ('initiateDrawControlMaps', info))
        if self.test_run: return DummyProcess()
        script = 'draw_turf_control_stage_maps.py'
        args = '%s %s' % (model, treatment)
        if self.dev_mode: args += ' -d'
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['ctrl_maps'] = initiateDrawControlMaps

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initiateDrawiThreatMaps(self, model, period):
        if self.debug:
            info = '%s %s' % (model, period)
            print '\initiateDrawGDDMaps', info
            #self.reporter.logInfo(CALL_MSG % ('initiateDrawiThreatMaps', info))
        if self.test_run: return DummyProcess()
        script = 'draw_turf_threat_risk_maps.py'
        args = '%s %s' % ( model, period)
        if self.dev_mode: args += ' -d'
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['threat_maps'] = initiateDrawiThreatMaps

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initiateBuildJsonFiles(self, group, model):
        if self.debug:
            info = '%s %s' % (group, model)
            print '\initiateBuildJsonFiles', info
            #self.reporter.logInfo(CALL_MSG % ('initiateBuildJson', info))
        if self.test_run: return DummyProcess()
        if group == 'control':
            script = 'generate_controls_json_files.py'
        else: script = 'generate_threat_json_files.py'
        args = '%s' % model
        if self.dev_mode: args += ' -d'
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['json'] = initiateBuildJsonFiles


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser = OptionParser(usage="usage: model [options]")
parser.add_option('--mrt', action='store', type='string', dest='max_run_time',
                  default=None)

parser.add_option('-l', action='store', type='string', dest='log_filepath',
                  default=None,
                  help='path to alternate file to be used for logging')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
test_run = options.test_run
if test_run: debug = True

if options.max_run_time is not None:
    max_run_time = options.max_run_time
    if max_run_time[-1] == ':':
        max_run_hours = int(max_run_time[:-1])
        max_run_minutes = 0
    elif max_run_time[0] == ':':
        max_run_hours = 0
        max_run_minutes = int(max_run_time[1:])
    else:
        colon = max_run_time.find(':')
        if colon > 0:
            max_run_hours = int(max_run_time[:colon])
            max_run_minutes = int(max_run_time[colon+1:])
        else:
            max_run_hours = int(max_run_time)
            max_run_minutes = 0
    max_run_time = datetime.timedelta(hours=max_run_hours,
                                      minutes=max_run_minutes)
    quit_time = datetime.datetime.now() + max_run_time
    if debug: print 'server quit time', quit_time
else:
    quit_time = None


model = args[0]
process_server = ProcessServer(model, dev_mode, debug, test_run)
if test_run:
    print 'ProcessServer.scripts :\n', process_server.all_scripts

elapsed_time = elapsedTime(UPDATE_START_TIME, True)
if quit_time is None or datetime.datetime.now() < quit_time:
    process_server.run()
    print 'Updates for %s completed in %s' % (model.title(), elapsed_time)
else:
    print 'Processing time limit exceeded.'
    print 'Update failed after', elapsedTime

