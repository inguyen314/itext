'''
Author: Ryan Larsen
Last Updated: 02-25-2019
Description: Create the Omaha District Levee Bulletin
'''

#
# Imports
#
import os, sys, inspect, datetime, time, DBAPI
try : 
    # Syntax does not work with CWMS 3.1 due to the update of the jython. Need to make sure iText jar is in the sys folder
    if iTextPdfPathname not in sys.path : sys.path.append(iTextPdfPathname)
except : 
    pass
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
from java.text              import NumberFormat
from java.util              import Locale
from time                   import mktime, localtime
from subprocess             import Popen
import java.lang

# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = "C:\\Users\\G0PDRRJL\\Documents\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\g7cwmspd\\cronjobs\\" # Used in the properties file to create pathname for Seals and Symbols
    BulletinsDirectory = CronjobsDirectory + 'Bulletins\\'
    ScriptDirectory = BulletinsDirectory + 'NWO_Levee\\'
    BulletinFilename = BulletinsDirectory + 'NWO_Levee_Bulletin.pdf'
    CsvFilename = BulletinsDirectory + 'NWO_Levee_Bulletin.csv'
    BulletinPropertiesPathname = ScriptDirectory + 'NWO_Levee_Bulletin_Properties.txt'
else :
    # Server pathnames
    ScriptDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = ScriptDirectory.split('/')
    BulletinsDirectory = '/'.join(PathList[: -1]) + '/'
    CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
    ScriptDirectory += '/'
    BulletinFilename = BulletinsDirectory + 'NWO_Levee_Bulletin.pdf'
    CsvFilename = BulletinsDirectory + 'NWO_Levee_Bulletin.csv'
    BulletinPropertiesPathname = ScriptDirectory + 'NWO_Levee_Bulletin_Properties.txt'

