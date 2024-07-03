'''
Author: Scott Hoffman
Last Updated: 09-16-2018
Description: Create the NWK 7 Day Lake Bulletin
'''

#
# Imports
#
from com.itextpdf.text      import Document, DocumentException, Rectangle, Paragraph, Phrase, Chunk, Font, FontFactory, BaseColor, PageSize, Element, Image
from com.itextpdf.text.Font import FontFamily
from com.itextpdf.text.pdf  import PdfWriter, PdfPCell, PdfPTable, PdfPage, PdfName, PdfPageEventHelper, BaseFont, PdfDocument
from hec.data.cwmsRating    import RatingSet
from hec.heclib.util        import HecTime
from hec.io                 import TimeSeriesContainer
from hec.script             import Constants, MessageBox
from java.awt.image         import BufferedImage
from java.io                import FileOutputStream, IOException
from java.lang              import System
from java.text              import NumberFormat, SimpleDateFormat
from java.util              import Locale, Calendar, TimeZone
from time                   import mktime, localtime
from subprocess             import Popen
import os, sys, inspect, datetime, time, DBAPI

#
# File pathnames
#
# PC pathnames
HomeDirectory = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\" # Used in the properties file to create pathname for Seals and Symbols
iTextPdfPathname = "C:\\Local_Software\\CWMS\\v3.1.0.781\\CAVI\\jar\\sys\\iText-5.0.6.jar"
BulletinFilename = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\Bulletins\\NWK_Lake_Weekly\\7daylak3.pdf"
ArchiveBulletinFilename = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\Bulletins\\NWK_Lake_Weekly\\7daylak3_%s.pdf"
CsvFilename = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\Bulletins\\NWK_Lake_Weekly\\7daylak3.csv"
CronjobsDirectory = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs"
BulletinPropertiesPathname = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\Bulletins\\NWK_Lake_Weekly\\NWK_Lake_Properties.txt"
'''

# Server pathnames
BulletinScriptDirectory = os.path.dirname(os.path.realpath(__file__))
PathList = BulletinScriptDirectory.split('/')
HomeDirectory = '/'.join(PathList[: -1]) + '/'
CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
BulletinScriptDirectory += '/'
BulletinFilename = HomeDirectory + '7daylak3.pdf'
ArchiveBulletinFilename = HomeDirectory + '7daylak3_%s.pdf'
CsvFilename = HomeDirectory + '7daylak3.csv'
BulletinTsFilePathname = HomeDirectory + 'Bulletins_Time_Series.txt'
BulletinPropertiesPathname = BulletinScriptDirectory + 'NWK_Lake_Properties.txt'
'''

if CronjobsDirectory not in sys.path : sys.path.append(CronjobsDirectory)

#
# Input
#
# Set debug = True to print all debug statements and = False to turn them off
debug = False

# Import variables in the time series and properties files
import DatabasePathnames
reload(DatabasePathnames)
from DatabasePathnames      import *
BulletinProperties = open(BulletinPropertiesPathname, "r"); exec(BulletinProperties)

##################################################################################################################################
#
# Functions
#

#
# bulletinFooter Function   : Creates a footer for the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def bulletinFooter( debug,  # Set to True to print all debug statements
                    Footer  # PdfPTable object
                    ) :
    # Add the footer image to the footer
    Img = Image.getInstance(FooterImage)
    Img.scalePercent(20)
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Img, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_LEFT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Footer.addCell(Cell)

    # Add the page numbers to the footer
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Page %d of 2' % Writer.getPageNumber(), TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Footer.addCell(Cell)
    
    return Footer

