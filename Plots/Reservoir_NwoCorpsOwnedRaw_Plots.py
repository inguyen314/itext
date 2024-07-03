# name=Reservoir_NwoCorpsOwnedRaw_Plots
# displayinmenu=false
# displaytouser=false
# displayinselector=false
'''
Author: Ben Sterbenz and Ryan Larsen 08-04-2020
Creates plots with any of the following: just precip data, just stage data, precip and Elev/Stage data, 
and Precip and Elev/Stage and radar-Elev/Stage data. The plots that are created are located in the cronjobs images folder

'''

# -------------------------------------------------------------------
# Required imports
# -------------------------------------------------------------------
from hec.heclib.util    import HecTime
from hec.script         import Plot, Constants
import java.lang
import sys, time, DBAPI, os, inspect, datetime, math, traceback, java

# -------------------------------------------------------------------
# Global variables
# -------------------------------------------------------------------
global CurveProperties, MarkerProperties, PlotProperties, StartTw

# -------------------------------------------------------------------
# Import database pathnames and plotting functions
# -------------------------------------------------------------------
# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
if OsName[ : 7] == 'windows' : 
	# PC pathnames
	CronjobsDirectory = "C:\\Users\\G6EDXJB9\\Documents\\cronjobs\\"
	PlotsDirectory = CronjobsDirectory + "Plots\\"
	ImagesDirectory = PlotsDirectory + "Images\\"
else :
	# Server pathnames
	PlotsDirectory = os.path.dirname(os.path.realpath(__file__))
	PathList = PlotsDirectory.split('/')
	CronjobsDirectory = '/'.join(PathList[: -1]) + '/'
	PlotsDirectory += '/'
	ImagesDirectory = PlotsDirectory + 'Images/NWO/'
print 'CronjobsDirectory = ', CronjobsDirectory, '\tScript Directory = ', PlotsDirectory, '\tImage Directory = ', ImagesDirectory

if CronjobsDirectory not in sys.path : sys.path.append(CronjobsDirectory)
if PlotsDirectory not in sys.path : sys.path.append(PlotsDirectory)

#
# Load DatabasePathnames.txt
#
while True :
	errorMessage = None
	DatabasePathnamesFile = os.path.join(CronjobsDirectory, "DatabasePathnames.txt")
	if not os.path.exists(DatabasePathnamesFile) :
		errorMessage = "DatabasePathnames.txt does not exist: %s" % DatabasePathnamesFile
	with open(DatabasePathnamesFile, "r") as f : exec(f.read())
	break
if errorMessage :
	print "ERROR : " + errorMessage


import Server_Utils
reload(Server_Utils)
from Server_Utils import createBlankTimeSeries, lineNo, outputDebug, createPlot, retrieveLongName

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False
PlotFilename = ImagesDirectory + '%sRaw.jpg'
PlotFilenameVolt = ImagesDirectory + '%sVolt.jpg'
# List of locations to be included on plot with both precip and elev/stage
StageOnly = [ 'LPSD', 'PONE', 'PA2A', 'AWND', 'ARSD']
StagePrecip = [ 'BLNE', 'COTT', 'BOHA', 'SC02', 'SC04', 'SC08', 'SC09', 'SC10', 'SC12', 'SC13', 'SC14', 'SC17', 'SC18', 'PA11', 'PA16', 'PA18', 'PA20', 'CHFI', 'BECR', 'CHCR']
RadarPrecip = [ 'PIST', 'COLD','BVNE','PTNE']
PrecipOnly = ['PGSD']
VoltOnly = ['LPSD', 'PONE', 'PA2A', 'AWND', 'ARSD', 'BLNE', 'COTT', 'BOHA', 'SC02', 'SC04', 'SC08', 'SC09', 'SC10', 'SC12', 'SC13', 'SC14', 'SC17', 'SC18', 'PA11', 'PA16', 'PA18', 'PA20', 'CHFI', 'BECR', 'PGSD','BVNE']
Voltx2 = ['PIST', 'COLD','PTNE']

# Plot info
PlotWidth= 975
PlotHeight = 735
PlotQuality = 100 # range of 0 (crappy) to 100 (great, but larger file)

