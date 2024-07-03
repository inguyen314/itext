'''
Author: Ryan Larsen
Last Updated: 02-21-2021
Description: Creates stage and flow plots for all river gages.

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
from Server_Utils import createBlankTimeSeries, lineNo, outputDebug, createPlot, retrieveLongName

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False

# Plot filename with a string substitution
PlotFilename = ImagesDirectory + '%s.jpg'

# List of locations to be included on plot
Locations = [   # GRFT Stations
                'NCSD', 'RVIA', 'AKIA', 'ANIA', 'SCSD', 'VRSD', 'PSIA', 'LGIA', 'CEIA', 'LVIA', 'MHIA', 'TUIA', 'MPIA', 'JMIA', 'KENE', 'GRNE',
                'NBNE', 'LUNE', 'OFK', 'WSNE', 'WTNE', 'MLNE', 'NLNE', 'ITNE', 'LCNE', 'GWNE', 'HCIA', 'ACIA', 'UENE', 'ROIA', 'RNIA', 'HAIA',
                'AUNE', 'UNNE', 'FLNE', 'GRAM', 'DESO', 'AGYM', 'SSMO', 'LCTM', 'TTNM', 'GLLM', 'CHMO', 'SMNM', 'PRIM', 'BLCM', 'RIFM',
                # Non-GRFT Stations
                'ASNE', 'BHMT', 'BIL', 'BIS', 'BRND', 'CCSD', 'CLMT', 'CSMT', 'DRSD', 'FPSD', 'HAND', 'HUSD', 'LESD', 'LOMT', 'LVMT', 'MAND', 
                'MIMT', 'MLS', 'NAMT', 'NRNE', 'OCSD', 'RBMT', 'SACO', 'SIMT', 'TOMT', 'TFMT', 'VIMT', 'VDNE', 'VRNE', 'WCND', 'WPMT', 'WHSD', 
                'RUMT', 'VGNE', 'WLSD',
                # Mainstem Stations
                'SUX', 'MKC', 'DENE', 'OMA', 'NCNE', 'BVNE', 'RUNE', 'STJ', 'BNMO', 'WVMO', 'HEMO', 'YKN', 'STL',
                # NWO Stations
                'ASSD', 'BACO', 'BRMT', 'BRSD', 'BZCO', 'CBKM', 'CDCO', 'CECL', 'COSD', 'DECL', 'DEN', 'ENCO', 'FLSD', 'FLWY', 'FRCL', 'FTSD',
                'GCND', 'GRCL', 'GYCL', 'HAMT', 'HEWY', 'HNCL', 'HOLM', 'HSSD', 'JAND', 'JMCO', 'JRCO', 'KAWY', 'KECL', 'LACO', 'LACL', 'LAND',
                'LGMT', 'MARM', 'MCMT', 'MELM', 'MOCL', 'PACO', 'PIND', 'PTCL', 'RCSD', 'RESD', 'RILW', 'RONE', 'RTCL', 'SBND', 'SECO', 'SIWY',
                'SKSD', 'SMCL', 'SRBB', 'SRCL', 'TBMT', 'UL6E', 'VAMT', 'VUMT', 'WAKP', 'WECL', 'WPSD', 'WRCH', 'WRKY', 'WRRY', 'WSSD', 'WTCO', 
                'WTSD',
                # NWK Stations
                'ACHK', 'ADAK', 'ARDK', 'ARHM', 'BAGM', 'BARK', 'BARN', 'BEDI', 'BROK', 'CDBK', 'BUNK', 'CDBK', 'CHPK', 'CHTI', 'CLAK', 'CLRI', 
                'CLRK', 'CMBN', 'CNKK', 'CPMO', 'CRTN', 'CSMK', 'DCM1', 'DDVM', 'DELK', 'DMRK', 'EKDK', 'EPKS', 'EWKS', 'FKFK', 'FRBN', 'FRI', 
                'FTNK', 'GARK', 'GDEK', 'GDRN', 'GFMO', 'GLNK', 'HACN', 'HARN', 'HNIA', 'HILK', 'HTNM', 'JRMM', 'KACM', 'KCKK', 'LCGK', 'LEKS', 
                'LGLK', 'LNDK', 'LIVM', 'LOVK', 'LWRK', 'MAMO', 'MARK', 'MEKS', 'MILB', 'MKSL', 'MLTI', 'MRRM', 'MRYK', 'MSCK', 'MUNK', 'NEVM',
                'NLSK', 'NOVM', 'NWCK', 'ORNN', 'OSBK', 'OTTK', 'OTVM', 'PALN', 'PDTM', 'PLKM', 'PLVM', 'PMNK', 'POKM', 'POMK', 'PRMI', 'PTSK',
                'PXCK', 'QUKS', 'RDGK', 'RUSK', 'SCMO', 'SCSK', 'SHJM', 'SIMK', 'SKTK', 'SMHM', 'STMN', 'STOM', 'STTM', 'STTN', 'TNGK', 'TOPK',
                'TPAK', 'TSTK', 'WAAK', 'WGKS', 'WILK', 'WODK', 'WOFK', 'WSHK'
                ]

Locations = ['NCNE']

# Dictionary of data
LocationProperties = {  # GRFT Stations
                        'NCSD'              :    {  'PlotTitle'         :   'Big Sioux River at North Cliff at Sioux Falls, SD\nFlood Stage = 16 ft',
                                                    },
                        'RVIA'              :    {  'PlotTitle'         :   'Rock River at Rock Valley, IA\nFlood Stage = 11 ft',
                                                    },
                        'AKIA'              :    {  'PlotTitle'         :   'Big Sioux River at Akron, IA\nFlood Stage = 16 ft',
                                                    },
                        'ANIA'              :    {  'PlotTitle'         :   'Floyd River at Alton, IA\nFlood Stage = 12 ft',
                                                    },
                        'SCSD'              :    {  'PlotTitle'         :   'James River at Scotland, SD\nFlood Stage = 13 ft',
                                                    },
                        'VRSD'              :    {  'PlotTitle'         :   'Vermillion River at Vermillion, SD\nFlood Stage = 21 ft',
                                                    },
                        'PSIA'              :    {  'PlotTitle'         :   'Soldier River at Pisgah, IA\nFlood Stage = 28 ft',
                                                    },
                        'LGIA'              :    {  'PlotTitle'         :   'Boyer River at Logan, IA\nFlood Stage = 19 ft',
                                                    },
                        'CEIA'              :    {  'PlotTitle'         :   'Little Sioux River at Correctionville, IA\nFlood Stage = 19 ft',
                                                    },
                        'LVIA'              :    {  'PlotTitle'         :   'Little Sioux River at Linn Grove, IA\nFlood Stage = 18 ft',
                                                    },
                        'MHIA'              :    {  'PlotTitle'         :   'Little Sioux River - M&H Ditch, IA\nFlood Stage = 25 ft',
                                                    },
                        'TUIA'              :    {  'PlotTitle'         :   'Little Sioux River at Turin, IA\nFlood Stage = 25 ft',
                                                    },
                        'MPIA'              :    {  'PlotTitle'         :   'Maple River at Mapleton, IA\nFlood Stage = 18 ft',
                                                    },
                        'JMIA'              :    {  'PlotTitle'         :   'Floyd River at James, IA\nFlood Stage = 26 ft',
                                                    },
                        'KENE'              :    {  'PlotTitle'         :   'Platte River at Kearney, NE\nFlood Stage = 4.5 ft',
                                                    },
                        'GRNE'              :    {  'PlotTitle'         :   'Platte River at Grand Island, NE\nFlood Stage = 4 ft',
                                                    },
                        'NBNE'              :    {  'PlotTitle'         :   'Platte River at North Bend, NE\nFlood Stage = 8 ft',
                                                    },
                        'LUNE'              :    {  'PlotTitle'         :   'Platte River at Louisville, NE\nFlood Stage = 9 ft',
                                                    },
                        'OFK'               :    {  'PlotTitle'         :   'Elkhorn River at Norfolk, NE\nFlood Stage = 8.5 ft',
                                                    },
                        'WSNE'              :    {  'PlotTitle'         :   'Elkhorn River at West Point, NE\nFlood Stage = 12 ft',
                                                    },
                        'WTNE'              :    {  'PlotTitle'         :   'Elkhorn River at Waterloo, NE\nFlood Stage = 15 ft',
                                                    },
                        'MLNE'              :    {  'PlotTitle'         :   'Middle Loup River at St. Paul, NE\nFlood Stage = 8 ft',
                                                    },
                        'NLNE'              :    {  'PlotTitle'         :   'North Loup River at St. Paul, NE\nFlood Stage = 5.5 ft',
                                                    },
                        'ITNE'              :    {  'PlotTitle'         :   'Wahoo Creek at Ithaca, NE\nFlood Stage = 19 ft',
                                                    },
                        'LCNE'              :    {  'PlotTitle'         :   'Salt Creek at Lincoln, NE\nFlood Stage = 20.5 ft',
                                                    },
                        'GWNE'              :    {  'PlotTitle'         :   'Salt Creek at Greenwood, NE\nFlood Stage = 20 ft',
                                                    },
                        'HCIA'              :    {  'PlotTitle'         :   'West Nishnabotna River at Hancock, IA\nFlood Stage = 13.5 ft',
                                                    },
                        'ACIA'              :    {  'PlotTitle'         :   'East Nishnabotna River Atlantic, IA\nFlood Stage = 19 ft',
                                                    },
                        'UENE'              :    {  'PlotTitle'         :   'Logan Creek at Uehling, NE\nFlood Stage = 18 ft',
                                                    },
                        'ROIA'              :    {  'PlotTitle'         :   'East Nishnabotna River at Red Oak, IA\nFlood Stage = 18 ft',
                                                    },
                        'RNIA'              :    {  'PlotTitle'         :   'West Nishnabotna River at Randolph, IA\nFlood Stage = 19 ft',
                                                    },
                        'HAIA'              :    {  'PlotTitle'         :   'Nishnabotna River at Hamburg, IA\nFlood Stage = 16 ft',
                                                    },
                        'AUNE'              :    {  'PlotTitle'         :   'Little Nemaha River at Auburn, NE\nFlood Stage = 22 ft',
                                                    },
                        'UNNE'              :    {  'PlotTitle'         :   'Weeping Water Creek at Union, NE\nFlood Stage = 25 ft',
                                                    },
                        'FLNE'              :    {  'PlotTitle'         :   'Big Nemaha River at Falls City, NE\nFlood Stage = 20 ft',
                                                    },
                        'GRAM'              :    {  'PlotTitle'         :   'Nodaway River at Graham, MO\nFlood Stage = 20 ft',
                                                    },
                        'DESO'              :    {  'PlotTitle'         :   'Kansas River at DeSoto, KS\nFlood Stage = 26 ft',
                                                    },
                        'AGYM'              :    {  'PlotTitle'         :   'Platte River at Agency, MO\nFlood Stage = 20 ft',
                                                    },
                        'SSMO'              :    {  'PlotTitle'         :   'Platte River at Sharps Station, MO\nFlood Stage = 26 ft',
                                                    },
                        'LCTM'              :    {  'PlotTitle'         :   'Little Blue River at Lake City, MO\nFlood Stage = 18 ft',
                                                    },
                        'TTNM'              :    {  'PlotTitle'         :   'Thompson River at Trenton, MO\nFlood Stage = 20 ft',
                                                    },
                        'GLLM'              :    {  'PlotTitle'         :   'Grand River at Gallatin, MO\nFlood Stage = 26 ft',
                                                    },
                        'CHMO'              :    {  'PlotTitle'         :   'Grand River at Chillicothe, MO\nFlood Stage = 24 ft',
                                                    },
                        'SMNM'              :    {  'PlotTitle'         :   'Grand River at Sumner, MO\nFlood Stage = 26 ft',
                                                    },
                        'PRIM'              :    {  'PlotTitle'         :   'Chariton River at Prairie Hill, MO\nFlood Stage = 15 ft',
                                                    },
                        'BLCM'              :    {  'PlotTitle'         :   'Blackwater River at Blue Lick, MO\nFlood Stage = 24 ft',
                                                    },
                        'RIFM'              :    {  'PlotTitle'         :   'Gasconade River at Rich Fountain, MO\nFlood Stage = 20 ft',
                                                    },
                        # Non-GRFT Stations
                        'BIL'               :    {  'PlotTitle'         :   'Yellowstone River at Billings, MT\nFlood Stage = 13 ft',
                                                    },
                        'BIS'               :    {  'PlotTitle'         :   'Missouri River at Bismarck, ND\nFlood Stage = 14.5 ft',
                                                    },
                        'CCSD'              :    {  'PlotTitle'         :   'Cheyenne River at Howes, SD\nFlood Stage = 14 ft',
                                                    },
                        'CLMT'              :    {  'PlotTitle'         :   'Missouri River at Culbertson, MT\nFlood Stage = 19 ft',
                                                    },
                        'CSMT'              :    {  'PlotTitle'         :   'Yellowstone River at Corwin Springs, MT\nFlood Stage = 11 ft',
                                                    },
                        'DRSD'              :    {  'PlotTitle'         :   'Big Sioux River at Dell Rapids, SD\nFlood Stage = 12 ft',
                                                    },
                        'FPSD'              :    {  'PlotTitle'         :   'Bad River at Fort Pierre, SD\nFlood Stage = 21 ft',
                                                    },
                        'HAND'              :    {  'PlotTitle'         :   'Knife River at Hazen, ND\nFlood Stage = 21 ft',
                                                    },
                        'LESD'              :    {  'PlotTitle'         :   'Grand River at Little Eagle, SD\nFlood Stage = 15 ft',
                                                    },
                        'LOMT'              :    {  'PlotTitle'         :   'Powder River at Locate, MT\nFlood Stage = 13.1 ft',
                                                    },
                        'MAND'              :    {  'PlotTitle'         :   'Heart River at Mandan, ND\nFlood Stage = 17 ft',
                                                    },
                        'MLS'               :    {  'PlotTitle'         :   'Yellowstone River at Miles City, MT\nFlood Stage = 13 ft',
                                                    },
                        'NAMT'              :    {  'PlotTitle'         :   'Milk River at Nashua, MT\nFlood Stage = 20 ft',
                                                    },
                        'NRNE'              :    {  'PlotTitle'         :   'Bazile Creek at Niobrara, NE\nFlood Stage = 9 ft',
                                                    },
                        'OCSD'              :    {  'PlotTitle'         :   'White River at Oacoma, SD\nFlood Stage = 13 ft',
                                                    },
                        'RBMT'              :    {  'PlotTitle'         :   'Missouri River at Landusky, MT\nFlood Stage = 25 ft',
                                                    },
                        'SACO'              :    {  'PlotTitle'         :   'Milk River at Saco, MT\nFlood Stage = 20 ft',
                                                    },
                        'WPMT'              :    {  'PlotTitle'         :   'Missouri River at Wolf Point, MT\nFlood Stage = 23.0 ft',
                                                    },
                        'WHSD'              :    {  'PlotTitle'         :   'Moreau River at Whitehorse, SD\nFlood Stage = 21 ft',
                                                    },
                        'WCND'              :    {  'PlotTitle'         :   'Little Missouri River at Watford City, ND\nFlood Stage = 20 ft',
                                                    },
                        'VIMT'              :    {  'PlotTitle'         :   'Missouri River at Virgelle, MT\nFlood Stage = 17 ft',
                                                    },
                        'VDNE'              :    {  'PlotTitle'         :   'Ponca Creek at Verdel, NE\nFlood Stage = 10 ft',
                                                    },
                        'SIMT'              :    {  'PlotTitle'         :   'Yellowstone River at Sidney, MT\nFlood Stage = 19 ft',
                                                    },
                        'BRND'              :    {  'PlotTitle'         :   'Cannonball River at Breien, ND\nFlood Stage = 10 ft',
                                                    },
                        'MIMT'              :    {  'PlotTitle'         :   'Tongue River at Miles City, MT\nFlood Stage = 5.8 ft',
                                                    },
                        'ASNE'              :    {  'PlotTitle'         :   'Platte River at Ashland, NE\nFlood Stage = 20 ft',
                                                    },
                        'BHMT'              :    {  'PlotTitle'         :   'Bighorn River at Bighorn, MT\nFlood Stage = 9 ft',
                                                    },
                        'VRNE'              :    {  'PlotTitle'         :   'Niobrara River near Verdel, NE\nFlood Stage=12 ft',
                                                    },
                        'LVMT'              :    {  'PlotTitle'         :   'Yellowstone River at Livingston, MT\nFlood Stage = 8 ft',
                                                    },
                        'TOMT'              :    {  'PlotTitle'         :   'Missouri River at Toston, MT\nFlood Stage = 10 ft',
                                                    },
                        'TFMT'              :    {  'PlotTitle'         :   'Jefferson River at Three Forks, MT\nFlood Stage = 7.5 ft',
                                                    },
                        'HUSD'              :    {  'PlotTitle'         :   'James River at Huron, SD\nFlood Stage = 12 ft',
                                                    },
                        'RUMT'              :    {  'PlotTitle'         :   'Musselshell River at Roundup, MT\nFlood Stage = 5.1 ft',
                                                    },
                        'VGNE'              :    {  'PlotTitle'         :   'Verdigre Creek at Verdigre, NE\nFlood Stage = NA',
                                                    },
                        'WLSD'              :    {  'PlotTitle'         :   'Keya Paha River at Wewela, SD\nFlood Stage = NA',
                                                    },
                        # Mainstem Stations
                        'SUX'               :    {  'PlotTitle'         :   'Missouri River at Sioux City, IA\nFlood Stage = 30 ft',
                                                    },
                        'MKC'               :    {  'PlotTitle'         :   'Missouri River at Kansas City, MO\nFlood Stage = 32 ft',
                                                    },
                        'DENE'              :    {  'PlotTitle'         :   'Missouri River at Decatur, NE\nFlood Stage = 35 ft',
                                                    },
                        'OMA'               :    {  'PlotTitle'         :   'Missouri River at Omaha, NE\nFlood Stage = 29 ft',
                                                    },
                        'NCNE'              :    {  'PlotTitle'         :   'Missouri River at Nebraska City, NE\nFlood Stage = 18 ft',
                                                    },
                        'BVNE'              :    {  'PlotTitle'         :   'Missouri River at Brownville, NE\nFlood Stage = 33 ft',
                                                    },
                        'RUNE'              :    {  'PlotTitle'         :   'Missouri River at Rulo, NE\nFlood Stage = 17 ft',
                                                    },
                        'STJ'               :    {  'PlotTitle'         :   'Missouri River at St. Joseph, MO\nFlood Stage = 17 ft',
                                                    },
                        'BNMO'              :    {  'PlotTitle'         :   'Missouri River at Boonville, MO\nFlood Stage = 21 ft',
                                                    },
                        'WVMO'              :    {  'PlotTitle'         :   'Missouri River at Waverly, MO\nFlood Stage = 20 ft',
                                                    },
                        'HEMO'              :    {  'PlotTitle'         :   'Missouri River at Hermann, MO\nFlood Stage = 21 ft',
                                                    },
                        'YKN'               :    {  'PlotTitle'         :   'Missouri River at Yankton, SD\nFlood Stage = 20 ft',
                                                    },
                        'STL'               :    {  'PlotTitle'         :   'Mississippi River at St. Louis, MO\nFlood Stage = NA',
                                                    },
                        # NWO Stations
                        'ASSD'              :    {  'PlotTitle'         :   'James River at Ashton, SD\nFlood Stage = 13 ft',
                                                    },
                        'BACO'              :    {  'PlotTitle'         :   'NF S Platte R nr Bailey, CO\nFlood Stage = NA',
                                                    },
                        'BRMT'              :    {  'PlotTitle'         :   'Beaverhead R nr Barretts, MT\nFlood Stage = 4 ft',
                                                    },
                        'BRSD'              :    {  'PlotTitle'         :   'Big Sioux River nr Bruce, SD\nFlood Stage = 8 ft',
                                                    },
                        'BZCO'              :    {  'PlotTitle'         :   'S Platte R at Balzac, CO\nFlood Stage = 9 ft',
                                                    },
                        'CBKM'              :    {  'PlotTitle'         :   'Cut Bank Cr nr Browning, MT\nFlood Stage = NA',
                                                    },
                        'CDCO'              :    {  'PlotTitle'         :   'Cherry Creek at Denver, CO\nFlood Stage = NA',
                                                    },
                        'CECL'              :    {  'PlotTitle'         :   'S Platte R bl Cheesman Dam, CO\nFlood Stage = 5.8 ft',
                                                    },
                        'COSD'              :    {  'PlotTitle'         :   'James River at Columbia, SD\nFlood Stage = 13 ft',
                                                    },
                        'DECL'              :    {  'PlotTitle'         :   'Clear Cr at Derby, CO\nFlood Stage = 8 ft',
                                                    },
                        'DEN'               :    {  'PlotTitle'         :   'S Platte R at Denver, CO\nFlood Stage = 9 ft',
                                                    },
                        'ENCO'              :    {  'PlotTitle'         :   'S Platte R at Union, CO\nFlood Stage = 10.5 ft',
                                                    },
                        'FLSD'              :    {  'PlotTitle'         :   'Big Sioux River at Florence, SD\nFlood Stage = 8 ft',
                                                    },
                        'FLWY'              :    {  'PlotTitle'         :   'Laramie R at Ft Laramie, WY\nFlood Stage = 6.5 ft',
                                                    },
                        'FRCL'              :    {  'PlotTitle'         :   'Cherry Cr at Franktown, CO\nFlood Stage = 6.6 ft',
                                                    },
                        'FTSD'              :    {  'PlotTitle'         :   'James River at Forestburg, SD\nFlood Stage = 12 ft',
                                                    },
                        'GCND'              :    {  'PlotTitle'         :   'James River at Grace City, ND\nFlood Stage = 12 ft',
                                                    },
                        'GRCL'              :    {  'PlotTitle'         :   'NF S Platte River at Grant, CO\nFlood Stage = NA',
                                                    },
                        'GLCL'              :    {  'PlotTitle'         :   'Clear Cr at Golden, CO\nFlood Stage = 7 ft',
                                                    },
                        'GYCL'              :    {  'PlotTitle'         :   'Cache La Poudre R nr Greeley, CO\nFlood Stage = 8 ft',
                                                    },
                        'HAMT'              :    {  'PlotTitle'         :   'L Bighorn R at Hardin, MT\nFlood Stage = 8 ft',
                                                    },
                        'HEWY'              :    {  'PlotTitle'         :   'North Platte River at State Line\nFlood Stage = 5 ft',
                                                    },
                        'HNCL'              :    {  'PlotTitle'         :   'S Platte R at Henderson, CO\nFlood Stage = 11 ft',
                                                    },
                        'HOLM'              :    {  'PlotTitle'         :   'Missouri River bl Holter Dam, MT\nFlood Stage = NA',
                                                    },
                        'HSSD'              :    {  'PlotTitle'         :   'Fall River at Hot Springs, SD\nFlood Stage = 13 ft',
                                                    },
                        'JAND'              :    {  'PlotTitle'         :   'James River at Jamestown, ND\nFlood Stage = 12 ft',
                                                    },
                        'JMCO'              :    {  'PlotTitle'         :   'S Platte R at Julesberg, Ch 1, CO\nFlood Stage = 9 ft',
                                                    },
                        'JRCO'              :    {  'PlotTitle'         :   'S Platte R at Julesberg, Ch 2, CO\nFlood Stage = 9 ft',
                                                    },
                        'KAWY'              :    {  'PlotTitle'         :   'Bighorn River at Kane, WY\nFlood Stage = 8 ft',
                                                    },
                        'KECL'              :    {  'PlotTitle'         :   'S Platte R at Kersey, CO\nFlood Stage = 10 ft',
                                                    },
                        'LACO'              :    {  'PlotTitle'         :   'Clear Creek at Lawson, CO\nFlood Stage = NA',
                                                    },
                        'LACL'              :    {  'PlotTitle'         :   'Big Thompson R at LaSalle, CO\nFlood Stage = 9.2 ft',
                                                    },
                        'LAND'              :    {  'PlotTitle'         :   'James River at Lamoure, ND\nFlood Stage = 14 ft',
                                                    },
                        'LGMT'              :    {  'PlotTitle'         :   'Gallatin River at Logan, MT\nFlood Stage = 7.5 ft',
                                                    },
                        'MARM'              :    {  'PlotTitle'         :   'Marias River nr Shelby, MT\nFlood Stage = 9 ft',
                                                    },
                        'MCMT'              :    {  'PlotTitle'         :   'Madison River nr McAllister, MT\nFlood Stage = 4.4 ft',
                                                    },
                        'MELM'              :    {  'PlotTitle'         :   'Big Hole River at Melrose, MT\nFlood Stage = 6.5 ft',
                                                    },
                        'MOCL'              :    {  'PlotTitle'         :   'Bear Cr at Morrison, CO\nFlood Stage = 7.5 ft',
                                                    },
                        'PACO'              :    {  'PlotTitle'         :   'Cherry Creek at Parker, CO\nFlood Stage = NA',
                                                    },
                        'PIND'              :    {  'PlotTitle'         :   'Pingree Creek at Pipestem, ND\nFlood Stage = 9 ft',
                                                    },
                        'PTCL'              :    {  'PlotTitle'         :   'St Vrain Creek at Platteville, CO\nFlood Stage = NA',
                                                    },
                        'RCSD'              :    {  'PlotTitle'         :   'Rapid Creek at Rapid City, SD\nFlood Stage = 7 ft',
                                                    },
                        'RESD'              :    {  'PlotTitle'         :   'James River at Redfield, SD\nFlood Stage = 14 ft',
                                                    },
                        'RILW'              :    {  'PlotTitle'         :   'Little Wind River nr Riverton, WY\nFlood Stage = 10 ft',
                                                    },
                        'RONE'              :    {  'PlotTitle'         :   'Salt Creek at Roca, NE\nFlood Stage = 19 ft',
                                                    },
                        'RTCL'              :    {  'PlotTitle'         :   'Roberts Tunnel into NF South Platte above Grant, CO\nFlood Stage = NA',
                                                    },
                        'SBND'              :    {  'PlotTitle'         :   'Heart River at Starck Bridge, ND\nFlood Stage = NA',
                                                    },
                        'SECO'              :    {  'PlotTitle'         :   'Plum Cr at Sedalia, CO\nFlood Stage = 5 ft',
                                                    },
                        'SIWY'              :    {  'PlotTitle'         :   'N Platte R at Sinclair, WY\nFlood Stage = NA',
                                                    },
                        'SKSD'              :    {  'PlotTitle'         :   'Skunk Creek nr Sioux Falls, SD\nFlood Stage = 11.5 ft',
                                                    },
                        'SMCL'              :    {  'PlotTitle'         :   'S Platte R ab Spinney Res, CO\nFlood Stage = NA',
                                                    },
                        'SRBB'              :    {  'PlotTitle'         :   'Shoshone R bl Buffalo Bill Dam, WY\nFlood Stage = 8 ft',
                                                    },
                        'SRCL'              :    {  'PlotTitle'         :   'Bear Cr at Sheridan, CO\nFlood Stage = 8 ft',
                                                    },
                        'TBMT'              :    {  'PlotTitle'         :   'Beaverhead R nr Twin Bridges, MT\nFlood Stage = 10 ft',
                                                    },
                        'UL6E'              :    {  'PlotTitle'         :   'Missouri River at Ulm, MT\nFlood Stage = 13 ft',
                                                    },
                        'VAMT'              :    {  'PlotTitle'         :   'Sun River at Vaughn, MT\nFlood Stage = 10 ft',
                                                    },
                        'VUMT'              :    {  'PlotTitle'         :   'Muddy Cr nr Vaughn, MT\nFlood Stage = 13.1 ft',
                                                    },
                        'WAKP'              :    {  'PlotTitle'         :   'Oak Creek at Wakpala, SD\nFlood Stage = 10 ft',
                                                    },
                        'WECL'              :    {  'PlotTitle'         :   'S Platte R at Weldona, CO = 9 ft',
                                                    },
                        'WPSD'              :    {  'PlotTitle'         :   'Elm River near Westport, SD\nFlood Stage = 14 ft',
                                                    },
                        'WRCH'              :    {  'PlotTitle'         :   'Wind R at Crowheart, WY\nFlood Stage = 6 ft',
                                                    },
                        'WRKY'              :    {  'PlotTitle'         :   'Wind R at Kinnear, WY\nFlood Stage = NA',
                                                    },
                        'WRRY'              :    {  'PlotTitle'         :   'Wind R at Riverton, WY\nFlood Stage = 9 ft',
                                                    },
                        'WSSD'              :    {  'PlotTitle'         :   'Cheyenne River at Wasta, SD\nFlood Stage = 16 ft',
                                                    },
                        'WTCO'              :    {  'PlotTitle'         :   'S Platte R at Waterton, CO\nFlood Stage = 6 ft',
                                                    },
                        'WTSD'              :    {  'PlotTitle'         :   'Big Sioux River at Watertown, SD\nFlood Stage = NA',
                                                    },
                        # NWK Stations
                        'ACHK'              :    {  'PlotTitle'         :   'S Fork Sappa Creek nr Achilles, KS\nFlood Stage = 13 ft',
                                                    },
                        'ADAK'              :    {  'PlotTitle'         :   'Salt Creek near Ada, KS\nFlood Stage = 18 ft',
                                                    },
                        'ARDK'              :    {  'PlotTitle'         :   'Smoky Hill River nr Arnold, KS\nFlood Stage = 7 ft',
                                                    },
                        'ARHM'              :    {  'PlotTitle'         :   'South Grand River at Archie, MO\nFlood Stage = 15 ft',
                                                    },
                        'BAGM'              :    {  'PlotTitle'         :   'Osage River below Bagnell Reservoir, MO\nFlood Stage = 25 ft',
                                                    },
                        'BARN'              :    {  'PlotTitle'         :   'Big Blue River at Barneston, NE\nFlood Stage = 20 ft',
                                                    },
                        'BEDI'              :    {  'PlotTitle'         :   'East Fork 102 River near Bedford, IA\nFlood Stage = 21 ft',
                                                    },
                        'BROK'              :    {  'PlotTitle'         :   'White Rock Cr nr Burr Oak, KS\nFlood Stage = 10 ft',
                                                    },
                        'CDBK'              :    {  'PlotTitle'         :   'Beaver Creek at Cedar Bluffs, KS\nFlood Stage = 10 ft',
                                                    },
                        'BUNK'              :    {  'PlotTitle'         :   'Smoky Hill River nr Bunker Hill, KS\nFlood Stage = 20 ft',
                                                    },
                        'CDBK'              :    {  'PlotTitle'         :   'Beaver Creek at Cedar Bluff, KS\nFlood Stage = NA',
                                                    },
                        'CHPK'              :    {  'PlotTitle'         :   'Chapman Creek nr Chapman, KS\nFlood Stage = NA',
                                                    },
                        'CHTI'              :    {  'PlotTitle'         :   'Chariton River near Chariton, IA\nFlood Stage = 15 ft',
                                                    },
                        'CLAK'              :    {  'PlotTitle'         :   'Republican River at Clay Center, KS\nFlood Stage = 15 ft',
                                                    },
                        'CLRI'              :    {  'PlotTitle'         :   'Nodaway River at Clarinda, IA\nFlood Stage = NA',
                                                    },
                        'CLRK'              :    {  'PlotTitle'         :   'Soldir Cr near Circleville, KS\nFlood Stage = NA',
                                                    },
                        'CMBN'              :    {  'PlotTitle'         :   'Republican River at Cambridge, NE\nFlood Stage = 9 ft',
                                                    },
                        'CNKK'              :    {  'PlotTitle'         :   'Republican River at Concordia, KS\nFlood Stage = 15 ft',
                                                    },
                        'CPMO'              :    {  'PlotTitle'         :   'Sac River near Caplinger Mills, MO\nFlood Stage = 14 ft',
                                                    },
                        'CRTN'              :    {  'PlotTitle'         :   'Big Blue River near Crete, NE\nFlood Stage = 18 ft',
                                                    },
                        'CSMK'              :    {  'PlotTitle'         :   'Big Blue River nr Manhattan, KS\nFlood Stage = NA',
                                                    },
                        'DCM1'              :    {  'PlotTitle'         :   'Tunnel Dam on the Osage R, MO\nFlood Stage = NA',
                                                    },
                        'DDVM'              :    {  'PlotTitle'         :   'Sac River near Dadeville, MO\nFlood Stage = NA',
                                                    },
                        'DELK'              :    {  'PlotTitle'         :   'Soldier Cr near Delia, KS\nFlood Stage = 17 ft',
                                                    },
                        'DMRK'              :    {  'PlotTitle'         :   'SF Solomon River at Damar, KS\nFlood Stage = 7 ft',
                                                    },
                        'EKDK'              :    {  'PlotTitle'         :   'Smoky Hill River near Elkader, KS\nFlood Stage = 8 ft',
                                                    },
                        'EPKS'              :    {  'PlotTitle'         :   'Smoky Hill River at Enterprise, KS\nFlood Stage = 26 ft',
                                                    },
                        'EWKS'              :    {  'PlotTitle'         :   'Smoky Hill River at Ellsworth, KS\nFlood Stage = 20 ft',
                                                    },
                        'FKFK'              :    {  'PlotTitle'         :   'Black Vermillion R nr Frankfort, KS\nFlood Stage = 19 ft',
                                                    },
                        'FRBN'              :    {  'PlotTitle'         :   'Little Blue River nr Fairbury, NE\nFlood Stage = 15 ft',
                                                    },
                        'FRI'               :    {  'PlotTitle'         :   'Kansas River at Fort Riley, KS\nFlood Stage = 21 ft',
                                                    },
                        'FTNK'              :    {  'PlotTitle'         :   'Little Osage River at Fulton, KS\nFlood Stage = 22 ft',
                                                    },
                        'GARK'              :    {  'PlotTitle'         :   'Pottawatomie Cr nr Garnett, KS\nFlood Stage = 26 ft',
                                                    },
                        'GDEK'              :    {  'PlotTitle'         :   'NF Solomon River at Glade, KS\nFlood Stage = 9 ft',
                                                    },
                        'GDRN'              :    {  'PlotTitle'         :   'Republican R at Guide Rock, NE\nFlood Stage = 16 ft',
                                                    },
                        'GFMO'              :    {  'PlotTitle'         :   'Turnback Cr above Greenfield, MO\nFlood Stage = NA',
                                                    },
                        'GLNK'              :    {  'PlotTitle'         :   'Solomon River bl Glen Elder, KS\nFlood Stage = 21 ft',
                                                    },
                        'HACN'              :    {  'PlotTitle'         :   'Republican R bl Harlan Co Dam, NE\nFlood Stage = NA',
                                                    },
                        'HARN'              :    {  'PlotTitle'         :   'Republican River near Hardy, NE\nFlood Stage = 11 ft',
                                                    },
                        'HNIA'              :    {  'PlotTitle'         :   'West Fork Ditch at Hornick, IA\nFlood Stage = NA',
                                                    },
                        'HILK'              :    {  'PlotTitle'         :   'Big Bull Cr bl Hillsdale, KS\nFlood Stage = 17 ft',
                                                    },
                        'HTNM'              :    {  'PlotTitle'         :   'Little Osage River at Horton, MO\nFlood Stage = 41 ft',
                                                    },
                        'JRMM'              :    {  'PlotTitle'         :   'Gasconade River at Jerome, MO\nFlood Stage = 15 ft',
                                                    },
                        'KACM'              :    {  'PlotTitle'         :   'Blue River at Bannister, KS\nFlood Stage = 21 ft',
                                                    },
                        'KCKK'              :    {  'PlotTitle'         :   'Kansas R at 23rd St in KC, KS\nFlood Stage = 23 ft',
                                                    },
                        'LCGK'              :    {  'PlotTitle'         :   'Solomon River bl Glen Elder, KS\nFlood Stage = NA',
                                                    },
                        'LEKS'              :    {  'PlotTitle'         :   'Kansas River at Lecompton, KS\nFlood Stage = 17 ft',
                                                    },
                        'LGLK'              :    {  'PlotTitle'         :   'Smoky Hill R nr Langley, KS\nFlood Stage = NA',
                                                    },
                        'LNDK'              :    {  'PlotTitle'         :   'Salt Cr Trib nr Lyndon, KS\nFlood Stage = 15 ft',
                                                    },
                        'LIVM'              :    {  'PlotTitle'         :   'Chariton River near Livonia, MO\nFlood Stage = NA',
                                                    },
                        'LOVK'              :    {  'PlotTitle'         :   'White Rock Cr bl Lovewell Dam, KS\nFlood Stage = NA',
                                                    },
                        'LWRK'              :    {  'PlotTitle'         :   'Wakarusa River nr Lawrence, KS\nFlood Stage = 23 ft',
                                                    },
                        'MAMO'              :    {  'PlotTitle'         :   'EF Little Chariton nr Macon, MO\nFlood Stage = 17 ft',
                                                    },
                        'MARK'              :    {  'PlotTitle'         :   'Marmaton River at Marmaton, KS\nFlood Stage = NA',
                                                    },
                        'MEKS'              :    {  'PlotTitle'         :   'Smoky Hill River nr Mentor, KS\nFlood Stage = 16 ft',
                                                    },
                        'MILB'              :    {  'PlotTitle'         :   'Republican R bl Milford Dam, KS\nFlood Stage = NA',
                                                    },
                        'MKSL'              :    {  'PlotTitle'         :   'Marais D C R nr KS-MO State Line\nFlood Stage = 25 ft',
                                                    },
                        'MLTI'              :    {  'PlotTitle'         :   'Chariton River near Moulton, IA\nFlood Stage = 35 ft',
                                                    },
                        'MRRM'              :    {  'PlotTitle'         :   'Little Sac River nr Morrisville, MO\nFlood Stage = NA',
                                                    },
                        'MRYK'              :    {  'PlotTitle'         :   'Big Blue River at Marysville, KS\nFlood Stage = 35 ft',
                                                    },
                        'MSCK'              :    {  'PlotTitle'         :   'Delaware River nr Muscotah, KS\nFlood Stage = 27 ft',
                                                    },
                        'MUNK'              :    {  'PlotTitle'         :   'Big Creek near Hays, KS\nFlood Stage = 18 ft',
                                                    },
                        'NEVM'              :    {  'PlotTitle'         :   'Marmaton River at Nevada, MO\nFlood Stage = 44 ft',
                                                    },
                        'NLSK'              :    {  'PlotTitle'         :   'Solomon River at Niles, KS\nFlood Stage = 24 ft',
                                                    },
                        'NOVM'              :    {  'PlotTitle'         :   'Chariton River at Novinger, MO\nFlood Stage = 20 ft',
                                                    },
                        'NWCK'              :    {  'PlotTitle'         :   'Smoky Hill River at New Cambria, KS\nFlood Stage = 25 ft',
                                                    },
                        'ORNN'              :    {  'PlotTitle'         :   'Republican River at Orleans, NE\nFlood Stage = 9 ft',
                                                    },
                        'OSBK'              :    {  'PlotTitle'         :   'SF Solomon River at Osborne, KS\nFlood Stage = 14 ft',
                                                    },
                        'OTTK'              :    {  'PlotTitle'         :   'Marais D C River nr Ottawa, KS\nFlood Stage = 31 ft',
                                                    },
                        'OTVM'              :    {  'PlotTitle'         :   'Lamine River near Otterville, MO\nFlood Stage = NA',
                                                    },
                        'PALN'              :    {  'PlotTitle'         :   'Frenchman Cr at Palisade, NE\nFlood Stage = NA',
                                                    },
                        'PDTM'              :    {  'PlotTitle'         :   'Pomme D T R bl PODT nr Hermitage, MO\nFlood Stage = NA',
                                                    },
                        'PLKM'              :    {  'PlotTitle'         :   'Lindley Creek near Polk, MO\nFlood Stage = 17 ft',
                                                    },
                        'PLVM'              :    {  'PlotTitle'         :   'Cedar Cr nr Pleasant View, MO\nFlood Stage = NA',
                                                    },
                        'PMNK'              :    {  'PlotTitle'         :   'Marais des Cygnes R nr Pomona, KS\nFlood Stage = 20 ft',
                                                    },
                        'POKM'              :    {  'PlotTitle'         :   'Pomme De Terre R at Polk, MO\nFlood Stage = 15 ft',
                                                    },
                        'POMK'              :    {  'PlotTitle'         :   '110-Mile Creek nr Quenemo, KS\nFlood Stage = NA',
                                                    },
                        'PRMI'              :    {  'PlotTitle'         :   'SF Chariton River at Promise City, IA\nFlood Stage = 18 ft',
                                                    },
                        'PTSK'              :    {  'PlotTitle'         :   'NF Solomon River at Portis, KS\nFlood Stage = 15 ft',
                                                    },
                        'PXCK'              :    {  'PlotTitle'         :   'Mill Creek near Paxico, KS\nFlood Stage = 19 ft',
                                                    },
                        'QUKS'              :    {  'PlotTitle'         :   'Marais Des Cygnes R nr Quenemo, KS\nFlood Stage = 17 ft',
                                                    },
                        'RDGK'              :    {  'PlotTitle'         :   'Marais Des Cygnes R nr Reading, KS\nFlood Stage = 19 ft',
                                                    },
                        'RUSK'              :    {  'PlotTitle'         :   'Saline River nr Russell, KS\nFlood Stage = 18 ft',
                                                    },
                        'SCMO'              :    {  'PlotTitle'         :   'Osage River above Schell City, MO\nFlood Stage = NA',
                                                    },
                        'SCSK'              :    {  'PlotTitle'         :   'Smoky Hill R nr Schoenchen, KS\nFlood Stage = 11 ft',
                                                    },
                        'SHJM'              :    {  'PlotTitle'         :   'Sac R at Hwy J bl Stockton Dam, MO\nFlood Stage = 18 ft',
                                                    },
                        'SIMK'              :    {  'PlotTitle'         :   'Solomon River near Simpson, KS\nFlood Stage = 20 ft',
                                                    },
                        'SKTK'              :    {  'PlotTitle'         :   'Bow Creek near Stockton, KS\nFlood Stage = 9 ft',
                                                    },
                        'SMHM'              :    {  'PlotTitle'         :   'Little Platte R nr Smithville, KS\nFlood Stage = 24 ft',
                                                    },
                        'STMN'              :    {  'PlotTitle'         :   'Sappa Cr nr Stamford, NE\nFlood Stage = 14 ft',
                                                    },
                        'STOM'              :    {  'PlotTitle'         :   'Sac River bl Stockton Dam, MO\nFlood Stage = NA',
                                                    },
                        'STTM'              :    {  'PlotTitle'         :   'Osage River bl St. Thomas, MO\nFlood Stage = 23 ft',
                                                    },
                        'STTN'              :    {  'PlotTitle'         :   'Republican R at Stratton, NE\nFlood Stage = 11 ft',
                                                    },
                        'TNGK'              :    {  'PlotTitle'         :   'Stranger Cr nr Tonganoxie, KS\nFlood Stage = 23 ft',
                                                    },
                        'TOPK'              :    {  'PlotTitle'         :   'Soldier Cr nr Topeka, KS\nFlood Stage = 12 ft',
                                                    },
                        'TPAK'              :    {  'PlotTitle'         :   'Kansas River at Topeka, KS\nFlood Stage = 26 ft',
                                                    },
                        'TSTK'              :    {  'PlotTitle'         :   'Saline River at Tescott, KS\nFlood Stage = 25 ft',
                                                    },
                        'WAAK'              :    {  'PlotTitle'         :   'Saline River at WaKeeney, KS\nFlood Stage = 13 ft',
                                                    },
                        'WGKS'              :    {  'PlotTitle'         :   'Kansas River at Wamego, KS\nFlood Stage = 19 ft',
                                                    },
                        'WILK'              :    {  'PlotTitle'         :   'Saline R bl Wilson Dam, KS\nFlood Stage = NA',
                                                    },
                        'WODK'              :    {  'PlotTitle'         :   'SF Solomon R at Woodston, KS\nFlood Stage = NA',
                                                    },
                        'WOFK'              :    {  'PlotTitle'         :   'Prairie Dog Cr nr Woodruff, KS\nFlood Stage = NA',
                                                    },
                        'WSHK'              :    {  'PlotTitle'         :   'Mill Creek at Washington, KS\nFlood Stage = 18 ft',
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
                PlotTitle = LongName.replace(' on ', '\n')
                LocationProperties.setdefault(location, {}).setdefault('PlotTitle', PlotTitle)

            outputDebug(debug, lineNo(), 'Creating plot for %s' % location)
            # Retrieve time series from database and add to list
            # Stage data
            if (StageInstHourBestNwdm % location) in PathnameList :
                try : StageTsc = CwmsDb.read(StageInstHourBestNwdm % location).getData()
                except : StageTsc = CwmsDb.get(StageInstHourBestNwdm % location)
            else :
                # Create a blank time series so the plot can be created
                StageTsc = createBlankTimeSeries(debug, '%s.Stage.Inst.1Hour.0.No Available Data' % location, 'ft', StartTw, EndTwStr)
            # Flow data
            if (FlowInstHourBestNwdm % location) in PathnameList :
                try : FlowTsc = CwmsDb.read(FlowInstHourBestNwdm % location).getData()
                except : FlowTsc = CwmsDb.get(FlowInstHourBestNwdm % location)
            else :
                # Create a blank time series so the plot can be created
                FlowTsc = createBlankTimeSeries(debug, '%s.Flow.Inst.1Hour.0.No Available Data' % location, 'cfs')
            
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
            ViewportLayoutsInfo = [ [   TopViewportLayout,    StageTsc,       'Y1',       'Stage'],
                                    [   BottomViewportLayout, FlowTsc,        'Y1',       'Flow']
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
