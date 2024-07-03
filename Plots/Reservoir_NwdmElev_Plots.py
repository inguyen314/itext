'''
Author: Ryan Larsen
Last Updated: 08-04-2020
Description: Creates elevation plots for all reservoirs in the Missouri River Basin.

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
global ElevInstHourBestMrbwm, ElevInstHourBestNwo, ElevInstHourRawUsbr, ElevInstDayRawUsbr, StageInstHourBestNwdm

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

# List of locations to be included on plot
Locations = [   # MRBWM Projects
                'FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT',
                # NWK Projects
                'KANS', 'CLIN', 'KIRN', 'LGVM', 'LNGB', 'LRMT', 'MECR', 'MELN', 'MILD', 'NORN', 'PERY', 'POMA', 'PODT', 'RATN', 'REWI', 'SMIE',
                'STON', 'TREN', 'TUCR', 'WEBR', 'WILN', 'BAGL', 'BONY', 'BSPM', 'CEBL', 'ENDS', 'GLEL', 'HACO', 'HAST', 'HILS', 'HW7M', 'LOVL',
                # NWO Projects
                'BECR', 'CHFI', 'COLD', 'PA11', 'PA16', 'PA18', 'PA20', 'SC02', 'SC04', 'SC08', 'SC09', 'SC10', 'SC12', 'SC13', 'SC14', 'SC17', 
                'SC18', 'BOHA', 'CHCR', 'COTT', 'PIST', 'BOYN', 'CAFE', 'GLEN', 'JATO', 'PACA', 'SHHI', 'YETL', 'BUBI', 'CLCA', 'HEBU', 'KEYO',
                'TIBR', 'CHMA', 'DFSD', 'GDMT', 'SDMT', 'TRCO', 'WCMT', 'ALCR', 'GRAR', 'SEMR', 'PATR', 'BFR', 'BULA', 'GUER', 'HEBN',
                'AWND', 'LPSD']

# Dictionary of data. Dictionary is filled with data within the script
LocationProperties = {  'KANS'              :    {  'PlotTitle'         :   'Kanopolis Lake on the Smoky Hill R, KS',
                                                    },
                        'CLIN'              :   {   'PlotTitle'         :   'Clinton Dam on the Wakarusa River, KS',
                                                    },
                        'KIRN'              :   {   'PlotTitle'         :   'Kirwin Dam on the NF Solomon R, KS',
                                                    },
                        'LGVM'              :   {   'PlotTitle'         :   'Longview Dam on the Little Blue R, MO',
                                                    },
                        'LNGB'              :   {   'PlotTitle'         :   'Long Branch Dam on the Chariton R, MO',
                                                    },
                        'LRMT'              :   {   'PlotTitle'         :   'Lima Dam on Red Rock River, MT',
                                                    },
                        'MECR'              :   {   'PlotTitle'         :   'Harry Strunk Res on Medicine Cr, NE',
                                                    },
                        'MELN'              :   {   'PlotTitle'         :   'Melvern Dam on the Marais Des Cygnes R, KS',
                                                    },
                        'MILD'              :   {   'PlotTitle'         :   'Milford Dam on the Republican R, KS',
                                                    },
                        'NORN'              :   {   'PlotTitle'         :   'Norton Dam / Keith Sebelius Res, KS',
                                                    },
                        'PERY'              :   {   'PlotTitle'         :   'Perry Cr Dam on Delaware R, KS',
                                                    },
                        'POMA'              :   {   'PlotTitle'         :   'Pomona Lake on 110-Mile Cr, KS',
                                                    },
                        'PODT'              :   {   'PlotTitle'         :   'Pomme De Terre Lake on P-D-T River, MO',
                                                    },
                        'RATN'              :   {   'PlotTitle'         :   'Rathbun Dam on the Chariton R, IA',
                                                    },
                        'REWI'              :   {   'PlotTitle'         :   'Hugh Butler Res on Red Willow Cr, NE',
                                                    },
                        'SMIE'              :   {   'PlotTitle'         :   'Smithville Dam on the L Platte R, MO',
                                                    },
                        'STON'              :   {   'PlotTitle'         :   'Stockton Dam on the Sac River, MO',
                                                    },
                        'TREN'              :   {   'PlotTitle'         :   'Trenton Dam / Swanson Res on the Rep R, NE',
                                                    },
                        'TUCR'              :   {   'PlotTitle'         :   'Tuttle Cr Dam on the Big Blue River, KS',
                                                    },
                        'WEBR'              :   {   'PlotTitle'         :   'Webster Dam on the SF Solomon R, KS',
                                                    },
                        'WILN'              :   {   'PlotTitle'         :   'Wilson Dam on the Saline River, KS',
                                                    },
                        'BAGL'              :   {   'PlotTitle'         :   'Bagnell Dam on the Osage River, MO',
                                                    },
                        'BONY'              :   {   'PlotTitle'         :   'Bonny Dam on the Republican R, CO',
                                                    },
                        'BSPM'              :   {   'PlotTitle'         :   'Blue Springs Dam on the L Blue R, MO',
                                                    },
                        'CEBL'              :   {   'PlotTitle'         :   'Cedar Bluff Dam on the Smoky Hill R, MT',
                                                    },
                        'ENDS'              :   {   'PlotTitle'         :   'Enders Lake on Frenchman Cr, NE',
                                                    },
                        'GLEL'              :   {   'PlotTitle'         :   'Waconda Lake on the Solomon R, KS',
                                                    },
                        'HACO'              :   {   'PlotTitle'         :   'Harlan Co Dam on the Republican R, NE',
                                                    },
                        'HAST'              :   {   'PlotTitle'         :   'Harry S Truman Dam on the M-D-C R, MO',
                                                    },
                        'HILS'              :   {   'PlotTitle'         :   'Hillsdale Lake on Big Bull Cr, KS',
                                                    },
                        'HW7M'              :   {   'PlotTitle'         :   'Osage R at Hwy 7 Br nr Warsaw, MO',
                                                    },
                        'LOVL'              :   {   'PlotTitle'         :   'Lovewell Dam on White Rock Cr, KS',
                                                    },
                        'BECR'              :   {   'PlotTitle'         :   'Bear Creek Dam on Bear Creek, Denver Metro, CO',
                                                    },
                        'CHFI'              :   {   'PlotTitle'         :   'Chatfield Dam on South Platte River, Denver Metro, CO',
                                                    },
                        'COLD'              :   {   'PlotTitle'         :   'Cold Brook Dam on Cold Brook, Hot Springs, SD',
                                                    },
                        'PA11'              :   {   'PlotTitle'         :   'Cunningham Lake / Papio Dam 11, Omaha, NE',
                                                    },
                        'PA16'              :   {   'PlotTitle'         :   'Standing Bear Lake / Papio Dam 16, Omaha, NE',
                                                    },
                        'PA18'              :   {   'PlotTitle'         :   'Zorinksy Lake / Papio Dam 18, Omaha, NE',
                                                    },
                        'PA20'              :   {   'PlotTitle'         :   'Wehrspann Lake / Papio Dam 20, Omaha Metro, NE',
                                                    },
                        'SC02'              :   {   'PlotTitle'         :   'Olive Branch Creek / Salt Cr Dam 2, Lincoln, NE',
                                                    },
                        'SC04'              :   {   'PlotTitle'         :   'Blue Stem Lake / Salt Cr Dam 4, Lincoln, NE',
                                                    },
                        'SC08'              :   {   'PlotTitle'         :   'Wagon Train Lake / Salt Cr Dam 8, Lincoln, NE',
                                                    },
                        'SC09'              :   {   'PlotTitle'         :   'Stagecoach Lake / Salt Cr Dam 9, Lincoln, NE',
                                                    },
                        'SC10'              :   {   'PlotTitle'         :   'Yankee Hill Lake / Salt Cr Dam 10, Lincoln, NE',
                                                    },
                        'SC12'              :   {   'PlotTitle'         :   'Conestoga Lake / Salt Cr Dam 12, Lincoln, NE',
                                                    },
                        'SC13'              :   {   'PlotTitle'         :   'Twin Lakes / Salt Cr Dam 13, Lincoln, NE',
                                                    },
                        'SC14'              :   {   'PlotTitle'         :   'Pawnee Lake / Salt Cr Dam 14, Lincoln, NE',
                                                    },
                        'SC17'              :   {   'PlotTitle'         :   'Holmes Lake / Salt Cr Dam 17, Lincoln, NE',
                                                    },
                        'SC18'              :   {   'PlotTitle'         :   'Branched Oak Lake / Salt Cr Dam 18, Lincoln, NE',
                                                    },
                        'BOHA'              :   {   'PlotTitle'         :   'Bowman-Haley Dam on Grand River, Bowman, ND',
                                                    },
                        'CHCR'              :   {   'PlotTitle'         :   'Cherry Creek Dam on Cherry Creek, Denver Metro, CO',
                                                    },
                        'COTT'              :   {   'PlotTitle'         :   'Cottonwood Springs Dam on Cottonwood Spring, Hot Springs, SD',
                                                    },
                        'PIST'              :   {   'PlotTitle'         :   'Pipestem Dam on Pipestem Creek, Jamestown, ND',
                                                    },
                        'BOYN'              :   {   'PlotTitle'         :   'Boysen Dam on Wind River, WY',
                                                    },
                        'CAFE'              :   {   'PlotTitle'         :   'Canyon Ferry Dam on Missouri River, MT',
                                                    },
                        'GLEN'              :   {   'PlotTitle'         :   'Glendo Dam on North Platte River, WY',
                                                    },
                        'JATO'              :   {   'PlotTitle'         :   'Jamestown Dam on James River, Jamestown, ND',
                                                    },
                        'PACA'              :   {   'PlotTitle'         :   'Pactola Dam on Rapid Creek, outside Rapid City, SD',
                                                    },
                        'SHHI'              :   {   'PlotTitle'         :   'Shadehill Dam on Grand River, SD',
                                                    },
                        'YETL'              :   {   'PlotTitle'         :   'Yellowtail Dam on Bighorn River, MT',
                                                    },
                        'BUBI'              :   {   'PlotTitle'         :   'Buffalo Bill Reservoir on Shoshone River, Cody, WY',
                                                    },
                        'CLCA'              :   {   'PlotTitle'         :   'Clark Canyon Dam on Red Rock River, MT',
                                                    },
                        'HEBU'              :   {   'PlotTitle'         :   'Heart Butte Dam on Heart River, ND',
                                                    },
                        'KEYO'              :   {   'PlotTitle'         :   'Keyhole Dam on Belle Fourche River, WY',
                                                    },
                        'TIBR'              :   {   'PlotTitle'         :   'Tiber Dam & Reservoir\nMarias River near Chester, MT',
                                                    },
                        'CHMA'              :   {   'PlotTitle'         :   'Cheesman Dam South Platte River, CO',
                                                    },
                        'DFSD'              :   {   'PlotTitle'         :   'Deerfield Dam Castle Creek, SD',
                                                    },
                        'FDMT'              :   {   'PlotTitle'         :   'Fresno Dam Milk River near Havre, MT',
                                                    },
                        'GDMT'              :   {   'PlotTitle'         :   'Gibson Dam North Fork Sun River, MT',
                                                    },
                        'SDMT'              :   {   'PlotTitle'         :   'Swift Reservoir Birch Creek, MT',
                                                    },
                        'TRCO'              :   {   'PlotTitle'         :   'Tarryall Reservoir near Tarryall, CO',
                                                    },
                        'WCMT'              :   {   'PlotTitle'         :   'Willow Creek Dam, MT',
                                                    },
                        'ALCR'              :   {   'PlotTitle'         :   'Alcova Dam on North Platte R, WY',
                                                    },
                        'GRAR'              :   {   'PlotTitle'         :   'Gray Reef Dam on North Platte R, WY',
                                                    },
                        'SEMR'              :   {   'PlotTitle'         :   'Seminoe Dam on North Platte R, WY',
                                                    },
                        'PATR'              :   {   'PlotTitle'         :   'Pathfinder Dam on North Platte R, WY',
                                                    },
                        'BFR'               :   {   'PlotTitle'         :   'Belle Fourche Dam on the Belle F R, WY',
                                                    },
                        'BULA'              :   {   'PlotTitle'         :   'Bull Lake Dam on Bull Lake Cr, WY',
                                                    },
                        'GUER'              :   {   'PlotTitle'         :   'Guernsey Dam on the N Platte R, WY',
                                                    },
                        'HEBN'              :   {   'PlotTitle'         :   'Hebgen Dam on the Madison River, MT',
                                                    },
                        'AWND'              :   {   'PlotTitle'         :   'Arrowwood Res on the James River, ND',
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
                            'Elev'           :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'Stage'          :    [ 'darkgreen',     'Solid',        2,            'None',      'darkgreen',    'Solid',         Constants.FALSE,    'Triangle',     7,                'darkgreen',        'darkgreen',        0,                  0,                  0],
                            'Flow'           :    [ 'blue',          'Solid',        2,            'None',      'blue',         'Solid',         Constants.FALSE,    'X',            7,                'blue',             'blue',             0,                  0,                  0],
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
    Lookback    = 16 # Number of days to lookback and set the start of the time window
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
                LongName = retrieveLongName(debug, conn, location)
                PlotTitle = LongName.replace(' on the ', '\n')
                LocationProperties.setdefault(location, {}).setdefault('PlotTitle', PlotTitle)
            
            outputDebug(debug, lineNo(), 'Creating plot for %s' % location)
            # Retrieve time series from database and add to list
            if (ElevInstHourBestMrbwm % location) in PathnameList :
                try : Tsc = CwmsDb.read(ElevInstHourBestMrbwm % location).getData()
                except: Tsc = CwmsDb.get(ElevInstHourBestMrbwm % location)
            elif (ElevInstHourRawUsbr % location) in PathnameList :
                try : Tsc = CwmsDb.read(ElevInstHourRawUsbr % location).getData()
                except : Tsc = CwmsDb.get(ElevInstHourRawUsbr % location)
            elif (ElevInstDayRawUsbr % location) in PathnameList :
                try : Tsc = CwmsDb.read(ElevInstDayRawUsbr % location).getData()
                except : Tsc = CwmsDb.get(ElevInstDayRawUsbr % location)
            elif (ElevInstHourBestNwo % location) in PathnameList :
                try : Tsc = CwmsDb.read(ElevInstHourBestNwo % location).getData()
                except : Tsc = CwmsDb.get(ElevInstHourBestNwo % location)
            elif (ElevInstHourBestNwk % location) in PathnameList :
                try : Tsc = CwmsDb.read(ElevInstHourBestNwk % location).getData()
                except : Tsc = CwmsDb.get(ElevInstHourBestNwk % location)
            elif (StageInstHourBestNwdm % location) in PathnameList :
                try : Tsc = CwmsDb.read(StageInstHourBestNwdm % location).getData()
                except : Tsc = CwmsDb.get(StageInstHourBestNwdm % location)
            else :
                # Create a blank time series so the plot can be created
                Tsc = createBlankTimeSeries(debug, '%s.Elev.Inst.1Hour.0.No Available Data' % location, 'ft', StartTw, EndTwStr)
            
            # Create plot
            plot = Plot.newPlot()
            layout = Plot.newPlotLayout()
            
            # Create viewports
            TopViewportLayout = layout.addViewport()
            
            # Assign what viewport layout and axis each time series will be applied to. Also specify which curve properties to use by specifying the CurvePropertyKey
            #    If defaults curve properties are wanted, specify the CurvePropertyKey as None
            #                           Viewport Layout       Time Series     Axes        CurvePropertyKey
            #                           -----------------     ------------    --------    ----------------
            ViewportLayoutsInfo = [ [   TopViewportLayout,    Tsc,            'Y1',       'Elev']
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
