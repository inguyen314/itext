from hec.data import DataSetIllegalArgumentException
from hec.data import Units
from hec.data.tx import QualityTx
from hec.heclib.util import HecTime
from hec.io import Conversion
from hec.lang import Const
from java.lang import System
from java.text import SimpleDateFormat
from java.util import Calendar
from java.util import TimeZone
import DBAPI
import fnmatch
import os
import socket
import string
import StringIO
import sys
import time
import traceback
import types
#-------------------------#
# set up global variables #
#-------------------------#
infile =sys.stdin
outfile=sys.stdout
errfile=sys.stderr

PROGRAM_HISTORY = [
   ["1.50 16Sep2019", "Fixed problems with value formats"],
   ["1.40 15Jul2019", "Removed DBI compatibility"],
   ["1.30 23Sep2011", "Added ability to use CWMS 2.x database via DB command line parameter"],
   ["1.20 13Dec2006", "Fixed problem with null quality; added DETAILED exception tracebacks"],
   ["1.10 15Apr2004", "Added OFFSET export modifier; udated to SHEF 2.0"],
   ["1.01 15Oct2004", "Fixed problem with using non-standard PE codes"],
   ["1.00 16Sep2004", "Original Version"]
]
PROGRAM_VERSION = PROGRAM_HISTORY[0][0]

NONE, BASIC, DETAILED, VERBOSE = 0, 1, 2, 3

SIGNIFICANT_DIGITS = 5

MASK = "-MASK-"

test_mode = False

log_level = BASIC

log_level_names = ["None", "Basic", "Detailed", "Verbose"]

missing_values = ["+", "m", "M", "-9999", "-9002"]

missing_value = "M"

output_formats = {"*" : "5"}

quality = {
   "BAD"        : "B",
   "ESTIMATED"  : "E",
   "GOOD"       : "G",
   "MANUAL"     : "M",
   "QUESTIONED" : "Q",
   "REJECTED"   : "R",
   "SCREENED"   : "S",
   "UNKNOWN"    : "Z"}

quality_keys = quality.keys()
quality_values = quality.values()

quality_level = "BERQ"

commands = {
   "DB"         : 'open_db("%s")',
   "DEBUG"      : 'set_log_level(%s)',
   "DELIMITER"  : "set_SHEF_delimiter('%s')",
   "FORMAT"     : 'set_output_format("%s")',
   "GROUP"      : 'set_grouping(%s)',
   "INCLUDE"    : 'process_input("%s")',
   "LINEWIDTH"  : 'set_output_linewidth("%s")',
   "LOCATION"   : 'map_location("%s")',
   "MISSING"    : 'set_missing_value("%s")',
   "OUTPUT"     : 'output_text("%s")',
   "PE"         : 'map_PE_code("%s")',
   "QUALITY"    : 'set_output_quality("%s")',
   "REVISED"    : 'set_revision_flag(%s)',
   "SYSTEM"     : 'set_output_units_system("%s")',
   "TIMEWINDOW" : 'set_time_window("%s")',
   "TS"         : 'map_TS_code("%s")',
   "TYPE"       : 'set_output_message_type("%s")',
   "TZONE"      : 'set_output_timezone("%s")'}

command_keys = commands.keys()
command_keys.sort()

export_modifiers = [
   "FACTOR",
   "LOCATION",
   "OFFSET",
   "PARAMETER",
   "TZONE",
   "UNITS"]

default_tz = TimeZone.getDefault()
default_output_tz = TimeZone.getTimeZone("UTC")
output_tz_name = "Z"

tz_ids = TimeZone.getAvailableIDs()

# SHEF Code    Java TimeZone ID         SHEF Location
#-----------   ---------------------    -----------------------
timezones = {
   "N"  : "Canada/Newfoundland", # Newfoundland local
   "NS" : "GMT-03:30",           # Newfoundland standard
   "A"  : "Canada/Atlantic",     # Atlantic local
   "AD" : "GMT-03:00",           # Atlantic daylight
   "AS" : "GMT-04:00",           # Atlantic standard
   "E"  : "US/Eastern",          # Eastern local
   "ED" : "GMT-04:00",           # Eastern daylight
   "ES" : "GMT-05:00",           # Eastern standard
   "C"  : "US/Central",          # Central
   "CD" : "GMT-05:00",           # Central daylight
   "CS" : "GMT-06:00",           # Central standard
   "J"  : "CTT",                 # China
   "M"  : "US/Mountain",         # Mountain local
   "MD" : "GMT-06:00",           # Mountain daylight
   "MS" : "GMT-07:00",           # Mountain standard
   "P"  : "US/Pacific",          # Pacific local
   "PD" : "GMT-07:00",           # Pacific daylight
   "PS" : "GMT-08:00",           # Pacific standard
   "Y"  : "Canada/Yukon",        # Yukon local
   "YD" : "GMT-07:00",           # Yukon daylight
   "YS" : "GMT-08:00",           # Yukon standard
   "H"  : "US/Hawaii",           # Hawaiian local
   "HS" : "US/Hawaii",           # Hawaiian standard
   "L"  : "US/Alaska",           # Alaskan local
   "LD" : "GMT-08:00",           # Alaskan daylight
   "LS" : "GMT-09:00",           # Alaskan standard
   "B"  : "Pacific/Midway",      # Bering local
   #"BD" : "???",                # Bering daylight
   "BS" : "Pacific/Midway",      # Bering standard
   "Z"  : "UTC"}                 # Zulu

#  Standard     Standard   Standard
#   SHEF PE      English     Metric
#      code        units      units
#  --------     --------   --------
shef_units = {
   "AD" : ("<none>" , "<none>" ),
   "AF" : ("<coded>", "<coded>"),
   "AG" : ("%"      , "%"      ),
   "AM" : ("<coded>", "<coded>"),
   "AT" : ("<coded>", "<coded>"),
   "AU" : ("<coded>", "<coded>"),
   "AW" : ("<coded>", "<coded>"),
   "BA" : ("IN"     , "MM"     ),
   "BB" : ("IN"     , "MM"     ),
   "BC" : ("IN"     , "MM"     ),
   "BD" : ("DF"     , "DC"     ),
   "BE" : ("IN"     , "MM"     ),
   "BF" : ("IN"     , "MM"     ),
   "BG" : ("%"      , "%"      ),
   "BH" : ("IN"     , "MM"     ),
   "BI" : ("IN"     , "MM"     ),
   "BJ" : ("IN"     , "MM"     ),
   "BK" : ("IN"     , "MM"     ),
   "BL" : ("IN"     , "MM"     ),
   "BM" : ("IN"     , "MM"     ),
   "BN" : ("IN"     , "MM"     ),
   "BO" : ("IN"     , "MM"     ),
   "BP" : ("IN"     , "MM"     ),
   "BQ" : ("IN"     , "MM"     ),
   "CA" : ("IN"     , "MM"     ),
   "CB" : ("IN"     , "MM"     ),
   "CC" : ("IN"     , "MM"     ),
   "CD" : ("IN"     , "MM"     ),
   "CE" : ("IN"     , "MM"     ),
   "CF" : ("IN"     , "MM"     ),
   "CG" : ("IN"     , "MM"     ),
   "CH" : ("IN"     , "MM"     ),
   "CI" : ("IN"     , "MM"     ),
   "CJ" : ("IN"     , "MM"     ),
   "CK" : ("IN"     , "MM"     ),
   "CL" : ("DF"     , "DC"     ),
   "CM" : ("DF"     , "DC"     ),
   "CN" : ("%"      , "%"      ),
   "CO" : ("<none>" , "<none>" ),
   "CP" : ("IN"     , "MM"     ),
   "CQ" : ("IN"     , "MM"     ),
   "CR" : ("IN"     , "MM"     ),
   "CS" : ("IN"     , "MM"     ),
   "CT" : ("<none>" , "<none>" ),
   "CU" : ("DF"     , "DC"     ),
   "CV" : ("DF"     , "DC"     ),
   "CW" : ("IN"     , "MM"     ),
   "CX" : ("IN"     , "MM"     ),
   "CY" : ("IN"     , "MM"     ),
   "CZ" : ("<none>" , "<none>" ),
   "EA" : ("IN"     , "MM"     ),
   "ED" : ("IN"     , "MM"     ),
   "EM" : ("IN"     , "MM"     ),
   "EP" : ("IN"     , "MM"     ),
   "ER" : ("IN/DAY" , "MM/DAY" ),
   "ET" : ("IN"     , "MM"     ),
   "EV" : ("IN"     , "MM"     ),
   "FA" : ("<none>" , "<none>" ),
   "FB" : ("<none>" , "<none>" ),
   "FC" : ("<none>" , "<none>" ),
   "FE" : ("<none>" , "<none>" ),
   "FK" : ("<none>" , "<none>" ),
   "FL" : ("<none>" , "<none>" ),
   "FP" : ("<none>" , "<none>" ),
   "FS" : ("<none>" , "<none>" ),
   "FT" : ("<none>" , "<none>" ),
   "FZ" : ("<none>" , "<none>" ),
   "GD" : ("IN"     , "MM"     ),
   "GR" : ("<coded>", "<coded>"),
   "GS" : ("<coded>", "<coded>"),
   "GT" : ("IN"     , "MM"     ),
   "HA" : ("FT"     , "M"      ),
   "HB" : ("FT"     , "M"      ),
   "HC" : ("FT"     , "M"      ),
   "HD" : ("FT"     , "M"      ),
   "HE" : ("FT"     , "M"      ),
   "HF" : ("FT"     , "M"      ),
   "HG" : ("FT"     , "M"      ),
   "HH" : ("FT"     , "M"      ),
   "HI" : ("<coded>", "<coded>"),
   "HJ" : ("FT"     , "M"      ),
   "HK" : ("FT"     , "M"      ),
   "HL" : ("FT"     , "M"      ),
   "HM" : ("FT"     , "M"      ),
   "HO" : ("FT"     , "M"      ),
   "HP" : ("FT"     , "M"      ),
   "HQ" : ("FT"     , "M"      ),
   "HR" : ("FT"     , "M"      ),
   "HS" : ("FT"     , "M"      ),
   "HT" : ("FT"     , "M"      ),
   "HU" : ("FT"     , "M"      ),
   "HW" : ("FT"     , "M"      ),
   "HZ" : ("KFT"    , "KM"     ),
   "IC" : ("%"      , "%"      ),
   "IE" : ("MI"     , "KM"     ),
   "IO" : ("FT"     , "M"      ),
   "IR" : ("<coded>", "<coded>"),
   "IT" : ("IN"     , "CM"     ),
   "LA" : ("KAC"    , "KM2"    ),
   "LC" : ("KAF"    , "MCM"    ),
   "LS" : ("KAF"    , "MCM"    ),
   "MD" : ("<coded>", "<coded>"),
   "MI" : ("IN"     , "CM"     ),
   "ML" : ("IN"     , "CM"     ),
   "MM" : ("%"      , "%"      ),
   "MN" : ("<coded>", "<coded>"),
   "MS" : ("IN"     , "MM"     ),
   "MT" : ("DF"     , "DC"     ),
   "MU" : ("IN"     , "CM"     ),
   "MV" : ("<coded>", "<coded>"),
   "MW" : ("%"      , "%"      ),
   "NC" : ("<coded>", "<coded>"),
   "NG" : ("FT"     , "M"      ),
   "NL" : ("<none>" , "<none>" ),
   "NN" : ("<none>" , "<none>" ),
   "NO" : ("<coded>", "<coded>"),
   "NS" : ("<none>" , "<none>" ),
   "PA" : ("IN-HG"  , "KPA"    ),
   "PC" : ("IN"     , "MM"     ),
   "PD" : ("IN-HG"  , "KPA"    ),
   "PE" : ("IN-HG"  , "KPA"    ),
   "PL" : ("IN-HG"  , "KPA"    ),
   "PM" : ("<coded>", "<coded>"),
   "PN" : ("IN"     , "MM"     ),
   "PP" : ("IN"     , "MM"     ),
   "PR" : ("IN/DAY" , "MM/DAY" ),
   "PT" : ("<coded>", "<coded>"),
   "QA" : ("KCFS"   , "CMS"    ),
   "QB" : ("IN"     , "MM"     ),
   "QC" : ("KAF"    , "MCM"    ),
   "QD" : ("KCFS"   , "CMS"    ),
   "QE" : ("%"      , "%"      ),
   "QF" : ("MPH"    , "KPH"    ),
   "QG" : ("KCFS"   , "CMS"    ),
   "QI" : ("KCFS"   , "CMS"    ),
   "QL" : ("KCFS"   , "CMS"    ),
   "QM" : ("KCFS"   , "CMS"    ),
   "QP" : ("KCFS"   , "CMS"    ),
   "QR" : ("KCFS"   , "CMS"    ),
   "QS" : ("KCFS"   , "CMS"    ),
   "QT" : ("KCFS"   , "CMS"    ),
   "QU" : ("KCFS"   , "CMS"    ),
   "QV" : ("KAF"    , "MCM"    ),
   "RA" : ("%"      , "%"      ),
   "RI" : ("LY"     , "LY"     ),
   "RN" : ("W/M2"   , "W/M2"   ),
   "RP" : ("%"      , "%"      ),
   "RT" : ("HRS"    , "HRS"    ),
   "SA" : ("%"      , "%"      ),
   "SD" : ("IN"     , "CM"     ),
   "SF" : ("IN"     , "CM"     ),
   "SI" : ("IN"     , "CM"     ),
   "SL" : ("KFT"    , "M"      ),
   "SR" : ("<coded>", "<coded>"),
   "SS" : ("<none> ", "<none>" ),
   "ST" : ("<coded>", "<coded>"),
   "SW" : ("IN"     , "MM"     ),
   "TA" : ("DF"     , "DC"     ),
   "TB" : ("<coded>", "<coded>"),
   "TC" : ("DF"     , "DC"     ),
   "TD" : ("DF"     , "DC"     ),
   "TE" : ("<coded>", "<coded>"),
   "TF" : ("DF"     , "DC"     ),
   "TH" : ("DF"     , "DC"     ),
   "TM" : ("DF"     , "DC"     ),
   "TP" : ("DF"     , "DC"     ),
   "TS" : ("DF"     , "DC"     ),
   "TV" : ("DF"     , "DC"     ),
   "TW" : ("DF"     , "DC"     ),
   "UC" : ("MI"     , "KM"     ),
   "UD" : ("D*10"   , "D*10"   ),
   "UG" : ("MPH"    , "M/S"    ),
   "UL" : ("MI"     , "KM"     ),
   "UP" : ("MPH"    , "M/S"    ),
   "UQ" : ("<coded>", "<coded>"),
   "UR" : ("D*10"   , "D*10"   ),
   "US" : ("MPH"    , "M/S"    ),
   "VB" : ("V"      , "V"      ),
   "VC" : ("MW"     , "MW"     ),
   "VE" : ("MWH"    , "MWH"    ),
   "VG" : ("MW"     , "MW"     ),
   "VH" : ("HRS"    , "HRS"    ),
   "VJ" : ("MWH"    , "MWH"    ),
   "VK" : ("<coded>", "<coded>"),
   "VL" : ("<coded>", "<coded>"),
   "VM" : ("<coded>", "<coded>"),
   "VP" : ("MW"     , "MW"     ),
   "VQ" : ("MWH"    , "MWH"    ),
   "VR" : ("<coded>", "<coded>"),
   "VS" : ("MWH"    , "MWH"    ),
   "VT" : ("MW"     , "MW"     ),
   "VU" : ("<coded>", "<coded>"),
   "VW" : ("MW"     , "MW"     ),
   "WA" : ("PPM"    , "MG/L"   ),
   "WC" : ("UMHO/CM", "UMHO/CM"),
   "WD" : ("IN"     , "CM"     ),
   "WG" : ("IN-HG"  , "MM-HG"  ),
   "WH" : ("PPM"    , "MG/L"   ),
   "WL" : ("PPM"    , "MG/L"   ),
   "WO" : ("PPM"    , "MG/L"   ),
   "WP" : ("<none>" , "<none>" ),
   "WT" : ("JTU"    , "JTU"    ),
   "WV" : ("FT/S"   , "M/S"    ),
   "XC" : ("TENTHS" , "TENTHS" ),
   "XG" : ("<none>" , "<none>" ),
   "XL" : ("<none>" , "<none>" ),
   "XP" : ("<coded>", "<coded>"),
   "XR" : ("%"      , "%"      ),
   "XU" : ("G/FT3"  , "G/M3"   ),
   "XV" : ("MI"     , "KM"     ),
   "XW" : ("<coded>", "<coded>"),
   "YA" : ("<none>" , "<none>" ),
   "YC" : ("<none>" , "<none>" ),
   "YF" : ("W"      , "W"      ),
   "YR" : ("W"      , "W"      ),
   "YS" : ("<none>" , "<none>" ),
   "YT" : ("<none>" , "<none>" )}