# Dictionary of data
DataDict = {	 'BECR'              :	{	'precipPath'     :   'BECR.Precip.Inst.15Minutes.0.Raw-LRGS',
							'surfacePath'	:	'BECR.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Bear Creek Dam on Bear Creek, Denver Metro, CO',
                                            		'voltPath'		:	'BECR.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'CHFI'              :		{	'precipPath'	:	'CHFI.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'CHFI.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Chatfield Dam on South Platte River, Denver Metro, CO',
                                            		'voltPath'		:	'CHFI.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'COLD'              :	{	'precipPath'	:	'COLD.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'COLD.Elev-orifice.Inst.15Minutes.0.Raw-LRGS',
                                            		'surfacePath2'	:	'COLD.Elev-radar.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Cold Brook Dam on Cold Brook, Hot Springs, SD',
                                            		'voltPath'		:	'COLD.Volt-Orifice.Inst.15Minutes.0.Raw-LRGS',
                                            		'volt2Path'	:	'COLD.Volt-Radar.Inst.15Minutes.0.Raw-LRGS',
                                            		'plot'			:	'OandR'
                                            	},
                'PA11'              :	{	'precipPath'	:	'PA11.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'PA11.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Cunningham Lake / Papio Dam 11, Omaha, NE',
                                            		'voltPath'		:	'PA11.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'PA16'              :	{	'precipPath'	:	'PA16.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'PA16.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Standing Bear Lake / Papio Dam 16, Omaha, NE',
                                            		'voltPath'		:	'PA16.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'PA18'              :	{	'precipPath'	:	'PA18.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'PA18.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		: 	'Zorinksy Lake / Papio Dam 18, Omaha, NE',
                                            		'voltPath'		:	'PA18.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'PA20'              :	{	'precipPath'	:	'PA20.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'PA20.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Wehrspann Lake / Papio Dam 20, Omaha Metro, NE',
                                            		'voltPath'		:	'PA20.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'PA2A'               :	{	'precipPath'	:	'',
                					'surfacePath'	:	'PA2A.Stage.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Silt Dam at Papio Creek Dam 20 near Omaha, NE',
                                            		'voltPath'		:	'PA2A.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'surface'
                                        	},
                'SC02'              :		{	'precipPath'	:	'SC02.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC02.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Olive Branch Creek / Salt Cr Dam 2, Lincoln, NE',
                                            		'voltPath'		:	'SC02.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC04'              :		{	'precipPath'	:	'SC04.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC04.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Blue Stem Lake / Salt Cr Dam 4, Lincoln, NE',
                                            		'voltPath'		:	'SC04.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC08'              :		{	'precipPath'	:	'SC08.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC08.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Wagon Train Lake / Salt Cr Dam 8, Lincoln, NE',
                                            		'voltPath'		:	'SC08.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC09'              :		{	'precipPath'	:	'SC09.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC09.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'  		:	'Stagecoach Lake / Salt Cr Dam 9, Lincoln, NE',
                                            		'voltPath'		:	'SC09.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC10'              :		{	'precipPath'	:	'SC10.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC10.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'  		:	'Yankee Hill Lake / Salt Cr Dam 10, Lincoln, NE',
                                            		'voltPath'		:	'SC10.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC12'              :		{	'precipPath'	:	'SC12.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC12.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'  		:	'Conestoga Lake / Salt Cr Dam 12, Lincoln, NE',
                                            		'voltPath'		:	'SC12.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC13'              :		{	'precipPath'	:	'SC13.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC13.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Twin Lakes / Salt Cr Dam 13, Lincoln, NE',
                                            		'voltPath'		:	'SC13.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'SC14'              :		{	'precipPath'	:	'SC14.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC14.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		: 	'Pawnee Lake / Salt Cr Dam 14, Lincoln, NE',
                                            		'voltPath'		:	'SC14.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                           	},
                'SC17'              :		{	'precipPath'	:	'SC17.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC17.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Holmes Lake / Salt Cr Dam 17, Lincoln, NE',
                                            		'voltPath'		:	'SC17.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                           	},
                'SC18'              :		{	'precipPath'	:	'SC18.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'SC18.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Branched Oak Lake / Salt Cr Dam 18, Lincoln, NE',
                                            		'voltPath'		:	'SC18.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                           	},
                'BOHA'              :	{	'precipPath'	:	'BOHA.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'BOHA.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		:	'Bowman-Haley Dam on Grand River, Bowman, ND',
                                            		'voltPath'		:	'BOHA.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                            	},
                'CHCR'              :	{ 	'precipPath'	:	'CHCR.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'CHCR.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'surfacePath2'	:	'CHCR.Elev-radar.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'		: 	'Cherry Creek Dam on Cherry Creek, Denver Metro, CO',
                                            		'voltPath'		:	'CHCR.Volt-Orifice.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'CHCR.Volt-Radar.Inst.1Hour.0.Raw-LRGS',
                                            		'plot'			:	'OandR'
                                            	},
                'COTT'              :	{	'precipPath'	:	'COTT.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'COTT.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Cottonwood Springs Dam on Cottonwood Spring, Hot Springs, SD',
                                            		'voltPath'		:	'COTT.Volt.Inst.15Minutes.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                				},
            	'LPSD'               :	{	'precipPath'	:	'',
                					'surfacePath'	:	'LPSD.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'  		:	'Lake Poinsett near Watertown, SD',
                                            		'voltPath'		:	'LPSD.Volt.Inst.15Minutes.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'surface'
                                        	},
                'PIST'    		  :	{	'precipPath'	:	'PIST-Office.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'PIST.Elev-orifice.Inst.15Minutes.0.Raw-LRGS',
                                            		'surfacePath2'	:	'PIST.Elev-radar.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle'  		: 	'Pipestem Dam on Pipestem Creek, Jamestown, ND',
                                            		'voltPath'		:	'PIST.Volt.Inst.15Minutes.0.Raw-LRGS',
                                            		'volt2Path'	:	'PIST-Office.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'plot'			:	'OandR'
                                        	},
                'AWND'               :	{	'precipPath'	:	'',
                					'surfacePath'	:	'AWND.Elev.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Arrowwood Res on the James River, ND',
                                            		'voltPath'		:	'AWND.Volt.Inst.15Minutes.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'surface'
                                        	},
		'BLNE'               :	{	'precipPath'	:	'BLNE.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'BLNE.Stage.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Missouri River at Blair, NE',
                                            		'voltPath'		:	'BLNE.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'PrecipElev'
                                        	},
                'PONE'               :	{	'precipPath'	:	'',
                					'surfacePath'	:	'PONE.Stage.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		:	'Missouri River at Ponca, NE',
                                            		'voltPath'		:	'PONE.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'surface'
                                        	},
                'BVNE'                    :     {       'precipPath'    :       'OMA.Precip.Inst.15Minutes.0.Raw-LRGS',
                                                        'surfacePath'   :       'BVNE.Stage-Orifice.Inst.15Minutes.0.Raw-LRGS',
                                                        'surfacePath2'  :       'BVNE.Stage-Radar.Inst.15Minutes.0.Raw-LRGS',
                                                        'PlotTitle'             :       'Missouri River at Brownville, NE',
                                                        'voltPath'              :       'BVNE.Volt.Inst.1Hour.0.Raw-LRGS',
                                                        'volt2Path'     :       '',
                                                        'plot'                  :       'OandR'
                                                },
                'PTNE'                    :     {       'precipPath'    :       'OMA.Precip.Inst.15Minutes.0.Raw-LRGS',
                                                        'surfacePath'   :       'PTNE.Stage-Orifice.Inst.15Minutes.0.Raw-LRGS',
                                                        'surfacePath2'  :       'PTNE.Stage-Radar.Inst.15Minutes.0.Raw-LRGS',
                                                        'PlotTitle'             :       'Missouri River at Plattsmouth, NE',
                                                        'voltPath'              :       'PTNE.Volt-Orifice.Inst.1Hour.0.Raw-LRGS',
                                                        'volt2Path'     	:       'PTNE.Volt-Radar.Inst.1Hour.0.Raw-LRGS',
                                                        'plot'                  :       'OandR'
                                                },
                'PGSD'               :	{	'precipPath'	:	'PGSD.Precip.Inst.15Minutes.0.Raw-LRGS',
                					'surfacePath'	:	'',
                                            		'PlotTitle' 		:	'Precipitation Station near Pringle, SD',
                                            		'voltPath'		:	'PGSD.Volt.Inst.15Minutes.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'precip'
                                            	},
                'ARSD'               :	{	'precipPath'	:	'',
                					'surfacePath'	:	'ARSD.Stage.Inst.15Minutes.0.Raw-LRGS',
                                            		'PlotTitle' 		: 	'Above Coldbrook Reservoir at Argyle Rd, Hot Springs, SD',
                                            		'voltPath'		:	'ARSD.Volt.Inst.1Hour.0.Raw-LRGS',
                                            		'volt2Path'	:	'',
                                            		'plot'			:	'surface'
                                            	},
                
                'CurveProperties'	:   {   'LineColor'         :   'red',
                                            'LineStyle'         :   'Solid',
                                            'LineWidth'         :   1,
                                            'SymbolVisible'     :   Constants.FALSE,
                                            'SymbolType'        :   'Square',
                                            'SymbolSize'        :   7,
                                            'SymbolLineColor'   :   'blue',
                                            'SymbolFillColor'   :   'blue',
                                            'SymbolInterval'    :   0,
                                            'SymbolSkipCount'   :   0,
                                            'FirstSymbolOffset'	:   0,
                                            'FillType'          :   'None',
                                            'FillColor'         :   'orange',
                                            'FillPattern'       :   'Solid',
                                            },
                'TitleProperties'   :	{   'Font'            	:    'Arial',
                                            'FontColor'        	:    'black',
                                            'FontStyle'        	:    'Normal',
                                            'FontSize'			:    20
                                            },

                }

######################################################################################################################################################
##########					START OF MAIN SCRIPT --- OBTAINING ELEVATION/STAGE PLOTS ONLY                                     ###############################################################
######################################################################################################################################################



# Curve, marker, and plot properties
'''
Colors = black, blue, cyan, darkblue, darkcyan, darkgray, darkgreen, darkmagenta, darkorange, darkpink, darkpurple, darkred, darkyellow, gray, green, lightblue,
         lightcyan, lightgray, lightgreen, lightmagenta, lightorang, lightpink, lightpurple, lightred, lightyellow, magenta, orange, pink, purple, red, white,
         yellow
Alignment = Left, Center, Right
Positions = Above, Center, Below,
Rotation, 0, 90, 180, 270
Fill Patterns = Solid, Cross, Diagonal Cross, Horizontal, FDiagonal, None, Vertical, BDiagonal
Fill Types = None, Above, Below,
Line Styles = Solid, Dash Dot, Dash, Dash Dot-Dot, Dot
Step Style = Normal, Step, Cubic
Symbol Types = Asterisk, Backslash, Backslash Square, Circle, Diamond, Forwardshlash, Forwardslash Square, Hash, Hash Diamond, Hash Square, Hash Triangle, Hash Triangle2,
               Hourglass, Open Circle, Open Diamond, Open Hourglass, Open Square, Open Triangle, Open Triangle2, Pipe, Pipe Diamond, Pipe Square, Plus, Plus Circle,
               Plus Diamond, Plus Square, Square, Triangle, Triangle2, X, X Circle, X Square, X Triangle, X Triangle2 
'''
# Properties assigned to the individual curves
CurveProperties =   {
                        #    Parameter              LineColor        LineStyle       LineWeight    Fill Type    Fill Color      Fill Pattern     SymbolVisible       SymbolType      SymbolSize        SymbolLineColor     SymbolFillColor     SymbolInterval      SymbolSkipCount     FirstSymbolOffset                
                        #    --------------         -----------      ------------    ----------    ----------   ------------    -------------    ----------------    ------------    -----------       ----------------    ----------------    ----------------    ----------------    -----------------           
                            'Elev'           :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'Stage'          :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'Flow'           :    [ 'blue',          'Solid',        2,            'None',      'blue',         'Solid',         Constants.FALSE,    'X',            7,                'blue',             'blue',             0,                  0,                  0],
                            'Elev-radar'         :    [ 'red',           'Solid',        2,            'None',      'red',          'Solid',         Constants.FALSE,    'Circle',       7,                'red',              'red',              0,                  0,                  0],
                            'Volt'        :    [ 'darkgray',          'Solid',        2,            'None',      'darkgray',         'Solid',         Constants.FALSE,    'Diamond',      7,                'darkgray',             'darkgray',             0,                  0,                  0],
                            'Precip'         :    [ 'blue',       'Solid',        2,            'None',      'blue',      'Solid',         Constants.FALSE,    'Square',       7,                'blue',          'blue',          0,                  0,                  0],
                    }

# Properties assigned to plot markers (NOT USED IN THIS SCRIPT)
MarkerProperties =  {
                        #    Marker                           Display (True or False)    Pathname             Value     Tsc            Label Text                                 Label Font         Axis           LabelAlignment     LabelPosition   LabelColor      LineStyle      LineColor    LineWidth                   
                        #    -----------------------          -----------------------    -------------        --------  -----------    -------------------------------------      ------------       ------------   ---------------    ------------    ------------    ----------     ----------   -----------        
                            'TopOfConsZone'             :   [ False,                     None,                None,     None,          'Base of Annual Flood Control Zone',       'Arial,Plain,12',  'Y1',          'left',            'above',        'black',        'Dash Dot',    'black',     1],         
                            'TopOfFloodCtrZone'         :   [ False,                     None,                None,     None,          'Base of Exclusive Flood Control Zone',    'Arial,Plain,12',  'Y1',          'left',            'above',        'darkred',      'Dash Dot',    'darkred',   1],        
                            'TopOfExclZone'             :   [ False,                     None,                None,     None,          'Top of Exclusive Flood Control Zone',     'Arial,Plain,12',  'Y1',          'left',            'above',        'darkcyan',     'Dash Dot',    'darkcyan',  1],        
                    }

# Properties assigned to the plot
PlotProperties = {  
                    # Title Properties
                    'Font'              :   'Arial',
                    'FontColor'         :   'black',
                    'FontStyle'         :   'Normal',
                    'FontSize'          :   20,
                    # Plot File Properties
                    'PlotWidth'         :   1000,
                    'PlotHeight'        :   800,
                    'PlotQuality'       :   100 # range of 0 (crappy) to 100 (great, but larger file)
                    }

# -------------------------------------------------------------------
# Main Script
# -------------------------------------------------------------------

try :
    #
    # Date and time
    #
	Lookback    = 10 									# Number of days to lookback and set the start of the time window
	CurDate     = datetime.datetime.now() 					# Current date
	EndTwStr    = CurDate.strftime('%d%b%Y %H%M')			#Setting the end time window string as today
	StartTw     = CurDate - datetime.timedelta(Lookback)			#Setting the start time window variable to Lookback days back
	StartTwStr  = StartTw.strftime('%d%b%Y %H%M')			#Setting the start time window string as Lookback days ago
	outputDebug(debug, lineNo(), 'Time window = %s -- %s' % (StartTwStr, EndTwStr))
	try :
		CwmsDb = DBAPI.open()						#opening cwms db
		if not CwmsDb : raise Exception		
		CwmsDb.setTimeWindow(StartTwStr, EndTwStr)		#setting the time window
		CwmsDb.setOfficeId('NWDM')					#setting the office ID to NWDM
		CwmsDb.setTimeZone('US/Central')				#Setting the timezone to 'US/Central' time
		conn = CwmsDb.getConnection()
	except :
		outputDebug(debug, lineNo(), 'Could not open DBI, exiting.')
		sys.exit(-1)
	
	# Get list of pathnames in database
	PathnameList = CwmsDb.getPathnameList()


    
############################################################################
################				PT. 1 ---- ELEVATION/STAGE			#######################
############################################################################


#Creating plots for locations with only elevation/stage gages


#for every project in the StageOnly array loop through the for loop
	for projectID in StageOnly :
		try :

			DataDict[projectID]['PlotTitle']	   							# Using the data dictionary setting the plot title 
			pathName = DataDict[projectID]['surfacePath']					#setting the pathName variable to the CWMS path for each project in this loop
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
			# Retrieve time series from database and add to list
			#if (pathName) in PathnameList :
			try : Tsc = CwmsDb.read(pathName).getData()					#Reading data then getting data from the database
			except : Tsc = CwmsDb.get(pathName)						#if that doesn't work just get the data from the database

			
			# Create plot
			plot = Plot.newPlot()			#Creating new plot
			layout = Plot.newPlotLayout()		#Setting a layout variable so we can make viewports
			
			# Create viewports
			TopViewportLayout = layout.addViewport()
			
			# Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
			#    If defaults curve properties are wanted, specify the CurvePropertyKey as None
			#                           Viewport Layout       Time Series     Axes        CurvePropertyKey
			#                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Stage']
									]

			# Add time series to plot and format curves
			plot = createPlot(  debug,               	# Set to True or False to print debug statements
								CwmsDb,              	# CWMS database connection
								projectID,            	# DCP ID of location
								plot,                		# Plot
								layout,              		# Plot layout
								ViewportLayoutsInfo, 	# Lists of ViewportLayouts, time series, and axis for each curve
								DataDict,  			# Properties of locations
								CurveProperties,     	# Properties of curves in the plot
								MarkerProperties,   	# Properties of markers in the plot
								PlotProperties,      	# Properties of plot
								)

			# Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilename % projectID.lower())
			plot.saveToJpeg (PlotFilename % projectID.lower(), PlotProperties['PlotQuality'])			#converting the plot to a jpeg image
			
			# Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Plot closed' % projectID)
		except :
			outputDebug(True, lineNo(), 'Could not create %s plot' % projectID)

        # Close plot
		try : plot.close()
		except : pass


#############################################################################################
######################		PT. 1-5 ----- CHCR RADAR ELEV PLOT		#######################################
#############################################################################################

	for projectID in ['CHCR'] :
		try :

			DataDict[projectID]['PlotTitle']	   							# Using the data dictionary setting the plot title 
			pathName = DataDict[projectID]['surfacePath2']					#setting the pathName variable to the CWMS path for each project in this loop
			outputDebug(debug, lineNo(), 'Creating radar plot for %s' % projectID)
			# Retrieve time series from database and add to list
			#if (pathName) in PathnameList :
			try : Tsc = CwmsDb.read(pathName).getData()					#Reading data then getting data from the database
			except : Tsc = CwmsDb.get(pathName)						#if that doesn't work just get the data from the database

			
			# Create plot
			plot = Plot.newPlot()			#Creating new plot
			layout = Plot.newPlotLayout()		#Setting a layout variable so we can make viewports
			
			# Create viewports
			TopViewportLayout = layout.addViewport()
			
			# Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
			#    If defaults curve properties are wanted, specify the CurvePropertyKey as None
			#                           Viewport Layout       Time Series     Axes        CurvePropertyKey
			#                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Stage']
									]

			# Add time series to plot and format curves
			plot = createPlot(  debug,               	# Set to True or False to print debug statements
								CwmsDb,              	# CWMS database connection
								projectID,            	# DCP ID of location
								plot,                		# Plot
								layout,              		# Plot layout
								ViewportLayoutsInfo, 	# Lists of ViewportLayouts, time series, and axis for each curve
								DataDict,  			# Properties of locations
								CurveProperties,     	# Properties of curves in the plot
								MarkerProperties,   	# Properties of markers in the plot
								PlotProperties,      	# Properties of plot
								)

			# Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', ImagesDirectory + '%sRadarRaw.jpg' % projectID.lower())
			plot.saveToJpeg (ImagesDirectory + '%sRadarRaw.jpg' % projectID.lower(), PlotProperties['PlotQuality'])			#converting the plot to a jpeg image
			
			# Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Radar Plot closed' % projectID)
		except :
			outputDebug(True, lineNo(), 'Could not create %s radar plot' % projectID)

        # Close plot
		try : plot.close()
		except : pass



#############################################################################################
######################		PT. 2 ---- PRECIPITATION + ELEVATION/STAGE				##########################
#############################################################################################


	
	# Add data and format plot
	for projectID in StagePrecip :
		try :
			# Retrieve LongName from database and modify to create the Plot Title. If there is a Plot Title already specified in LocationProperties, use that.
			#    Not all base locations have 
			
	                DataDict[projectID]['PlotTitle']							#Same as "PT. 1 ELEVATION/STAGE"
			PathName1 = DataDict[projectID]['surfacePath']				#Same as "PT. 1 ELEVATION/STAGE"
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
			# Retrieve time series from database and add to list
			# Elevation data
			
			try : surfaceTsc = CwmsDb.read(PathName1).getData()			#Same as "PT. 1 ELEVATION/STAGE"
			except : surfaceTsc = CwmsDb.get(PathName1)				#Same as "PT. 1 ELEVATION/STAGE"

			PathName2 = DataDict[projectID]['precipPath']				#Adding a new pathname to be used in the plot (precip)
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)	
			# Retrieve time series from database and add to list
			# Elevation data
			
			try : precipTsc = CwmsDb.read(PathName2).getData()			#Having CWMS read and get data from PathName2
			except : precipTsc = CwmsDb.get(PathName2)				#If it didn't work just get the data from PathName2
			    
	
	                
	                # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
	                
	                # Create viewports
			TopViewportLayout = layout.addViewport(50)		#making the total image be split  into 2 plots with a viewport on the top and bottom
			BottomViewportLayout = layout.addViewport(50)		#the 50 means 50:50 split
	                
	                # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
	                #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
	                #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
	                #                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    precipTsc,      'Y1',       'Precip'],		#Need a top and bottom viewport so we can see both precip and stage/elevation 
	                                        [   BottomViewportLayout, surfaceTsc,        'Y1',       'Stage']
	                                            ]
	    
	            
	                # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
	                                    CwmsDb,              # CWMS database connection
	                                    projectID,            # DCP ID of location
	                                    plot,                # Plot
	                                    layout,              # Plot layout
	                                    ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
	                                    DataDict,  # Properties of locations
	                                    CurveProperties,     # Properties of curves in the plot
	                                    MarkerProperties,    # Properties of markers in the plot
	                                    PlotProperties,      # Properties of plot
	                                    )
	        
			plot.setName(projectID + ' -plot window') 
	        	        # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilename % projectID.lower())
			plot.saveToJpeg (PlotFilename % projectID.lower(), PlotProperties['PlotQuality'])		#converting the plot to a jpeg image
	                
	                # Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Plot closed' % projectID)
		except :
				outputDebug(True, lineNo(), 'Could not create %s plot' % projectID)
				print(traceback.format_exc())
	       	         # Close plot
				try : 
					plot.close()
					outputDebug(True, lineNo(), '%s Plot closed' % projectID)
				except : pass


#########################################################################################
########################			PT. 3 - RADAR + ORIFICE + PRECIP				######################
#########################################################################################

	for projectID in RadarPrecip :
		try :
			# Retrieve LongName from database and modify to create the Plot Title. If there is a Plot Title already specified in LocationProperties, use that.
			#    Not all base locations have 
			
	                DataDict[projectID]['PlotTitle']								#Same as PT. 1 and PT. 2
			PathName1 = DataDict[projectID]['surfacePath']					#Same as PT. 1 and PT. 2
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
			
			try : surfaceTsc = CwmsDb.read(PathName1).getData()				#Same as PT. 1 and PT. 2
			except : surfaceTsc = CwmsDb.get(PathName1)					#Same as PT. 1 and PT. 2


			PathName2 = DataDict[projectID]['precipPath']					#Same as PT. 2
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)		#Same as PT. 2
			
			try : precipTsc = CwmsDb.read(PathName2).getData()				#Same as PT. 2
			except : precipTsc = CwmsDb.get(PathName2)					#Same as PT. 2


			PathName3 = DataDict[projectID]['surfacePath2']					#third pathname will be used for the radar gages
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
			
			try : surfaceTsc2 = CwmsDb.read(PathName3).getData()
			except : surfaceTsc2 = CwmsDb.get(PathName3)
			    
	
	                
	                # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
	                
	                # Create viewports
			TopViewportLayout = layout.addViewport(50)
			BottomViewportLayout = layout.addViewport(50)
	                
	                # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
	                #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
	                #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
	                #                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    precipTsc,      'Y1',       'Precip'],
						[   BottomViewportLayout, surfaceTsc2,     'Y1',       'Elev-radar'],
	                  			[   BottomViewportLayout, surfaceTsc,        'Y1',       'Stage'],
	                                       
	                                            ]
	    
	            
	                # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
	                                    CwmsDb,              # CWMS database connection
	                                    projectID,            # DCP ID of location
	                                    plot,                # Plot
	                                    layout,              # Plot layout
	                                    ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
	                                    DataDict,  # Properties of locations
	                                    CurveProperties,     # Properties of curves in the plot
	                                    MarkerProperties,    # Properties of markers in the plot
	                                    PlotProperties,      # Properties of plot
	                                    )
	        
			plot.setName(projectID + ' -plot window') 
	        	        # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilename % projectID.lower())
			plot.saveToJpeg (PlotFilename % projectID.lower(), PlotProperties['PlotQuality'])			#Saving plot as a jpeg image
	                
	                # Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Plot closed' % projectID)
		except :
				outputDebug(True, lineNo(), 'Could not create %s plot' % projectID)
				print(traceback.format_exc())
	       	         # Close plot
				try : 
					plot.close()
					outputDebug(True, lineNo(), '%s Plot closed' % projectID)
				except : pass


#########################################################################################
########################					PT. 4 - PRECIP						######################
#########################################################################################

    # Add data and format plot
	for projectID in PrecipOnly :
		try :
            
			DataDict[projectID]['PlotTitle']	   
			pathName = DataDict[projectID]['precipPath']
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
            # Retrieve time series from database and add to list
            #if (pathName) in PathnameList :
			try : Tsc = CwmsDb.read(pathName).getData()
			except : Tsc = CwmsDb.get(pathName)

            
            # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
            
            # Create viewports
        	    	TopViewportLayout = layout.addViewport()
            
            # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
            #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
            #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
            #                           -----------------     ------------    --------    ----------------
          	  	ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Precip']
                                    ]
    
            # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
                                CwmsDb,              # CWMS database connection
                                projectID,            # DCP ID of location
                                plot,                # Plot
                                layout,              # Plot layout
                                ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
                                DataDict,  # Properties of locations
                                CurveProperties,     # Properties of curves in the plot
                                MarkerProperties,    # Properties of markers in the plot
                                PlotProperties,      # Properties of plot
                                )
    
            # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilename % projectID.lower())
			plot.saveToJpeg (PlotFilename % projectID.lower(), PlotProperties['PlotQuality'])
            
            # Close plot
           	 	plot.close()
            		outputDebug(debug, lineNo(), '%s Plot closed' % projectID)
		except :
			outputDebug(True, lineNo(), 'Could not create %s plot' % projectID)
		print(traceback.format_exc())
	    # Close plot
		try : plot.close()
		except : pass

################################################################################
########################		PT. 5 - VOLTS ONLY 		#################################
################################################################################
	PathnameList = CwmsDb.getPathnameList()
	for projectID in VoltOnly :
		try :
		    
			DataDict[projectID]['PlotTitle']	   
			pathName = DataDict[projectID]['voltPath']
			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
			print pathName + ' PathName'
			print pathName in PathnameList
		    # Retrieve time series from database and add to list
		    #if (pathName) in PathnameList :
			if pathName in PathnameList :
		            try : Tsc = CwmsDb.read(pathName).getData()
		            except : Tsc = CwmsDb.get(pathName)
			else :
		        # Create a blank time series so the plot can be created
		        	Tsc = createBlankTimeSeries(debug, '%s.Volt.Inst.15Minutes.0.No Available Data' % projectID, 'Volts', StartTw, EndTwStr)
		    
		    # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
		    
		    # Create viewports
			TopViewportLayout = layout.addViewport()
		    
		    # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
		    #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
		    #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
		    #                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Volt']
		                            ]
		
		    # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
		                        CwmsDb,              # CWMS database connection
		                        projectID,            # DCP ID of location
		                        plot,                # Plot
		                        layout,              # Plot layout
		                        ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
		                        DataDict,  # Properties of locations
		                        CurveProperties,     # Properties of curves in the plot
		                        MarkerProperties,    # Properties of markers in the plot
		                        PlotProperties,      # Properties of plot
		                        )
		
		    # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilenameVolt % projectID.lower())
			plot.saveToJpeg (PlotFilenameVolt % projectID.lower(), PlotProperties['PlotQuality'])
		    
		    # Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Plot closed' % projectID)
		except :
			outputDebug(True, lineNo(), 'Could not create %s plot' % projectID)
		print(traceback.format_exc())
		    # Close plot
		try : plot.close()
		except : pass


################################################################################
########################		PT. 5.1- CHCR VOLT-ORIFICE ONLY 		#######################
################################################################################
	PathnameList = CwmsDb.getPathnameList()
	for projectID in ['CHCR'] :
		try :
		    
			DataDict[projectID]['PlotTitle']	   
			pathName = DataDict[projectID]['voltPath']
			outputDebug(debug, lineNo(), 'Creating plot for %s Volt-Orifice' % projectID)
			print pathName + ' PathName'
			print pathName in PathnameList
		    # Retrieve time series from database and add to list
		    #if (pathName) in PathnameList :
			if pathName in PathnameList :
		            try : Tsc = CwmsDb.read(pathName).getData()
		            except : Tsc = CwmsDb.get(pathName)
			else :
		        # Create a blank time series so the plot can be created
		        	Tsc = createBlankTimeSeries(debug, '%s.Volt.Inst.15Minutes.0.No Available Data' % projectID, 'Volts', StartTw, EndTwStr)
		    
		    # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
		    
		    # Create viewports
			TopViewportLayout = layout.addViewport()
		    
		    # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
		    #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
		    #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
		    #                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Volt']
		                            ]
		
		    # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
		                        CwmsDb,              # CWMS database connection
		                        projectID,            # DCP ID of location
		                        plot,                # Plot
		                        layout,              # Plot layout
		                        ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
		                        DataDict,  # Properties of locations
		                        CurveProperties,     # Properties of curves in the plot
		                        MarkerProperties,    # Properties of markers in the plot
		                        PlotProperties,      # Properties of plot
		                        )
		
		    # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', ImagesDirectory + '%sVoltOrifice.jpg' % projectID.lower())
			plot.saveToJpeg (ImagesDirectory + '%sVoltOrifice.jpg' % projectID.lower(), PlotProperties['PlotQuality'])
		    
		    # Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Volt-Orifice Plot closed' % projectID)
		except :
			outputDebug(True, lineNo(), 'Could not create %s Volt-Orifice plot' % projectID)
		print(traceback.format_exc())
		    # Close plot
		try : plot.close()
		except : pass


################################################################################
########################		PT. 5.1- CHCR VOLT-ORIFICE ONLY 		#######################
################################################################################
	PathnameList = CwmsDb.getPathnameList()
	for projectID in ['CHCR'] :
		try :
		    
			DataDict[projectID]['PlotTitle']	   
			pathName = DataDict[projectID]['volt2Path']
			outputDebug(debug, lineNo(), 'Creating plot for %s Volt-Radar' % projectID)
			print pathName + ' PathName'
			print pathName in PathnameList
		    # Retrieve time series from database and add to list
		    #if (pathName) in PathnameList :
			if pathName in PathnameList :
		            try : Tsc = CwmsDb.read(pathName).getData()
		            except : Tsc = CwmsDb.get(pathName)
			else :
		        # Create a blank time series so the plot can be created
		        	Tsc = createBlankTimeSeries(debug, '%s.Volt.Inst.15Minutes.0.No Available Data' % projectID, 'Volts', StartTw, EndTwStr)
		    
		    # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
		    
		    # Create viewports
			TopViewportLayout = layout.addViewport()
		    
		    # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
		    #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
		    #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
		    #                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Volt']
		                            ]
		
		    # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
		                        CwmsDb,              # CWMS database connection
		                        projectID,            # DCP ID of location
		                        plot,                # Plot
		                        layout,              # Plot layout
		                        ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
		                        DataDict,  # Properties of locations
		                        CurveProperties,     # Properties of curves in the plot
		                        MarkerProperties,    # Properties of markers in the plot
		                        PlotProperties,      # Properties of plot
		                        )
		
		    # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', ImagesDirectory + '%sVoltRadar.jpg' % projectID.lower())
			plot.saveToJpeg (ImagesDirectory + '%sVoltRadar.jpg' % projectID.lower(), PlotProperties['PlotQuality'])
		    
		    # Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Volt-Radar Plot closed' % projectID)
		except :
			outputDebug(True, lineNo(), 'Could not create %s Volt-Radar plot' % projectID)
		print(traceback.format_exc())
		    # Close plot
		try : plot.close()
		except : pass

		