print 'BulletinsDirectory = ', BulletinsDirectory, '\tScript Directory = ', ScriptDirectory, '\tCronjobsDirectory = ', CronjobsDirectory
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
# table1Data Function   : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table1Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName,   # String name for data section of table
                CsvData,    # Csv data   
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
        PublicName = retrievePublicName(debug, conn, project)
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == DataBlocks[-1] :
            LastDataBlock = True
        else : LastDataBlock = False
        outputDebug(debug, lineNo(), 'Last Data Block = ', LastDataBlock)
        
        # Reset TotalColSpan to 0
        TotalColSpan = 0
        
        # Retrieve list of levees associated with gage
        LeveeList = LeveeDict[project]['LeveeList']

        # Retrieve flood stage information
        NwsActionStage = retrieveLocationLevel(debug, conn, CwmsDb, StageNwsAction % project)
        NwsFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, StageNwsFlood % project)
        NwsModFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, StageNwsModFlood % project)
        NwsMajorFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, StageNwsMajFlood % project)
        
        # Add gage information
        GageData = DataOrder[ : 6]
        for data in GageData :
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)

            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)

            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
            RowSpan = len(LeveeList); ColSpan = TableLayoutDict[TableName]['ColSpan']
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding']
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
            # Project Bulletin Name
            if data == 'PublicName' :
                # Create a formatted string that will be added to the table
                if project == 'WSN' : CellData = Phrase(Chunk('*' + PublicName, TextFont))
                else : CellData = Phrase(Chunk(PublicName, TextFont))
                
                # Store value to DataDict
                if project == 'WSN' : DataBlockDict['DataBlocks'][TableDataName][project][data] = '*' + PublicName
                else : DataBlockDict['DataBlocks'][TableDataName][project][data] = PublicName

                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastDataBlock : BorderWidths = [0.25, 0.5, 1, 1]
                else : BorderWidths = [0.25, 0.5, 0.25, 1]
                CellPadding = [2, 2, 2, 3]                
            # River Mile of Gage
            elif data == 'RiverMile' :
                try :
                    RiverMile = str(LeveeDict[project]['RiverMile'])
                    
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(RiverMile, TextFont))
                except :
                    RiverMile = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastDataBlock : BorderWidths = [0.25, 0.25, 1, 0.5]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # Stage of Gage
            elif data == 'Stage' :
                try :
                    StageGageTsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName][data] % project).getData()
                    StageGage = StageGageTsc.values[-1]
                    if StageGage == Constants.UNDEFINED : raise ValueError
                    outputDebug(debug, lineNo(), 'StageGage = ', StageGage)
                    
                    # Create a formatted string that will be added to the table
                    StageGage = round(StageGage, 1)
                    outputDebug(debug, lineNo(), 'Rounded StageGage = ', StageGage)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % StageGage, TextFont))
                except :
                    StageGage = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                if LastDataBlock : BorderWidths = [0.25, 0.25, 1, 0.25]
                
                if StageGage != Null and StageGage != Missing :
                    if StageGage > NwsMajorFloodStage :
                        BackgroundColor = Color12
                    elif StageGage > NwsModFloodStage :
                        BackgroundColor = Color10
                    elif StageGage > NwsFloodStage :
                        BackgroundColor = Color11
                    elif StageGage > NwsActionStage :
                        BackgroundColor = Color9
            # 24-Hr Change
            elif data == '24-Hr Change' :
                try :
                    StageGageTsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName]['Stage'] % project).getData()
                    if StageGage == Missing or StageGageTsc.values[0] == Constants.UNDEFINED : raise ValueError
                    Stage1HrChange = StageGageTsc.values[-1] - StageGageTsc.values[0]
                    outputDebug(debug, lineNo(), 'Stage1HrChange = ', Stage1HrChange)
                    
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Stage1HrChange, TextFont))
                except :
                    Stage1HrChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                if LastDataBlock : BorderWidths = [0.25, 0.25, 1, 0.25]
            # Peak Forecasted Stage
            elif data == 'FcstStage' :
                try :
                    if project in ['WSN'] :
                        PeakFcstStage = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        StageGageTsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName]['Stage'] % project, StartObsTwStr, EndTwStr).getData()
                        LastObsStage = StageGageTsc.values[-1]#max(StageGageTsc.values)
                        FcstStageTsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName][data] % project, EndTwStr, EndFcstTwStr).getData()
                        PeakFcstStage = max(FcstStageTsc.values)
                        if PeakFcstStage == Constants.UNDEFINED or LastObsStage == Constants.UNDEFINED : raise ValueError
                        
                        # Create a formatted string that will be added to the table
                        if PeakFcstStage > LastObsStage :#PeakObsStage : 
                            PeakFcstStage = round(PeakFcstStage, 1)
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PeakFcstStage, TextFont))
                        elif PeakFcstStage <= LastObsStage :#PeakObsStage : 
                            PeakFcstStage = 'Crested'
                            CellData = Phrase(Chunk(PeakFcstStage, TextFont))
                except :
                    PeakFcstStage = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                if LastDataBlock : BorderWidths = [0.25, 0.25, 1, 0.25]
                
                if PeakFcstStage != Null and PeakFcstStage != Missing :
                    if PeakFcstStage == 'Crested' : 
                        pass
                    elif PeakFcstStage > NwsMajorFloodStage :
                        BackgroundColor = Color12
                    elif PeakFcstStage > NwsModFloodStage :
                        BackgroundColor = Color10
                    elif PeakFcstStage > NwsFloodStage :
                        BackgroundColor = Color11
                    elif PeakFcstStage > NwsActionStage :
                        BackgroundColor = Color9
            # Date of Peak Forecasted Stage
            elif data == 'PeakStageDate' :
                try :
                    if project in ['WSN'] :
                        DateOfPeakStageStr = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
                        if PeakFcstStage == 'Crested' :
                            DateOfPeakStageStr = 'Crested'
                        elif PeakFcstStage == Missing :
                            raise ValueError
                        else :
                            FcstStageTsc = CwmsDb.get(DataBlockDict['DataBlocks'][TableDataName]['FcstStage'] % project, EndTwStr, EndFcstTwStr)
                            PeakFcstStage = max(FcstStageTsc.values)
                            
                            StageValues = FcstStageTsc.values
                            PeakStageIndex = StageValues.index(PeakFcstStage)
                            DateOfPeakStageHecTime = HecTime(); DateOfPeakStageHecTime.set(FcstStageTsc.times[PeakStageIndex])
                            DateOfPeakStageStr = DateOfPeakStageHecTime.dateAndTime(4)
                        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DateOfPeakStageStr, TextFont))
                except :
                    DateOfPeakStage = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Change default cell properties
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastDataBlock : BorderWidths = [0.25, 0.5, 1, 0.25]
                else : BorderWidths = [0.25, 0.5, 0.25, 0.25]
        
            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)
            
            TotalColSpan += ColSpan
            
        LeveeData = DataOrder[6 : ]
        for levee in LeveeList :
            # If adding the last project in the last data block, create a trigger to use a thick bottom border
            if levee == LeveeList[-1] and LastDataBlock :
                LastLine = True
            else : LastLine = False

            # Retrieve flood stage information
            TopOfLevee = LeveeDict[levee]['TopOfLeveeStage']
            if project == 'OMA' :
                ToeOfLevee = 29.0
            else :
                ToeOfLevee = NwsFloodStage

            for data in LeveeData :
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
                if data == 'Levee Name' :
                    try :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(levee, TextFont))
                    except :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Missing, TextFont))
    
                    # Change default cell properties
                    HorizontalAlignment = Element.ALIGN_LEFT
                    BorderColors = [Color2, Color2, Color2, Color3]
                    if LastLine : BorderWidths = [0.25, 0.25, 1, 0.5]
                    else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
                # Freeboard
                elif data == 'Freeboard' :
                    try :
                        Freeboard = round(TopOfLevee - StageGage, 1)
                        
                        outputDebug(debug, lineNo(), 'StageGage = ', StageGage, '\tTopOfLevee = ', TopOfLevee, '\tFreeboard = ', Freeboard)
                        
                        # Create a formatted string that will be added to the table
                        if LeveeDict[levee]['Breached'] :
                            Freeboard = 'Breached'
                            TextFont = Font6
                            BackgroundColor = Color17
                        elif Freeboard < DataBlockDict['DataBlocks'][TableDataName]['Freeboard1'] :
                            BackgroundColor = Color16
                        elif DataBlockDict['DataBlocks'][TableDataName]['Freeboard1'] <= Freeboard < DataBlockDict['DataBlocks'][TableDataName]['Freeboard2'] :
                            BackgroundColor = Color14
                        elif DataBlockDict['DataBlocks'][TableDataName]['Freeboard2'] <= Freeboard < DataBlockDict['DataBlocks'][TableDataName]['Freeboard3'] :
                            BackgroundColor = Color13
                        
                        if LeveeDict[levee]['Breached'] :
                            CellData = Phrase(Chunk(Freeboard, TextFont))
                        else :
                            Freeboard = round(Freeboard, 1)
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Freeboard, TextFont))
                    except :
                        Freeboard = Missing
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Missing, TextFont))
    
                    # Change default cell properties
                    if LastLine : 
                        BorderWidths = [0.25, 0.25, 1, 0.25]
                # Percent Loading
                elif data == 'PercentLoading' :
                    try :
                        if StageGage >= ToeOfLevee : PercentLoading = round((StageGage - ToeOfLevee) / (TopOfLevee - ToeOfLevee) * 100., 1)
                        else : PercentLoading = 0.0
                        
                        outputDebug(debug, lineNo(), 'StageGage = ', StageGage, '\tTopOfLevee = ', TopOfLevee, '\tToeOfLevee = ', ToeOfLevee, '\tFreeboard = ', Freeboard)
                        
                        # Create a formatted string that will be added to the table
                        PercentLoading = round(PercentLoading, 1)

                        # Create a formatted string that will be added to the table
                        if LeveeDict[levee]['Breached'] :
                            PercentLoading = 'Breached'
                            TextFont = Font6
                            BackgroundColor = Color17
                        elif PercentLoading > DataBlockDict['DataBlocks'][TableDataName]['Loading1'] :
                            BackgroundColor = Color16
                        elif DataBlockDict['DataBlocks'][TableDataName]['Loading1'] >= PercentLoading > DataBlockDict['DataBlocks'][TableDataName]['Loading2'] :
                            BackgroundColor = Color14
                        elif DataBlockDict['DataBlocks'][TableDataName]['Loading2'] >= PercentLoading > DataBlockDict['DataBlocks'][TableDataName]['Loading3'] :
                            BackgroundColor = Color13
                        
                        if LeveeDict[levee]['Breached'] :
                            CellData = Phrase(Chunk(PercentLoading, TextFont))
                        else :
                            PercentLoading = round(PercentLoading, 1)
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PercentLoading, TextFont))
                    except :
                        PercentLoading = Missing
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Missing, TextFont))
    
                    # Change default cell properties
                    if LastLine : BorderWidths = [0.25, 0.25, 1, 0.25]
                # Fcst Freeboard
                elif data == 'FcstFreeboard' :
                    try :
                        if project in ['WSN'] :
                            FcstFreeboard = Null
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(Null, TextFont))
                        else :
                            if PeakFcstStage == 'Crested' :
                                FcstFreeboard = 'Crested'
                                # Create a formatted string that will be added to the table
                                CellData = Phrase(Chunk(FcstFreeboard, TextFont))
                            else :
                                FcstFreeboard = round(TopOfLevee - PeakFcstStage, 1)
                                
                                outputDebug(debug, lineNo(), 'PeakFcstStage = ', PeakFcstStage, 'TopOfLevee = ', TopOfLevee, '\tFcstFreeboard = ', FcstFreeboard)
                                
                                # Create a formatted string that will be added to the table
                                if LeveeDict[levee]['Breached'] :
                                    FcstFreeboard = 'Breached'
                                    TextFont = Font6
                                    BackgroundColor = Color17
                                elif FcstFreeboard < DataBlockDict['DataBlocks'][TableDataName]['Freeboard1'] :
                                    BackgroundColor = Color16
                                elif DataBlockDict['DataBlocks'][TableDataName]['Freeboard1'] <= FcstFreeboard < DataBlockDict['DataBlocks'][TableDataName]['Freeboard2'] :
                                    BackgroundColor = Color14
                                elif DataBlockDict['DataBlocks'][TableDataName]['Freeboard2'] <= FcstFreeboard < DataBlockDict['DataBlocks'][TableDataName]['Freeboard3'] :
                                    BackgroundColor = Color13
                                
                                if LeveeDict[levee]['Breached'] :
                                    CellData = Phrase(Chunk(FcstFreeboard, TextFont))
                                else :
                                    FcstFreeboard = round(FcstFreeboard, 1)
                                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcstFreeboard, TextFont))
                    except :
                        FcstFreeboard = Missing
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Missing, TextFont))
    
                    # Change default cell properties
                    if LastLine : BorderWidths = [0.25, 0.25, 1, 0.25]
                 # Fcst Percent Loading of Levee
                elif data == 'FcstPercentLoading' :
                    try :
                        if project in ['WSN'] :
                            FcstPercentLoading = Null
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(Null, TextFont))
                        else :
                            if PeakFcstStage == 'Crested' :
                                FcstPercentLoading = 'Crested'
                                # Create a formatted string that will be added to the table
                                CellData = Phrase(Chunk(FcstPercentLoading, TextFont))
                            else :
                                if PeakFcstStage >= ToeOfLevee : FcstPercentLoading = round((PeakFcstStage - ToeOfLevee) / (TopOfLevee - ToeOfLevee) * 100., 1)
                                else : FcstPercentLoading = 0.0
                                
                                outputDebug(debug, lineNo(), 'PeakFcstStage = ', PeakFcstStage, '\tTopOfLevee = ', TopOfLevee, 
                                            '\tToeOfLevee = ', ToeOfLevee, '\tFcstFreeboard = ', FcstFreeboard, '\tFcstPercentLoading = ', FcstPercentLoading)
                                
                                # Create a formatted string that will be added to the table
                                FcstPercentLoading = round(FcstPercentLoading, 1)

                                # Create a formatted string that will be added to the table
                                if LeveeDict[levee]['Breached'] :
                                    FcstPercentLoading = 'Breached'
                                    TextFont = Font6
                                    BackgroundColor = Color17
                                elif FcstPercentLoading > DataBlockDict['DataBlocks'][TableDataName]['Loading1'] :
                                    BackgroundColor = Color16
                                elif DataBlockDict['DataBlocks'][TableDataName]['Loading1'] >= FcstPercentLoading > DataBlockDict['DataBlocks'][TableDataName]['Loading2'] :
                                    BackgroundColor = Color14
                                elif DataBlockDict['DataBlocks'][TableDataName]['Loading2'] >= FcstPercentLoading > DataBlockDict['DataBlocks'][TableDataName]['Loading3'] :
                                    BackgroundColor = Color13
                                
                                if LeveeDict[levee]['Breached'] :
                                    CellData = Phrase(Chunk(FcstPercentLoading, TextFont))
                                else :
                                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % FcstPercentLoading, TextFont))
                    except :
                        FcstPercentLoading = Missing
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Missing, TextFont))
    
                    # Change default cell properties
                    if LastLine : BorderWidths = [0.25, 1, 1, 0.25]
                    else : BorderWidths = [0.25, 1, 0.25, 0.25]
    
                # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
                Table.addCell(Cell)
    
            
    return Table, CsvData
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
    Cell = createCell(debug, Phrase(Chunk('Freeboard/Overtopping estimates may not include all low areas. Overtopping could occur at stages 1-2 feet below estimated value.', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], Table1Columns, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
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
        Table1Columns - 2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    return TableFootnote
#
# table1Heading Function    : Creates the heading for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def table1Heading(  debug,  # Set to True to print all debug statements
                    Table,  # PdfPTable object
                    CsvData # Csv data
                    ) :
    #
    # Create Table1 Heading 
    #
    # Column 0 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Stream Gage', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [1, 0.5, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('River Mile', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], 
        [Color2, Color2, Color2, Color3], [1, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData
    
    # Column 2 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Stage\n(feet)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('24-Hr Change\n(feet)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 4 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Peak Fcst Stage\n(feet)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 0.25, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 5 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Date & Time\nPeak Stage (CDT)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [1, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 6 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Levee Name', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [1, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 7 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Freeboard\n(feet)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], [1, 0.25, 0.25, 0.25], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 8 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Percent\nLoading', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], [1, 0.25, 0.25, 0.25], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 9 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Fcst Freeboard\n(feet)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], [1, 0.25, 0.25, 0.25], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 10 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Fcst Percent\nLoading', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [1, 1, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    return Table, CsvData

#
# table2Data Function   : Creates the Data1 block for Table2 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table2Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                CsvData,    # Csv data
                ) :
    # Column 0-4
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], Table2Columns, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    #
    # Row 1
    #
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('NWS Operational Fcst includes 48 Hours QPF', Font7)), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('NWS Flood Categories', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Levee Freeboard/Loading', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [1, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    #
    # Row 2
    #
    # Column 0
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('*Missouri R at Williston Fcst includes 5 Days QPF', Font7)), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Action', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color9)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('> 5 ft / 0-25%', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    #
    # Row 3
    #
    # Column 0
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Minor', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color11)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('2-5 ft / 25-75%', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color13)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    #
    # Row 4
    #
    # Column 0
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Moderate', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color10)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('< 2 ft / 75-100%', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color14)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    #
    # Row 5
    #
    # Column 0
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Major', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 1, 1], TableLayoutDict['Table1']['VariableBorders'], Color12)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Overtop / > 100%', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color16)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    #
    # Row 5
    #
    # Column 0-2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', Font7))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Breached', Font6))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 1, 1], TableLayoutDict['Table1']['VariableBorders'], Color17)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData
                
    return Table, CsvData

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
    # Global Variables
    #
    global TimeSinceEpoch
    
    #
    # Date and Time Window Info
    #
    CurDateTime = datetime.datetime.now()
    CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm
    if UseCurDate :
        Date = datetime.datetime.now() # Current date
        TimeObj = time.strptime(CurDateTimeStr, '%m-%d-%Y %H:%M')
    else :
        TimeObj = time.strptime(HistoricBulletinDate, '%d%b%Y %H%M')
        TimeObj = localtime(mktime(TimeObj)) # Convert TimeObj to local time so it includes the DST component
        Date    = datetime.datetime.fromtimestamp(mktime(TimeObj))

    StartTw             = Date - datetime.timedelta(hours = 25) # Need to use 25 hours since the last value is from 1 hour ago
    StartTwHour         = StartTw.hour
    StartTwStr          = StartTw.strftime('%d%b%Y') + ' %02d00' % StartTwHour # Start of time window for the database formatted as ddmmmyyyy 2400
    StartObsTw          = Date - datetime.timedelta(10)
    StartObsTwHour      = StartObsTw.hour
    StartObsTwStr       = StartObsTw.strftime('%d%b%Y') + ' %02d00' % StartObsTwHour # Start of time window for the database formatted as ddmmmyyyy 2400
    EndTw               = Date - datetime.timedelta(hours = 1)
    EndTwHour           = EndTw.hour
    EndTwStr            = EndTw.strftime('%d%b%Y') + ' %02d00' % EndTwHour # End of time window for the database formatted as ddmmmyyyy 2400
    EndFcstTw           = Date + datetime.timedelta(7)
    EndFcstTwStr        = EndFcstTw.strftime('%d%b%Y') + ' %02d00' % EndTwHour # End of time window for the database formatted as ddmmmyyyy 2400
    ProjectDateTimeStr  = EndTw.strftime('%m-%d-%Y') + ' %02d:00' % EndTwHour # Project date and time for bulletin formatted as mm-dd-yyyy 2400
    TimeSinceEpoch      = mktime(TimeObj) # Time object used for ratings
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, '\tStart of Observed Time Window = ', StartObsTwStr,
        '\tProject Date and Time = ', ProjectDateTimeStr, '\tTimeSinceEpoch = ', TimeSinceEpoch)
    
    #
    # Open database connection
    #
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('US/Central')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('NWDM')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()# Create a java.sql.Connection

    #
    # Create tables with a finite number of columns that will be written to the pdf file
    #
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)
    
    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)
    
    # Table2: Contains all data and data headings
    Table2 = PdfPTable(Table2Columns)

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
    
    # Table Columns and Order of Variables for Table1 and Table2
    Table2ColumnWidth = 0
    DataOrder, Table1ColumnWidths, Table2ColumnWidths = [], [], []
    for column in range(Table1Columns) :
        # Column Key
        ColumnKey = 'Column%d' % column
        
        DataOrder.append(TableLayoutDict['Table1'][ColumnKey]['Key'])
        Table1ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey]['ColumnWidth'])
        
        Table2ColumnWidth += TableLayoutDict['Table1'][ColumnKey]['ColumnWidth']
        if column == 3 : 
            Table2ColumnWidths.append(Table2ColumnWidth)
            Table2ColumnWidth = 0
        elif column == 5 :
            Table2ColumnWidths.append(Table2ColumnWidth)
            Table2ColumnWidth = 0
        elif column == 6 :
            Table2ColumnWidths.append(Table2ColumnWidth)
            Table2ColumnWidth = 0
        elif column == 10 :
            Table2ColumnWidths.append(Table2ColumnWidth)
            Table2ColumnWidth = 0
        
    Table1.setWidths(Table1ColumnWidths)
    Table2.setWidths(Table2ColumnWidths)
    
    # Table1Footnote Columns
    Table1Footnote.setWidths([10] * Table1Columns)

    # BulletinFootnote Columns
    BulletinFooter.setWidths([10] * FooterColumns)
        
    #
    # Add data to Title Block that will be at the top of the bulletin
    #
    CsvData = ''
    TitleBlock, CsvData = titleBlock(debug, TitleBlock, CsvData)
    
    #
    # Add data to the heading for Table1
    #
    Table1, CsvData = table1Heading(debug, Table1, CsvData)

    #
    # Add data to the data blocks for Table1
    #
    DataBlocks = ['Data1', 'Data2', 'Data3', 'Data4', 'Data5']
    for DataBlock in DataBlocks :
        Table1, CsvData = table1Data(debug, Table1, 'Table1', DataBlock, CsvData)

    #
    # Add data to the table footnotes for Table1
    #
    Table1Footnote = table1Footnote(debug, Table1Footnote)

    #
    # Add data to  Table2
    #
    Table2, CsvData = table2Data(debug, Table2, CsvData)
    
    #
    # Create Pdf file and write tables to create bulletin
    #
    BulletinPdf = Document()
    Writer = PdfWriter.getInstance(BulletinPdf, FileOutputStream(BulletinFilename))
    BulletinPdf.setPageSize(PageSize.LETTER.rotate()) # Set the page size
    PageSize = BulletinPdf.getPageSize()
    PageWidth = PageSize.getWidth()
    BulletinPdf.setMargins(LeftMargin, RightMargin, TopMargin, BottomMargin) # Left, Right, Top, Bottom
    BulletinPdf.setMarginMirroring(True) 
    BulletinPdf.open()
    BulletinPdf.add(TitleBlock) # Add TitleBlock to the PDF
    BulletinPdf.add(Table1) # Add Table1 to the PDF
    BulletinPdf.add(Table1Footnote) # Add Table1's footnotes
    BulletinPdf.add(Table2) # Add Table2 to the PDF
    BulletinFooter.setTotalWidth(PageWidth - 48) # Total width is 792 pixels (11 inches) minus the left and right margins (24 pixels each)
    # Build a footer with page numbers and add to PDF
    BulletinFooter = bulletinFooter(debug, BulletinFooter)
    BulletinFooter.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent())
    
    # 
    # Create csv file
    #
    CsvFile = open(CsvFilename, 'w')
    CsvFile.write(CsvData)
finally :
    try : CwmsDb.done()
    except : pass
    try : conn.done()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass
    try : CsvFile.close()
    except : pass

