'''
Author: Ryan Larsen
Last Updated: 03-03-2019
Description: Creates elevation, inflow (6hr), and outflow (6hr) plots for the Tri-Lakes reservoirs in the Missouri River Basin.

Script Procedure
    1. The plot will display 10 days of data starting with the most recent data
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
global CurveProperties, MarkerProperties, PlotProperties, StartTw, EndTwStr

#Moving the plot creation to the UI Thread from the Jython thread
'''
class Runnable(Runnable):
    def __init__(self, runFunction):
        self._runFunction = runFunction
    def run(self):
        self._runFunction()
'''
                 
                
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
    ImagesDirectory = PlotsDirectory + 'Images/'
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
from Server_Utils import createBlankTimeSeries, lineNo, outputDebug, createPlot, retrieveLocationLevel, retrieveLongName

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False

# Plot filename with a string substitution
PlotFilename = ImagesDirectory + '%svolt.jpg'

# List of locations to be included on plot
Locations = [   # Voltage Projects
            'ARSD', 'BLNE', 'BVNE', 'CHCR', 'COLD', 'COTT', 'LPSD', 'PA16', 'PA20', 'PA2A', 'PGSD', 'PIST-Office', 'PIST', 'SC02', 'SC04', 'SC08', 'SC09', 'SC10', 'SC12', 'SC13', 'SC14', 'SC18'   
            ]


# Dictionary of data
LocationProperties = {  'ARSD'          :   {   'PlotTitle'         :   'Fall River at Argyle Road, SD',
                                                },
                    'BLNE'              :   {   'PlotTitle'         :   'Missouri River at Blair, NE',
                                                },
                    'BVNE'              :   {   'PlotTitle'         :   'Missouri River at Brownville, NE',
                                                },
                    'CHCR'              :   {   'PlotTitle'         :   'Cherry Creek Dam on Cherry Creek, Denver Metro, CO',
                                                },
                    'COLD'              :   {   'PlotTitle'         :   'Cold Brook Dam on Cold Br. near Hot Springs, SD',
                                                },
                    'COTT'              :   {   'PlotTitle'         :   'Cottonwood Springs Dam near Hot Springs, SD',
                                                },
                    'LPSD'               :   {   'PlotTitle'         :   'Lake Poinsett near Watertown, SD',
                                                },
                    'PA16'              :   {   'PlotTitle'         :   'Papio Creek 16 Dam & Reservoir on Standing Bear Lake, Omaha, NE',
                                                },
                    'PA20'              :   {   'PlotTitle'         :   'Papio Creek 20 Dam & Reservoir on Lake Wehrspann, Omaha, NE',
                                                },
                    'PA2A'              :   {   'PlotTitle'         :   'Papio Creek 20 Sediment Dam, Omaha, NE',
                                                },
                    'PGSD'              :   {   'PlotTitle'         :   'Beaver Creek near Pringle, SD',
                                                },
                    'PIST'              :   {   'PlotTitle'         :   'Pipestem Dam & Reservoir on Pipestem Creek near Jamestown, SD',
                                                },
                    'PIST-Office'       :   {   'PlotTitle'         :   'Pipestem Office on Pipestem Creek near Jamestown, SD',
                                                },
                    'SC02'              :   {   'PlotTitle'         :   'Salt Creek 2 Dam & Reservoir on Olive Creek near Lincoln, NE',
                                                },
                    'SC04'              :   {   'PlotTitle'         :   'Salt Creek 4 Dam & Reservoir on North Branch Salt Creek near Lincoln, NE',
                                                },
                    'SC08'              :   {   'PlotTitle'         :   'Salt Creek 8 Dam & Reservoir on Hickman Branch near Lincoln, NE',
                                                },
                    'SC09'              :   {   'PlotTitle'         :   'Salt Creek 9 Dam & Reservoir on Hickman Branch near Lincoln, NE',
                                                },
                    'SC10'              :   {   'PlotTitle'         :   'Salt Creek 10 Dam & Reservoir on Cardwell Branch near Lincoln, NE',
                                                },
                    'SC12'              :   {   'PlotTitle'         :   'Salt Creek 12 Dam & Reservoir on Holmes Creek near Lincoln, NE',
                                                },
                    'SC13'              :   {   'PlotTitle'         :   'Salt Creek 13 Dam & Reservoir on Twin Lakes near Lincoln, NE',
                                                },
                    'SC14'              :   {   'PlotTitle'         :   'Salt Creek 14 Dam & Reservoir on Middle Creek near Lincoln, NE',
                                                },
                    'SC18'              :   {   'PlotTitle'         :   'Salt Creek 18 Dam & Reservoir on Oak Creek near Lincoln, NE',
                                                },
            }

# Curve, marker, and plot properties
'''
Colors = black, blue, cyan, darkblue, darkcyan, darkgray, darkgreen, darkmagenta, darkorange, darkpink, darkpurple, darkred, darkyellow, gray, green, lightblue,
     lightcyan, lightgray, lightgreen, lightmagenta, lightorange, lightpink, lightpurple, lightred, lightyellow, magenta, orange, pink, purple, red, white,
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
                    #    Parameter              LineColor        LineStyle       LineWeight    Fill Type    Fill Color      Fill Pattern     SymbolVisible       SymbolType        SymbolSize        SymbolLineColor     SymbolFillColor     SymbolInterval      SymbolSkipCount     FirstSymbolOffset                
                    #    --------------         -----------      ------------    ----------    ----------   ------------    -------------    ----------------    ------------      -----------       ----------------    ----------------    ----------------    ----------------    -----------------           
                        'Volt'           :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Open Triangle',  7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
       
                }