#
# createCell Function   : Creates a PdfPCell for tables
# Author/Editor         : Ryan Larsen
# Last updated          : 12-20-2017
#
def createCell( debug,                  # Set to True to print all debug statments
                CellData,               # Data that will appear within the cell
                RowSpan,                # Specifies number of rows information within cell will span
                ColSpan,                # Specifies number of columns information within cell will span
                HorizontalAlignment,    # Specifies horizontal alignment: ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT
                VerticalAlignment,      # Specifies vertical alignment: ALIGN_CENTER, ALIGN_TOP, ALIGN_BOTTOM
                CellPadding,            # List of cell padding around text: [Top, Right, Bottom, Left]
                BorderColors,           # List of border colors: [Top, Right, Bottom, Left]
                BorderWidths,           # List of border widths: [Top, Right, Bottom, Left]
                VariableBorders,        # Allows or denies variable borders: True, False
                BackgroundColor         # Color of cell background
                ) :
    Cell = PdfPCell(CellData)
    Cell.setRowspan(RowSpan); Cell.setColspan(ColSpan)
    Cell.setHorizontalAlignment(HorizontalAlignment); Cell.setVerticalAlignment(VerticalAlignment)
    Cell.setPaddingTop(CellPadding[0]); Cell.setPaddingRight(CellPadding[1]); Cell.setPaddingBottom(CellPadding[2]); Cell.setPaddingLeft(CellPadding[3])
    Cell.setBorderColorTop(BorderColors[0]); Cell.setBorderColorRight(BorderColors[1]); Cell.setBorderColorBottom(BorderColors[2]); Cell.setBorderColorLeft(BorderColors[3])
    Cell.setBorderWidthTop(BorderWidths[0]); Cell.setBorderWidthRight(BorderWidths[1]); Cell.setBorderWidthBottom(BorderWidths[2]); Cell.setBorderWidthLeft(BorderWidths[3])
    Cell.setUseVariableBorders(VariableBorders)
    Cell.setBackgroundColor(BackgroundColor)

    return Cell

#
# lineNo Function   : Retrieves the line number of the script.  Used when debugging
# Author/Editor     : Ryan Larsen
# Last updated      : 12-09-2016
#
def lineNo() :
    return inspect.currentframe().f_back.f_lineno

#
# outputDebug Function  : Debugging function that prints specified arguments
# Author/Editor         : Ryan Larsen
# Last updated          : 03-27-2017
#
def outputDebug(    *args
                    ) :
    ArgCount = len(args)
    if ArgCount < 2 :
        raise ValueError('Expected at least 2 arguments, got %d' % argCount)
    if type(args[0]) != type(True) :
        raise ValueError('Expected first argument to be either True or False')
    if type(args[1]) != type(1) :
        raise ValueError('Expected second argument to be line number')

    if args[0] == True: 
        DebugStatement = 'Debug Line %d   |\t' % args[1]
        for x in range(2, ArgCount, 1) :
            DebugStatement += str(args[x])
        print DebugStatement
###########################################################################################
#
# retrieveElevatonDatum Function : Retrieves Elevation datum
# Author/Editor                  : Scott Hoffman
# Last updated                   : 06-25-2018
#
def retrieveElevatonDatum(debug,        # Set to True to print all debug statements
                        conn,           #
                        BaseLocation,   # Full name of time series container
                        ) :
    try :
        stmt = conn.prepareStatement('''
                                    select distinct
                                    bl.elevation as base_location_elevation
                                    from cwms_v_loc loc
                                    inner join cwms_v_loc bl on bl.base_location_code = loc.base_location_code
                                        and bl.db_office_id = loc.db_office_id
                                        and bl.unit_system = loc.unit_system
                                    where loc.UNIT_SYSTEM = 'EN'
                                        and loc.db_office_id = :1
                                        and bl.location_id = :2
                                    ''')
        stmt.setString(1, 'NWDM')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()

        while rs.next() :
            ElevationDatum = str(rs.getString(1))
            break
    finally :
        stmt.close()
        rs.close()
    return ElevationDatum
##############################################################################################
#
# retrievePublicName Function    : Retrieves reservoir zone data
# Author/Editor                  : Ryan Larsen
# Last updated                   : 01-30-2018
#
def retrievePublicName( debug,          # Set to True to print all debug statements
                        conn,           # 
                        BaseLocation,   # Full name of time series container
                        ) :
    try :
        stmt = conn.prepareStatement('''
                                    select distinct
                                    bl.public_name as base_location_public_name
                                    from cwms_v_loc loc 
                                    inner join cwms_v_loc bl on bl.base_location_code = loc.base_location_code
                                        and bl.db_office_id = loc.db_office_id 
                                        and bl.unit_system = loc.unit_system
                                    where loc.UNIT_SYSTEM = 'EN' 
                                        and loc.db_office_id = :1 
                                        and bl.location_id = :2
                                    ''')   
        stmt.setString(1, 'NWDM')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()
        
        while rs.next() : 
            PublicName = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()

    return PublicName
#################################################################################################
#
# checkTs Function    : Check if the TS is in the database
# Author/Editor       : Scott Hoffman
#
def checkTs(timeseries,
            conn,) :
    try :
       stmt = conn.createStatement()
       #check if timeseries exist in DB
       sql = "select * from CWMS_20.av_cwms_ts_id where cwms_ts_id='" + timeseries + "'"
       rset = stmt.executeQuery(sql)
       if rset.next() :
          #Found timeseries
          flag = 'true'
       else :
          flag = 'false'
    finally :
       stmt.close()
       rset.close()
    return flag
################################################################################################
#
# retrieveLocationLevel Function    : Retrieves reservoir zone data
# Author/Editor                     : Mike Perryman
# Last updated                      : 05-01-2017
#
def retrieveLocationLevel(  debug,          # Set to True to print all debug statements
                            conn,           # 
                            CwmsDb,         # DBAPI connection
                            TscFullName,    # Full name of time series container
                            ) :
    CurDate         = datetime.datetime.now() # Current date
    StartTimeStr    = CurDate.strftime('%d%b%Y ') + '0000' # Start date formatted as ddmmmyyy 0000
    EndTimeStr      = CurDate.strftime('%d%b%Y ') + '0000' # End date formatted as ddmmmyyy 0000

    level_1a = TimeSeriesContainer()
    level_1a_parts = TscFullName.split('.')
    level_1aId_parts = level_1a_parts[:]
    level_1aId = '.'.join(level_1aId_parts)
    
    level_1a.fullName  = TscFullName
    level_1a.location  = level_1a_parts[0]
    level_1a.parameter = level_1a_parts[1]
    level_1a.interval  = 0
    level_1a.version   = level_1a_parts[-1]
    if level_1a_parts[1] == 'Stor' : level_1a.units = 'ac-ft'
    elif level_1a_parts[1] == 'Elev' : level_1a.units = 'ft'
    elif level_1a_parts[1] == 'Flow' : level_1a.units = 'cfs'
    elif level_1a_parts[1] == 'Stage' : level_1a.units = 'ft'
    level_1a.type      = 'INST-VAL'
    
    try :
        stmt = conn.prepareStatement('''
                              select * from table(cwms_level.retrieve_location_level_values(
                              p_location_level_id => :1,
                              p_level_units       => :2,
                              p_start_time        => to_date(:3, 'ddmonyyyy hh24mi'),
                              p_end_time          => to_date(:4, 'ddmonyyyy hh24mi'),
                              p_timezone_id       => :5))
                        ''')   
        stmt.setString(1, level_1aId)
        stmt.setString(2, level_1a.units)
        stmt.setString(3, StartTimeStr)
        stmt.setString(4, EndTimeStr)
        stmt.setString(5, CwmsDb.getTimeZoneName())
        rs = stmt.executeQuery()
        while rs.next() : 
            LocationLevel = rs.getDouble(2)
            break
    finally :
        stmt.close()
        rs.close()
    
    return LocationLevel


