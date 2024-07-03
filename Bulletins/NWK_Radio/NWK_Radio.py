'''
Author: 
Last Updated: 02-25-2019
Description: Create the NWK Radio Bulletin
'''
# -------------------------------------------------------------------
# Required imports
# -------------------------------------------------------------------
from com.itextpdf.text      import Document, DocumentException, Rectangle, Paragraph, Phrase, Chunk, Font, FontFactory, BaseColor, PageSize, Element, Image
from com.itextpdf.text.Font import FontFamily
from com.itextpdf.text.pdf  import PdfWriter, PdfPCell, PdfPTable, PdfPage, PdfName, PdfPageEventHelper, BaseFont
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
import java.lang
import os, sys, inspect, datetime, time, DBAPI

# -------------------------------------------------------------------
# Import database pathnames and plotting functions
# -------------------------------------------------------------------
# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\" # Used in the properties file to create pathname for Seals and Symbols
    BulletinsDirectory = CronjobsDirectory + "Bulletins\\"
    ScriptDirectory = BulletinsDirectory + "NWK_Radio\\"
    BulletinFilename = BulletinsDirectory + "NWK_Radio.pdf"
    BulletinPropertiesPathname = ScriptDirectory + "NWK_Radio_Properties.txt"
else :
    # Server pathnames
    ScriptDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = ScriptDirectory.split('/')
    BulletinsDirectory = '/'.join(PathList[: -1]) + '/'
    CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
    ScriptDirectory += '/'
    BulletinFilename = BulletinsDirectory + 'NWK_Radio.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'NWK_Radio_Properties.txt'    

print 'BulletinsDirectory = ', BulletinsDirectory, '\tScript Directory = ', ScriptDirectory
print 'BulletinFilename = ', BulletinFilename, '\tBulletinPropertiesPathname = ', BulletinPropertiesPathname

if CronjobsDirectory not in sys.path : sys.path.append(CronjobsDirectory)
if BulletinsDirectory not in sys.path : sys.path.append(BulletinsDirectory)
if ScriptDirectory not in sys.path : sys.path.append(ScriptDirectory)

#
# Load DatabasePathnames.txt and BulletinProperties
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
BulletinProperties = open(BulletinPropertiesPathname, "r"); exec(BulletinProperties)

# Import server utilities
import Server_Utils
reload(Server_Utils)
from Server_Utils import lineNo, outputDebug, retrieveLocationLevel, retrievePublicName

