'''
Author: Ryan Larsen
Last Updated: 04-23-2021
Description: Creates plots comparing current and last year stage and flow for mainstem river gages.

Script Procedure
    1. The plot will display XX days of data starting with the most recent data
    2. Time series pathnames are imported from the DatabasePathnames.txt file, which is located in the cronjobs directory.
        a. These pathnames allow for string substitutions of the base location
    3. The plot layout is configured using the ViewportLayoutsInfo dictionary. The user can specify which viewport, Y axis, and curve properties each time series will
       be displayed with.
    4. User can change curve properties (i.e. color, line width, etc.) by editing the CurveProperties dictionary for the type of data that is to being displayed. 
       If a marker is to be used (i.e. base of flood control), the user can edit the marker properties in the MarkerProperties dictionary. The plot size, font, plot quality,
       etc. can be edited in the PlotProperties dictionary. All three of these dictionaries can be found in the Input section of the script.
    5. If the user wants to specify a plot title, it is entered in the LocationProperties dictionary with the Base Location as the first key and 'PlotTitle' as the second
       key (i.e. LocationProperties = {'KANS' : {'PlotTitle' : 'Kanopolis Lake on the Smoky Hill R, KS'}}. If the Base Location's Long Name has been setup in the database,
       the Base Location should not be entered into the LocationProperties dictionary and the script will use the Long Name to create the PlotTitle and will save it to the
       LocationProperties dictionary. The Long Name for reservoirs should be formatted as 'Dam Name' & Reservoir on 'River Name' near 'City, State'. For example, Gavins
       Point's Long Name is Gavins Point Dam & Reservoir on Missouri River near Yankton, SD. The Long Name for river gages should be formatted as 'River Name' at/near
       'City, State'. For example, the gage at Sioux City, IA is Missouri River at Sioux City, IA. If a river gage has a specified flood stage, it will add that to the
       PlotTitle as a second line. 
    6. All of this information is then passed to the createPlot function, which resides in the ServerUtils.py file in the cronjobs directory. This function will create the
       plot with the specified properties. It will also auto scale the Y axes to fit the data better. Without the auto-scaling feature, the default scaling sometimes shrinks
       the axes too much and makes it difficult to read the data.
To create a plot for a new location
    1. Add the DCP ID to the Locations list in the Input section.
    2. Add the DCP ID to the LocationProperties dictionary in the Input section if a PlotTitle will not be automatically generated from the Long Name.
    3. Add a plot title to the LocationProperties dictionary. This will be displayed at the top of the chart. 
    4. Modify any curve, marker, or plot properties in the CurveProperties, MarkerProperties, or PlotProperties, respectively.
    5. Add the viewport, time series, axis designations, and CurvePropertiesKey in the ViewportLayoutsInfo dictionary in the Main section.
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
global CurveProperties, MarkerProperties, PlotProperties

# -------------------------------------------------------------------
# Import database pathnames and plotting functions
# -------------------------------------------------------------------
# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\Scripts\\MRBWM\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\"
    PlotsDirectory = CronjobsDirectory + "Plots\\"
    ImagesDirectory = PlotsDirectory + "Images\\"
else :
    # Server pathnames
    PlotsDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = PlotsDirectory.split('/')
    CronjobsDirectory = '/'.join(PathList[: -1]) + '/'
    PlotsDirectory += '/'
    ImagesDirectory = PlotsDirectory + 'Images/MRBWM/'
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

# Import server utilities
import Server_Utils
reload(Server_Utils)
from Server_Utils import createBlankTimeSeries, lineNo, outputDebug, createPlot, retrieveLongName

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False

# Plot filename with a string substitution
PlotFilename = ImagesDirectory + '%scomp.jpg'

# List of locations to be included on plot
Locations = [   # Mainstem Stations
                'GAPT', 'YKN', 'SUX', 'DENE', 'OMA', 'NCNE', 'RUNE', 'STJ', 'MKC', 'WVMO', 'BNMO', 'HEMO'
                ]

# Dictionary of data
LocationProperties = {  # Mainstem Stations
                        'YKN'               :    {  'PlotTitle'         :   'Missouri River at Yankton, SD\nFlood Stage = 20 ft',
                                                    },
                        'DENE'              :    {  'PlotTitle'         :   'Missouri River at Decatur, NE\nFlood Stage = 35 ft',
                                                    },
                        'SUX'               :    {  'PlotTitle'         :   'Missouri River at Sioux City, IA\nFlood Stage = 30 ft',
                                                    },
                        'OMA'               :    {  'PlotTitle'         :   'Missouri River at Omaha, NE\nFlood Stage = 27 ft',
                                                    },
                        'NCNE'              :    {  'PlotTitle'         :   'Missouri River at Nebraska City, NE\nFlood Stage = 18 ft',
                                                    },
                        'RUNE'              :    {  'PlotTitle'         :   'Missouri River at Rulo, NE\nFlood Stage = 17 ft',
                                                    },
                        'STJ'               :    {  'PlotTitle'         :   'Missouri River at St. Joseph, MO\nFlood Stage = 17 ft',
                                                    },
                        'MKC'               :    {  'PlotTitle'         :   'Missouri River at Kansas City, MO\nFlood Stage = 32 ft',
                                                    },
                        'WVMO'              :    {  'PlotTitle'         :   'Missouri River at Waverly, MO\nFlood Stage = 20 ft',
                                                    },
                        'BNMO'              :    {  'PlotTitle'         :   'Missouri River at Boonville, MO\nFlood Stage = 21 ft',
                                                    },
                        'HEMO'              :    {  'PlotTitle'         :   'Missouri River at Hermann, MO\nFlood Stage = 21 ft',
                                                    },
                }

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
                            'CurElev'        :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'PastElev'       :    [ 'red',           'Solid',        2,            'None',      'red',          'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'CurStage'       :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'PastStage'      :    [ 'red',           'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'CurFlow'        :    [ 'blue',          'Solid',        2,            'None',      'blue',         'Solid',         Constants.FALSE,    'X',            7,                'blue',             'blue',             0,                  0,                  0],
                            'PastFlow'       :    [ 'darkyellow',    'Solid',        2,            'None',      'blue',         'Solid',         Constants.FALSE,    'X',            7,                'blue',             'blue',             0,                  0,                  0],
                            'Inflow'         :    [ 'red',           'Solid',        2,            'None',      'red',          'Solid',         Constants.FALSE,    'Circle',       7,                'red',              'red',              0,                  0,                  0],
                            'Storage'        :    [ 'gray',          'Solid',        2,            'None',      'gray',         'Solid',         Constants.FALSE,    'Diamond',      7,                'gray',             'gray',             0,                  0,                  0],
                            'Precip'         :    [ 'darkred',       'Solid',        2,            'None',      'darkred',      'Solid',         Constants.FALSE,    'Square',       7,                'darkred',          'darkred',          0,                  0,                  0],
                    }

# Properties assigned to plot markers
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
    Lookback            = 90 # Number of days to lookback and set the start of the time window
    CurDate             = datetime.datetime.now() # Current date
    CurYear             = CurDate.year
    LastYrYear          = CurYear - 1
    CurStartTw          = CurDate - datetime.timedelta(Lookback)
    CurStartTwStr       = CurStartTw.strftime('%d%b%Y %H%M')
    LastYrStartYear     = CurStartTw.year - 1
    LastYrStartTw       = CurStartTw.replace(year = LastYrStartYear)
    LastYrStartTwStr    = LastYrStartTw.strftime('%d%b%Y %H%M')
    CurEndTw            = CurDate# + datetime.timedelta(Lookback)
    CurEndTwStr         = CurEndTw.strftime('%d%b%Y %H%M')
    LastYrEndYear       = CurEndTw.year - 1
    LastYrEndTw         = CurEndTw.replace(year = LastYrEndYear)
    LastYrEndTwStr      = LastYrEndTw.strftime('%d%b%Y %H%M')
    outputDebug(True, lineNo(), 'Current Year Time window = %s -- %s' % (CurStartTwStr, CurEndTwStr),
                '\n\t\tLast Year Time Window = %s -- %s' % (LastYrStartTwStr, LastYrEndTwStr))
    try :
        CwmsDb = DBAPI.open()
        if not CwmsDb : raise Exception
        CwmsDb.setTimeWindow(LastYrStartTwStr, CurEndTwStr)
        CwmsDb.setOfficeId('NWDM')
        CwmsDb.setTimeZone('US/Central')
        CwmsDb.setTrimMissing(False)
        conn = CwmsDb.getConnection()
    except :
        outputDebug(debug, lineNo(), 'Could not open DBI, exiting.')
        sys.exit(-1)
    
    # Get list of pathnames in database
    PathnameList = CwmsDb.getPathnameList()
    
    # Add data and format plot
    for location in Locations :
        try :
            # Retrieve LongName from database and modify to create the Plot Title. If there is a Plot Title already specified in LocationProperties, use that.
            #    Not all base locations have 
            try : 
                LocationProperties[location]['PlotTitle']
            except :
                LongName = retrieveLongName(debug, conn, location)
                PlotTitle = LongName.replace(' on ', '\n')
                LocationProperties.setdefault(location, {}).setdefault('PlotTitle', PlotTitle)

            outputDebug(debug, lineNo(), 'Creating plot for %s' % location)
            # Retrieve time series from database and add to list
            # Stage or Elevation data
            if (ElevInstHourBestMrbwm % location) in PathnameList :
                try : 
                    CurStageTsc = CwmsDb.read(ElevInstHourBestMrbwm % location, CurStartTwStr, CurEndTwStr).getData()
                    LastYrStageTsc = CwmsDb.read(ElevInstHourBestMrbwm % location, LastYrStartTwStr, LastYrEndTwStr).getData()
                except : 
                    CurStageTsc = CwmsDb.get(ElevInstHourBestMrbwm % location, CurStartTwStr, CurEndTwStr)
                    LastYrStageTsc = CwmsDb.get(ElevInstHourBestMrbwm % location, LastYrStartTwStr, LastYrEndTwStr)
            elif (StageInstHourBestNwdm % location) in PathnameList :
                try : 
                    CurStageTsc = CwmsDb.read(StageInstHourBestNwdm % location, CurStartTwStr, CurEndTwStr).getData()
                    LastYrStageTsc = CwmsDb.read(StageInstHourBestNwdm % location, LastYrStartTwStr, LastYrEndTwStr).getData()
                except :
                    CurStageTsc = CwmsDb.read(StageInstHourBestNwdm % location, CurStartTwStr, CurEndTwStr).getData()
                    LastYrStageTsc = CwmsDb.read(StageInstHourBestNwdm % location, LastYrStartTwStr, LastYrEndTwStr).getData()
            else :
                # Create a blank time series so the plot can be created
                CurStageTsc = createBlankTimeSeries(debug, '%s.Stage.Inst.1Hour.0.No Available Data Current Year' % location, 'ft', StartTw, EndTwStr)
                LastYrStageTsc = createBlankTimeSeries(debug, '%s.Stage.Inst.1Hour.0.No Available Data Last Year' % location, 'ft', StartTw, EndTwStr)

            # Change version
            CurStageFullname = CurStageTsc.fullName
            CurStageParts = CurStageFullname.split('.')
            CurStageTsc.version = '%d %s' % (CurYear, CurStageTsc.version)
            CurStageParts[-1] = CurStageTsc.version
            CurStageTsc.fullName = '.'.join(CurStageParts)

            LastYrStageFullname = LastYrStageTsc.fullName
            LastYrStageParts = LastYrStageFullname.split('.')
            LastYrStageTsc.version = '%d %s' % (LastYrYear, LastYrStageTsc.version)
            LastYrStageParts[-1] = LastYrStageTsc.version
            LastYrStageTsc.fullName = '.'.join(LastYrStageParts)
            
            # Screen 29Feb from time series. If plotting data from a leap year and non leap year, an error will occur because the number of values are not the same
            CurStageValues, CurStageTimes = [], []
            for x in range(len(CurStageTsc.values)) :
                hecTime = HecTime(); hecTime.set(CurStageTsc.times[x])
                if hecTime.date(4)[ : 5] != '29Feb' : 
                    CurStageValues.append(CurStageTsc.values[x])
                    CurStageTimes.append(CurStageTsc.times[x])
            CurStageTsc.values = CurStageValues
            CurStageTsc.numberValues = len(CurStageValues)
            CurStageTsc.times = CurStageTimes
            CurStageTsc.startTime = CurStageTimes[0]
            CurStageTsc.endTime = CurStageTimes[-1]
            
            LastYrStageValues, LastYrStageTimes = [], []
            for x in range(len(LastYrStageTsc.values)) :
                hecTime = HecTime(); hecTime.set(LastYrStageTsc.times[x])
                if hecTime.date(4)[ : 5] != '29Feb' : 
                    LastYrStageValues.append(LastYrStageTsc.values[x])
                    LastYrStageTimes.append(LastYrStageTsc.times[x])

            LastYrStageTsc.values = LastYrStageValues
            LastYrStageTsc.numberValues = len(LastYrStageValues)
            # Shift last years data to this year to synchronize the plot
            LastYrStageTsc.times = CurStageTsc.times
            LastYrStageTsc.startTime = LastYrStageTimes[0]
            LastYrStageTsc.endTime = LastYrStageTimes[-1]
            
            # Flow data
            if (FlowOutInstHourBestMrbwm % location) in PathnameList :
                try : 
                    CurFlowTsc = CwmsDb.read(FlowOutInstHourBestMrbwm % location, CurStartTwStr, CurEndTwStr).getData()
                    LastYrFlowTsc = CwmsDb.read(FlowOutInstHourBestMrbwm % location, LastYrStartTwStr, LastYrEndTwStr).getData()
                except : 
                    CurFlowTsc = CwmsDb.get(FlowOutInstHourBestMrbwm % location, CurStartTwStr, CurEndTwStr)
                    LastYrFlowTsc = CwmsDb.get(FlowOutInstHourBestMrbwm % location, LastYrStartTwStr, LastYrEndTwStr)
            elif (FlowInstHourBestNwdm % location) in PathnameList :
                try :
                    CurFlowTsc = CwmsDb.read(FlowInstHourBestNwdm % location, CurStartTwStr, CurEndTwStr).getData()
                    LastYrFlowTsc = CwmsDb.read(FlowInstHourBestNwdm % location, LastYrStartTwStr, LastYrEndTwStr).getData()
                except : 
                    CurFlowTsc = CwmsDb.get(FlowInstHourBestNwdm % location, CurStartTwStr, CurEndTwStr)
                    LastYrFlowTsc = CwmsDb.get(FlowInstHourBestNwdm % location, LastYrStartTwStr, LastYrEndTwStr)
            else :
                # Create a blank time series so the plot can be created
                CurFlowTsc = createBlankTimeSeries(debug, '%s.Flow.Inst.1Hour.0.No Available Data Current Year' % location, 'cfs')
                LastYrFlowTsc = createBlankTimeSeries(debug, '%s.Flow.Inst.1Hour.0.No Available Data Last Year' % location, 'cfs')

            # Change version
            CurFlowFullname = CurFlowTsc.fullName
            CurFlowParts = CurFlowFullname.split('.')
            CurFlowTsc.version = '%d %s' % (CurYear, CurFlowTsc.version)
            CurFlowParts[-1] = CurFlowTsc.version
            CurFlowTsc.fullName = '.'.join(CurFlowParts)

            LastYrFlowFullname = LastYrFlowTsc.fullName
            LastYrFlowParts = LastYrFlowFullname.split('.')
            LastYrFlowTsc.version = '%d %s' % (LastYrYear, LastYrFlowTsc.version)
            LastYrFlowParts[-1] = LastYrFlowTsc.version
            LastYrFlowTsc.fullName = '.'.join(LastYrFlowParts)
            
            # Screen 29Feb from time series. If plotting data from a leap year and non leap year, an error will occur because the number of values are not the same
            CurFlowValues, CurFlowTimes = [], []
            for x in range(len(CurFlowTsc.values)) :
                hecTime = HecTime(); hecTime.set(CurFlowTsc.times[x])
                if hecTime.date(4)[ : 5] != '29Feb' : 
                    CurFlowValues.append(CurFlowTsc.values[x])
                    CurFlowTimes.append(CurFlowTsc.times[x])
            CurFlowTsc.values = CurFlowValues
            CurFlowTsc.numberValues = len(CurFlowValues)
            CurFlowTsc.times = CurFlowTimes
            CurFlowTsc.startTime = CurFlowTimes[0]
            CurFlowTsc.endTime = CurFlowTimes[-1]
            
            LastYrFlowValues, LastYrFlowTimes = [], []
            for x in range(len(LastYrFlowTsc.values)) :
                hecTime = HecTime(); hecTime.set(LastYrFlowTsc.times[x])
                if hecTime.date(4)[ : 5] != '29Feb' : 
                    LastYrFlowValues.append(LastYrFlowTsc.values[x])
                    LastYrFlowTimes.append(LastYrFlowTsc.times[x])
            LastYrFlowTsc.values = LastYrFlowValues
            LastYrFlowTsc.numberValues = len(LastYrFlowValues)
            # Shift last years data to this year to synchronize the plot
            LastYrFlowTsc.times = CurFlowTsc.times
            LastYrFlowTsc.startTime = LastYrFlowTimes[0]
            LastYrFlowTsc.endTime = LastYrFlowTimes[-1]

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
            ViewportLayoutsInfo = [ [   TopViewportLayout,    CurStageTsc,    'Y1',       'CurStage'],
                                    [   TopViewportLayout,    LastYrStageTsc, 'Y1',       'PastStage'],
                                    [   BottomViewportLayout, CurFlowTsc,     'Y1',       'CurFlow'],
                                    [   BottomViewportLayout, LastYrFlowTsc,  'Y1',       'PastFlow']
                                    ]
    
            # Add time series to plot and format curves
            plot = createPlot(  debug,               # Set to True or False to print debug statements
                                CwmsDb,              # CWMS database connection
                                location,            # DCP ID of location
                                plot,                # Plot
                                layout,              # Plot layout
                                ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
                                LocationProperties,  # Properties of locations
                                CurveProperties,     # Properties of curves in the plot
                                MarkerProperties,    # Properties of markers in the plot
                                PlotProperties,      # Properties of plot
                                )
    
            # Save plot file
            outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilename % location.lower())
            plot.saveToJpeg (PlotFilename % location.lower(), PlotProperties['PlotQuality'])
            
            # Close plot
            plot.close()
            outputDebug(debug, lineNo(), '%s Plot closed' % location)
        except Exception, e : 
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
            # Close plot
            try : plot.close()
            except : pass
        except java.lang.Exception, e : 
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
            # Close plot
            try : plot.close()
            except : pass
finally :
    # Close database connection
    try : 
        CwmsDb.done()
        outputDebug(True, lineNo(), 'DBAPI connection closed')
    except : 
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)        
        
    try : 
        conn.close()
        outputDebug(True, lineNo(), 'Java SQL connection closed')
    except : 
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)        
