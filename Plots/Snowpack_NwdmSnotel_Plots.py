'''
Author: Ryan Larsen
Last Updated: 09-29-2021
Description: Creates SWE comparison plots for specified snotel gages in the Missouri River Basin. Various gages all plotted on the same viewport.

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
from hec.heclib.util        import HecTime
from hec.hecmath            import TimeSeriesMath
from hec.script             import Plot, Constants
from time                   import mktime, localtime
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
from Server_Utils import createBlankTimeSeries, lineNo, outputDebug, createPlot, retrieveLongName

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False

# Plot filename with a string substitution
PlotFilename = ImagesDirectory + '%s.jpg'

Locations = [   # SNOTEL Basins
                'BOYN_Basin', 'CAFE_Basin', 'CAFE_Basin-BlwCanyonFerry', 'CAFE_Basin-Gallatin', 'CAFE_Basin-Jefferson', 'CAFE_Basin-Madison', 'CHFI_Basin-SouthPlatte', 
                'CHFI_Basin-UpperSouthPlatte', 'CLCA_Basin', 'GLEN_Basin-AlcovaToGLEN', 'GLEN_Basin', 'GLEN_Basin-Laramie', 'GLEN_Basin-Sweetwater', 
                'GLEN_Basin-UpperNorthPlatte', 'KEYO_Basin', 'MRB_Basin', 'PACA_Basin', 'PRB_Basin', 'SJMU_Basin', 'TIBR_Basin', 'GARR_Basin-Powder', 'GARR_Basin-Tongue',
                'GARR_Basin-UpperYellowstone', 'YETL_Basin','YETL_Basin-Bighorn', 'YETL_Basin-Shoshone', 'FTPK_Basin', 'FTPK_Basin-Blw7000','FTPK_Basin-7000To8500',
                'FTPK_Basin-Ab8500', 'GARR_Basin', 'GARR_Basin-Blw7000', 'GARR_Basin-7000To8500', 'GARR_Basin-Ab8500'
                ]

# Dictionary of data
LocationProperties = {}

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
                            'SWE'            :    [ 'blue',          'Solid',        2,            'None',      'blue',         'Solid',         Constants.FALSE,    'Triangle',     7,                'blue',             'blue',             0,                  0,                  0],
                            'SWEPast'        :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'X',            7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'SWE30yr'        :    [ 'red',           'Solid',        2,            'None',      'red',          'Solid',         Constants.FALSE,    'Triangle',     7,                'red',              'red',              0,                  0,                  0],
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
    CurDate     = datetime.datetime.now() # Current date
    CurMon      = CurDate.month
    CurYear     = CurDate.year
    
    # Start and end time for the 30 year average time series
    Ave30YrYear = 2013
    Ave30YrStartTwStr = '01Oct%d 0100' % (Ave30YrYear - 1)
    Ave30YrEndTwStr = '01Oct%d 0000' % Ave30YrYear
    
    # Start and end time for the current and past year's time series
    if CurMon >= 10. : 
        StartTwStr = '01Oct%d 0100' % CurYear
        EndTwStr = '01Oct%d 0000' % (CurYear + 1)
        PrevStartTwStr = '01Oct%d 0100' % (CurYear - 1)
        CurSnowpackYear = CurYear + 1
        PrevSnowpackYear = CurYear
    else : 
        StartTwStr = '01Oct%d 0100' % (CurYear - 1)
        EndTwStr = '01Oct%d 0000' % CurYear
        PrevStartTwStr = '01Oct%d 0100' % (CurYear - 2)
        CurSnowpackYear = CurYear
        PrevSnowpackYear = CurYear - 1
    Shift30Yr = CurSnowpackYear - Ave30YrYear # Number of years needed to shift the 30 year average time series to present day
    PrevEndTwStr = StartTwStr
    StartTw = time.strptime(StartTwStr, '%d%b%Y %H%M')
    StartTw = localtime(mktime(StartTw)) # Convert StartTw to local time so it includes the DST component
    StartTw = datetime.datetime.fromtimestamp(mktime(StartTw))
    outputDebug(debug, lineNo(), 'Time window = %s -- %s' % (StartTwStr, EndTwStr), '\tPrevious Time Window = %s --  %s' % (PrevStartTwStr, PrevEndTwStr))
    
    # Open a database connection
    try :
        CwmsDb = DBAPI.open()
        if not CwmsDb : raise Exception
        CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
        CwmsDb.setOfficeId('NWDM')
        CwmsDb.setTimeZone('Etc/GMT+6')
        conn = CwmsDb.getConnection()
    except :
        outputDebug(debug, lineNo(), 'Could not open DBI, exiting.')
        sys.exit(-1)
    
    # Get list of pathnames in database
    PathnameList = CwmsDb.getPathnameList()
    
    # Add data and format plot
    for location in Locations :
        try :
            # Save plot title to LocationProperties dictionary
            LocationProperties.setdefault(location, {}).setdefault('PlotTitle', '%s SWE Comparison Plot\nSource Data: NRCS' % location)

            outputDebug(debug, lineNo(), 'Creating plot for %s' % location)
            # Retrieve time series from database and add to list
            # Current and Past Year's Data
            if (DepthSweInstDayRevNrcs % location) in PathnameList :
                CurDepthSweTsc = CwmsDb.get(DepthSweInstDayRevNrcs % location)
                CurDepthSweTscParts = CurDepthSweTsc.fullName.split('.')
                # Change version to current year and erase subversion for the plot legend
                Version = str(CurSnowpackYear)
                SubVersion = ''
                CurDepthSweTscParts[-1] = Version
                CurDepthSweTscFullName = '.'.join(CurDepthSweTscParts)
                CurDepthSweTsc.version = Version
                CurDepthSweTsc.subVersion = SubVersion
                CurDepthSweTsc.fullName = CurDepthSweTscFullName
                
                
                try : PrevDepthSweHm = CwmsDb.read(DepthSweInstDayRevNrcs % location, PrevStartTwStr, PrevEndTwStr)
                except : 
                    Tsc = CwmsDb.get(DepthSweInstDayRevNrcs % location, PrevStartTwStr, PrevEndTwStr)
                    PrevDepthSweHm = TimeSeriesMath(Tsc)
                PrevDepthSweTsc = PrevDepthSweHm.shiftInTime('1Y').getData()
                PrevDepthSweTscParts = PrevDepthSweTsc.fullName.split('.')
                # Change version to current year and erase subversion for the plot legend
                Version = str(PrevSnowpackYear)
                SubVersion = ''
                PrevDepthSweTscParts[-1] = Version
                PrevDepthSweTscFullName = '.'.join(PrevDepthSweTscParts)
                PrevDepthSweTsc.version = Version
                PrevDepthSweTsc.subVersion = SubVersion
                PrevDepthSweTsc.fullName = PrevDepthSweTscFullName
            else :
                # Create a blank time series so the plot can be created
                CurDepthSweTsc = createBlankTimeSeries(debug, '%s.Depth-SWE.Inst.1Day.0.No Available Data' % location, 'in', StartTw, EndTwStr)
                PrevDepthSweTsc = createBlankTimeSeries(debug, '%s.Depth-SWE.Inst.1Day.0.No Available Data' % location, 'in', StartTw, EndTwStr)
            # 30 Year Average Data
            if (DepthSweAve30yrRevNrcs % location) in PathnameList :
                CurDepthSwe30yrHm = CwmsDb.read(DepthSweAve30yrRevNrcs % location, Ave30YrStartTwStr, Ave30YrEndTwStr)
                CurDepthSwe30yrTsc = CurDepthSwe30yrHm.shiftInTime('%dY' % Shift30Yr).getData()
                CurDepthSwe30yrTscParts = CurDepthSwe30yrTsc.fullName.split('.')
                AveYears = CurDepthSwe30yrTscParts[-1].split(';')
                outputDebug(debug, lineNo(), 'AveYears = ', AveYears)
                # Change version to current year and erase subversion for the plot legend
                Version = '%s-%s Ave' % (AveYears[-2], AveYears[-1])
                SubVersion = ''
                CurDepthSwe30yrTscParts[-1] = Version
                CurDepthSwe30yrTscFullName = '.'.join(CurDepthSwe30yrTscParts)
                CurDepthSwe30yrTsc.version = Version
                CurDepthSwe30yrTsc.subVersion = SubVersion
                CurDepthSwe30yrTsc.fullName = CurDepthSwe30yrTscFullName
            else :
                outputDebug(True, lineNo(), DepthSweAve30yrRevNrcs % location, ' not in database.')
                # Create a blank time series so the plot can be created
                CurDepthSwe30yrTsc = createBlankTimeSeries(debug, '%s.Depth-SWE.Inst.1Day.0.No Available Data' % location, 'in', StartTw, EndTwStr)
            
            # Create plot
            plot = Plot.newPlot()
            layout = Plot.newPlotLayout()
            
            # Create viewports
            TopViewportLayout = layout.addViewport()
            
            # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
            #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
            #                           Viewport Layout       Time Series         Axes        CurvePropertyKey
            #                           -----------------     ------------        --------    ----------------
            ViewportLayoutsInfo = [ [   TopViewportLayout,    CurDepthSweTsc,     'Y1',       'SWE'],
                                    [   TopViewportLayout,    PrevDepthSweTsc,    'Y1',       'SWEPast'],
                                    [   TopViewportLayout,    CurDepthSwe30yrTsc, 'Y1',       'SWE30yr']
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