# Properties assigned to plot markers
MarkerProperties =  {
                    #    Marker                           Display (True or False)    Pathname             Value     Tsc            Label Text                                 Label Font         Axis           LabelAlignment     LabelPosition   LabelColor      LineStyle      LineColor    LineWidth                   
                    #    -----------------------          -----------------------    -------------        --------  -----------    -------------------------------------      ------------       ------------   ---------------    ------------    ------------    ----------     ----------   -----------        
                        'TopOfConsZone'             :   [ False,                     None,                None,     None,          'Base of Annual Flood Control Zone',       'Arial,Plain,12',  'Y1',          'left',            'above',        'black',        'Dash Dot',    'black',     1],                  
                             'TopOfFloodCtrZone'             :   [ False,                     None,                None,     None,          'Base of Exclusive Flood Control Zone',    'Arial,Plain,12',  'Y1',          'left',            'above',        'darkred',      'Dash Dot',    'darkred',   1],        
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
    Lookback    = 10 # Number of days to lookback and set the start of the time window
    CurDate     = datetime.datetime.now() # Current date
    EndTwStr    = CurDate.strftime('%d%b%Y %H%M')
    StartTw     = CurDate - datetime.timedelta(Lookback)
    StartTwStr  = StartTw.strftime('%d%b%Y %H%M')
    outputDebug(debug, lineNo(), 'Time window = %s -- %s' % (StartTwStr, EndTwStr))
    print StartTw
    print StartTwStr
    print EndTwStr
    try :
        CwmsDb = DBAPI.open()
        if not CwmsDb : raise Exception
        CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
        CwmsDb.setOfficeId('NWDM')
        CwmsDb.setTimeZone('GMT')
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
                PlotTitle = LongName.replace(' on the ', '\n')
                LocationProperties.setdefault(location, {}).setdefault('PlotTitle', PlotTitle)
    
            outputDebug(debug, lineNo(), 'Creating plot for %s' % location)                
            # Retrieve time series from database and add to list                                                  
            # 15 minute Volt Data
            if (VoltInst15minRawLrgs % location) in PathnameList :
                try : VoltTsc = CwmsDb.read(VoltInst15minRawLrgs % location).getData()
                except : VoltTsc = CwmsDb.get(VoltInst15minRawLrgs % location)
            elif  (VoltInstHourRawLrgs % location) in PathnameList :
                try : VoltTsc = CwmsDb.read(VoltInstHourRawLrgs % location).getData()
                except : VoltTsc = CwmsDb.get(VoltInstHourRawLrgs % location)
            else :
                # Create a blank time series so the plot can be created
                VoltTsc = createBlankTimeSeries(debug, '%s.Volt.Inst.15minutes.0.Raw-LRGS' % location, 'V', StartTw, EndTwStr)
    
            
            
            # Create plot
            plot = Plot.newPlot()
            layout = Plot.newPlotLayout()
            
            # Create viewports
            TopViewportLayout = layout.addViewport()
            
            
            # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
            #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
            #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
            #                           -----------------     ------------    --------    ----------------
            ViewportLayoutsInfo = [ [   TopViewportLayout,    VoltTsc,        'Y1',       'Volt'],
                                    
                                        ]
    
            # Retrieve zone values from database and assign what time series each marker will be applied to.
            #    There is a place holder in the MarkerProperties dictionary.
            '''for key in MarkerProperties.keys() :
                if MarkerProperties[key][0] :
                    # Retrieve value
                    ZoneFullName = MarkerProperties[key][1] % location
                    try : ZoneValue = retrieveLocationLevel(debug, CwmsDb, ZoneFullName)
                    except : ZoneValue = None
                    MarkerProperties[key][2] = ZoneValue
    
                    # Specify which viewport marker will be applied
                    MarkerProperties[key][3] = ElevTsc # Variable that markers are applied to. This allows createPlot to retrieve the correct viewport to add the markers'''
                                                       #    It doesn't matter if there are multiple time series in the viewport. As long as the time series specified here
                                                       #    is in viewport that the markers should appear in, the createPlot function will add the markers correctly.
    
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
    
            plot.setName(location + ' -plot window')
            # Save plot file
            outputDebug(debug, lineNo(), 'PlotFilename = ', PlotFilename % location.lower())
            plot.saveToJpeg (PlotFilename % location.lower(), PlotProperties['PlotQuality'])
            
            # Close plot
            plot.close()
            outputDebug(debug, lineNo(), '%s Plot closed' % location)
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