################################################################################
########################		PT. 6 - PIST & PIST-OFFICE VOLTS 		#######################
################################################################################
	PathnameList = CwmsDb.getPathnameList()
	for projectID in Voltx2 :
		try :
		    
			DataDict[projectID]['PlotTitle']	   
			pathName = DataDict[projectID]['voltPath']
			pathName2 = DataDict[projectID]['volt2Path']

			outputDebug(debug, lineNo(), 'Creating plot for %s' % projectID)
			print pathName + ' PathName'
			print pathName in PathnameList
			
		    # Retrieve time series from database and add to list
		    #if (pathName) in PathnameList :
			if pathName in PathnameList :
		            try : PistDam = CwmsDb.read(pathName).getData()
		            except : PistDam = CwmsDb.get(pathName)
			else :
		        # Create a blank time series so the plot can be created
		        	PistDam = createBlankTimeSeries(debug, '%s.Volt.Inst.15Minutes.0.No Available Data' % projectID, 'Volts', StartTw, EndTwStr)

			if pathName2 in PathnameList :
		            try : PistOffice = CwmsDb.read(pathName2).getData()
		            except : PistOffice = CwmsDb.get(pathName2)
			else :
		        # Create a blank time series so the plot can be created
		        	PistOffice = createBlankTimeSeries(debug, '%s.Volt.Inst.15Minutes.0.No Available Data' % projectID, 'Volts', StartTw, EndTwStr)		       
		    
		    # Create plot
			plot = Plot.newPlot()
			layout = Plot.newPlotLayout()
		    
		    # Create viewports
			TopViewportLayout = layout.addViewport()
		    
		    # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
		    #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
		    #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
		    #                           -----------------     ------------    --------    ----------------
			ViewportLayoutsInfo = [ [   TopViewportLayout,    PistDam,            'Y1',       'Volt'],
								[   TopViewportLayout,    PistOffice,            'Y1',       'Flow']
		                            ]
		
		    # Add time series to plot and format curves
			plot = createPlot(  debug,               # Set to True or False to print debug statements
		                        CwmsDb,              # CWMS database connection
		                        projectID,            # DCP ID of location
		                        plot,                # Plot
		                        layout,              # Plot layout
		                        ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
		                        DataDict,  # Properties of locations
		                        CurveProperties,     # Properties of curves in the plot
		                        MarkerProperties,    # Properties of markers in the plot
		                        PlotProperties,      # Properties of plot
		                        )
		
		    # Save plot file
			outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilenameVolt % projectID.lower())
			plot.saveToJpeg (PlotFilenameVolt % projectID.lower(), PlotProperties['PlotQuality'])
		    
		    # Close plot
			plot.close()
			outputDebug(debug, lineNo(), '%s Plot closed' % projectID)
		except Exception, e : 
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
			formatted_lines = traceback.format_exc().splitlines()
			TracebackStr = '\n'.join(formatted_lines)
			outputDebug(True, lineNo(), 'Could not create %s plot' % location)
			print TracebackStr
		except java.lang.Exception, e : 
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
			formatted_lines = traceback.format_exc().splitlines()
			TracebackStr = '\n'.join(formatted_lines)
			outputDebug(True, lineNo(), 'Could not create %s plot' % location)
			print TracebackStr

			# Close plot
			try : plot.close()
			except : pass
finally :
    # Close database connection
    try : 
        CwmsDb.done()
        outputDebug(True, lineNo(), 'Database connection closed')
    except : pass
    try : 
        conn.done()
        outputDebug(True, lineNo(), 'Database connection closed')
    except : pass