standard_pe_codes = shef_units.keys()
standard_pe_codes.sort()

#     Code   Value   Description
#    -----   -----   -------------------------------------------------------
shef_durations = {
   "A" : (1008, "8 Hours"),
   "B" : (1002, "2 Hours"),
   "C" : (15  , "15 Minutes"),
   "D" : (2001, "1 Day"),
   "F" : (1004, "4 Hours"),
   "H" : (1001, "1 Hour"),
   "I" : (0   , "Instantaneous"),
   "J" : (30  , "30 Minutes"),
   "K" : (1012, "12 Hours"),
   "L" : (1018, "18 Hours"),
   "M" : (3001, "1 Month"),
   "N" : (2015, "Mid Month (1st - 15th)"),
   "P" : (5004, "Previous 7 a.m. local to time of observation"),
   "Q" : (1006, "6 Hours"),
   "R" : (5002, "Period of Record"),
   "S" : (5001, "Seasonal partial period, e.g. Jan 1 (to current date)"),
   "T" : (1003, "3 Hours"),
   "U" : (1   , "1 Minute"),
   "V" : (5003, "Variable, duration defined separately"),
   "W" : (2007, "1 Week"),
   "X" : (5005, "Unknown Duration"),
   "Y" : (4001, "1 Year"),
   "Z" : (5000, "Default Duration")}

start_time = HecTime()
start_time.showTimeAsBeginningOfDay(True)
end_time = HecTime()
end_time.showTimeAsBeginningOfDay(False)

output_revised = False

output_english = True

output_grouped = True

output_message_type = ".E"

output_linewidth = 80

delimiter = " / "

filename_stack = []

mapped_locations = {MASK : {}}
mapped_pe_codes  = {MASK : {MASK : {}}}
mapped_ts_codes  = {
   MASK : {},
   "DCP"     : "RG",
   "DROT"    : "RG",
   "DRGS"    : "RG",
   "LRGS"    : "RG",
   "GOES"    : "RG",
   "FCST"    : "FZ"}

fatal_error = False

db  = None

units_obj = None

output_list = []

environment = {}

#------------------#
# define functions #
#------------------#
def get_user() :

   '''Get the user name and computer address
   '''
   username = "unknown"
   computer = "unknown"
   try :
      username = os.environ["USER"]
   except :
      try :
         username = os.environ["USERNAME"]
      except :
         try :
            username = os.environ["LOGNAME"]
         except :
            pass
   try :
      computer = socket.gethostbyname(socket.gethostname())
   except :
      pass

   return "%s@%s" % (username, computer)

def strip_comments(text) :

   '''Strip comments from input line
   '''
   hash_pos = text.find("#")
   if hash_pos != -1 :
      quoted = []
      quote = ''
      for i in range(len(text)) :
         if text[i] in "'\"" :
            quoted.append(i)
            if text[i] == quote :
               quote = ''
            elif not quote :
               quote = text[i]
         elif quote :
            quoted.append(i)
      while hash_pos != -1 :
         if hash_pos in quoted :
            next_pos = text[hash_pos+1].find("#")
            if next_pos == -1 :
               hash_pos = -1
            else :
               hash_pos += next_pos + 1
         else :
            if hash_pos > 0 and text[hash_pos-1] == '\\' :
               text = text[:hash_pos-1] + text[hash_pos:]
               next_pos = text[hash_pos:].find("#")
               if next_pos == -1 :
                  hash_pos = -1
               else :
                  hash_pos += next_pos
            else :
               text = text[:hash_pos].strip()
               hash_pos = -1
               break
   return text


def replace_variables(text) :

   '''Perform variable substitution like in shell (e.g. $var)
   '''
   i = text.rfind("$(")
   while i != -1 :
      j = text[i:].find(")")
      if j == -1 :
         raise ValueError, "Unbalanced parentheses : %s" % text
      text = text[:i] + replace_variables(text[i+2:i+j]) + text[i+j+1:]
      i = text.rfind("$(")
   fields = text.split("$")
   for i in range(1, len(fields)) :
      if len(fields[i-1]) == 0 or fields[i-1][-1] != '\\' :
         for j in range(len(fields[i])) :
            if not fields[i][j].isalnum() and fields[i][j] != '_' :
               var_value = getenv(fields[i][:j])
               fields[i] = var_value + fields[i][j:]
               break
         else :
            fields[i] = getenv(fields[i])
      else :
         fields[i-1] = fields[i-1][:-1]
         fields[i] = "$" + fields[i]
   return ''.join(fields)

def assign_variables(line) :

   '''Perform variable assignment like in shell (e.g THIS=that)
   '''
   try    : key, value = map(string.strip, line.split("=", 1))
   except : return

   if not value :
      putenv(key, "")
   else :
      if len(key.split()) != 1 : raise ValueError, "Invalid variable assignment"
      putenv(key, value)

def getenv(key, default="") :

   '''like os.getenv(), but checks local dictionary first
   '''
   name = key.upper()
   try :
      return environment[name]
   except :
      try    : return os.environ[name]
      except : return default

def putenv(key, value) :

   '''like os.putenv(), but puts to local dictionary
   '''
   global environment
   environment[key.upper()] = value

def to_string(param) :

   '''Return a string representation of the parameter, without quotes if it is a string
   '''
   if type(param) in (types.StringType, types.UnicodeType) : return param
   return repr(param)

def get_start_time() :

   '''Return the start time string
   '''
   return start_time.dateAndTime(104).replace(",", "").replace(":", "")

def get_end_time() :

   '''Return the start time string
   '''
   return end_time.dateAndTime(104).replace(",", "").replace(":", "")