###################################################################################################
#
# table1Data Function   : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table1Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName,    # String name for data section of table
                startTime,
                endTime,
                dateArray,
                locDict
                ) :
    Table.setSplitLate(False)
    Table.setSplitRows(True) 

    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)

    # Data Block Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font45)), TableLayoutDict[TableName]['RowSpan'], 
            Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [0, 2, 2, 3], 
            TableLayoutDict[TableName]['BorderColors'], [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
    Table.addCell(Cell)

    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        PublicName = locDict[project]['BulletinName']
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == DataBlocks[-1] and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False

        # Reset TotalColSpan to 0
        TotalColSpan = 0

        projectElev = True
        projectInflow = True
        projectFlowTot = True
        
        for data in DataOrder :
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)

            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)

            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
            RowSpan = TableLayoutDict[TableName]['RowSpan']; 
            ColSpan = TableLayoutDict[TableName]['ColSpan']   
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding']#[Top, Right, Bottom, Left]
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
            # 0 - Project Bulletin Name
            if data == 'PublicName' :
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                CellPadding = [0, 2, 2, 3] #[Top, Right, Bottom, Left]#Indent the project names               
                BorderWidths = [0.25, 0.5, 0.25, 1] #[Top, Right, Bottom, Left]

                # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                Table.addCell(Cell)
            # 1 - TopOfConsZoneElev
            elif data == 'TopOfConsZoneElev' :
                ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                try :
                    MpElevZone = retrieveLocationLevel(debug, conn, CwmsDb, ElevZoneFullName)
                    outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)

                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpElevZone, TextFont))
                except :
                    MpElevZone = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(MpElevZone, TextFont))

                # Change default cell properties
                ColSpan = 9
                HorizontalAlignment = Element.ALIGN_LEFT 
                BorderWidths = [0.25, 1, 0.25, 0.5]
                BorderColors = [Color2, Color2, Color2, Color3]

                # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                Table.addCell(Cell)
            # 2 - Elevation
            elif data == 'Elevation' :
                if (projectElev == True) :
                    CellData = Phrase(Chunk('Elevation', TextFont))
                                        
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, 2, Element.ALIGN_LEFT, VerticalAlignment, [0, 2, 2, 15], 
                                      [Color2, Color3, Color2, Color2], [0.25, 0.5, 0.25, 1], VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
                    
                    projectElev = False
                if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
                    if DataBlockDict['DataBlocks'][TableDataName][data] % project in PathnameList :
                        TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    elif '%s.Elev.Inst.1Hour.0.Combined-rev' % locDict[project]['DbLocation'] in PathnameList :
                        TscPathname = '%s.Elev.Inst.1Hour.0.Combined-rev' % locDict[project]['DbLocation']    
                    #TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % locDict[project]['DbLocation']    
                    if checkTs(TscPathname, conn) == 'true' :
                        try :
                            startTime =  dateArray[0]
                            endTime = dateArray[len(dateArray)-1]
                            
                            if project in ['STON', 'HAST', 'BAGL']:
                                startTime = startTime.replace("1200", "0600")
                                endTime = endTime.replace("1200", "0600")
                            
                            Tsc = CwmsDb.get(TscPathname, startTime, endTime)    
                            myArray = Tsc.values
                            if len(myArray) < len(dateArray) :
                                while len(myArray) < len(dateArray) :
                                    myArray.append(Constants.UNDEFINED)

                            for x in range(0,len(dateArray),1):
                                if myArray != Null :
                                    EleValue = myArray[x]
                                else : 
                                    EleValue = Missing
                                
                                # If previous day's value is missing raise an exception and using the missing value
                                if EleValue == Constants.UNDEFINED :
                                    EleValue = Missing
                                
                                # Create a formatted string that will be added to the table
                                if EleValue == Missing :
                                    CellData = Phrase(Chunk(Missing, TextFont))
                                else : 
                                    CellData = Phrase(Chunk(TableLayoutDict[TableName]['Column2'][1]['Format'] % EleValue, TextFont))
                                
                                # Change default cell properties
                                if x == len(dateArray)-1 :
                                    BorderWidths = [0.25, 1, 0.25, 0.25] #[Top, Right, Bottom, Left]
                                    BorderColors = TableLayoutDict[TableName]['BorderColors']
                                elif x == 0 :
                                    BorderWidths = [0.25, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
                                    BorderColors = [Color2, Color2, Color2, Color3]
                                else :
                                    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
                                    BorderColors = TableLayoutDict[TableName]['BorderColors']
                                
                                # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                Table.addCell(Cell)
                        except :
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(Missing, TextFont))
                            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                            Table.addCell(Cell)
                    else :
                        #None, set value to Null
                        CellData = Phrase(Chunk(Missing, TextFont))
                        # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                        Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                        Table.addCell(Cell)
                else :
                    #None, set value to Null
                    CellData = Phrase(Chunk(Null, TextFont))
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
            # 3 Inflow
            elif data == 'FlowIn':
                if(projectInflow == True) :
                    CellData = Phrase(Chunk('Inflow', TextFont))
                    
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, 2, Element.ALIGN_LEFT, VerticalAlignment, [0, 2, 2, 15], 
                                      [Color2, Color3, Color2, Color2], [0.25, 0.5, 0.25, 1], VariableBorders, BackgroundColor)
                    Table.addCell(Cell)

                    projectInflow = False
    
                    if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
                        if DataBlockDict['DataBlocks'][TableDataName][data] % project in PathnameList :
                            TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project    
                        elif '%s.Flow-In.Ave.1Day.1Day.Combined-rev' % locDict[project]['DbLocation'] in PathnameList :
                            TscPathname = '%s.Flow-In.Ave.1Day.1Day.Combined-rev' % locDict[project]['DbLocation']    
                        #TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % locDict[project]['DbLocation']
                        if checkTs(TscPathname, conn) == 'true' :
                            try :
                                startTime =  dateArray[0]
                                endTime = dateArray[len(dateArray)-1]
                                
                                if project in ['STON', 'HAST', 'BAGL']:
                                    startTime = startTime.replace("1200", "0600")
                                    endTime = endTime.replace("1200", "0600")
                                
                                Tsc = CwmsDb.get(TscPathname, startTime, endTime)
                                myArray = Tsc.values
                                if len(myArray) < len(dateArray) :
                                    while len(myArray) < len(dateArray) :
                                        myArray.append(Constants.UNDEFINED) 
                                
                                for x in range(0,len(dateArray),1) :
                                    if myArray != Null :
                                        InflowValue = myArray[x]
                                    else :
                                        InflowValue = Missing
                                
                                    # If value is missing raise an exception and using the missing value
                                    if InflowValue == Constants.UNDEFINED : 
                                        InflowValue = Missing
                                    
                                    # Create a formatted string that will be added to the table
                                    if InflowValue == Missing :
                                        CellData = Phrase(Chunk(Missing, TextFont))
                                    else :
                                        CellData = Phrase(Chunk(TableLayoutDict[TableName]['Column2'][2]['Format'].format(int(InflowValue)), TextFont))
                                    
                                    # Change default cell properties
                                    if x == len(dateArray)-1 :
                                        BorderWidths = [0.25, 1, 0.25, 0.25] #[Top, Right, Bottom, Left]
                                        BorderColors = TableLayoutDict[TableName]['BorderColors']
                                    elif x == 0 :
                                        BorderWidths = [0.25, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
                                        BorderColors = [Color2, Color2, Color2, Color3]
                                    else :
                                        BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
                                        BorderColors = TableLayoutDict[TableName]['BorderColors']

                                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                    Table.addCell(Cell)
                            except :
                                InflowValue = Missing
                                CellData = Phrase(Chunk(Missing, TextFont))
                                # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                Table.addCell(Cell)
                else :
                    #Timeseries not found in the database, set value to Null
                    CellData = Phrase(Chunk(Null, TextFont))
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
            # 4 FlowTotal 
            elif data == 'FlowTotal' :
                if (projectFlowTot == True) :
                    BorderWidths = [0.25, 0.5, 0.25, 1]
                    '''
                    # Change default cell properties
                    if x == len(dateArray)-1 :
                        BorderWidths = [0.25, 0.5, 0.25, 1] #[Top, Right, Bottom, Left]
                    else :
                        BorderWidths = [0.25, 0.5, 0.25, 1]
                    '''
                    
                    if project == 'LOVL' or project == 'STON' :
                        BorderWidths = [0.25, 0.5, 1, 1] #[Top, Right, Bottom, Left]

                    CellData = Phrase(Chunk('Outflow', TextFont))
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, 2, Element.ALIGN_LEFT, VerticalAlignment, [0, 2, 2, 15], 
                                      [Color2, Color3, Color2, Color2], BorderWidths, VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
                    projectFlowTot = False    
                    
                    if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
                        if DataBlockDict['DataBlocks'][TableDataName][data] % project in PathnameList :
                            TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project    
                        elif '%s.Flow-Total.Ave.1Day.1Day.Combined-rev' % locDict[project]['DbLocation'] in PathnameList :
                            TscPathname = '%s.Flow-Total.Ave.1Day.1Day.Combined-rev' % locDict[project]['DbLocation']    
                        #TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % locDict[project]['DbLocation']
                        if checkTs(TscPathname, conn) == 'true' :
                            try :
                                startTime =  dateArray[0]
                                endTime = dateArray[len(dateArray)-1]
                                
                                if project in ['STON', 'HAST', 'BAGL']:    
                                    startTime = startTime.replace("1200", "0600")
                                    endTime = endTime.replace("1200", "0600")
                                
                                Tsc = CwmsDb.get(TscPathname, startTime, endTime)
                                myArray = Tsc.values
                                if len(myArray) < len(dateArray):
                                    while len(myArray) < len(dateArray):
                                        myArray.append(Constants.UNDEFINED)
                                
                                for x in range(0,len(dateArray),1):
                                    if myArray != Null :
                                        FlowTotValue = myArray[x]
                                    else :
                                        FlowTotValue = Missing    
                                
                                    # If value is missing raise an exception and using the missing value
                                    if FlowTotValue == Constants.UNDEFINED : 
                                        FlowTotValue = Missing
                                     
                                    if FlowTotValue != Missing :
                                        CellData = Phrase(Chunk(TableLayoutDict[TableName]['Column2'][3]['Format'].format(int(FlowTotValue)), TextFont))
                                    else :
                                        CellData = Phrase(Chunk(Missing, TextFont))
                                
                                    # Change default cell properties
                                    if x == len(dateArray)-1 :
                                        if project == 'LOVL' or project == 'STON' : BorderWidths = [0.25, 1, 1, 0.25] #[Top, Right, Bottom, Left]
                                        else : BorderWidths = [0.25, 1, 0.25, 0.25] #[Top, Right, Bottom, Left]
                                        BorderColors = TableLayoutDict[TableName]['BorderColors']
                                    elif x == 0 :
                                        if project == 'LOVL' or project == 'STON' : BorderWidths = [0.25, 0.25, 1, 0.5] #[Top, Right, Bottom, Left]
                                        else : BorderWidths = [0.25, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
                                        BorderColors = [Color2, Color2, Color2, Color3]
                                    else :
                                        if project == 'LOVL' or project == 'STON' : BorderWidths = [0.25, 0.25, 1, 0.25] #[Top, Right, Bottom, Left]
                                        else : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]    
                                        BorderColors = TableLayoutDict[TableName]['BorderColors']

                                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                    Table.addCell(Cell)
                            except :
                                CellData = Phrase(Chunk(Missing, TextFont))
                                # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                                Table.addCell(Cell)
                        else :
                            #Timeseries not found in the database, set value to Null
                            CellData = Phrase(Chunk(Null, TextFont))
                            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                            Table.addCell(Cell)
                else :
                    CellData = Phrase(Chunk(Null, TextFont))    
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
        
        #
        # Add a blank row to push rows to next page. Then add heading continued from previous page
        #
        if project == 'STON' :
            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            CellData = Phrase(Chunk('', TextFont))
            Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
                TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict[TableName]['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
                TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
            Cell.setBorder(Rectangle.NO_BORDER)
            Cell.setFixedHeight(25.)
            Table.addCell(Cell)

            HeadingCont = DataBlockDict['DataBlocks'][TableDataName]['Heading'] + ' Cont.'
            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Cell = createCell(debug, Phrase(Chunk(HeadingCont, Font45)), TableLayoutDict[TableName]['RowSpan'], 
                    Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [0, 2, 2, 3], 
                    TableLayoutDict[TableName]['BorderColors'], [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
            Table.addCell(Cell)
        
    return Table    
#
# table1Heading Function    : Creates the heading for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def table1Heading(  debug,  # Set to True to print all debug statements
                    Table,  # PdfPTable object
                    calendarDay,
                    calFormat
                    ) :
    #
    # Create Table1 Heading 
    #
    # Column 0 Heading
    #createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    #0
    CellData = Phrase(Chunk('Project', Font4))
    BorderWidths = [1, 0.5, 0.25, 1] 
    Cell = createCell(debug,CellData, 3, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #1
    CellData = Phrase(Chunk('Date:\nDay:\nM/P Elev', Font4))
    BorderWidths = [1, 0.5, 0.25, 0.5] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_LEFT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color3], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #2
    calendarDay.add(Calendar.DAY_OF_MONTH, -7)
    calFormat = SimpleDateFormat("dd MMM")
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    calFormat = SimpleDateFormat("dd MMM")
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #3
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #4
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #5
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #6
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #7
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #8
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    #9
    calendarDay.add(Calendar.DAY_OF_MONTH, +1)
    utcTimestamp = calFormat.format(calendarDay.getTime())
    dayInWkFormat = SimpleDateFormat("EEE")
    dayInWkTimestamp = dayInWkFormat.format(calendarDay.getTime())
    CellData = Phrase(Chunk(utcTimestamp+"\n"+dayInWkTimestamp, Font4))
    BorderWidths = [1, 1, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 2, Element.ALIGN_RIGHT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    return Table

#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def titleBlock( debug,      # Set to True to print all debug statements
                TitleBlock, # PdfPTable object
                CsvData     # Csv data
                ) :
    #
    # Add USACE Logo, title block lines, and seal to TitleBlock
    #
    TitleLines = [TitleLine1, TitleLine2, TitleLine3, TitleLine4]

    # Add the USACE Logo to the TitleBlock
    Img = Image.getInstance(UsaceLogo)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(Element.ALIGN_LEFT); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine1, Font1))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [2, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData

    # Add the seal to the TitleBlock
    Img = Image.getInstance(Seal)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(TableLayoutDict['Table1']['HorizontalAlignment']); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.LEFT); Cell.setBorderColorLeft(Color1); Cell.setBorderWidthLeft(0.5)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine2 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine2, Font2))
    Cell = createCell(debug, Phrase(Chunk(TitleLine2, Font2)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData
    
    # Add TitleLine3 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData

    # Add TitleLine4 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TitleBlock.addCell(Cell)

    return TitleBlock, CsvData

##################################################################
# Main Script
##################################################################
try :    
    #
    # Date and Time Window Info
    #
    CurDateTime = datetime.datetime.now()
    CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm
    if UseCurDate :
        Date = datetime.datetime.now() # Current date
    else :
        TimeObj = time.strptime(HistoricBulletinDate, '%d%b%Y %H%M')
        TimeObj = localtime(mktime(TimeObj)) # Convert TimeObj to local time so it includes the DST component
        Date    = datetime.datetime.fromtimestamp(mktime(TimeObj))

    calendarNow = Calendar.getInstance()
    tsFormat = SimpleDateFormat("dd MMM")

    date_list = []
    calNow = Calendar.getInstance()
    calNow.add(Calendar.DAY_OF_MONTH, -8)
    calFormat = SimpleDateFormat("ddMMMYYYY 1200")
    for x in range(0, 8, 1):
        calNow.add(Calendar.DAY_OF_MONTH, 1)
    nowTimestamp = calFormat.format(calNow.getTime())
    date_list.append(nowTimestamp)
    
    StartTw             = Date - datetime.timedelta(2)
    StartTwStr          = StartTw.strftime('%d%b%Y 2400') # Start of time window for the database formatted as ddmmmyyyy 2400
    EndTribTwStr        = Date
    EndTw               = Date
    EndTribTw           = Date - datetime.timedelta(2)
    TrimTwStr           = EndTw.strftime('%d%b%Y 2400') 
    EndTwStr            = EndTribTw.strftime('%d%b%Y 2400') # End of time window for the database formatted as ddmmmyyyy 2400
    ProjectDateTimeStr  = EndTw.strftime('%m-%d-%Y 24:00') # Project date and time for bulletin formatted as mm-dd-yyyy 2400
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, 
        '\tProject Date and Time = ', ProjectDateTimeStr)
    
    #
    # Open database connection
    #
    
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('UTC')
    CwmsDb.setTimeWindow(TrimTwStr, EndTwStr)
    CwmsDb.setOfficeId('NWDM')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()# Create a java.sql.Connection
     
    # 
    # Retrieve public names for all projects shown in bulletin. Remove 'Reservoir' from public name for spacing purposes
    #
    locations = LocationDict.keys()
    for location in locations :
        PublicName = retrievePublicName(debug, conn, location)
        BulletinName = PublicName
        LocationDict[location].setdefault('PublicName', PublicName)
        LocationDict[location].setdefault('BulletinName', BulletinName)
    
    locations2 = LocationDict2.keys()
    for location2 in locations2 :
        PublicName = retrievePublicName(debug, conn, location2)
        BulletinName = PublicName
        LocationDict2[location2].setdefault('PublicName', PublicName)
        LocationDict2[location2].setdefault('BulletinName', BulletinName)

    #
    # Create Pdf file and write tables to create bulletin
    #
    BulletinPdf = Document()
    Writer = PdfWriter.getInstance(BulletinPdf, FileOutputStream(BulletinFilename))

    #
    # Create tables with a finite number of columns that will be written to the pdf file
    #
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)
    
    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)

    # Table2: Contains all data and data headings
    Table2 = PdfPTable(Table1Columns)

    # Table1Footnote: Contains the footnotes for Table1
    Table1Footnote = PdfPTable(Table1Columns)

    # BulletinFooter: Footer for the bulletin
    BulletinFooter = PdfPTable(FooterColumns)
    BulletinFooter2 = PdfPTable(FooterColumns)
    
    #
    # Specify column widths
    #
    # Title Block Columns
    TitleBlockColumnWidths = [10] * Table1Columns
    TitleBlockColumnWidths[0] = 25
    TitleBlockColumnWidths[-1] = 17
    TitleBlock.setWidths(TitleBlockColumnWidths)

    # Table Columns and Order of Variables for Table1
    DataOrder, ColumnWidths = ['PublicName', 'TopOfConsZoneElev', 'Elevation', 'FlowIn', 'FlowTotal'], []
    for column in range(Table1Columns) :
        # Column Key
        ColumnKey = 'Column%d' % column
        if column < 2 :
            ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey]['ColumnWidth'])
        else :
            ColumnWidths.append(TableLayoutDict['Table1']['Column2'][1]['ColumnWidth'])
    Table1.setWidths(ColumnWidths)
    Table2.setWidths(ColumnWidths)
    
    #
    # Add data to Title Block that will be at the top of the bulletin
    #
    CsvData = ''
    TitleBlock, CsvData = titleBlock(debug, TitleBlock, CsvData)

    #
    # Add data to the heading for Table1
    #
    Table1 = table1Heading(debug, Table1, calendarNow, tsFormat)

    #
    # Add data to the data blocks for Table1
    #
    DataBlocks = ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6']
    for DataBlock in DataBlocks :
        startTime = TrimTwStr
        endTime = EndTwStr
        Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, date_list, LocationDict)

    #
    # Create bulletin header that is repeated on each page
    #
    Table1.setHeaderRows(3)
    
    #
    # Write tables to create bulletin
    #
    BulletinPdf.setPageSize(PageSize.LETTER) # Set the page size
    PageWidth = BulletinPdf.getPageSize().getWidth()
    BulletinPdf.setMargins(LeftMargin, RightMargin, TopMargin, BottomMargin) # Left, Right, Top, Bottom
    BulletinPdf.setMarginMirroring(True) 
    BulletinPdf.open()
    BulletinFooter = bulletinFooter(debug, BulletinFooter)
    BulletinFooter.setTotalWidth(PageWidth - 48)
    BulletinFooter.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent()) #Add the footer
    BulletinPdf.add(TitleBlock) # Add TitleBlock to the PDF
    BulletinPdf.add(Table1) # Add Table1 to the PDF
    BulletinFooter2 = bulletinFooter(debug, BulletinFooter2)
    BulletinFooter2.setTotalWidth(PageWidth - 48)
    BulletinFooter2.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent()) #Add the footer
finally :
    try : CwmsDb.done()
    except : pass
    try : conn.done()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass


