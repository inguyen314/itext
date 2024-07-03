'''
Author: Ryan Larsen
Last Updated: 11-29-2017
Description: Create the Missouri River Basin Reservoir Bulletin
'''
#
# Pathnames
#
iTextPdfPathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWD\\MRBWM_Reservoir\\itextpdf.jar"
BulletinFilename = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWD\\MRBWM_Reservoir\\MRBWM_Reservoir_iText2.pdf"
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
                CellText,               # Text that will appear within the cell
                CellFont,               # Font of text
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
    Cell = PdfPCell(Phrase(Chunk(CellText, CellFont)))
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
    del level_1aId_parts[3]
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
# table1Data1 Function  : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table1Data1(    debug,  # Set to True to print all debug statements
                    Table1  # PdfPTable object
                    ) :
    #
    # Create Data1 Block
    #
    # Data1 Block Heading
    Cell = PdfPCell(Phrase(Chunk(DataBlockDict['DataBlocks']['Table1Data1']['Heading'], Font5)))
    Cell.setRowspan(1); Cell.setColspan(Table1Columns)
    Cell.setBackgroundColor(Color7)
    Cell.setHorizontalAlignment(Element.ALIGN_LEFT)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(2); Cell.setBorderWidthRight(2)
    Cell.setBorderColor(Color2)
    Cell.setPaddingBottom(3); Cell.setPaddingLeft(3)
    Table1.addCell(Cell)
    
    # Data
    for project in DataBlockDict['DataBlocks']['Table1Data1']['ProjectList'] :
        for column in range(Table1Columns) :
            # Column Key
            ColumnKey = 'Column%d' % column
            
            # Default cell properties. If there is a special case, the properties will be changed.
            Font = Font4
            HorizontalAlignment = Element.ALIGN_RIGHT
            RowSpan = 1; ColSpan = 1
            VariableBorders = True
            BorderColorTop = Color2; BorderColorBottom = Color2; BorderColorLeft = Color2; BorderColorRight = Color2
            BorderWidthTop = 0.25; BorderWidthBottom = 0.25; BorderWidthLeft = 0.25; BorderWidthRight = 0.25
            BackgroundColor = Color4
            PaddingTop = 1; PaddingBottom = 2; PaddingLeft = 1; PaddingRight = 1
            
            # Project bulletin name
            if ColumnKey == 'Column0' :
                Value = LocationDict[project]['BulletinName']
                
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderWidthLeft = 2
                PaddingLeft = 3
            # MP elevation
            elif ColumnKey == 'Column1' :
                try :
                    if project == 'SYS' :
                        Value = Null
                    else :
                        TempValue = retrieveReservoirZone(debug, DataBlockDict['DataBlocks']['Table1Data1'][ColumnKey] % project)
                        
                        # Rate the elevation value
                        conn = CwmsDb.getConnection() # Create a java.sql.Connection
                        System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                            #   CCP currently uses (11-17-2017) and seems to work the fastest
                        ElevStorPdc = RatingSet.fromDatabase(conn, MrrElevStorCurve % LocationDict[project]['DbLocation'])
                        PdcTime = int(time.time() * 1000) # Time used for retrieving the Pdc storage curves
                        ElevStorPdc.setDefaultValueTime(PdcTime)
                        DataBlockDict['DataBlocks']['Table1Data1']['Column3'] = ElevStorPdc.rate(TempValue)
                        if 'SystemMpStor' not in locals() : SystemMpStor = DataBlockDict['DataBlocks']['Table1Data1']['Column3']
                        else : SystemMpStor += DataBlockDict['DataBlocks']['Table1Data1']['Column3']
                        Value = '%.1f' % TempValue
                except :
                    Value = Missing
            # FC elevation
            elif ColumnKey == 'Column2' :
                try :
                    if project == 'SYS' :
                        Value = Null
                    else :
                        TempValue = retrieveReservoirZone(debug, DataBlockDict['DataBlocks']['Table1Data1'][ColumnKey] % project)
                        
                        # Rate the elevation value
                        conn = CwmsDb.getConnection() # Create a java.sql.Connection
                        System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                            #   CCP currently uses (11-17-2017) and seems to work the fastest
                        ElevStorPdc = RatingSet.fromDatabase(conn, MrrElevStorCurve % LocationDict[project]['DbLocation'])
                        PdcTime = int(time.time() * 1000) # Time used for retrieving the Pdc storage curves
                        ElevStorPdc.setDefaultValueTime(PdcTime)
                        DataBlockDict['DataBlocks']['Table1Data1']['Column4'] = ElevStorPdc.rate(TempValue)
                        if 'SystemFcStor' not in locals() : SystemFcStor = DataBlockDict['DataBlocks']['Table1Data1']['Column4']
                        else : SystemFcStor += DataBlockDict['DataBlocks']['Table1Data1']['Column4']
                        Value = '%.1f' % TempValue
                except :
                    Value = Missing
            # Rated MP and FC storages
            elif ColumnKey == 'Column3' or ColumnKey == 'Column4' :
                try :
                    if project == 'SYS' and ColumnKey == 'Column3' : 
                        Value = '%.0f' % SystemMpStor
                    elif project == 'SYS' and ColumnKey == 'Column4' : 
                        Value = '%.0f' % SystemFcStor
                    else :
                        Value = '%.0f' % DataBlockDict['DataBlocks']['Table1Data1'][ColumnKey]
                except :
                    Value = Missing
            # Elevation
            elif ColumnKey == 'Column5' :
                try :
                    if project == 'SYS' :
                        Value = Null
                    else :
                        Tsc = CwmsDb.get(DataBlockDict['DataBlocks']['Table1Data1'][ColumnKey] % LocationDict[project]['DbLocation'])
                        Value = '%.2f' % Tsc.values[-1]
                                        
                        # Set DylElevChange to Missing if there are missing hourly data
                        if Constants.UNDEFINED in [Tsc.values[-1], Tsc.values[0]] : DlyElevChange = Missing
                        else : DlyElevChange = Tsc.values[-1] - Tsc.values[0]
                except :
                    Value = Missing
            # Daily elevation change
            elif ColumnKey == 'Column6' :
                try :
                    if project == 'SYS' :
                        Value = Null
                    else :
                        if DlyElevChange != Missing :
                            Value = '%.2f' % DlyElevChange
                        else :
                            Value = DlyElevChange
                except :
                    Value = Missing
            # Storage, Inflow, and Release
            elif ColumnKey == 'Column7' or ColumnKey == 'Column8' or ColumnKey == 'Column9' :
                try :
                    if project == 'SYS' and ColumnKey != 'Column7' :
                        Value = Null
                    else :
                        if project != 'SYS' :
                            Tsc = CwmsDb.get(DataBlockDict['DataBlocks']['Table1Data1'][ColumnKey] % LocationDict[project]['DbLocation'])
                            if ColumnKey == 'Column7' :
                                if 'SystemStor' not in locals() : SystemStor = Tsc.values[-1]
                                else : SystemStor += Tsc.values[-1]
                                outputDebug(debug, lineNo(), '%s Storage = ' % project, Tsc.values[-1], 
                                    '\tSystem Storage = ', SystemStor)
                        
                        if project == 'SYS' and ColumnKey == 'Column7' :
                            Value = '%.0f' % SystemStor
                        else :
                            Value = '%.0f' % Tsc.values[-1]
                        
                        # Save storage value so percentages can be calculated
                        if ColumnKey == 'Column7' : Storage = Tsc.values[-1]
                except :
                    Value = Missing
            # MP Percentage
            elif ColumnKey == 'Column10' :
                try :
                    if project == 'SYS' :
                        MpStoragePercentage = (SystemStor / SystemMpStor) * 100.
                    else :
                        MpStoragePercentage = (Storage / DataBlockDict['DataBlocks']['Table1Data1']['Column3']) * 100.

                    if MpStoragePercentage > 100. : MpStoragePercentage = 100.
                    Value = '%.1f' % MpStoragePercentage
                except :
                    Value = Missing
            # FC Storage
            elif ColumnKey == 'Column11' :
                try :
                    if project == 'SYS' :
                        FcStorage = SystemStor - SystemMpStor
                        outputDebug(debug, lineNo(), '%s Storage = ' % project, SystemStor, 
                            '\tSystem Fc Storage = ', SystemFcStor)
                    else :
                        FcStorage = Storage - DataBlockDict['DataBlocks']['Table1Data1']['Column3']

                    if FcStorage < 0. : FcStorage = 0.
                    Value = '%.0f' % FcStorage
                except :
                    Value = Missing
            # FC Percentage
            elif ColumnKey == 'Column12' :
                try :
                    if project == 'SYS' :
                        FcStoragePercentage = (FcStorage / (SystemFcStor - SystemMpStor)) * 100.
                    else :
                        FcStoragePercentage = (FcStorage / (DataBlockDict['DataBlocks']['Table1Data1']['Column4'] - DataBlockDict['DataBlocks']['Table1Data1']['Column3'])) * 100.

                    if FcStoragePercentage > 100. : FcStoragePercentage = 100.
                    Value = '%.1f' % FcStoragePercentage
                    
                    # Change default cell properties
                    BorderWidthRight = 2
                    if FcStoragePercentage > DataBlockDict['DataBlocks']['Table1Data1']['RedStor'] : BackgroundColor = Color10 # Red
                    elif DataBlockDict['DataBlocks']['Table1Data1']['YellowStor'] < FcStoragePercentage <= DataBlockDict['DataBlocks']['Table1Data1']['RedStor'] : BackgroundColor = Color9 # Yellow
                    else : BackgroundColor = Color8 # Green
                except :
                    Value = Missing
            
            outputDebug(debug, lineNo(), 'ColumnKey = ', ColumnKey, '\tValue = ', Value)
            Cell = PdfPCell(Phrase(Chunk(Value, Font)))
            Cell.setRowspan(RowSpan); Cell.setColspan(ColSpan)
            Cell.setHorizontalAlignment(HorizontalAlignment)
            Cell.setUseVariableBorders(VariableBorders)
            Cell.setBorderColorTop(BorderColorTop); Cell.setBorderColorBottom(BorderColorBottom); Cell.setBorderColorLeft(BorderColorLeft); Cell.setBorderColorRight(BorderColorRight)
            Cell.setBorderWidthTop(BorderWidthTop); Cell.setBorderWidthBottom(BorderWidthBottom); Cell.setBorderWidthLeft(BorderWidthLeft); Cell.setBorderWidthRight(BorderWidthRight)
            Cell.setBackgroundColor(BackgroundColor)
            Cell.setPaddingTop(PaddingTop); Cell.setPaddingBottom(PaddingBottom)
            Table1.addCell(Cell)

    return Table1
#
# table1Heading Function    : Creates the heading for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def table1Heading(  debug,  # Set to True to print all debug statements
                    Table1  # PdfPTable object
                    ) :
    #
    # Create Table1 Heading 
    #
    # Column 0 Heading
    Cell = PdfPCell(Phrase(Chunk('Project', Font3)))
    Cell.setRowspan(1); Cell.setColspan(1)
    Cell.setFixedHeight(20)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(2); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(2); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color5)
    Table1.addCell(Cell)

    # Column 1-4 Heading
    Cell = PdfPCell(Phrase(Chunk('Project Information', Font3)))
    Cell.setRowspan(1); Cell.setColspan(4)
    Cell.setFixedHeight(20)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(2); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color5)
    Table1.addCell(Cell)

    # Column 5-9 Heading
    Cell = PdfPCell(Phrase(Chunk('Current Data', Font3)))
    Cell.setRowspan(1); Cell.setColspan(5)
    Cell.setFixedHeight(20)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(2); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColorTop(Color2); Cell.setBorderColorBottom(Color2); Cell.setBorderColorLeft(Color2); Cell.setBorderColorRight(Color2)
    Cell.setBackgroundColor(Color5)
    Table1.addCell(Cell)

    # Column 10-12 Heading
    Cell = PdfPCell(Phrase(Chunk('Occupied Storage', Font3)))
    Cell.setRowspan(1); Cell.setColspan(3)
    Cell.setFixedHeight(20)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(2); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(2)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color5)
    Table1.addCell(Cell)
    
    # Blank Column 0 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk(' ', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(2); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 1-2 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Elevations (ft)', Font4)))
    Cell.setRowspan(1); Cell.setColspan(2)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 3-4 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Cumulative Stor (ac-ft)', Font4)))
    Cell.setRowspan(1); Cell.setColspan(2)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 5 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Elev\n(ft)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 6 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Dly Elev Chnge (ft)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Cell.setPaddingLeft(0.); Cell.setPaddingRight(0.)
    Table1.addCell(Cell)

    # Column 7 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Storage\n(ac-ft)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 8 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Inflow\n(cfs)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColorTop(Color2); Cell.setBorderColorBottom(Color2); Cell.setBorderColorLeft(Color2); Cell.setBorderColorRight(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 9 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('Release\n(cfs)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 10 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('MP\n(%)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 11 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('FC\n(ac-ft)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 12 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('FC\n(%)', Font4)))
    Cell.setRowspan(2); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_BOTTOM)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(2)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 1 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('MP', Font4)))
    Cell.setRowspan(1); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 2 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('FC', Font4)))
    Cell.setRowspan(1); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 3 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('MP', Font4)))
    Cell.setRowspan(1); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    # Column 4 Sub-Heading
    Cell = PdfPCell(Phrase(Chunk('FC', Font4)))
    Cell.setRowspan(1); Cell.setColspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_CENTER); Cell.setVerticalAlignment(Element.ALIGN_CENTER)
    Cell.setUseVariableBorders(True)
    Cell.setBorderWidthTop(0.25); Cell.setBorderWidthBottom(0.25); Cell.setBorderWidthLeft(0.25); Cell.setBorderWidthRight(0.25)
    Cell.setBorderColor(Color2)
    Cell.setBackgroundColor(Color6)
    Table1.addCell(Cell)

    return Table1

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
    Cell = PdfPCell(Img)
    Cell.setHorizontalAlignment(Element.ALIGN_LEFT)
    Cell.setRowspan(len(TitleLines))
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to the TitleBlock
    Cell = PdfPCell(Phrase(Chunk(TitleLine1, Font1)))
    Cell.setRowspan(1); Cell.setColspan(Table1Columns - 2)
    Cell.setHorizontalAlignment(Element.ALIGN_RIGHT)
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setPaddingTop(14); Cell.setPaddingRight(5)
    TitleBlock.addCell(Cell)
    
    # Add the seal to the TitleBlock
    Img = Image.getInstance(Seal)
    Img.scalePercent(1.6)
    Cell = PdfPCell(Img)
    Cell.setHorizontalAlignment(Element.ALIGN_RIGHT)
    Cell.setRowspan(len(TitleLines))
    Cell.setUseVariableBorders(True)
    Cell.setBorder(Rectangle.LEFT)
    Cell.setBorderColorLeft(Color1)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine2 to the TitleBlock
    Cell = PdfPCell(Phrase(Chunk(TitleLine2, Font2)))
    Cell.setColspan(Table1Columns - 2)
    Cell.setRowspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_RIGHT)
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setPaddingTop(0)
    Cell.setPaddingRight(5)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine3 to the TitleBlock
    Cell = PdfPCell(Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)))
    Cell.setColspan(Table1Columns - 2)
    Cell.setRowspan(1)
    Cell.setHorizontalAlignment(Element.ALIGN_RIGHT)
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setPaddingTop(0); Cell.setPaddingRight(5)
    TitleBlock.addCell(Cell)

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    Cell = PdfPCell(Phrase(Chunk('', Font1)))
    Cell.setRowspan(1); Cell.setColspan(Table1Columns)
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
    
    # Table Columns
    Table1ColumnWidths = [12] * Table1Columns
    for column in range(Table1Columns) :
        if column == 0 :
            Table1ColumnWidths[column] = 45
        elif column in [3, 4, 7, 9, 11] :
            Table1ColumnWidths[column] = 15
        elif column in [5] :
            Table1ColumnWidths[column] = 13
        elif column in [6] :
            Table1ColumnWidths[column] = 17
        elif column in [10, 12] :
            Table1ColumnWidths[column] = 10
    Table1.setWidths(Table1ColumnWidths)
    
    #
    # Create Title Block that will be at the top of the bulletin
    #
    TitleBlock = titleBlock(debug, TitleBlock)

    #
    # Create the heading for Table1
    #
    Table1 = table1Heading(debug, Table1)
    Table1 = table1Data1(debug, Table1)

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