def set_log_level(level) :

   '''Set the log output level
   '''
   global log_level
   param_type = type(level)
   if param_type not in [types.IntType, types.StringType, types.UnicodeType] :
      raise TypeError, "Expected IntType or StringType, got %s" % `param_type`

   if param_type in (types.StringType, types.UnicodeType) :
      try :
         level = eval(level.upper())
      except NameError :
         raise ValueError, \
         'Log level text "%s" not recognized; must be one of "%s" or "%s"' % \
         (level, ', "'.join(log_level_names[:-1]), log_level_names[-1])

   log_level = max(NONE, min(level, VERBOSE))
   log_output(NONE, "Log level set to %d (%s)" % (log_level, log_level_names[log_level]))

def log_output(level, message) :

   '''Log the output according to message level
   '''
   if type(message) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(message)`

   if log_level >= level :
      prefix = log_level_names[level].upper().ljust(8)
      lines = message.split("\n")
      for line in lines :
         errfile.write("%s : %s\n" % (prefix, line))
      errfile.write("\n")
      errfile.flush()

def output_text(message) :

   '''Output user text
   '''
   output_shef_data()
   if type(message) in (types.StringType, types.UnicodeType) :
      lines = [message]
   else :
      lines = [`message`]

   while len(lines[-1]) > output_linewidth :
      extra = lines[-1][output_linewidth:]
      lines[-1] = lines[-1][:output_linewidth]
      lines.append(extra)

   for line in lines : outfile.write("%s\n" % line)

def set_output_format(param) :

   '''Set the data format by PE code
   '''
   global output_formats
   if type(param) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(param)`

   output_shef_data()
   formats = []
   for fmt_spec in map(string.strip,  param.split(",")) :
      try :
         pe_code, output = map(string.strip,  fmt_spec.upper().replace(")", "").split("("))
         if len(pe_code) != 2 and pe_code != "*" : raise ValueError
         fmt = ""
         significant_digits = ""
         if "/" in output :
            significant_digits, fmt = map(string.strip, output.split("/"))
         else :
            try :
               int(output)
               significant_digits = output
            except :
               fmt = output
         if fmt :
            if fmt[0] in "-+" :
               start = 1
            else :
               start = 0
            if fmt[-1].upper() == "Q" :
               end = -1
            else :
               end = len(fmt)
            w, p = map(int, fmt[start:end].split("."))
            if w < p+2 : raise ValueError
         if significant_digits and int(significant_digits) < 1 : raise ValueError
         formats.append((pe_code, output))
      except :
         raise ValueError, 'Invalid format "%s", must be "pe([s][/][+|-]w.p[Q])"' % fmt_spec

   for pe_code, format in formats :
      if pe_code == "*" :
         if not format : format = `SIGNIFICANT_DIGITS`
         output_formats = {"*" : format}
      else :
         output_formats[pe_code] = format
      log_output(DETAILED, 'Set output data format for "%s" to "%s"' % (pe_code, format))


def set_SHEF_delimiter(delim) :

   '''Set the SHEF message delimiter
   '''
   global delimiter
   output_shef_data()
   if type(delim) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(delim)`

   bad_delimiter = False
   if len(delim) < 3 or delim[0] != '"' or delim[-1] != '"' : bad_delimiter = True
   if not bad_delimiter :
      spaces, slashes, others = 0, 0, 0
      for c in delim[1:-1] :
         if   c == ' ' : spaces  += 1
         elif c == '/' : slashes += 1
         else          : others  += 1
      if spaces > 14 or slashes > 1 or others > 0 : bad_delimiter = True

   if bad_delimiter :
      raise ValueError, \
         'Invalid delimiter <%s>, must be "/" with optional spaces (up to 14) between quotes and slash.' % \
         delim

   delimiter = delim[1:-1]
   log_output(DETAILED, 'Delimiter set to "%s".' % delimiter)

def set_missing_value(value) :

   '''Set the format for missing data values
   '''
   global missing_value
   output_shef_data()
   if type(value) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(value)`

   if value not in missing_values :
      raise ValueError, \
         'Invalid missing value "%s", must be "%s" or "%s"' % \
         (value, '", "'.join(missing_values[:-1]), missing_values[-1])

   missing_value = value
   log_output(DETAILED, 'Missing value format set to "%s"' % missing_value)

def set_revision_flag(state) :

   '''Set whether the SHEF messages will be marked as revised
   '''
   global output_revised
   output_shef_data()
   param_type = type(state)
   if param_type not in [types.IntType, types.StringType, types.UnicodeType] :
      raise TypeError, "Expected IntType or StringType, got %s" % `param_type`

   if param_type in (types.StringType, types.UnicodeType) :
      if state.upper() in ["True", "YES", "ON"] :
         output_revised = True
      elif state.upper() in ["False", "NO", "OFF"] :
         output_revised = False
      else :
         raise ValueError, \
            'Revision flag text "%s" not recognized, must be "True", "False", "YES", "NO", "ON", or "OFF".' % \
            state.upper()
   else :
      if state in [True, False] :
         output_revised = state
      else :
         raise ValueError, \
            'Revision flag "%d" not recognized, must be "%d" or "%d".' % \
            (state, True, False)
   log_output(DETAILED, 'Revised flag set to %d (%s)' % (output_revised, ["NO", "YES"][output_revised]))
   output_shef_data()

def set_grouping(state) :

   '''Set whether the SHEF messages will be marked as revised
   '''
   global output_grouped
   param_type = type(state)
   if param_type not in [types.IntType, types.StringType, types.UnicodeType] :
      raise TypeError, "Expected IntType or StringType, got %s" % `param_type`

   if param_type in (types.StringType, types.UnicodeType) :
      if state.upper() in ["True", "YES", "ON"] :
         output_grouped = True
      elif state.upper() in ["False", "NO", "OFF"] :
         output_grouped = False
      else :
         raise ValueError, \
            'Grouping flag text "%s" not recognized, must be "True", "False", "YES", "NO", "ON", or "OFF".' % \
            state.upper()
   else :
      if state in [True, False] :
         output_grouped = state
      else :
         raise ValueError, \
            'Grouping flag "%d" not recognized, must be "%d" or "%d".' % \
            (state, True, False)
   log_output(DETAILED, 'Grouping set to %d (%s)' % (output_revised, ["NO", "YES"][output_grouped]))
   output_shef_data()

def set_output_linewidth(width):

   '''Set the output line width
   '''
   global output_linewidth
   param_type = type(width)
   if param_type not in [types.IntType, types.StringType, types.UnicodeType] :
      raise TypeError, "Expected IntType or StringType, got %s" % `param_type`

   output_shef_data()
   if param_type in (types.StringType, types.UnicodeType) :
      try :
         width = int(width)
      except ValueError :
         raise ValueError, 'Invalid line width: "%s".' % width

   if width > 1000 :
      raise ValueError, 'Line width of %d exceeds SHEF maximum of 1000.' % width
   elif width == 0 :
      raise ValueError, 'Invalid line width: %d.' % width

   output_linewidth = width
   log_output(DETAILED, 'Line width set to %d' % output_linewidth)

def set_output_quality(flags) :

   '''Set the quality code output flags
   '''
   global quality_level
   output_shef_data()
   old_flags = list(quality_level)
   param_type = type(flags)
   if param_type in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `param_type`

   uc_flags = flags.upper()
   if uc_flags == "NONE" :
      new_flags = uc_flags = []
   elif uc_flags == "ALL" :
      uc_flags = list(quality_values)
   else :
      uc_flags = uc_flags.replace(" ", "").split(",")
   add = sub = False
   for i in range(len(uc_flags)) :
      flag = uc_flags[i]
      if   flag[0] == '+' :
         add = True
         sub = False
         flag = flag[1:]
      elif flag[0] == '-' :
         add = False
         sub = True
         flag = flag[1:]
      if flag in quality_values :
         this_flag = flag
      else :
         for key in quality_keys :
            if key.startswith(flag) :
               this_flag = quality[key]
               break
         else :
            raise ValueError, \
               'Invalid quality flag "%s", must be "%s" or "%s"' % \
               (flag, '", "'.join(quality_values + quality_keys[:-1]), quality_keys[-1])
      if i :
         if not add and not sub : add = True
      else :
         if add or sub : new_flags = old_flags[:]
      if add :
         if not this_flag in new_flags : new_flags.append(this_flag)
      elif sub :
         if this_flag in new_flags : new_flags.remove(this_flag)
      else :
         new_flags = [this_flag]

   new_flags.sort()
   quality_level = "".join(new_flags)

   if quality_level :
      keys = []
      for key in quality_keys :
         if quality[key] in quality_level : keys.append(key)

      log_output(DETAILED, 'Output data quality set to "%s"' % ('", "'.join(keys)))
   else :
      log_output(DETAILED, 'Output data quality set to "NONE"')


def set_output_message_type(format) :

   '''Set the output format to .E or .A (regular time series only)
   '''
   global output_message_type
   if type(format) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(format)`

   uc_format = format.upper()
   if uc_format not in (".A", ".E") :
      raise ValueError, 'Expected ".A" or ".E", got "%s".' % uc_format

   output_message_type = uc_format
   log_output(DETAILED, 'Preferred regular time-series message type set to %s' % uc_format)

def set_time_window(tw_str) :

   '''Set the time window for exported data
   '''
   global start_time, end_time
   if type(tw_str) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(tw_str)`

   relative_time = tw_str.strip().upper()[0] == "T"
   if relative_time :
      tz = default_tz
   else :
      last_word = tw_str.split()[-1]
      uc_last = last_word.upper()
      if uc_last.isalpha and uc_last in timezones.keys() :
         tz = TimeZone.getTimeZone(timezones[uc_last])
         tw_str = tw_str[:-len(last_word)].strip()
      elif last_word in tz_ids :
         tz = TimeZone.getTimeZone(last_word)
         tw_str = tw_str[:-len(last_word)].strip()
      else :
         tz = default_tz

   start_time.setUndefined()
   end_time.setUndefined()
   if HecTime.getTimeWindow(tw_str, start_time, end_time) :
      raise ValueError, 'Invalid time window: "%s"' % tw_str

   if not end_time.greaterThan(start_time) :
      start_time.setUndefined()
      end_time.setUndefined()
      raise ValueError, 'Invalid time window: "%s", start time is not after end time' % tw_str

   cal = Calendar.getInstance()
   cal.clear()
   cal.setTimeZone(tz)
   cal.set(
      start_time.year(),
      start_time.month() - 1,
      start_time.day(),
      start_time.hour(),
      start_time.minute(),
      start_time.second())
   start_time.setTimeInMillis(cal.getTimeInMillis())
   cal.set(
      end_time.year(),
      end_time.month() - 1,
      end_time.day(),
      end_time.hour(),
      end_time.minute(),
      end_time.second())
   end_time.setTimeInMillis(cal.getTimeInMillis())

   if db  : db.setTimeWindow(get_start_time(), get_end_time())
   log_output(DETAILED, 'Time window set to "%s", "%s" UTC' % (get_start_time(), get_end_time()))

def set_output_timezone(tz_str) :

   '''Set the time zone for exported data
   '''
   global output_tz_name
   output_shef_data()
   if type(tz_str) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(tz_str)`

   uc_tz = tz_str.upper()
   try :
      tz = TimeZone.getTimeZone(timezones[uc_tz])
      output_tz_name = uc_tz
   except KeyError :
      raise ValueError, 'Invalid time zone: "%s"' % tz_str

   log_output(DETAILED, "Data will be exported time-stamped as %s (%s)." % (uc_tz, tz.getID()))

def set_output_units_system(system) :

   '''Set the units system for exported data
   '''
   global output_english
   output_shef_data()
   if type(system) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(system)`

   uc_system = system.upper()
   if "ENGLISH".startswith(uc_system) :
      output_english = True
   elif "SI".startswith(uc_system) or "METRIC".startswith(uc_system) :
      output_english = False
   else :
      raise ValueError, 'Invalid units system "%s", should be "ENGLISH", "SI", or "METRIC".' % uc_system

   if output_english :
      log_output(DETAILED, "Data will be exported in ENGLISH units")
   else :
      log_output(DETAILED, "Data will be exported in SI units")

