'''
Author: Ryan Larsen
Last Updated: 12-31-2017
Description: Create the Omaha District Reservoir Bulletin
'''
#
# Pathnames
#
# PC pathnames
'''
iTextPdfPathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\itextpdf.jar"
BulletinFilename = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWO\\NWO_Reservoir\\NWO_Reservoir_Bulletin_iText.pdf"
BulletinTsFilePathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\2017_Bulletins_Time_Series_12-31.txt"
BulletinPropertiesPathname = "\\\\nwo-netapp1\\Water Management\\Public\\Users\\IText\\Bulletins\\NWO\\NWO_Reservoir\\NWO_Reservoir_Bulletin_Properties.txt"
'''
# Unix pathnames
iTextPdfPathname = "/netapp/g7cwmspd/cronjobs/Bulletins/itextpdf.jar"
BulletinFilename = "/netapp/g7cwmspd/cronjobs/Bulletins/NWO_Reservoir_Bulletin_iText.pdf"
BulletinTsFilePathname = "/netapp/g7cwmspd/cronjobs/Bulletins/2017_Bulletins_Time_Series_12-31.txt"
BulletinPropertiesPathname = "/netapp/g7cwmspd/cronjobs/Bulletins/NWO_Reservoir_Bulletin_Properties.txt"

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
from hec.script             import Constants, MessageBox
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
            RowSpan = TableLayoutDict[TableName]['RowSpan']; ColSpan = TableLayoutDict[TableName]['ColSpan']
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding']
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
            # Project Bulletin Name
            if data == 'PublicName' :
                # Buffalo Bill is not a Section 7 project
                if project == 'BUBI' : PublicName = PublicName + '*' 
                
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                
                # Store value to DataDict
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PublicName

                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 1]
                else : BorderWidths = [0.25, 0.5, 0.25, 1]
                CellPadding = [2, 2, 2, 3]                
            # MP elevation
            elif data == 'TopOfConsZoneElev' :
                try :
                    if project in ['SYS'] : 
                        MpElevZone = Null
                        # Create a formatted string that will be added to the table
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
                        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpElevZone, TextFont))
                except :
                    MpElevZone = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), MpElevZone)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = MpElevZone

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.5]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # FC elevation
            elif data == 'TopOfExclZoneElev' :
                try :
                    if project in ['SYS', 'BUBI', 'LAUD', 'POCA'] : # BUBI does not have a rating curve in the database
                        FcElevZone = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                        
                        # Retrieve reservoir elevation zone value
                        FcElevZone = retrieveReservoirZone(debug, ElevZoneFullName)
                        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcElevZone, TextFont))
                except :
                    FcElevZone = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), FcElevZone)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = FcElevZone

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
            # Rated MP storages
            elif data == 'TopOfConsZoneStor' :
                try :
                    if MpElevZone == Null and project not in ['SYS'] : # Even though System does not have a MpElevZone, a storage zone is calculated
                        MpStorZone = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif MpElevZone == Missing :
                        raise ValueError
                    else :
                        if project in ['SYS'] :
                            MpStorZone = 0.
                            for MainstemProject in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT'] :
                                MpStorZone += DataBlockDict['DataBlocks'][TableDataName][MainstemProject][data]
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
                            
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpStorZone, TextFont))
                except :
                    MpStorZone = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), MpStorZone)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = MpStorZone

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
            # Rated FC storages
            elif data == 'TopOfExclZoneStor' :
                try :
                    if FcElevZone == Null and project != 'SYS' :
                        FcStorZone = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif FcElevZone == Missing :
                        raise ValueError
                    else :
                        if project in ['SYS'] :
                            FcStorZone = 0.
                            for MainstemProject in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT'] :
                                FcStorZone += DataBlockDict['DataBlocks'][TableDataName][MainstemProject][data]
                        else :
                            # Rate the elevation value
                            conn = CwmsDb.getConnection() # Create a java.sql.Connection
                            System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                                #   CCP currently uses (11-17-2017) and seems to work the fastest
                            ElevStorPdc = RatingSet.fromDatabase(conn, DataBlockDict['DataBlocks'][TableDataName]['RatingCurve'] % LocationDict[project]['DbLocation'])
                            PdcTime = int(time.time() * 1000) # Time used for retrieving the Pdc storage curves
                            ElevStorPdc.setDefaultValueTime(PdcTime)
                            FcStorZone = ElevStorPdc.rate(FcElevZone)
                            
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStorZone, TextFont))
                except :
                    FcStorZone = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), FcStorZone)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = FcStorZone

                # Change default cell properties
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 0.25]
                else : BorderWidths = [0.25, 0.5, 0.25, 0.25]
            # Elevation
            elif data == 'Elevation' :
                try :
                    if project in ['SYS'] :
                        PrevElev, Prev2xElev = Null, Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        Tsc = CwmsDb.get(DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation'])
                        PrevElev = Tsc.values[-1] # Previous day's midnight value
                        Prev2xElev = Tsc.values[0] # 2 days previous midnight value
                        
                        # If previous day's value is missing raise an exception and using the missing value
                        if PrevElev == Constants.UNDEFINED : raise ValueError
                        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevElev, TextFont))
                except :
                    PrevElev, Prev2xElev = Missing, Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevElev)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevElev
                DataBlockDict['DataBlocks'][TableDataName][project][data + '2x'] = Prev2xElev

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]

                # Insert special characters for Lake Audubon
                if (DataBlockDict['DataBlocks']['Table1Data3']['PocaSpecialChar'] or DataBlockDict['DataBlocks']['Table1Data3']['Sc12SpecialChar']) and \
                    (project == 'POCA' or project == 'SC12') :
                    if project == 'POCA' : SpecialChar = PocaSpecialChar
                    elif project == 'SC12' : SpecialChar = Sc12SpecialChar

                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(SpecialChar, TextFont))
                    
                    # Store value to DataDict
                    outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), SpecialChar)
                    DataBlockDict['DataBlocks'][TableDataName][project][data] = SpecialChar
    
                    # Change default cell properties
                    BorderColors = [Color2, Color2, Color2, Color3]
                    if LastProject : BorderWidths = [0.25, 1, 1, 0.5]
                    else : BorderWidths = [0.25, 1, 0.25, 0.5]
                    ColSpan = 8
                    HorizontalAlignment = Element.ALIGN_CENTER
                    
                    # Add cell to table and then break loop
                    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                    Table.addCell(Cell)
                    break
                else :
                    BorderColors = [Color2, Color2, Color2, Color3]
                    if LastProject : BorderWidths = [0.25, 0.25, 1, 0.5]
                    else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # Daily elevation change
            elif data == 'ElevChange' :
                try :
                    if project in ['SYS'] :
                        DlyElevChange = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        DlyElevChange = DataBlockDict['DataBlocks'][TableDataName][project]['Elevation'] - DataBlockDict['DataBlocks'][TableDataName][project]['Elevation2x']

                        # Format the value. If the daily elevation change is greater than 1.0 foot, bold the font and set the background color to red
                        if DlyElevChange > 1. :
                            # Change default cell properties
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, Font5))
                            BackgroundColor = Color10 # Red
                        else :
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, TextFont))
                except :
                    DlyElevChange == Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), DlyElevChange)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = DlyElevChange

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
            # Storage, Inflow, and Release
            elif data == 'Storage' or data == 'FlowIn' or data == 'FlowTotal' :
                try :
                    if project == 'LAUD' and DataBlockDict['DataBlocks']['Table1Data3']['LaudSpecialChar'] and data == 'Storage' :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(LaudSpecialChar, TextFont))
                        
                        # Store value to DataDict
                        outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), LaudSpecialChar)
                        DataBlockDict['DataBlocks'][TableDataName][project][data] = LaudSpecialChar
    
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
                            if data != 'Storage' : 
                                Value = Null
                            else : 
                                Value = 0.
                                for MainstemProject in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT'] :
                                    Value += DataBlockDict['DataBlocks'][TableDataName][MainstemProject][data]
                        else :
                            TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
                            # BUBI does not have the default storage time series. Use the TribStorInstHrUsbr time series
                            if project == 'BUBI' and data == 'Storage' :
                                TscPathname = TribStorInstHrUsbr % LocationDict[project]['DbLocation']
                            Tsc = CwmsDb.get(TscPathname)
                            Value = Tsc.values[-1]
                            
                        # If value is missing raise an exception and using the missing value
                        if Value == Constants.UNDEFINED : raise ValueError
    
                        # Create a formatted string that will be added to the table
                        if Value == Null : CellData = Phrase(Chunk(Null, TextFont))
                        else : CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Value, TextFont))
                except :
                    Value = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), Value)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = Value

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
                if data == 'FlotTotal' :
                    BorderColors = [Color2, Color3, Color2, Color2]
                    if LastProject : BorderWidths = [0.25, 0.5, 1, 0.25]
                    else : BorderWidths = [0.25, 0.5, 0.25, 0.25]
            # MP Percentage
            elif data == 'MpStorPercentOccupied' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['TopOfConsZoneStor'] == Null :
                        MpStorPercent = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        MpStorPercent = (DataBlockDict['DataBlocks'][TableDataName][project]['Storage'] / DataBlockDict['DataBlocks'][TableDataName][project]['TopOfConsZoneStor']) * 100.
        
                        if MpStorPercent > 100. : MpStorPercent = 100.
                        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpStorPercent, TextFont))
                except :
                    MpStorPercent = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                
                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), MpStorPercent)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = MpStorPercent

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.5]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # FC Storage
            elif data == 'FcStorOccupied' :
                try :
                    if FcStorZone == Null :
                        FcStor = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        FcStor = DataBlockDict['DataBlocks'][TableDataName][project]['Storage'] - DataBlockDict['DataBlocks'][TableDataName][project]['TopOfConsZoneStor']
    
                        if FcStor < 0. : FcStor = 0.
    
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStor, TextFont))
                except :
                    FcStor = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), FcStor)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = FcStor

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
            # FC Percentage
            elif data == 'FcStorPercentOccupied' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['TopOfExclZoneStor'] == Null and \
                        DataBlockDict['DataBlocks'][TableDataName][project]['FcStorOccupied'] == Null :
                        FcStorPercent = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif DataBlockDict['DataBlocks'][TableDataName][project]['TopOfExclZoneStor'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['TopOfConsZoneStor'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['FcStorOccupied'] == Missing :
                        raise ValueError
                    else :
                        FcStorPercent = (DataBlockDict['DataBlocks'][TableDataName][project]['FcStorOccupied'] / 
                            (DataBlockDict['DataBlocks'][TableDataName][project]['TopOfExclZoneStor'] - DataBlockDict['DataBlocks'][TableDataName][project]['TopOfConsZoneStor'])) * 100.
        
                        if FcStorPercent > 100. : FcStorPercent = 100.
        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcStorPercent, TextFont))
                    
                        if FcStorPercent > DataBlockDict['DataBlocks'][TableDataName]['RedStor'] : BackgroundColor = Color10 # Red
                        elif DataBlockDict['DataBlocks'][TableDataName]['YellowStor'] < FcStorPercent <= DataBlockDict['DataBlocks'][TableDataName]['RedStor'] : BackgroundColor = Color9 # Yellow
                        elif DataBlockDict['DataBlocks'][TableDataName]['GreenStor'] <= FcStorPercent : BackgroundColor = Color8 # Green
                except :
                    FcStorPercent = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), FcStorPercent)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = FcStorPercent

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 1, 1, 0.25]
                else : BorderWidths = [0.25, 1, 0.25, 0.25]
                

            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)
            
    return Table
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
    Cell = createCell(debug, Phrase(Chunk('MP = Multipurpose', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('FC = Flood Control', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)
    
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('-- = N/A Data', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('M = Missing Data', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('*Buffalo Bill is not a Section 7 Project', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        5, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('All Corps and USBR tributary project elevations are reported in NGVD29 except for Cherry Creek and Pipestem Dams, which are in local project datums.', 
        TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], Table1Columns, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    return TableFootnote
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
    Img.scalePercent(12)
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
    
    # Table1Footnote Columns
    Table1Footnote.setWidths([10] * Table1Columns)

    # Table1Footnote Columns
    BulletinFooter.setWidths([10] * FooterColumns)
        
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
    DataBlocks = ['Data1', 'Data2', 'Data3']
    for DataBlock in DataBlocks :
        Table1 = table1Data(debug, Table1, 'Table1', DataBlock)

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
    BulletinFooter.writeSelectedRows(0, -1, 24, BulletinPdf.bottom(BulletinPdf.bottomMargin()), Writer.getDirectContent())

    MessageBox.showInformation('Bulletin Complete', 'Script Status')
finally :
    try : CwmsDb.done()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass

