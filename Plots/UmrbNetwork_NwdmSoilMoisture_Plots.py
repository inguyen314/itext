'''
Author: Ryan Larsen
Last Updated: 09-28-2021
Description: Creates soil moisture plots for all Upper Missouri River Basin Monitoring Network gages.

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
    ImagesDirectory = PlotsDirectory + "Images\\NWD\\"
else :
    # Server pathnames
    PlotsDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = PlotsDirectory.split('/')
    CronjobsDirectory = '/'.join(PathList[: -1]) + '/'
    PlotsDirectory += '/'
    ImagesDirectory = PlotsDirectory + 'Images/NWD/'
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
from Server_Utils import createBlankTimeSeries, lineNo, outputDebug, createPlot, retrievePublicName

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False

# Plot filename with a string substitution
PlotFilename = ImagesDirectory + '%s_SM.jpg'

# List of locations to be included on plot
Locations = [   # UMRB Monitoring Network Stations
                'BKMS2', 'SHMW4'
                ]


# Dictionary of data
LocationProperties = {  # UMRB Monitoring Network Stations
                        #'BKMS2'             :    {  'PlotTitle'         :   'UMRB Monitoring Network - Brookings, SD\nSoil Moisture',
                        #                            },
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
                            'SoilMoisture02' :    [ 'blue',          'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'SoilMoisture04' :    [ 'red',           'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'SoilMoisture08' :    [ 'darkgreen',     'Solid',        2,            'None',      'blue',         'Solid',         Constants.FALSE,    'X',            7,                'blue',             'blue',             0,                  0,                  0],
                            'SoilMoisture20' :    [ 'black',         'Solid',        2,            'None',      'red',          'Solid',         Constants.FALSE,    'Circle',       7,                'red',              'red',              0,                  0,                  0],
                            'SoilMoisture40' :    [ 'purple',        'Solid',        2,            'None',      'gray',         'Solid',         Constants.FALSE,    'Diamond',      7,                'gray',             'gray',             0,                  0,                  0],
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
                    'PlotHeight'        :   1200,
                    'PlotQuality'       :   100 # range of 0 (crappy) to 100 (great, but larger file)
                    }

# -------------------------------------------------------------------
# Main Script
# -------------------------------------------------------------------
try :
    #
    # Date and time
    #
    Lookback    = 20 # Number of days to lookback and set the start of the time window
    CurDate     = datetime.datetime.now() # Current date
    EndTwStr    = CurDate.strftime('%d%b%Y %H%M')
    StartTw     = CurDate - datetime.timedelta(Lookback)
    StartTwStr  = StartTw.strftime('%d%b%Y %H%M')
    outputDebug(debug, lineNo(), 'Time window = %s -- %s' % (StartTwStr, EndTwStr))
    try :
        CwmsDb = DBAPI.open()
        if not CwmsDb : raise Exception
        CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
        CwmsDb.setOfficeId('NWDM')
        CwmsDb.setTimeZone('US/Central')
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
                PublicName = retrievePublicName(debug, conn, location)
                PublicLocation = PublicName.replace('Mesonet Station at ', '')
                PlotTitle = 'UMRB Monitoring Network - %s\nSoil Moisture' % PublicLocation
                LocationProperties.setdefault(location, {}).setdefault('PlotTitle', PlotTitle)

            outputDebug(debug, lineNo(), 'Creating plot for %s' % location)
            # Retrieve time series from database and add to list
            TimeSeriesContainerList = []
            for depth in [2, 4, 8, 20, 40] : 
                # Soil Moisture data
                if (SoilMoistureInstHourRawMadis % (location, depth)) in PathnameList :
                    try : SoilMoistureTsc = CwmsDb.read(SoilMoistureInstHourRawMadis % (location, depth)).getData()
                    except : SoilMoistureTsc = CwmsDb.get(SoilMoistureInstHourRawMadis % (location, depth))
                else :
                    # Create a blank time series so the plot can be created
                    SoilMoistureTsc = createBlankTimeSeries(debug, '%s-D%02din.%%-SoilMoisture.Inst.1Hour.0.No Available Data' % (location, depth), '%', StartTw, EndTwStr)
                TimeSeriesContainerList.append(SoilMoistureTsc)
            
            # Create plot
            plot = Plot.newPlot()
            layout = Plot.newPlotLayout()
            
            # Create viewports
            ViewportList = []
            for x in range(len(TimeSeriesContainerList)) :
                NewViewport = layout.addViewport()
                ViewportList.append(NewViewport)
            ViewPortWeights = layout.getViewportWeights()
            
            # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
            #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
            #                           Viewport Layout       Time Series                   Axes        CurvePropertyKey
            #                           -----------------     ------------                  --------    ----------------
            ViewportLayoutsInfo = [ [   ViewportList[0],      TimeSeriesContainerList[0],   'Y1',       'SoilMoisture02'],
                                    [   ViewportList[1],      TimeSeriesContainerList[1],   'Y1',       'SoilMoisture04'],
                                    [   ViewportList[2],      TimeSeriesContainerList[2],   'Y1',       'SoilMoisture08'],
                                    [   ViewportList[3],      TimeSeriesContainerList[3],   'Y1',       'SoilMoisture20'],
                                    [   ViewportList[4],      TimeSeriesContainerList[4],   'Y1',       'SoilMoisture40'],
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
