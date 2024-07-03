'''
Author: Ryan Larsen
Last Updated: 12-20-2017
Description: Create the Missouri River Basin Reservoir Bulletin
'''
#
# Pathnames
#
iTextPdfPathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWD\\MRBWM_Reservoir\\itextpdf.jar"
BulletinFilename = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWD\\MRBWM_Reservoir\\MRBWM_Reservoir_iText.pdf"
BulletinTsFilePathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWD\\MRBWM_Reservoir\\Bulletins_Time_Series.txt"
BulletinPropertiesPathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWD\\MRBWM_Reservoir\\Mrbwm_Reservoir_Bulletin_Properties.txt"

#
# Imports
#
# Get directory of the iText-5.0.6.jar.  itextpdf.jar should be stored in ...\\CAVI\\sys\\jar
if iTextPdfPathname not in sys.path : sys.path.append(iTextPdfPathname)

from com.itextpdf.text      import Document, DocumentException, Rectangle, Paragraph, Phrase, Chunk, Font, FontFactory, BaseColor, FontFactory, PageSize, Element, Image
from com.itextpdf.text.Font import FontFamily
from com.itextpdf.text.pdf  import PdfWriter, PdfPCell, PdfPTable, PdfPage, PdfName, PdfPageEventHelper, BaseFont
from hec.data.cwmsRating    import RatingSet
from hec.heclib.util        import HecTime
from hec.io                 import TimeSeriesContainer
from hec.script             import Constants
#from hec.script             import *
#from hec.hecmath            import *
#from hec.heclib.util        import *
#from hec.io                 import *
#from hec.heclib.dss         import *
from java.awt.image         import BufferedImage
from java.io                import FileOutputStream, IOException
from java.lang              import System
from subprocess             import Popen
import os, sys, inspect, datetime, time, DBAPI

#
# Input
#
# Set debug = True to print all debug statements and = False to turn them off
debug = True

# Import time series and properties files
BulletinTsFile = open(BulletinTsFilePathname, "r"); exec(BulletinTsFile.read())
BulletinProperties = open(BulletinPropertiesPathname, "r"); exec(BulletinProperties.read())

##################################################################################################################################
##################################################################################################################################

#
# Functions
#

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

#
# retrieveReservoirZone Function    : Retrieves reservoir zone data
# Author/Editor                     : Mike Perryman
# Last updated                      : 05-01-2017
#
def retrieveReservoirZone(  debug,          # Set to True to print all debug statements
                            TscFullName,    # Full name of time series container
                            ) :
    CurDate            = datetime.datetime.now() # Current date
    StartTimeStr    = CurDate.strftime('%d%b%Y ') + '0000' # Start date formatted as ddmmmyyy 0000
    EndTimeStr        = CurDate.strftime('%d%b%Y ') + '0000' # End date formatted as ddmmmyyy 0000

    level_1a = TimeSeriesContainer()
    level_1a_parts = TscFullName.split('.')
    level_1aId_parts = level_1a_parts[:]
    level_1aId = '.'.join(level_1aId_parts)
    outputDebug(debug, lineNo(), 'level_1a_parts = ', level_1a_parts, '\tlevel_1aId_parts = ', level_1aId_parts, 
        '\n\t\tlevel_1aId = ', level_1aId)
    
    level_1a.fullName  = TscFullName
    level_1a.location  = level_1a_parts[0]
    level_1a.parameter = level_1a_parts[1]
    level_1a.interval  = 0
    level_1a.version   = level_1a_parts[-1]
    if level_1a_parts[1] == 'Stor' : level_1a.units = 'ac-ft'
    elif level_1a_parts[1] == 'Elev' : level_1a.units = 'ft'
    level_1a.type      = 'INST-VAL'
    
    conn = CwmsDb.getConnection()
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
        return rs.getDouble(2)

#
# table1Data Function   : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table1Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName    # String name for data section of table
                ) :
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)
    
    # Data Block Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font5)), TableLayoutDict[TableName]['RowSpan'], 
        Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [2, 2, 3, 3], TableLayoutDict[TableName]['BorderColors'], 
        [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
    Table.addCell(Cell)
        
    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        PublicName = LocationDict[project]['BulletinName']
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)
        
        for data in DataOrder :
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)

            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
            RowSpan = TableLayoutDict[TableName]['RowSpan']; ColSpan = TableLayoutDict[TableName]['ColSpan']
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding']
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
            # Project Bulletin Name
            if data == 'PublicName' :
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderWidths = [0.25, 0.25, 0.25, 1]
                CellPadding = [2, 2, 2, 3]
                
                if project == 'BUBI' : PublicName = PublicName + '*' # Buffalo Bill is not a Section 7 project
                CellData = Phrase(Chunk(PublicName, TextFont))
            # MP elevation
            elif data == 'TopOfConsZoneElev' :
                try :
                    if project in ['SYS', 'BUBI'] : # BUBI does not have a rating curve in the database
                        CellData = Phrase(Chunk(Null, TextFont))
                        MpStorZone = Null
                    else :
                        ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                        if project == 'BUBI' : ElevZoneFullName = TopOfConsZone % project # Buffalo Bill does not have a joint use pool
                        
                        # Retrieve reservoir elevation zone value
                        MpElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                        outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % DataBlockDict['DataBlocks'][TableDataName][data], MpElevZone)
                        
                        # Rate the elevation value
                        conn = CwmsDb.getConnection() # Create a java.sql.Connection
                        System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                            #   CCP currently uses (11-17-2017) and seems to work the fastest
                        ElevStorPdc = RatingSet.fromDatabase(conn, DataBlockDict['DataBlocks'][TableDataName]['RatingCurve'] % LocationDict[project]['DbLocation'])
                        PdcTime = int(time.time() * 1000) # Time used for retrieving the Pdc storage curves
                        ElevStorPdc.setDefaultValueTime(PdcTime)
                        MpStorZone = ElevStorPdc.rate(MpElevZone)
                        
                        # Calculate System MP Storage Zone
                        if 'SysMpStorZone' not in locals() : SysMpStorZone = MpStorZone
                        else : SysMpStorZone += MpStorZone
                        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpElevZone, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
                    MpStorZone = Missing
            # FC elevation
            elif data == 'TopOfExclZoneElev' :
                try :
                    if project in ['SYS', 'BUBI'] : # BUBI does not have a rating curve in the database
                        CellData = Phrase(Chunk(Null, TextFont))
                        FcStorZone = Null
                    else :
                        ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                        
                        # Retrieve reservoir elevation zone value
                        FcElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                        
                        # Rate the elevation value
                        conn = CwmsDb.getConnection() # Create a java.sql.Connection
                        System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                            #   CCP currently uses (11-17-2017) and seems to work the fastest
                        ElevStorPdc = RatingSet.fromDatabase(conn, DataBlockDict['DataBlocks'][TableDataName]['RatingCurve'] % LocationDict[project]['DbLocation'])
                        PdcTime = int(time.time() * 1000) # Time used for retrieving the Pdc storage curves
                        ElevStorPdc.setDefaultValueTime(PdcTime)
                        FcStorZone = ElevStorPdc.rate(FcElevZone)
                        
                        # Calculate System FC Storage Zone
                        if 'SysFcStorZone' not in locals() : SysFcStorZone = FcStorZone
                        else : SysFcStorZone += FcStorZone
                        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcElevZone, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
                    FcStorZone = Null
            # Rated MP and FC storages
            elif data == 'TopOfConsZoneStor' or data == 'TopOfExclZoneStor' :
                try :
                    if project in ['SYS'] and data == 'TopOfConsZoneStor' : 
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % SysMpStorZone, TextFont))
                    elif project in ['SYS'] and data == 'TopOfExclZoneStor' : 
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % SysFcStorZone, TextFont))
                    elif data == 'TopOfConsZoneStor' and MpStorZone != Null or MpStorZone != Missing : 
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpStorZone, TextFont))
                    elif data == 'TopOfExclZoneStor' and MpStorZone != Null or MpStorZone != Missing : 
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStorZone, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
            # Elevation
            elif data == 'Elevation' :
                try :
                    if project in ['SYS'] :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        Tsc = CwmsDb.get(DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation'])
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Tsc.values[-1], TextFont))
                                        
                        # Set DylElevChange to Missing if there are missing hourly data
                        if Constants.UNDEFINED in [Tsc.values[-1], Tsc.values[0]] : DlyElevChange = Missing
                        else : DlyElevChange = Tsc.values[-1] - Tsc.values[0]
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
            # Daily elevation change
            elif data == 'ElevChange' :
                try :
                    if project in ['SYS'] :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        if DlyElevChange != Missing :
                            # Format the value
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, TextFont))
                        else :
                            CellData = Phrase(Chunk(DlyElevChange, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
            # Storage, Inflow, and Release
            elif data == 'Storage' or data == 'FlowIn' or data == 'FlowTotal' :
                try :
                    if project in ['SYS'] and data != 'Storage' :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        if project != 'SYS' :
                            Tsc = CwmsDb.get(DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation'])
                            if data == 'Storage' :
                                if 'SysStor' not in locals() : SysStor = Tsc.values[-1]
                                else : SysStor += Tsc.values[-1]
                                outputDebug(debug, lineNo(), '%s Storage = ' % project, Tsc.values[-1], 
                                    '\tSystem Storage = ', SysStor)
                        
                        if project in ['SYS'] and data == 'Storage' :
                            # Format the value
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % SysStor, TextFont))
                        else :
                            # Format the value
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Tsc.values[-1], TextFont))
                        
                        # Save storage value so percentages can be calculated
                        if data == 'Storage' : ProjStorage = Tsc.values[-1]
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
            # MP Percentage
            elif data == 'MpStorPercentOccupied' :
                try :
                    if project in ['SYS'] :
                        MpStorPercent = (SysStor / SysMpStorZone) * 100.
                    else :
                        MpStorPercent = (ProjStorage / MpStorZone) * 100.
    
                    if MpStorPercent > 100. : MpStorPercent = 100.
                    
                    # Format the value
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpStorPercent, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
            # FC Storage
            elif data == 'FcStorOccupied' :
                try :
                    if project in ['SYS'] :
                        FcStor = SysStor - SysMpStorZone
                        outputDebug(debug, lineNo(), '%s Storage = ' % project, SysStor, 
                            '\tSystem Fc Storage = ', FcStor)
                    else :
                        FcStor = ProjStorage - MpStorZone

                    if FcStor < 0. : FcStor = 0.

                    # Format the value
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStor, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
            # FC Percentage
            elif data == 'FcStorPercentOccupied' :
                try :
                    if project in ['SYS'] :
                        FcStorPercent = (FcStor / (SysFcStorZone - SysMpStorZone)) * 100.
                    else :
                        FcStorPercent = (FcStor / (FcStorZone - MpStorZone)) * 100.
    
                    if FcStorPercent > 100. : FcStorPercent = 100.
    
                    # Format the value
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStorPercent, TextFont))
                    
                    # Change default cell properties
                    BorderWidths = [0.25, 1, 0.25, 0.25]
                    if FcStorPercent > DataBlockDict['DataBlocks'][TableDataName]['RedStor'] : BackgroundColor = Color10 # Red
                    elif DataBlockDict['DataBlocks'][TableDataName]['YellowStor'] < FcStorPercent <= DataBlockDict['DataBlocks'][TableDataName]['RedStor'] : BackgroundColor = Color9 # Yellow
                    else : BackgroundColor = Color8 # Green
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
                

            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
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
    # Column 0 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Project', Font3)), TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 0.25, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)

    # Column 1-4 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Project Information', Font3)), TableLayoutDict['Table1']['RowSpan'], 4, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)

    # Column 5-9 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Current Data', Font3)), TableLayoutDict['Table1']['RowSpan'], 5, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)

    # Column 10-12 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Occupied Storage', Font3)), TableLayoutDict['Table1']['RowSpan'], 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 1, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)
    
    # Blank Column 0 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [0.25, 0.25, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 1-2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Elevations (ft)', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 2, 
        Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], 
        TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)

    # Column 3-4 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Cumulative Stor (ac-ft)', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 2, 
        Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 5 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Elev\n(ft)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 6 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Dly Elev Chnge (ft)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, [1, 0, 1, 0], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 7 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Storage\n(ac-ft)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 8 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Inflow\n(cfs)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 9 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Release\n(cfs)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 10 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('MP\n(%)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 11 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('FC\n(ac-ft)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 12 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('FC\n(%)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [0.25, 1, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 1 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('MP', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('FC', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 3 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('MP', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 4 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('FC', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], 
        TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)

    return Table

#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def titleBlock( debug,      # Set to True to print all debug statements
                TitleBlock  # PdfPTable object
                ) :
    #
    # Add USACE Logo, title block lines, and seal to TitleBlock
    #
    TitleLines = [TitleLine1, TitleLine2, TitleLine3]

    # Add the USACE Logo to the TitleBlock
    Img = Image.getInstance(UsaceLogo)
    Img.scalePercent(15)
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Img, len(TitleLines), TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_LEFT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine1, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [14, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    
    # Add the seal to the TitleBlock
    Img = Image.getInstance(Seal)
    Img.scalePercent(1.6)
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Img, len(TitleLines), TableLayoutDict['Table1']['ColSpan'], TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color1], 
        [0.25, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.LEFT)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine2 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine2, Font2)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine3 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
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

##################################################################################################################################
##################################################################################################################################

#
# Classes
#

##################################################################################################################################
##################################################################################################################################

#
# Main Script
#
try :
    #
    # Date and Time Window Info
    #
    CurDate = datetime.datetime.now() # Current date
    StartTw = CurDate - datetime.timedelta(2)
    StartTwStr = StartTw.strftime('%d%b%Y 2400') # Start of time window for the database formatted as ddmmmyyyy 2400
    EndTw = CurDate - datetime.timedelta(1)
    EndTwStr = EndTw.strftime('%d%b%Y 2400') # End of time window for the database formatted as ddmmmyyyy 2400
    ProjectDateTimeStr = EndTw.strftime('%m-%d-%Y 24:00') # Project date and time for bulletin formatted as mm-dd-yyyy 2400
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, 
        '\tProject Date and Time = ', ProjectDateTimeStr)
    
    #
    # Open database connection
    #
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('US/Central')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('NWDM')
    CwmsDb.setTrimMissing(False)
    #PathnameList = CwmsDb.getPathnameList()

    #
    # Create tables with a finite number of columns that will be written to the pdf file
    #
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)
    
    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)

    #
    # Specify column widths
    #
    # Title Block Columns
    TitleBlockColumnWidths = [10] * Table1Columns
    TitleBlockColumnWidths[0] = 25
    TitleBlockColumnWidths[-1] = 17
    TitleBlock.setWidths(TitleBlockColumnWidths)
    
    # Table Columns and Order of Variables
    DataOrder, ColumnWidths = [], []
    for column in range(Table1Columns) :
        # Column Key
        ColumnKey = 'Column%d' % column
        
        DataOrder.append(TableLayoutDict['Table1'][ColumnKey]['Key'])
        ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey]['ColumnWidth'])
    Table1.setWidths(ColumnWidths)
        
    #
    # Create Title Block that will be at the top of the bulletin
    #
    TitleBlock = titleBlock(debug, TitleBlock)

    #
    # Create the heading for Table1
    #
    Table1 = table1Heading(debug, Table1)
    Table1 = table1Data(debug, Table1, 'Table1', 'Data1')
    Table1 = table1Data(debug, Table1, 'Table1', 'Data2')

    #
    # Create Pdf file and write tables to create bulletin
    #
    BulletinPdf = Document()
    BulletinPdf.setPageSize(PageSize.LETTER) # Set the page size
    BulletinPdf.setMargins(-48, -48, 24, 24) # Left, Right, Top, Bottom
    BulletinPdf.setMarginMirroring(True) 
    PdfWriter.getInstance(BulletinPdf, FileOutputStream(BulletinFilename))
    BulletinPdf.open()
    BulletinPdf.add(TitleBlock)
    BulletinPdf.add(Table1)
    
    outputDebug(debug, lineNo(), 'BulletinFilename = ', BulletinFilename)
    MessageBox.showInformation('Bulletin Complete', 'Script Status')

finally :
    try : CwmsDb.done()
    except : pass
    try : BulletinPdf.close()
    except : pass