#
# Input
#
# Set debug = True to print all debug statements and = False to turn them off
debug = False

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
    Cell = createCell(debug, Phrase(Chunk('Page %d of 1' % Writer.getPageNumber(), TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
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
	#print "Got ElevDatum: " + str(ElevationDatum)  
    return ElevationDatum
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
       #print "sql: " + sql		
       rset = stmt.executeQuery(sql)
       if rset.next() :
          #Found timeseries
          flag = 'true'
       else :
          flag = 'false'
          #print "\nTimeseries not found in the database: " + timeseries
    finally :
       stmt.close()
       rset.close()
    return flag
################################################################################################
#
# table1Data Function   : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table1Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName,    # String name for data section of table
        		aDate,
        		utcTime,
        		startUtcTime,
        		endUtcTime
                ) :
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)
    # Data Block Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font5)), TableLayoutDict[TableName]['RowSpan'],
            Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [1, 2, 1, 3], TableLayoutDict[TableName]['BorderColors'],
            [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
    #Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)

    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        PublicName = retrievePublicName(debug, conn, project)
        if PublicName.find(" & Reservoir") != -1: 
            BulletinName = PublicName.replace(' & Reservoir', '')
        elif PublicName.find("Missouri R at") != -1:
            BulletinName = PublicName.replace('Missouri R at ', '')
        elif PublicName.find("Missouri River at") != -1:
            BulletinName = PublicName.replace('Missouri River at ', '')
        elif PublicName.find("Gasconade R nr") != -1:
            BulletinName = PublicName.replace('Gasconade R nr ', '')
        elif PublicName.find("Osage River bl") != -1:
            BulletinName = PublicName.replace('Osage River bl ', '')
        elif PublicName.find("Grand River near") != -1:
            BulletinName = PublicName.replace('Grand River near ', '')
        elif PublicName.find("Nebr City") != -1:
            BulletinName = PublicName.replace('"Nebr City', 'Nebraska City')
        else :
            BulletinName = PublicName
        outputDebug(debug, lineNo(), 'Creating %s row' % BulletinName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == DataBlocks[-1] and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False
        
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
            #CellPadding = TableLayoutDict[TableName]['CellPadding']
            CellPadding = [0, 2, 1, 3] #[Top, Right, Bottom, Left]
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
            # 0 - Project Bulletin Name
            if data == 'PublicName' :
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                
                # Store value to DataDict
                #DataBlockDict['DataBlocks'][TableDataName][project][data] = PublicName
                
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                CellPadding = [1, 2, 1, 7] #[Top, Right, Bottom, Left]               
                if LastProject : BorderWidths = [0.25, 0.25, 1, 1] #[Top, Right, Bottom, Left]
                else : BorderWidths = [0.25, 0.25, 0.25, 1] #[Top, Right, Bottom, Left]
            # 1 - River Mile
            elif data == 'RiverMile' :
                try :
                    if project not in ['JRMM', 'RIFM', 'STTM', 'STL'] : 
                        RivMile = LocationDict[project]['RiverMile']
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RivMile, TextFont))
                    else :
                        CellData = Phrase(Chunk(Null, TextFont))

                except Exception, e :
                    print "River Mile Exception = " + str(e) 
                    RivMile = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

            # 2 - elevation datum
            elif data == 'ElevDatum' :
                try :
                    #Get the Elvation Datum
                    ElevationDatum = retrieveElevatonDatum(debug, conn, project)
                        
                    # Create a formatted string that will be added to the table
                    if ElevationDatum == Null or ElevationDatum == 'None' :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % float(ElevationDatum), TextFont))

                except Exception, e :
                    print "Elevation Datum Exception = " + str(e)	
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

            # 3 - Flood Stage
            elif data == 'FloodStage' :
                try :
                    CellData = Phrase(Chunk(Null, TextFont))
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    NwsFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)
                            
                    if NwsFloodStage != Null or NwsFloodStage != 'None' :
                        # Create a formatted string that will be added to the table
                       CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % NwsFloodStage, TextFont))
                    else:
                       CellData = Phrase(Chunk(Missing, TextFont))
                except Exception, e :
                    print "FloodStage Exception = " + str(e)

            # 4 - Date 
            elif data == 'Date' :
                try :
                    CellData = Phrase(Chunk(Null, TextFont))
                    # Create a formatted date that will be added to the table
                    aDate = SimpleDateFormat("MM/dd/yyyy").format(Date)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % aDate, TextFont))
                except Exception, e :
                    print "Date Exception = " + str(e)
                    CellData = Phrase(Chunk(Null, TextFont))

            # 5 - Time
            elif data == 'Time' :
                try :
                    CellData = Phrase(Chunk(Null, TextFont))
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % utcTime, TextFont))
                except Exception, e :
                    print "Time Exception = " + str(e)

            # 6 - Stage
            elif data == 'Stage' :
                if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project	
                    if checkTs(TscPathname, conn) == 'true' :
                        try :
                            Tsc = CwmsDb.get(TscPathname, endUtcTime, startUtcTime) 
                            currentStage = Tsc.values[-1] #Current stage 
                            previousDayStage = Tsc.values[0]  #previous days stage
                            previous6HrStage = Tsc.values[18]  #previous 6 hour stage
                            prevDayStageChg = currentStage - previousDayStage #previous days stage change
                            prevStage6HrChg = currentStage - previous6HrStage #previous 6 hour stage change
                            
                            # If previous day's value is missing raise an exception and using the missing value
                            if currentStage == Constants.UNDEFINED : raise ValueError 
                            elif previousDayStage < 0  : prevDayStageChg = Missing 
                            elif previous6HrStage < 0 : prevStage6HrChg = Missing
                            
                            DataBlockDict['DataBlocks'][TableDataName][project][data + 'Change6'] = prevStage6HrChg
                            DataBlockDict['DataBlocks'][TableDataName][project][data + 'Change24'] = prevDayStageChg
                        
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % currentStage, TextFont))

                        except Exception, e :
                            print "Elevation Exception = " + str(e)
                            currentStage, prevDayStageChg, prevStage6HrChg = Missing, Missing, Missing
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(Missing, TextFont))

                    else :
                        #None, set value to Null
                        CellData = Phrase(Chunk(Missing, TextFont))
                else :
                    #None, set value to Null
                    CellData = Phrase(Chunk(Null, TextFont))

            # 7 Stage elevation change 6 hourS
            elif data == 'StageChange6' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['StageChange6'] == Missing : 
                        raise ValueError
				
                    Hr6ElevChange  = DataBlockDict['DataBlocks'][TableDataName][project]['StageChange6']
                    if Hr6ElevChange == 0.0 :
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % "", TextFont))
                    else :
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Hr6ElevChange, TextFont))
                except Exception, e :
                    print "ElevChange 6hr Exception = " + str(e)	
                    DlyElevChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

            elif data == 'StageChange24' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['StageChange24'] == Missing :
                        raise ValueError

                    DlyElevChange = DataBlockDict['DataBlocks'][TableDataName][project]['StageChange24']
                    if DlyElevChange == 0.0 :
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % "", TextFont))
                    else :
                         CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, TextFont))

                except Exception, e :
                    print "ElevChange 24hr Exception = " + str(e)
                    DlyElevChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))	

            if data == 'StageChange24' and not LastProject :
                BorderWidths = [0.25, 1, 0.25, 0.25] #[Top, Right, Bottom, Left]
            elif data == 'StageChange24' and LastProject :
                BorderWidths = [0.25, 1, 1, 0.25] #[Top, Right, Bottom, Left]
            if LastProject and data != 'StageChange24' and data != 'PublicName' : BorderWidths = [0.25, 0.25, 1, 0.25] #[Top, Right, Bottom, Left]

            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)

    return Table	
