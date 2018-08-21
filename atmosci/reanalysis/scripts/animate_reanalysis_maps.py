#! /usr/bin/env python

import os, sys
import datetime

from turftool.maps.factory import TurfMapFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default=None)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--delay', action='store', type='int', dest='delay',
                  default=30)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
delay = options.delay
dev_mode = options.dev_mode
region_key = options.region
verbose = options.verbose or debug

threat_key = args[0]
num_date_args = len(args) - 1
if len(args) > 1:
    target_year = int(args[1])
else: target_year = datetime.date.today().year

# factory for building and accessing map files
factory = TurfMapFileFactory()
if dev_mode: factory.useDirpathsForMode('dev')
if region_key is None:
    region = factory.regionConfig(factory.project.region)
else: region = factory.regionConfig(region_key)

map_dirpath = factory.turfMapDirpath(threat_key, target_year, region)
if debug: print '  map dirpath :', map_dirpath

file_template = factory.turfMapFilename(threat_key, None, region)
map_filename = file_template.replace('||DATE||','*')
if debug: print ' map filename :', map_filename

animation_filepath = \
    factory.turfAnimationFilepath(threat_key, target_year, region)
if debug: print 'anim filepath :', animation_filepath


animate_cmd_template = factory.maps.animate_command
if debug: print ' cmd template :', animate_cmd_template
command = animate_cmd_template % (delay, map_filename, animation_filepath)
print '\n', command

os.chdir(map_dirpath)
os.system(command)