def map_location(param) :

   '''Maps a CWMS location to a SHEF location
   '''
   global mapped_locations
   output_shef_data()
   if type(param) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(param)`

   cwms, shef = map(string.strip,  param.split("=", 1))
   shef = shef.upper()
   if len(shef) not in range(3, 9) :
      raise ValueError, 'Invalid location "%s", must be 3-8 characters long' % shef

   if "*" in cwms or "?" in cwms :
      if mapped_locations[MASK].has_key(cwms) :
         prev = mapped_locations[MASK][cwms]
         if prev == shef :
            log_output(
               DETAILED,
               'CWMS locations matching "%s" already mapped to SHEF location "%s".'  % \
               (cwms, shef))
         else :
            mapped_locations[MASK][cwms] = shef
            log_output(
               DETAILED,
               'CWMS locations matching "%s" previously mapped to SHEF location "%s", changed to "%s".'  % \
               (cwms, prev, shef))
      else :
         mapped_locations[MASK][cwms] = shef
         log_output(DETAILED, 'CWMS locations matching "%s" mapped to SHEF location "%s".'  % (cwms, shef))
   else :
      if mapped_locations.has_key(cwms) :
         prev = mapped_locations[cwms]
         if prev == shef :
            log_output(
               DETAILED,
               'CWMS location "%s" already mapped to SHEF location "%s".'  % \
               (cwms, shef))
         else :
            mapped_locations[cwms] = shef
            log_output(
               DETAILED,
               'CWMS location "%s" previously mapped to SHEF location "%s", changed to "%s".'  % \
               (cwms, prev, shef))
      else :
         mapped_locations[cwms] = shef
         log_output(DETAILED, 'CWMS location "%s" mapped to SHEF location "%s".'  % (cwms, shef))

def map_PE_code(param) :

   '''Maps a CWMS parameter and parameter type to a SHEF PE code
   '''
   global mapped_pe_codes
   output_shef_data()
   if type(param) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(param)`

   cwms, shef = map(string.strip,  param.split("=", 1))
   shef = shef.upper()
   if len(shef) != 2 :
      raise ValueError, 'Invalid PE code "%s", must be 2 characters long' % shef

   cwms_param, cwms_param_type = cwms.split(".")
   if "*" in cwms_param or "?" in cwms_param :
      #-----------------#
      # param is a mask #
      #-----------------#
      if mapped_pe_codes[MASK].has_key(cwms_param) :
         #---------------------------------#
         # param mask already in main hash #
         #---------------------------------#
         if "*" in cwms_param_type or "?" in cwms_param_type :
            #----------------------#
            # param type is a mask #
            #----------------------#
            if mapped_pe_codes[MASK][cwms_param][MASK].has_key(cwms_param_type) :
               #-----------------------------------------------#
               # param type mask is already in param mask hash #
               #-----------------------------------------------#
               prev = mapped_pe_codes[MASK][cwms_param][MASK][cwms_param_type]
               if prev == shef :
                  log_output(
                     DETAILED,
                     'CWMS params matching "%s" with types matching "%s" already mapped to SHEF PE code "%s".' %\
                     (cwms_param, cwms_param_type, shef))
               else :
                  mapped_pe_codes[MASK][cwms_param][MASK][cwms_param_type] = shef
                  log_output(
                     DETAILED,
                     'CWMS params matching "%s" with types matching "%s" previously mapped to SHEF PE code "%s", changed to "%s".' %\
                     (cwms_param, cwms_param_type, prev, shef))
            else :
               #-------------------------------------------#
               # param type mask is not in param mask hash #
               #-------------------------------------------#
               mapped_pe_codes[MASK][cwms_param][MASK][cwms_param_type] = shef
               log_output(
                  DETAILED,
                  'CWMS params matching "%s" with types matching "%s" mapped to SHEF PE code "%s".' %\
                  (cwms_param, cwms_param_type, shef))
         else :
            #-------------------------------#
            # param type is a normal string #
            #-------------------------------#
            if mapped_pe_codes[MASK][cwms_param].has_key(cwms_param_type) :
               #------------------------------------------#
               # param type is already in param mask hash #
               #------------------------------------------#
               prev = mapped_pe_codes[MASK][cwms_param][cwms_param_type]
               if prev == shef :
                  log_output(
                     DETAILED,
                     'CWMS params matching "%s" with type "%s" already mapped to SHEF PE code "%s".' %\
                     (cwms_param, cwms_param_type, shef))
               else :
                  mapped_pe_codes[MASK][cwms_param][cwms_param_type] = shef
                  log_output(
                     DETAILED,
                     'CWMS params matching "%s" with type "%s" previously mapped to SHEF PE code "%s", changed to "%s".' %\
                     (cwms_param, cwms_param_type, prev, shef))
            else :
               #--------------------------------------#
               # param type is not in param mask hash #
               #--------------------------------------#
               mapped_pe_codes[MASK][cwms_param][cwms_param_type] = shef
               log_output(
                  DETAILED,
                  'CWMS params matching "%s" with type "%s" mapped to SHEF PE code "%s".' %\
                  (cwms_param, cwms_param_type, shef))
      else :
         #-----------------------------#
         # param mask not in main hash #
         #-----------------------------#
         mapped_pe_codes[MASK][cwms_param] = {MASK : {}}
         if "*" in cwms_param_type or "?" in cwms_param_type :
            #----------------------#
            # param type is a mask #
            #----------------------#
            mapped_pe_codes[MASK][cwms_param][MASK][cwms_param_type] = shef
            log_output(
               DETAILED,
               'CWMS params matching "%s" with types matching "%s" mapped to SHEF PE code "%s".' %\
               (cwms_param, cwms_param_type, shef))
         else :
            #-------------------------------#
            # param type is a normal string #
            #-------------------------------#
            mapped_pe_codes[MASK][cwms_param][cwms_param_type] = shef
            log_output(
               DETAILED,
               'CWMS params matching "%s" with type "%s" mapped to SHEF PE code "%s".' %\
               (cwms_param, cwms_param_type, shef))
   else :
      #--------------------------#
      # param is a normal string #
      #--------------------------#
      if mapped_pe_codes.has_key(cwms_param) :
         #----------------------------#
         # param already in main hash #
         #----------------------------#
         if "*" in cwms_param_type or "?" in cwms_param_type :
            #----------------------#
            # param type is a mask #
            #----------------------#
            if mapped_pe_codes[cwms_param][MASK].has_key(cwms_param_type) :
               #---------------------------------------#
               # param type already in param mask hash #
               #---------------------------------------#
               prev = mapped_pe_codes[cwms_param][MASK][cwms_param_type]
               if prev == shef :
                  log_output(
                     DETAILED,
                     'CWMS param "%s" with types matching "%s" already mapped to SHEF PE code "%s".' %\
                     (cwms_param, cwms_param_type, shef))
               else :
                  mapped_pe_codes[cwms_param][MASK][cwms_param_type] = shef
                  log_output(
                     DETAILED,
                     'CWMS param "%s" with types matching "%s" previously mapped to SHEF PE code "%s", changed to "%s".' %\
                     (cwms_param, cwms_param_type, prev, shef))
            else :
               #-----------------------------------#
               # param type not in param mask hash #
               #-----------------------------------#
               mapped_pe_codes[cwms_param][MASK][cwms_param_type] = shef
               log_output(
                  DETAILED,
                  'CWMS param "%s" with types matching "%s" mapped to SHEF PE code "%s".' %\
                  (cwms_param, cwms_param_type, shef))
         else :
            #-------------------------------#
            # param type is a normal string #
            #-------------------------------#
            if mapped_pe_codes[cwms_param].has_key(cwms_param_type) :
               #-------------------------------------#
               # param type is already in param hash #
               #-------------------------------------#
               prev = mapped_pe_codes[cwms_param][cwms_param_type]
               if prev == shef :
                  log_output(
                     DETAILED,
                     'CWMS param "%s" with type "%s" already mapped to SHEF PE code "%s".' %\
                     (cwms_param, cwms_param_type, shef))
               else :
                  mapped_pe_codes[cwms_param][cwms_param_type] = shef
                  log_output(
                     DETAILED,
                     'CWMS param "%s" with type "%s" previously mapped to SHEF PE code "%s", changed to "%s".' %\
                     (cwms_param, cwms_param_type, prev, shef))
            else :
               #---------------------------------#
               # param type is not in param hash #
               #---------------------------------#
               mapped_pe_codes[cwms_param][cwms_param_type] = shef
               log_output(
                  DETAILED,
                  'CWMS param "%s" with type "%s" mapped to SHEF PE code "%s".' %\
                  (cwms_param, cwms_param_type, shef))
      else :
         #------------------------#
         # param not in main hash #
         #------------------------#
         mapped_pe_codes[cwms_param] = {MASK : {}}
         if "*" in cwms_param_type or "?" in cwms_param_type :
            #----------------------#
            # param type is a mask #
            #----------------------#
            mapped_pe_codes[cwms_param][MASK][cwms_param_type] = shef
            log_output(
               DETAILED,
               'CWMS param "%s" with types matching "%s" mapped to SHEF PE code "%s".' %\
               (cwms_param, cwms_param_type, shef))
         else :
            #------------------------#
            # param type is a normal #
            #------------------------#
            mapped_pe_codes[cwms_param][cwms_param_type] = shef
            log_output(
               DETAILED,
               'CWMS param "%s" with type "%s" mapped to SHEF PE code "%s".' %\
               (cwms_param, cwms_param_type, shef))


def map_TS_code(param) :

   '''Maps a CWMS version to a SHEF TS code
   '''
   global mapped_ts_codes
   output_shef_data()
   if type(param) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(param)`

   cwms, shef = map(string.strip,  param.split("=", 1))
   shef = shef.upper()
   if len(shef) != 2 :
      raise ValueError, 'Invalid TS code "%s", must be 2 characters long' % shef

   if "*" in cwms or "?" in cwms :
      if mapped_ts_codes[MASK].has_key(cwms) :
         prev = mapped_ts_codes[MASK][cwms]
         if prev == shef :
            log_output(
               DETAILED,
               'CWMS versions matching "%s" already mapped to SHEF TS code "%s".'  % \
               (cwms, shef))
         else :
            mapped_ts_codes[MASK][cwms] = shef
            log_output(
               DETAILED,
               'CWMS versions matching "%s" previously mapped to SHEF TS code "%s", changed to "%s".'  % \
               (cwms, prev, shef))
      else :
         mapped_ts_codes[MASK][cwms] = shef
         log_output(DETAILED, 'CWMS versions matching "%s" mapped to SHEF TS code "%s".'  % (cwms, shef))
   else :
      if mapped_ts_codes.has_key(cwms) :
         prev = mapped_ts_codes[cwms]
         if prev == shef :
            log_output(
               DETAILED,
               'CWMS version "%s" already mapped to SHEF TS code "%s".'  % \
               (cwms, shef))
         else :
            mapped_ts_codes[MASK][cwms] = shef
            log_output(
               DETAILED,
               'CWMS version "%s" previously mapped to SHEF TS code "%s", changed to "%s".'  % \
               (cwms, prev, shef))
      else :
         mapped_ts_codes[cwms] = shef
         log_output(DETAILED, 'CWMS version "%s" mapped to SHEF TS code "%s".'  % (cwms, shef))

def open_db(db_str) :

   '''Open the specified database
   '''
   global db, fatal_error

   if db :
      db.close()
      db = None

   if type(db_str) not in (types.StringType, types.UnicodeType) :
      fatal_error = True
      raise TypeError, "Expected a StringType, got %s" % `type(db_str)`

   try :
      if db_str.upper() == 'LOCAL' :
         db = DBAPI.open()
      else :
         db = DBAPI.open(db_str)
   except :
      fatal_error = True
      raise
   log_output(VERBOSE, "DBAPI module version is %s" % DBAPI.getVersion())

   db.setUnitSystem("SI")
   if start_time.isDefined() and end_time.isDefined() : db.setTimeWindow(get_start_time(), get_end_time())
   log_output(DETAILED, 'Connected to "%s" for office "%s".' % (db.getFileName(), db.getOfficeId()))


def get_units_description(unit) :

   '''
   Returns the description of SHEF units
   '''
   if type(unit) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(unit)`
   unit_names = {
      "%"      : "percent",
      "<CODED>"   : "Encoded value(s)",
      "<NONE>" : "No units",
      "CM"     : "Centimeters",
      "CMS"    : "Cubic meters per second",
      "D*10"      : "Tens of degrees",
      "DC"     : "Degrees Centigrade",
      "DF"     : "Degrees Fahrenheit",
      "FT"     : "Feet",
      "FT/S"      : "Feet per second",
      "G/FT3"     : "Grams per cubic foot",
      "G/M3"      : "Grams per cubic meter",
      "HRMN"      : "Hours and minutes",
      "HRS"    : "Hours",
      "IN"     : "Inches",
      "IN/DAY" : "Inches per day",
      "IN-HG"     : "Inches of mercury",
      "JTU"    : "Jackson turbidity units",
      "KAC"    : "Thousands of acres",
      "KAF"    : "Thousands of acre-feet",
      "KCFS"      : "Thousands of cubic feet per second",
      "KFT"    : "Thousands of feet",
      "KM"     : "Kilometers",
      "KM2"    : "Square kilometers",
      "KPA"    : "Kilopaschals",
      "KPH"    : "Kilometers per hour",
      "LY"     : "Langleys",
      "M"         : "Meters",
      "M/S"    : "Meters per second",
      "MCM"    : "Millions of cubic meters",
      "MG/L"      : "Milligram per liter",
      "MI"     : "Miles",
      "MM"     : "Millimeters",
      "MM/DAY" : "Millimeters per day",
      "MM-HG"     : "Millmeters of mercury",
      "MPH"    : "Miles per hour",
      "MW"     : "Megawatts",
      "MWH"    : "Megawatt-hours",
      "PPM"    : "Parts per million",
      "SWE/S"     : "Unit snow water equivalent per unit snow",
      "TENTHS" : "Tenths of whole",
      "UMHO/CM"   : "Micro-mhos per centimeter (micro-siemens/cm)",
      "V"         : "Volts",
      "W"         : "Watts",
      "W/M2"      : "Watts per sqare meter"
      }

   return unit_names[unit.upper()]

def get_units_conversion(pe_code, is_english) :

   '''
   Returns:
      1.) The SHEF units name
      2.) The CWMS units used as a intermediate
      3.) The factor (SHEF-units = CWMS-units * factor)
   '''

   if type(pe_code) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(pe_code)`

   English, SI = 0, 1
   Metric = SI

   shef2cwms = {
      "DF"     : ("F", 1.0),
      "DC"     : ("C", 1.0),
      "D*10"   : ("DEG", 10.0),
      "G/FT3"  : ("MG/L", 0.0283168),
      "G/M3"   : ("MG/L", 1.0),
      "HRS"    : ("SEC", 1.0 / 3600.0),
      "KAC"    : ("ACRE", 0.001),
      "KFT"    : ("FT", 0.001),
      "LY"     : ("LANGLEY", 1.0),
      "MCM"    : ("M3", 0.000001),
      "TENTHS" : ("%", 0.10),
      "V"      : ("VOLT", 1.0)}

   factor = 1.0
   units = None
   name = None

   try :
      english, si = shef_units[pe_code]
      if is_english :
         if not english.startswith("<") :
            try :
               units = Units(english)
            except :
               name, factor = shef2cwms[english.upper()]
               units = Units(name)
            if units.isSetToUndefined() : units = None
         name = english
      else :
         if not si.startswith("<") :
            try :
               units = Units(si)
            except :
               name, factor = shef2cwms[si.upper()]
               units = Units(name)
            if units.isSetToUndefined() : units = None
         name = si
   except :
      pass

   if units : units = "%s" % units.toString() # convert to python string
   return name, units, factor


def get_duration(cwms_duration) :

   '''Returns a SHEF duration code and variable duration specifier for a CWMS duration
   '''

   if type(cwms_duration) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_duration)`

   durations = {
      "0"      : ("I", None),
      "1Minute"   : ("U", None),
      "2Minutes"  : ("V", "DVN02"),
      "3Minutes"  : ("V", "DVN03"),
      "4Minutes"  : ("V", "DVN04"),
      "5Minutes"  : ("V", "DVN05"),
      "6Minutes"  : ("V", "DVN05"),
      "10Minutes" : ("V", "DVN10"),
      "12Minutes" : ("V", "DVN12"),
      "15Minutes" : ("C", None),
      "20Minutes" : ("V", "DVN20"),
      "30Minutes" : ("J", None),
      "1Hour"     : ("H", None),
      "2Hours" : ("B", None),
      "3Hours" : ("T", None),
      "4Hours" : ("F", None),
      "6Hours" : ("Q", None),
      "8Hours" : ("A", None),
      "12Hours"   : ("K", None),
      "1Day"      : ("D", None),
      "1Week"     : ("W", None),
      "1Month" : ("M", None),
      "1Year"     : ("Y", None),
      "1Decade"   : ("V", "DVY10")}

   try :
      duration, variable_code = durations[cwms_duration]
   except KeyError :
      log_output(
         DETAILED,
         'Duration "%s" has no corresponding SHEF duration code' % \
         param)
      duration, variable_code = None, None

   return duration, variable_code


def get_PE_code(cwms_parameter, cwms_parameter_type) :

   '''Returns a SHEF Physical Element code for a CWMS parameter and parameter type

   Rules for usage of the pe_codes dictionary :

   Type of value for cwms_parameter key    contents
   ------------------------------------    ------------------------------------------------------
   List. . . . . . . . . . . . . . . . . . Contains dictionary keyed by cwms_parameter_type,
                                           whose usage rules are the same as the main dictionary.

   Dictionary. . . . . . . . . . . . . . . Contains a dictionary keyed by the sub-parameter part,
                                           if any.

   String. . . . . . . . . . . . . . . . . The SHEF PE code to use.

   None. . . . . . . . . . . . . . . . . . SHEF PE code cannot be deduced, must be explicitly
                                           provided.
   '''

   if type(cwms_parameter) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_parameter)`
   if type(cwms_parameter_type) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_parameter_type)`

   #----------------------------------#
   # first, check the mapped PE codes #
   #----------------------------------#
   if mapped_pe_codes.has_key(cwms_parameter) :
      if mapped_pe_codes[cwms_parameter].has_key(cwms_parameter_type) :
         return mapped_pe_codes[cwms_parameter][cwms_parameter_type]
      else :
         for mask in mapped_pe_codes[cwms_parameter][MASK].keys() :
            if fnmatch.fnmatchcase(cwms_parameter_type, mask) :
               return mapped_pe_codes[cwms_parameter][MASK][mask]
   else :
      for param_mask in mapped_pe_codes[MASK].keys() :
         if fnmatch.fnmatchcase(cwms_parameter, param_mask) :
            if mapped_pe_codes[MASK][param_mask].has_key(cwms_parameter_type) :
               return mapped_pe_codes[MASK][param_mask][cwms_parameter_type]
            else :
               for type_mask in mapped_pe_codes[MASK][param_mask][MASK].keys() :
                  if fnmatch.fnmatchcase(cwms_parameter_type, type_mask) :
                     return mapped_pe_codes[MASK][param_mask][MASK][type_mask]

   #----------------------------#
   # check the default PE codes #
   #----------------------------#

   pe_codes = {
      "%"      : None,
      "Area"      : "LA",
      "Code"      : None,
      "Conc"      : None,
      "Cond"      : "WC",
      "Count"     : None,
      "Currency"  : None,
      "Depth"     : {"Snow" : "SD"},
      "Dir"    : [{
         "Const"     : None,
         "Inst"      : {"Wind" : "UD"},
         "Ave"       : None,
         "Total"     : None,
         "Max"       : {"Wind" : "UR"},
         "Min"       : None}],
      "Elev"      : {
         None        : "HP",
         "Pool"      : "HP",
         "Tailwater" : "HT"},
      "Energy" : "VE",
      "Evap"      : "EV",
      "EvapRate"  : "ER",
      "Fish"          : {
         None        : "FT",
         "Shad"      : "FA",
         "Sockeye"   : "FB",
         "Chinook"   : "FC",
         "Chum"      : "FE",
         "Coho"      : "FK",
         "Ladder"    : "FL",
         "Pink"      : "FP",
         "Steelhead" : "FS"},
      "Flow"      : {
         None        : "QR",
         "Unreg"     : "QR",
         "Reg"       : "QU",
         "Spillway"  : "QS",
         "Total    " : "QT",
         "Turbine"   : "QG",
         "Diversion" : "QD",
         "In"        : "QI",
         "Pump"      : "QP"},
      "Frost"     : "GD",
      "Length" : None,
      "Opening"   : "NG",
      "PercRate"  : None,
      "pH"     : "WP",
      "Power"     : "VT",
      "Precip" : [{
         "Const"     : None,
         "Inst"      : {
            None    : "PC",
            "Inc"   : "PP",
            "Cum"   : "PC"},
         "Ave"       : None,
         "Total"     : "PC",
         "Max"       : None,
         "Min"       : None}],
      "Pres"      : "PA",
      "Rad"    : "RI",
      "Speed"     : [{
         "Const"     : None,
         "Inst"      : {"Wind" : "US"},
         "Ave"       : None,
         "Total"     : None,
         "Max"       : {"Wind" : "UP"},
         "Min"       : None}],
      "Stage"     : "HG",
      "Stor"      : "LS",
      "Temp"      : {
         "Air"       : "TA",
         "Water"     : "TW"},
      "Thick"     : {"Ice" : "IT"},
      "Timing" : None,
      "Turb"      : "WT",
      "TurbJ"     : "WT",
      "TurbN"     : None,
      "Volt"      : "VB",
      "Width"     : None,
      "LossRate"  : None,
      "InitDef"   : None,
      "Travel" : {"Wind" : "UC"},
      "SpinRate"  : None,
      "FlowPerArea"  : None,
      "Irrad"     : None,
      "Melt"      : None,
      "Penalty"   : None}

   #-------------------------------------#
   # split outfile the sub-parameter, if any #
   #-------------------------------------#
   try :
      param, sub_param = cwms_parameter.split("-", 1)
      log_output(
         VERBOSE,
         'Parameter "%s" split into "%s" and "%s"' % \
         (cwms_parameter, param, sub_param))
   except :
      param, sub_param = cwms_parameter, None

   #--------------------------------------------------#
   # determine if we have anything for this parameter #
   #--------------------------------------------------#
   pe_code = None
   try :
      pe_code = pe_codes[param]
   except KeyError :
      log_output(DETAILED, 'Parameter "%s" has no corresponding SHEF PE code' % param)
      pe_code = None

   #-------------------------------------#
   # wade through the rules listed above #
   #-------------------------------------#
   if type(pe_code) in (types.StringType, types.UnicodeType) :
      #--------------------#
      # the actual PE code #
      #--------------------#
      pass
   elif type(pe_code) == types.DictType :
      #-----------------------------------#
      # dictionary keyed to sub-parameter #
      #-----------------------------------#
      log_output(VERBOSE, 'Parameter "%s" has SHEF PE code keyed to the sub-parameter' % param)
      try :
         pe_code = pe_code[sub_param]
      except KeyError :
         log_output(
            DETAILED,
            'Parameter "%s", sub-parameter "%s" has no corresponding SHEF PE code' %\
            (param, sub_param))
         pe_code = None
   elif type(pe_code) == types.ListType :
      #----------------------------------------------------------------#
      # list (singleton) contains a dictionary keyed to parameter type #
      #----------------------------------------------------------------#
      log_output(VERBOSE, 'Parameter "%s" has SHEF PE code keyed to the parameter type' % param)
      try :
         pe_code = pe_code[0][cwms_parameter_type]
         if type(pe_code) == types.DictType :
            try :
               pe_code = pe_code[sub_param]
            except KeyError :
               log_output(
                  DETAILED,
                  'Parameter "%s", sub-parameter "%s" has no corresponding SHEF PE code' % \
                  (param, sub_param))
               pe_code = None
      except KeyError :
         log_output(
            DETAILED,
            'Parameter "%s", parameter type "%s" has no corresponding SHEF PE code' % \
            (param, cwms_parameter_type))
         pe_code = None

   return pe_code