#
# table1Heading Function    : Creates the heading for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def table1Heading(  debug,  # Set to True to print all debug statements
                    Table  # PdfPTable object
                    ) :
    #
    # Create Table1 Heading 
    #
    Row1Height = 35 # Row 1 has a fixed height equal to Row1Height
    # Column 0 Heading
    #createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    #0
    CellData = Phrase(Chunk('STATION', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug,CellData, 3, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [1, 0.25, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #1
    CellData = Phrase(Chunk('RIVER\nMILE', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #2
    CellData = Phrase(Chunk('DATUM \n\n (FT NGVD 29)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #3
    CellData = Phrase(Chunk('FLOOD\nSTAGE\n(FT)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #4
    CellData = Phrase(Chunk('DATE\n\n(MMDDYYYY)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #5
    CellData = Phrase(Chunk('TIME\n\n(GMT)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #6
    CellData = Phrase(Chunk('STAGE\n\n(FT)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #7
    CellData = Phrase(Chunk('6HR\nCHG\n(FT)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    #8
    CellData = Phrase(Chunk('24HR\nCHG\n(FT)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 1, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(Row1Height)
    Table.addCell(Cell)
    return Table

#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def titleBlock( debug,      # Set to True to print all debug statements
                TitleBlock, # PdfPTable object
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
    
    # Add TitleLine3 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)

    # Add TitleLine4 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TitleBlock.addCell(Cell)

    return TitleBlock

#
# table1Footnote Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def table1Footnote( debug,          # Set to True to print all debug statements
                    TableFootnote,  # PdfPTable object
                    ) :
    # Add a blank line to the table footer to separate the footer from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('   Daylight Savings Time = GMT- 5 Hours,', Font8)), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Central Standard Time = GMT - 6 Hours', Font8)), TableLayoutDict['Table1']['RowSpan'], 
        7, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)
        
    return TableFootnote

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

	
    calendarUTC = Calendar.getInstance()
    calendarUTC.setTimeZone(TimeZone.getTimeZone('UTC'))
    calendarUTC.add(Calendar.HOUR_OF_DAY, -1)
    tsFormat = SimpleDateFormat("HH:00")
    tsFormat.setTimeZone(TimeZone.getTimeZone('UTC'))
    utcHrTimestamp = tsFormat.format(calendarUTC.getTime())

    tsFormat = SimpleDateFormat("ddMMMyyyy HH00")
    tsFormat.setTimeZone(TimeZone.getTimeZone('UTC'))
    utcTimeStart = tsFormat.format(calendarUTC.getTime())

    calendarUTC.add(Calendar.DAY_OF_MONTH, -1)
    utcTimeEnd = tsFormat.format(calendarUTC.getTime())

    StartTw             = Date - datetime.timedelta(2)
    StartTwStr          = StartTw.strftime('%d%b%Y 2400') # Start of time window for the database formatted as ddmmmyyyy 2400
    EndTw               = Date - datetime.timedelta(1)
    EndTwStr            = EndTw.strftime('%d%b%Y 2400') # End of time window for the database formatted as ddmmmyyyy 2400
    ProjectDateTimeStr  = Date.strftime('%m-%d-%Y') + ' %s' % utcHrTimestamp # Project date and time for bulletin formatted as mm-dd-yyyy 2400
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, 
        '\tProject Date and Time = ', ProjectDateTimeStr)
    
    #
    # Open database connection
    #
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('UTC')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('NWDM')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()# Create a java.sql.Connection

    # 
    # Retrieve public names for all projects shown in bulletin. Remove 'Reservoir' from public name for spacing purposes
    #
    locations = LocationDict.keys()
    for location in locations :
        PublicName = retrievePublicName(debug, conn, location)
	if PublicName.find(" & Reservoir") != -1: 
            BulletinName = PublicName.replace(' & Reservoir', '')
	elif PublicName.find("Missouri R at") != -1:
	    BulletinName = PublicName.replace('Missouri R at ', '')
	elif PublicName.find("Missouri River at") != -1:
	    BulletinName = PublicName.replace('Missouri River at ', '')
	elif PublicName.find("Gasconade R nr") != -1:
           BulletinName = PublicName.replace('Gasconade R nr ', '')
	elif PublicName.find("Osage River bl") != -1:
           BulletinName = PublicName.replace('Osage River bl ', '')
	elif PublicName.find("Grand River near") != -1:
           BulletinName = PublicName.replace('Grand River near ', '')
	elif PublicName.find("Nebr City") != -1:
           BulletinName = PublicName.replace('"Nebr City', 'Nebraska City')
	else :
	    BulletinName = PublicName
        LocationDict[location].setdefault('PublicName', PublicName)
        LocationDict[location].setdefault('BulletinName', BulletinName)
       
    #
    # Create tables with a finite number of columns that will be written to the pdf file
    #
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)
    
    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)

    # Table1Footnote: Contains the footnotes for Table1
    Table1Footnote = PdfPTable(Table1Columns)

    # BulletinFooter: Footer for the bulletin
    BulletinFooter = PdfPTable(FooterColumns)
    
    #
    # Specify column widths
    #
    # Title Block Columns
    TitleBlockColumnWidths = [10] * Table1Columns
    TitleBlockColumnWidths[0] = 25
    TitleBlockColumnWidths[-1] = 17
    TitleBlock.setWidths(TitleBlockColumnWidths)
    
    # Table Columns and Order of Variables for Table1
    DataOrder, ColumnWidths = [], []
    for column in range(Table1Columns) :
        # Column Key
        ColumnKey = 'Column%d' % column

        DataOrder.append(TableLayoutDict['Table1'][ColumnKey]['Key'])
        ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey]['ColumnWidth'])
    Table1.setWidths(ColumnWidths)
    
    #
    # Add data to Title Block that will be at the top of the bulletin
    #
    TitleBlock = titleBlock(debug, TitleBlock)

    #
    # Add data to the heading for Table1
    #
    Table1 = table1Heading(debug, Table1)

    #
    # Add data to the data blocks for Table1
    #
    DataBlocks = ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6']

    for DataBlock in DataBlocks :
	Table1 = table1Data(debug, Table1, 'Table1', DataBlock, Date, utcHrTimestamp, utcTimeStart, utcTimeEnd) 

    #
    # Add data to the table footnotes for Table1
    #
    Table1Footnote = table1Footnote(debug, Table1Footnote)

    #
    # Create Pdf file and write tables to create bulletin
    #
    BulletinPdf = Document()
    Writer = PdfWriter.getInstance(BulletinPdf, FileOutputStream(BulletinFilename))
    BulletinPdf.setPageSize(PageSize.LETTER) # Set the page size
    BulletinPdf.setMargins(LeftMargin, RightMargin, TopMargin, BottomMargin) # Left, Right, Top, Bottom
    BulletinPdf.setMarginMirroring(True) 
    BulletinPdf.open()
    BulletinPdf.add(TitleBlock) # Add TitleBlock to the PDF
    BulletinPdf.add(Table1) # Add Table1 to the PDF
    BulletinPdf.add(Table1Footnote) # Add Table1's footnotes
    BulletinFooter.setTotalWidth(612 - 48) # Total width is 612 pixels (8.5 inches) minus the left and right margins (24 pixels each)
    # Build a footer with page numbers and add to PDF
    BulletinFooter = bulletinFooter(debug, BulletinFooter)
    BulletinFooter.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent())

finally :
    try : CwmsDb.done()
    except : pass
    try : conn.done()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass


