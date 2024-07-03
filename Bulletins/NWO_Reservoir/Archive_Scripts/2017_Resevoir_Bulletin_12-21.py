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

from com.itextpdf.text      import Document, DocumentException, Rectangle, Paragraph, Phrase, Chunk, Font, FontFactory, BaseColor, PageSize, Element, Image
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
                BorderColors = [Color2, Color3, Color2, Color2]
                BorderWidths = [0.25, 0.5, 0.25, 1]
                CellPadding = [2, 2, 2, 3]
                
                # Buffalo Bill is not a Section 7 project
                if project == 'BUBI' : PublicName = PublicName + '*' 
                
                CellData = Phrase(Chunk(PublicName, TextFont))
            # MP elevation
            elif data == 'TopOfConsZoneElev' :
                try :
                    if project in ['SYS'] : 
                        MpElevZone = Null
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                        if project == 'CAFE' : ElevZoneFullName = TopOfReplZone % project # Canyon Ferry uses the Top of Replacment Zone
                        
                        # Retrieve reservoir elevation zone value. Section 7 and Corps projects have varying names. First try the TopOfJointZone. Then try
                        #   the TopOfConsZone. Then try the TopOfInactZone if the project is in a specific list. If that does not work, raise an 
                        #   exception so the value is shown as missing.
                        try :
                            MpElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                            outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)
                        except :
                            try :
                                ElevZoneFullName = TopOfConsZone % project
                                MpElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                                outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)
                            except :
                                if project in ['SC02', 'SC09', 'SC12', 'SC14'] :
                                    ElevZoneFullName = TopOfInactZone % project
                                    MpElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                                    outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)
                                else :
                                    raise ValueError
                        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpElevZone, TextFont))
                except :
                    MpElevZone = Missing
                    CellData = Phrase(Chunk(Missing, TextFont))
                    outputDebug(debug, lineNo(), 'Set %s TopOfConsZoneElev = ' % project, Missing)

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # FC elevation
            elif data == 'TopOfExclZoneElev' :
                try :
                    if project in ['SYS', 'BUBI', 'LAUD', 'POCA'] : # BUBI does not have a rating curve in the database
                        FcElevZone = Null
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                        
                        # Retrieve reservoir elevation zone value
                        FcElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcElevZone, TextFont))
                except :
                    FcElevZone = Missing
                    CellData = Phrase(Chunk(Missing, TextFont))
            # Rated MP storages
            elif data == 'TopOfConsZoneStor' :
                try :
                    if MpElevZone == Null and project not in ['SYS'] : # Even though System does not have a MpElevZone, a storage zone is calculated
                        MpStorZone = Null
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif MpElevZone == Missing :
                        raise ValueError
                    else :
                        if project in ['SYS'] :
                            MpStorZone = SysMpStorZone
                            outputDebug(debug, lineNo(), '%s MpStorZone = ' % project, SysMpStorZone)
                        elif project in ['BUBI', 'LAUD', 'POCA'] : # BUBI does not have a rating curve in the database
                            StorZoneFullName = TopOfConsStorZone % project
                            
                            # Retrieve reservoir elevation zone value
                            MpStorZone = retrieveReservoirZone(debug, StorZoneFullName)
                        else :
                            # Rate the elevation value
                            conn = CwmsDb.getConnection() # Create a java.sql.Connection
                            System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                                #   CCP currently uses (11-17-2017) and seems to work the fastest
                            ElevStorPdc = RatingSet.fromDatabase(conn, DataBlockDict['DataBlocks'][TableDataName]['RatingCurve'] % LocationDict[project]['DbLocation'])
                            PdcTime = int(time.time() * 1000) # Time used for retrieving the Pdc storage curves
                            ElevStorPdc.setDefaultValueTime(PdcTime)
                            MpStorZone = ElevStorPdc.rate(MpElevZone)
                            
                            # Calculate System FC Storage Zone
                            if 'SysMpStorZone' not in locals() : SysMpStorZone = MpStorZone
                            else : SysMpStorZone += MpStorZone
                            outputDebug(debug, lineNo(), '%s MpStorZone = ' % project, MpStorZone, '\tSysMpStorZone = ', SysMpStorZone)
                            
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpStorZone, TextFont))
                except :
                    MpStorZone = Missing
                    CellData = Phrase(Chunk(Missing, TextFont))
            # Rated FC storages
            elif data == 'TopOfExclZoneStor' :
                try :
                    if FcElevZone == Null and project != 'SYS' :
                        FcStorZone = Null
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif FcElevZone == Missing :
                        raise ValueError
                    else :
                        if project in ['SYS'] :
                            FcStorZone = SysFcStorZone
                        else :
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
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStorZone, TextFont))
                except :
                    FcStorZone = Missing
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                BorderColors = [Color2, Color3, Color2, Color2]
                BorderWidths = [0.25, 0.5, 0.25, 0.25]
            # Elevation
            elif data == 'Elevation' :
                try :
                    if project in ['SYS'] :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        Tsc = CwmsDb.get(DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation'])
                        PrevValue = Tsc.values[-1] # Previous day's midnight value
                        Prev2xValue = Tsc.values[0] # 2 days previous midnight value
                        
                        # If previous day's value is missing raise an exception and using the missing value
                        if PrevValue == Constants.UNDEFINED : raise ValueError
                        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevValue, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Insert special characters for Lake Audubon
                if (DataBlockDict['DataBlocks']['Table1Data3']['PocaSpecialChar'] or DataBlockDict['DataBlocks']['Table1Data3']['Sc12SpecialChar']) and \
                    (project == 'POCA' or project == 'SC12') :
                    if project == 'POCA' : CellData = Phrase(Chunk(PocaSpecialChar, TextFont))
                    elif project == 'SC12' : CellData = Phrase(Chunk(Sc12SpecialChar, TextFont))
                    
                    # Change default cell properties
                    BorderColors = [Color2, Color2, Color2, Color3]
                    BorderWidths = [0.25, 1, 0.25, 0.5]
                    ColSpan = 8
                    HorizontalAlignment = Element.ALIGN_CENTER
                    
                    # Add cell to table and then break loop
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
                    break
                else :
                    BorderColors = [Color2, Color2, Color2, Color3]
                    BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # Daily elevation change
            elif data == 'ElevChange' :
                try :
                    if project in ['SYS'] :
                        DlyElevChange = Null
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        DlyElevChange = PrevValue - Prev2xValue

                        # Format the value. If the daily elevation change is greater than 1.0 foot, bold the font and set the background color to red
                        if DlyElevChange > 1. :
                            # Change default cell properties
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, Font5))
                            BackgroundColor = Color10 # Red
                        else :
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, TextFont))
                except :
                    DlyElevChange == Missing
                    CellData = Phrase(Chunk(Missing, TextFont))
            # Storage, Inflow, and Release
            elif data == 'Storage' or data == 'FlowIn' or data == 'FlowTotal' :
                try :
                    if project in ['SYS'] and data != 'Storage' :
                        CellData = Phrase(Chunk(Null, TextFont))
                    # Insert special characters for Lake Audubon
                    elif project == 'LAUD' and DataBlockDict['DataBlocks']['Table1Data3']['LaudSpecialChar'] and data == 'Storage' :
                        CellData = Phrase(Chunk(LaudSpecialChar, TextFont))
                        
                        # Change default cell properties
                        BorderWidths = [0.25, 1, 0.25, 0.25]
                        ColSpan = 6
                        HorizontalAlignment = Element.ALIGN_CENTER

                        # Add cell to table and then break loop
                        # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                        Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                        Table.addCell(Cell)
                        break
                    else :
                        if project in ['SYS'] :
                            Value = SysStor
                        else :
                            TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
                            # BUBI does not have the default storage time series. Use the TribStorInstHrUsbr time series
                            if project == 'BUBI' and data == 'Storage' :
                                TscPathname = TribStorInstHrUsbr % LocationDict[project]['DbLocation']
                            Tsc = CwmsDb.get(TscPathname)
                            Value = Tsc.values[-1]
                            
                            # Save project and System storage values so percentages can be calculated
                            if data == 'Storage' : 
                                ProjStorage = Value
                                outputDebug(debug, lineNo(), '%s ProjStorage = ' % project, ProjStorage, 
                                    DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation'])
                                
                                # If value is missing raise an exception and using the missing value
                                if ProjStorage == Constants.UNDEFINED : 
                                    raise ValueError
                                else :
                                    if 'SysStor' not in locals() : SysStor = ProjStorage
                                    else : SysStor += ProjStorage
                                    outputDebug(debug, lineNo(), '%s Storage = ' % project, ProjStorage, 
                                        '\tSystem Storage = ', SysStor)
                        
                        # If value is missing raise an exception and using the missing value
                        if Value == Constants.UNDEFINED : raise ValueError

                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Value, TextFont))
                except :
                    Value = Missing
                    if data == 'Storage' : 
                        ProjStorage, SysStor = Missing, Missing
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                if data == 'FlotTotal' :
                    BorderColors = [Color2, Color3, Color2, Color2]
                    BorderWidths = [0.25, 0.5, 0.25, 0.25]
            # MP Percentage
            elif data == 'MpStorPercentOccupied' :
                try :
                    if MpStorZone == Null :
                        # Format the value
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        if project in ['SYS'] :
                            MpStorPercent = (SysStor / SysMpStorZone) * 100.
                        else :
                            MpStorPercent = (ProjStorage / MpStorZone) * 100.
        
                        if MpStorPercent > 100. : MpStorPercent = 100.
                        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpStorPercent, TextFont))
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))
                
                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # FC Storage
            elif data == 'FcStorOccupied' :
                try :
                    if FcStorZone == Null :
                        # Format the value
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
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
                    if FcStorZone == Null or MpStorZone == Null or FcStor == Null or SysFcStorZone == Null or SysMpStorZone == Null :
                        # Format the value
                        CellData = Phrase(Chunk(Null, TextFont))
                    if FcStorZone == Missing or MpStorZone == Missing or FcStor == Missing or SysFcStorZone == Missing or SysMpStorZone == Missing :
                        raise ValueError
                    else :
                        if project in ['SYS'] :
                            FcStorPercent = (FcStor / (SysFcStorZone - SysMpStorZone)) * 100.
                        else :
                            FcStorPercent = (FcStor / (FcStorZone - MpStorZone)) * 100.
        
                        if FcStorPercent > 100. : FcStorPercent = 100.
        
                        # Format the value
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStorPercent, TextFont))
                    
                        if FcStorPercent > DataBlockDict['DataBlocks'][TableDataName]['RedStor'] : BackgroundColor = Color10 # Red
                        elif DataBlockDict['DataBlocks'][TableDataName]['YellowStor'] < FcStorPercent <= DataBlockDict['DataBlocks'][TableDataName]['RedStor'] : BackgroundColor = Color9 # Yellow
                        elif DataBlockDict['DataBlocks'][TableDataName]['GreenStor'] <= FcStorPercent : BackgroundColor = Color8 # Green
                except :
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                BorderWidths = [0.25, 1, 0.25, 0.25]
                

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
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [1, 0.5, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)

    # Column 1-4 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Project Information', Font3)), TableLayoutDict['Table1']['RowSpan'], 4, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color3], 
        [1, 0.5, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)

    # Column 5-9 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Current Data', Font3)), TableLayoutDict['Table1']['RowSpan'], 5, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color3], 
        [1, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)

    # Column 10-12 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Occupied Storage', Font3)), TableLayoutDict['Table1']['RowSpan'], 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [1, 1, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Cell.setFixedHeight(20)
    Table.addCell(Cell)
    
    # Blank Column 0 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 1-2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Elevations (ft)', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 2, 
        Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], 
        [Color2, Color2, Color2, Color3], [0.25, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)

    # Column 3-4 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Cumulative Stor (ac-ft)', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 2, 
        Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 5 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Elev\n(ft)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], 
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
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)

    # Column 10 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('MP\n(%)', TableLayoutDict['Table1']['TextFont'])), 2, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, 
        TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], [0.25, 0.25, 0.25, 0.5], 
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
        TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], [0.25, 0.25, 0.25, 0.5], 
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
        [Color2, Color3, Color2, Color2], [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], 
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
    for DataBlock in ['Data1', 'Data2', 'Data3'] :
        Table1 = table1Data(debug, Table1, 'Table1', DataBlock)

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