def get_extremum(cwms_parameter_type, cwms_duration) :

   '''Return the SHEF extremum character for cwms parameter type & duration
   '''

   if type(cwms_parameter_type) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_parameter_type)`
   if type(cwms_duration) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_duration)`

   extrema = {
      "Max" : {
         "1Hour"   : "D",
         "3Hours"  : "E",
         "6Hours"  : "R",
         "12Hours" : "Y",
         "1Day"    : "X",
         "1Week"   : "W",
         "1Month"  : "V",
         "1Year"   : "U"},
      "Min" : {
         "1Hour"   : "F",
         "3Hours"  : "G",
         "6Hours"  : "N",
         "12Hours" : "P",
         "1Day"    : "M",
         "1Week"   : "N",
         "1Month"  : "L",
         "1Year"   : "K"}}

   try :
      extremum = extrema[cwms_parameter_type][cwms_duration]
   except KeyError :
      log_output(
         VERBOSE,
         'Parameter type "%s", duration "%s" has no corresponding SHEF Extremum code' % \
         (cwms_parameter_type, cwms_duration))
      extremum = "Z"

   return extremum

def get_TS_code(cwms_version) :

   '''Returns the SHEF type and source code for a cwms version
   '''

   if type(cwms_version) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_version)`

   if mapped_ts_codes.has_key(cwms_version) : return mapped_ts_codes[cwms_version]

   for mask in mapped_ts_codes[MASK].keys() :
      if fnmatch.fnmatchcase(cwms_version, mask) : return mapped_ts_codes[MASK][mask]

   log_output(VERBOSE, 'Version "%s" has no corresponding SHEF TS code' % cwms_version)
   return "ZZ"

def get_location(cwms_location) :

   '''Returns the SHEF location identifier for a CWMS location
   '''

   if type(cwms_location) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_location)`

   if type(cwms_location) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_location)`

   if mapped_locations.has_key(cwms_location) : return mapped_locations[cwms_location]

   for mask in mapped_locations[MASK].keys() :
      if fnmatch.fnmatchcase(cwms_location, mask) : return mapped_locations[MASK][mask]

   shef_location = cwms_location.split()[0].upper()[:8]
   if len(shef_location) < 3 :
      shef_location = "_" * (3 - len(shef_location)) + shef_location

   log_output(VERBOSE, 'Version "%s" has no corresponding SHEF location, using "%s"' % (cwms_location, shef_location))
   return shef_location


def get_shef_description(cwms_description) :

   '''Returns the location, default (computed) parameter (PE,D,TS,E,P)
   and variable duration code for a cwms description
   '''

   if type(cwms_description) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected StringType, got %s" % `type(cwms_description)`

   shef_parameter, variable_duration_code = None, None

   log_output(VERBOSE, "Splitting %s into components" % cwms_description)
   cwms_location, cwms_parameter, parameter_type, interval, cwms_duration, version = cwms_description.split(".")
   shef_location = get_location(cwms_location)
   pe_code = get_PE_code(cwms_parameter, parameter_type)
   if pe_code :
      shef_duration, variable_duration_code = get_duration(cwms_duration)
      if shef_duration :
         ts_code = get_TS_code(version)
         extremum = get_extremum(parameter_type, cwms_duration)
         shef_parameter = "%s%s%s%sZ" % (pe_code, shef_duration, ts_code, extremum)

   if not shef_parameter :
      raise ValueError, 'CWMS description "%s" has no corresponding SHEF parameter' % cwms_description
   return shef_location, shef_parameter, variable_duration_code

def format(f, significant_digits=6) :

   '''Formats a floating-point value
   '''
   string = `f`
   exp_pos = string.find('E')
   if exp_pos != -1 :
      exponent = int(string[exp_pos+1:])
      string = string[:exp_pos]
   else :
      exponent = 0
   if string[0] == '-' :
      negative = True
      string = string[1:]
   else :
      negative = False
      if string[0] == '+' : string = string[1:]
   decimal_pos = string.find(".") + exponent
   string = string.replace(".", "")
   if decimal_pos <= 0 :
      string = ('0' * (-decimal_pos+1)) + string
      decimal_pos = 1
   leading_zeros = 0
   while string.startswith('0') :
      string = string[1:]
      leading_zeros += 1
   if not string :
      string = "0.0"
   else :
      if len(string) > significant_digits :
         increment = int(string[significant_digits]) > 4
         i = int(string[:significant_digits])
         if increment : i += 1
         string = `i`
         if len(string) > significant_digits : decimal_pos += 1
      string = ('0' * leading_zeros) + string
      if decimal_pos > len(string) :
         string = string + ('0' * (decimal_pos - len(string)))
      string = string[:decimal_pos] + "." + string[decimal_pos:]
      if negative : string = "-" + string
      while string[-1] == '0' : string = string[:-1]
   return string.rjust(significant_digits + 2)

def is_screened(tsc, index) :

   '''Returns whether the specified quality is set to screened
   '''
   return tsc.quality and QualityTx.isScreened(QualityTx.getBytes(tsc.quality[index]))

def is_missing(tsc, index) :

   '''Returns whether the specified quality is set to missing
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      and  QualityTx.isMissing(QualityTx.getBytes(tsc.quality[index])))

def is_okay(tsc, index) :

   '''Returns whether the specified quality is set to okay
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      and  QualityTx.isOkay(QualityTx.getBytes(tsc.quality[index])))

def is_rejected(tsc, index) :

   '''Returns whether the specified quality is set to rejected
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      and  QualityTx.isReject(QualityTx.getBytes(tsc.quality[index])))

def is_questioned(tsc, index) :

   '''Returns whether the specified quality is set to questionable
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      and  QualityTx.isQuestion(QualityTx.getBytes(tsc.quality[index])))

def is_estimated(tsc, index) :

   '''Returns whether the specified quality is set to automatically estimated
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      and  QualityTx.isReplaceLinearInterpolation(QualityTx.getBytes(tsc.quality[index])))

def is_interactive(tsc, index) :

   '''Returns whether the specified quality is set to interactively accepted or replaced
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      or  (QualityTx.isReplaceManualChange(QualityTx.getBytes(tsc.quality[index])) \
      or   QualityTx.isReplaceGraphicalChange(QualityTx.getBytes(tsc.quality[index]))))

def is_restored(tsc, index) :

   '''Returns whether the specified quality is set to interactively accepted or replaced
   '''
   return tsc.quality \
      and (is_screened(tsc, index) \
      and  QualityTx.isRevisedToOriginalAccepted(QualityTx.getBytes(tsc.quality[index])))

def format_with_quality(parameter, tsc, index) :

   '''Formats a SHEF floating-point value according to PE code and quality
   '''
   global output_formats
   missing = is_missing(tsc, index) or Const.isUndefined(tsc.values[index])
   try    : fmt = output_formats[parameter[:2]]
   except : fmt = output_formats["*"]
   start = 1 if fmt[0] in "-+" else 0
   end  = -1 if fmt[-1] == "Q" else len(fmt)
   raw_fmt = fmt[start:end]
   try :
      significant_digits = int(raw_fmt)
      if missing : return missing_value
      string = format(tsc.values[index], significant_digits).strip()
   except :
      try    : significant_digits, decimal_places = map(int, raw_fmt.split("."))
      except : significant_digits = SIGNIFICANT_DIGITS
      value = float(format((tsc.values[index], 0.)[missing], significant_digits).strip())
      string = ("%%%sf" % raw_fmt) % abs(value)
      if fmt[0] in "-+" : string = " " + string
      pos = string.rfind(" ")
      if value < 0.0 :
         if pos == -1 :
            string = "-" + string
         else :
            string = string[:pos] + "-" + string[pos+1:]
      elif fmt[0] == "+" :
         if pos == -1 :
            string = "+" + string
         else :
            string = string[:pos] + "+" + string[pos+1:]
   if missing :
      string = missing_value.rjust(len(string))
      if fmt[-1] == "Q" : string += " "
   else :
      if quality_level :
         if    is_rejected(tsc, index)    :
            if is_interactive(tsc, index) : qual = 'B'
            else                          : qual = 'R'
         elif is_questioned(tsc, index)   : qual = 'Q'
         elif is_estimated(tsc, index)    : qual = 'E'
         elif is_restored(tsc, index)     : qual = 'G'
         elif is_okay(tsc, index)         :
            if is_interactive(tsc, index) : qual = 'G'
            else                          : qual = 'S'
         else                             :
            if is_interactive(tsc, index) : qual = 'M'
            else                          : qual = 'Z'

         if qual in quality_level : string += qual

      if fmt[-1] == "Q" and not string[-1].isalpha()  : string += " "

   return string

def output_shef_message(line) :

   '''Outputs a single message, possibly breaking into multiple lines to meet line width constraints
   '''
   message_type = line[1]
   fields = line.split(delimiter)
   if len(fields[0]) > output_linewidth :
      raise ValueError, \
         'Line width of %d is too small for minimum message line of "%s"' % \
         (output_linewidth, fields[0])
   count = -1
   while fields :
      count += 1
      if count :
         prefix = ".%s%d " % (message_type, count % 10)
      else :
         prefix = ""
      output = "%s%s" % (prefix, delimiter.join(fields))
      if len(output) <= output_linewidth :
         outfile.write("%s\n" % output)
         fields = []
      else :
         for i in range(2, len(fields) + 1) :
            output = "%s%s" % (prefix, delimiter.join(fields[:i]))
            if len(output) > output_linewidth :
               outfile.write("%s%s\n" % (prefix, delimiter.join(fields[:i-1])))
               del fields[:i-1]
               break

def output_shef_data(tsc=None, shef_location=None, shef_parameter=None, variable_duration_code=None, tz_name=None) :

   '''Outputs the data in SHEF format
   '''
   global output_list
   #-------------------------------------------------------------------#
   # determine whether we should output the data now, or accumulate it #
   #-------------------------------------------------------------------#
   if not output_grouped or not tsc or (tsc.interval > 0 and output_message_type == ".E") :
      accumulate = False
   elif output_list :
      last_tsc, last_location, last_parameter, last_duration_code, last_tz = output_list[-1]
      if shef_location == last_location and tz_name == last_tz :
         accumulate = True
      else :
         accumulate = False

   else :
      accumulate = True
   if accumulate :
      #---------------------#
      # accumulate the data #
      #---------------------#
      output_list.append((tsc, shef_location, shef_parameter, variable_duration_code, tz_name))
   else :
      #-----------------------------#
      # output the accumulated data #
      #-----------------------------#
      cal = Calendar.getInstance()
      time_format = SimpleDateFormat("yyyyMMdd 'Z DH'HHmm")
      if output_list :
         location = output_list[0][1]
         tz = output_list[0][-1]
         tscs = []
         parameters = []
         duration_codes = []
         times = []
         for i in range(len(output_list)) :
            tscs.append(output_list[i][0])
            parameters.append(output_list[i][2])
            duration_codes.append(output_list[i][3])
         for i in range(len(tscs)) :
            for j in range(len(tscs[i].times)) :
               if tscs[i].times[j] not in times : times.append(tscs[i].times[j])
         times.sort()
         time_format.setTimeZone(TimeZone.getTimeZone(timezones[tz]))
         duration_code = None
         for i in range(len(times)) :
            cal.setTimeInMillis(Conversion.toMillis(times[i]))
            if output_revised :
               output = ".AR %s" % location
            else :
               output = ".A %s" % location
            output += " %s" % time_format.format(cal.getTime()).replace("Z", tz)
            if output_english :
               output += delimiter + "DUE"
            else :
               output += delimiter + "DUS"
            for j in range(len(tscs)) :
               try :
                  k = list(tscs[j].times).index(times[i])
               except :
                  continue
               if duration_codes[j] and duration_codes[j] != duration_code :
                  duration_code = duration_codes[j]
                  output += "%s%s " % (delimiter, duration_code)
               output += "%s%s %s" % (delimiter, parameters[j], format_with_quality(parameters[j], tscs[j], k))
            output_shef_message(output)
         output_list = []
         outfile.write("\n")

      #-------------------------#
      # output the current data #
      #-------------------------#
      if tsc :
         time_format.setTimeZone(TimeZone.getTimeZone(timezones[tz_name]))
         if output_message_type == ".A" or tsc.interval <= 0 :
            for i in range(len(tsc.times)) :
               cal.setTimeInMillis(Conversion.toMillis(tsc.times[i]))
               if output_revised :
                  output = ".AR %s" % shef_location
               else :
                  output = ".A %s" % shef_location
               output += " %s" % time_format.format(cal.getTime()).replace("Z", tz_name)
               if output_english :
                  output += delimiter + "DUE"
               else :
                  output += delimiter + "DUS"
               if variable_duration_code :
                  output += "%s%s " % (delimiter, variable_duration_code)
               output += "%s%s %s" % (delimiter, shef_parameter, format_with_quality(shef_parameter, tsc, i))
               output_shef_message(output)
            outfile.write("\n")
         else :
            if   not tsc.interval % 525600 : interval_string = "DIY+%2.2d" % (tsc.interval / 525600)
            elif not tsc.interval % 43200  : interval_string = "DIM+%2.2d" % (tsc.interval / 43200)
            elif not tsc.interval % 1440   : interval_string = "DID+%2.2d" % (tsc.interval / 1440)
            elif not tsc.interval % 60     : interval_string = "DIH+%2.2d" % (tsc.interval / 60)
            else                           : interval_string = "DIN+%2.2d" % tsc.interval
            cal.setTimeInMillis(Conversion.toMillis(tsc.times[0]))
            if output_revised :
               output = ".ER %s" % shef_location
            else :
               output = ".E %s" % shef_location
            output += " %s" % time_format.format(cal.getTime()).replace("Z", tz_name)
            if output_english :
               output += delimiter + "DUE"
            else :
               output += delimiter + "DUS"
            if variable_duration_code :
               output += "%s%s " % (delimiter, variable_duration_code)
            output += "%s%s" % (delimiter, shef_parameter)
            output += "%s%s" % (delimiter, interval_string)
            for i in range(len(tsc.times)) :
               output += "%s%s" % (delimiter, format_with_quality(shef_parameter, tsc, i))
            output_shef_message(output)

def process_export_line(line) :

   '''Read the specified data and output to SHEF
   '''
   offset = 0.0
   global fatal_error, units_obj
   if not db :
      fatal_error = True
      raise Exception, "No database is currently open."

   if not start_time.isDefined() or not end_time.isDefined() :
      raise Exception, "No time window is currently defined."

   if type(line) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected a StringType, got %s" % `type(line)`

   if units_obj :
      units_obj_name = "%s" % units_obj.toString() # convert java String to python string
   else :
      units_obj_name = ""
   #---------------------------------------------#
   # split the line into description & modifiers #
   #---------------------------------------------#
   fields = map(string.strip, line.split(";",  1))
   cwms_description = fields[0]
   #---------------------------------------------------------#
   # set the defaults to be used in the absence of modifiers #
   #---------------------------------------------------------#
   shef_location, shef_parameter, variable_duration_code = get_shef_description(cwms_description)
   shef_units, cwms_units, factor = get_units_conversion(shef_parameter[:2], output_english)
   tz_name = output_tz_name
   #---------------------------------#
   # identify any modifiers supplied #
   #---------------------------------#
   modifiers = {}
   if len(fields) > 1 :
      options = map(string.strip, fields[1].split(","))
      for option in options :
         try :
            key, value = map(string.strip,  option.split("="))
            key = key.upper()
         except :
            raise ValueError, 'Invalid export modifier: "%s"' % option
         matched = []
         for modifier in export_modifiers :
            if modifier.startswith(key) :
               matched.append(modifier)
         if not matched :
            raise ValueError, 'Invalid export modifier: "%s"' % option
         if len(matched) > 1 :
            raise ValueError, \
               'Export modifier "%s" is ambiguous.  It matches %s.' % \
               (key, `matched`.replace("'", '"'))
         key = matched[0]
         if modifiers.has_key(key) :
            raise ValueError, 'Export modifier "%s" specified more than once.' % key
         modifiers[key] = value
   #----------------------#
   # handle the modifiers #
   #----------------------#
   if modifiers.has_key("PARAMETER") :
      #---------------------------------------------#
      # SHEF parameter (possibly partial) specified #
      #---------------------------------------------#
      param = modifiers["PARAMETER"].upper()
      if len(param) > 7 :
         raise ValueError, 'Invalid parameter "%s", must be 2-7 characters long' % param
      if len(param) > 2 :
         duration = param[2]
         if not duration in shef_durations.keys() :
            raise ValueError, \
               'Parameter "%s" contains non-SHEF duration "%s".' % \
               (param, duration)
         if duration != shef_parameter[2] :
            if duration != 'I' and shef_parameter[2] != 'I' : # allow re-definition to/from instantaneous
               raise ValueError, \
                  'Parameter "%s" contains SHEF duration ("%s") which differs from that computed from CWMS description ("%s").' %\
                  (param, duration, shef_parameter[2])
      if shef_parameter :
         if len(param) < 7 :
            shef_parameter = param[:7] + shef_parameter[len(param):]
         else :
            shef_parameter = param
      else :
         if len(param) < 7 :
            shef_parameter = param + 'Z' * (7 - len(param))
         else :
            shef_parameter = param
      shef_units, cwms_units, factor = get_units_conversion(shef_parameter[:2], output_english)
   if not shef_parameter :
      raise ValueError, 'No SHEF parameter for "%s".' % cwms_description
   if modifiers.has_key("LOCATION") :
      #-------------------------#
      # SHEF location specified #
      #-------------------------#
      shef_location = modifiers["LOCATION"].upper()
      if len(shef_location) not in range(3, 9) :
         raise ValueError, 'Invalid location "%s", must be 3-8 characters long' % shef_location
   if modifiers.has_key("TZONE") :
      #---------------------#
      # time zone specified #
      #---------------------#
      tz_str = modifiers["TZONE"].upper()
      if not timezones.has_key(tz_str) :
         raise ValueError, 'Invalid time zone: "%s"' % tz_str
      tz_name = tz_str
   if modifiers.has_key("UNITS") :
      #-----------------#
      # units specified #
      #-----------------#
      if modifiers.has_key("FACTOR") :
         raise ValueError, "Cannot specify UNITS and FACTOR for same data."
      units_str = modifiers["UNITS"]
      if not shef_units or units_str.upper() != shef_units.upper() :
         if shef_parameter[:2] in standard_pe_codes :
            log_output(
               BASIC,
               'Outputting non-standard units "%s" instead of standard units "%s" for PE code "%s".' %\
               (units_str, shef_units, shef_parameter[:2]))
         shef_units, cwms_units, factor = units_str, units_str, 1.0
   if modifiers.has_key("FACTOR") :
      #------------------#
      # factor specified #
      #------------------#
      factor_str = modifiers["FACTOR"]
      try :
         factor = float(factor_str)
      except :
         raise ValueError, 'Invalid factor string: "%s".' % factor_str
      if shef_parameter[:2] in standard_pe_codes and not modifiers.has_key("OFFSET") :
         log_output(
            BASIC,
            'Outputting unknown units (database units * %s) instead of standard units "%s" for PE code "%s".' %\
            (factor_str, shef_units, shef_parameter[:2]))
      shef_units, cwms_units = None, None
   if modifiers.has_key("OFFSET") :
      #------------------#
      # offset specified #
      #------------------#
      offset_str = modifiers["OFFSET"]
      try :
         offset = float(offset_str)
      except :
         raise ValueError, 'Invalid offset string: "%s".' % offset_str
      if shef_parameter[:2] in standard_pe_codes :
         if modifiers.has_key("FACTOR") :
            if offset > 0 :
               log_output(
                  BASIC,
                  'Outputting unknown units (database units * %s + %s) instead of standard units "%s" for PE code "%s".' %\
                  (factor_str, offset_str, shef_units, shef_parameter[:2]))
            else :
               log_output(
                  BASIC,
                  'Outputting unknown units (database units * %s - %s) instead of standard units "%s" for PE code "%s".' %\
                  (factor_str, offset_str.replace("-", ""), shef_units, shef_parameter[:2]))
         else :
            log_output(
               BASIC,
               'Offsetting retrieved data by %s for PE code "%s".' %\
               (offset_str, shef_parameter[:2]))

   if cwms_units :
      if not units_obj or cwms_units.upper() != units_obj_name.upper() :
         try :
            units_obj = Units(cwms_units)
            units_obj_name = "%s" % units_obj.toString() # convert java String to python string
         except DataSetIllegalArgumentException :
            units_obj = Units(cwms_units, True)
            units_obj_name = "%s" % units_obj.toString() # convert java String to python string
            if units_obj.isSetToUndefined() :
               raise ValueError, 'Invalid units: "%s"' % cwms_units
            else :
               log_output(
                  BASIC,
                  'Invalid units: "%s", using best guess: "%s".\n==>%s' % \
                  (cwms_units, units_obj_name, line))
   tsc = db.get(cwms_description)
   if cwms_units :
      intermediate_units = None
      if not Units.canConvertBetweenUnits(tsc.units, units_obj_name) :
         for units in Units.getAvailableUnits() :
            if Units.canConvertBetweenUnits(tsc.units, units) and \
               Units.canConvertBetweenUnits(units, units_obj_name) :
                  intermediate_units = units
                  break
         else :
            if factor == 1.0 :
               raise ValueError, \
                  'Cannot convert from database units "%s" to SHEF units "%s".' % \
                  (tsc.units, units_obj_name)
            else :
               raise ValueError, \
                  'Cannot convert from database units "%s" to intermediate units "%s".' % \
                  (tsc.units, units_obj_name)
      if intermediate_units :
         try :
            Units.convertUnits(tsc.values, tsc.units, intermediate_units)
         except UnitsConversionException :
            raise ValueError, \
               'Error converting from database units "%s" to intermediate units "%s".' % \
               (tsc.units, units_obj_name)
         try :
            Units.convertUnits(tsc.values, intermediate_units, units_obj_name)
         except UnitsConversionException :
            if factor == 1.0 :
               raise ValueError, \
                  'Error converting from intermediate units "%s" to SHEF units "%s".' % \
                  (intermediate_units, units_obj_name)
            else :
               raise ValueError, \
                  'Error converting from first intermediate units "%s" to second intermediate units "%s".' % \
                  (intermediate_units, units_obj_name)
      else :
         try :
            Units.convertUnits(tsc.values, tsc.units, units_obj_name)
         except UnitsConversionException :
            if factor == 1.0 :
               raise ValueError, \
                  'Error converting from database units "%s" to SHEF units "%s".' % \
                  (tsc.units, units_obj_name)
            else :
               raise ValueError, \
                  'Error converting from database units "%s" to intermediate units "%s".' % \
                  (tsc.units, units_obj_name)
   if factor != 1.0 :
      for i in range(len(tsc.values)) :
         if Const.isDefined(tsc.values[i]) : tsc.values[i] *= factor

   if offset != 0.0 :
      for i in range(len(tsc.values)) :
         if Const.isDefined(tsc.values[i]) : tsc.values[i] += offset

   output_shef_data(tsc, shef_location, shef_parameter, variable_duration_code, tz_name)

def get_command(string) :

   '''Returns the full command for the string, if any
   '''

   if type(string) not in (types.StringType, types.UnicodeType) :
      raise TypeError, "Expected a StringType, got %s" % `type(string)`

   uc_string = string.upper()
   matches = []

   for i in range(len(command_keys)) :
      if command_keys[i] == (uc_string) : return command_keys[i]
      if command_keys[i].startswith(uc_string) : matches.append(i)
   if matches :
      if len(matches) == 1 :
         return command_keys[matches[0]]
      else :
         matched = []
         for i in range(len(matches)) : matched.append(command_keys[matches[i]])
         message = 'Command "%s" is ambiguous.  It matches %s.' % (uc_string, `matched`.replace("'", '"'))
         raise ValueError, message
   else :
      raise ValueError, 'Command "%s" not recognized.' % uc_string

def process_input(file_obj) :

   '''Process input (command) lines from the file object
   '''
   global filename_stack
   obj_type = type(file_obj)
   if obj_type in (types.StringType, types.UnicodeType) :
      f = open(file_obj, "rt")
   elif obj_type == types.FileType :
      f = file_obj
   else :
      raise TypeError, "Expected StringType or FileType, got %s" % `obj_type`

   filename = f.name
   if filename[0] != "<" : filename = os.path.abspath(filename)

   for open_file in filename_stack :
      if os.path.samefile(filename, open_file) :
         f.close()
         raise ValueError, "File %s cannot be processed recursively" % filename

   filename_stack.append(filename)
   log_output(BASIC, "Procesing input file %s" % filename)

   try :
      line_number = 0
      while not fatal_error :
         line_number += 1
         actual_line = f.readline()
         if not actual_line : # EOF, blank actual_line will be "\n"
            try :
               output_shef_data()
            except Exception, e :
               message = " ".join(map(to_string, e.args))
               log_output(
                  BASIC,
                  "Error processing export at line %d of file %s\n>>>%s" % \
                  (line_number - 1, filename, message))
               tbInfo = StringIO.StringIO()
               sys.stderr = tbInfo
               traceback.print_exc()
               sys.stderr = sys.__stderr__
               log_output(DETAILED, tbInfo.getvalue())
               tbInfo.close()
            break
         actual_line = actual_line.strip()
         if not actual_line : continue
         line = strip_comments(actual_line)
         if not line : continue
         line = replace_variables(line).strip()
         if not line : continue
         if len(line.split("=")[0].strip().split(".")) == 6 :
            try :
               process_export_line(line)
            except Exception, e :
               message = " ".join(map(to_string, e.args))
               tbInfo = StringIO.StringIO()
               sys.stderr = tbInfo
               traceback.print_exc()
               sys.stderr = sys.__stderr__
               tbInfo.close()
               if line == actual_line :
                  log_output(
                     BASIC,
                     "Error processing export at line %d of file %s\n-->%s\n>>>%s" % \
                     (line_number, filename, line, message))
               else :
                  log_output(
                     BASIC,
                     "Error processing export at line %d of file %s\n-->%s\n-->%s\n>>>%s" % \
                     (line_number, filename, actual_line, line, message))
               tbInfo = StringIO.StringIO()
               sys.stderr = tbInfo
               traceback.print_exc()
               sys.stderr = sys.__stderr__
               log_output(DETAILED, tbInfo.getvalue())
               tbInfo.close()
               continue
         else :
            words = line.split()
            pos = words[0].find("=")
            if pos != -1 :
               if len(words) > 1 :
                  words[1] = words[0][pos+1:] + words[1]
               else :
                  words.append(words[0][pos+1:])
               words[0] = words[0][:pos]
            try :
               command = get_command(words[0])
            except ValueError, ve :
               try :
                  assign_variables(line)
               except :
                  message = " ".join(ve.args)
                  if line == actual_line :
                     log_output(
                        BASIC,
                        "Invalid command at line %d of file %s\n-->%s\n>>>%s" % \
                        (line_number, filename, line, message))
                  else :
                     log_output(
                        BASIC,
                        "Invalid command at line %d of file %s\n-->%s\n-->%s\n>>>%s" % \
                        (line_number, filename, actual_line, line, message))
                  tbInfo = StringIO.StringIO()
                  sys.stderr = tbInfo
                  traceback.print_exc()
                  sys.stderr = sys.__stderr__
                  log_output(DETAILED, tbInfo.getvalue())
                  tbInfo.close()
               continue

            if words[0] == line :
               parameter = ""
            else :
               parameter = line[len(words[0]):]
               if parameter[0] == "=" or command == "OUTPUT" : parameter = parameter[1:]
               if command != "OUTPUT" : parameter = parameter.strip()
            try :
               if command in ["DEBUG", "REVISED", "GROUP"] :
                  try    : parameter = eval("int(%s)" % parameter)
                  except : parameter = '"%s"' % parameter
               elif command == "INCLUDE" :
                  if not os.path.isabs(parameter) :
                     parameter = os.path.abspath(os.path.join(os.path.dirname(filename), parameter))
                  parameter = parameter.replace("\\", "\\\\")
               cmd = commands[command]
               if   cmd.find("'%s'") != -1 : parameter = parameter.replace("'", "\\'")
               elif cmd.find('"%s"') != -1 : parameter = parameter.replace('"', '\\"')
               exec(cmd % parameter)
            except Exception, e :
               message = " ".join(map(to_string, e.args))
               if line == actual_line :
                  log_output(
                     BASIC,
                     "Error processing command at line %d of file %s\n-->%s\n>>>%s" % \
                     (line_number, filename, line, message))
               else :
                  log_output(
                     BASIC,
                     "Error processing command at line %d of file %s\n-->%s\n-->%s\n>>>%s" % \
                     (line_number, filename, actual_line, line, message))
               tbInfo = StringIO.StringIO()
               sys.stderr = tbInfo
               traceback.print_exc()
               sys.stderr = sys.__stderr__
               log_output(DETAILED, tbInfo.getvalue())
               tbInfo.close()
               continue

      if fatal_error :
         log_output(BASIC, "Aborting input file %s due to fatal error." % filename)
      else :
         log_output(DETAILED, "Finished processing input file %s" % filename)
      f.close()
   finally :
      filename_stack = filename_stack[:-1]


def process_execution_line() :

   '''Process the execution line arguments
   '''
   global infile, outfile, errfile, fatal_error
   sequence = range(1, len(sys.argv))
   for i in sequence :
      arg = sys.argv[i]
      if arg[0] in "-/" : arg = arg[1:]
      if arg.find("=") != -1 :
         key, value = arg.split("=", 1)
         param = sys.argv[i]
      else :
         if i == len(sys.argv) - 1 :
            errfile.write('Program argument "%s" provided without a value!\n' % sys.argv[i])
            fatal_error = True
            break
         key, value = arg, sys.argv[i+1]
         param = "%s %s" % (sys.argv[i], sys.argv[i+1])
         sequence.remove(i+1)
      try :
         command = get_command(key)
         if command not in [
            "DB",
            "DEBUG",
            "DELIMITER",
            "FORMAT",
            "GROUP",
            "LINEWIDTH",
            "MISSING",
            "QUALITY",
            "REVISED",
            "SYSTEM",
            "TIMEWINDOW",
            "TYPE",
            "TZONE"] :
            raise ValueError
         if command in ["DEBUG", "REVISED", "GROUP"] :
            try    : value = eval("int(%s)" % value)
            except : value = '"%s"' % value
         try :
            exec(commands[command] % value)
         except Exception, e :
            message = " ".join(map(to_string, e.args))
            errfile.write("Error processing parameter: %s\n>>>%s\n" % (param, message))
            fatal_error = True
            break
      except ValueError :
         uc_key = key.upper()
         if   uc_key == "IN"  : infile = value
         elif uc_key == "OUT" : outfile = open(value, "w")
         elif uc_key == "LOG" : errfile = open(value, "w")
         else :
            errfile.write("Unexpected parameter:%s\n" % param)
            fatal_error = True
            break

#----------------#
# startup chores #
#----------------#
starting_time = time.time()
command_line = " ".join(sys.argv)
banner = "ExportSHEF version %s\nStarted at %s\nStarted by %s\nCommand line = %s" % \
   (PROGRAM_VERSION, time.ctime(starting_time), get_user(), command_line)
log_output(BASIC, banner)
process_execution_line()

#-------------#
# do the work #
#-------------#
if errfile != sys.stderr : log_output(BASIC, banner)
if not fatal_error : process_input(infile)

#-----------#
# shut down #
#-----------#
if db  : db.close()
ending_time = time.time()
seconds = int(ending_time - starting_time)
hours = seconds / 3600
seconds -= 3600 * hours
minutes = seconds / 60
seconds -= 60 * minutes
banner = "ExportSHEF version %s\nEnded at %s\nElapsed Time = %2.2d:%2.2d:%2.2d" % \
   (PROGRAM_VERSION, time.ctime(ending_time), hours, minutes, seconds)
log_output(BASIC, banner)
outfile.flush()
System.exit(0)