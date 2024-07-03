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
from java.text              import NumberFormat
from java.util              import Locale, Calendar, TimeZone
from time                   import mktime, localtime
from subprocess             import Popen
import java.lang
import os, sys, inspect, datetime, time, DBAPI

# -------------------------------------------------------------------
# Import database pathnames and plotting functions
# -------------------------------------------------------------------

# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
print '================================================================================================================================================================= OS'
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
#
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = r'D:\Water Control\web\rebuild_internal_web\dev\cronjobs\\' # Used in the properties file to create pathname for Seals and Symbols
    BulletinsDirectory = CronjobsDirectory + 'Bulletins\\'
    ScriptDirectory = BulletinsDirectory + 'MVS\\'
    BulletinFilename = BulletinsDirectory + 'MVS_Morning_Report_Bulletin.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'MVS_Morning_Report_Bulletin_Properties.txt'
else :
    # Server pathnames
    ScriptDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = ScriptDirectory.split('/')
    BulletinsDirectory = '/'.join(PathList[: -1]) + '/'
    CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
    ScriptDirectory += '/'
    BulletinFilename = BulletinsDirectory + 'MVS_Morning_Report_Bulletin.pdf'
    ArchiveBulletinFilename = BulletinsDirectory + 'MVS_Morning_Report_Bulletin_%s.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'MVS_Morning_Report_Bulletin_Properties.txt'    
#'\t' in '\tBulletinPropertiesPathname = ' is a tab
print 'BulletinsDirectory = ', BulletinsDirectory
print 'ScriptDirectory = ', ScriptDirectory
print 'BulletinFilename = ', BulletinFilename
print 'BulletinPropertiesPathname = ', BulletinPropertiesPathname

if CronjobsDirectory not in sys.path : sys.path.append(CronjobsDirectory)
if BulletinsDirectory not in sys.path : sys.path.append(BulletinsDirectory)
if ScriptDirectory not in sys.path : sys.path.append(ScriptDirectory)
#
# Load DatabasePathnames.txt and BulletinProperties
#
# TODOO
print 'BulletinProperties = ' , BulletinPropertiesPathname
#
# NOTEE: Checking running on OS or Server 
while True :
    errorMessage = None
    DatabasePathnamesFile = os.path.join(CronjobsDirectory, "DatabasePathnames.txt")
    print 'DatabasePathnamesFile = ' + str(DatabasePathnamesFile)
    if not os.path.exists(DatabasePathnamesFile) :
        errorMessage = "DatabasePathnames.txt does not exist: %s" % DatabasePathnamesFile
    with open(DatabasePathnamesFile, "r") as f : exec(f.read())
    break
if errorMessage :
    print "ERROR : " + errorMessage
BulletinProperties = open(BulletinPropertiesPathname, "r"); exec(BulletinProperties)
#
# Import Server_Utils
import Server_Utils
reload(Server_Utils)
from Server_Utils import lineNo, outputDebug, retrieveLocationLevel, retrievePublicName, retrieveElevatonDatum, retrieveRiverMile, retrieveGroup, \
    retrieveGroupLPMS, retrieveGageZero29, createCell, is_dst, retrieveLocationLevel2
#
# Set debug = True to print all debug statements and = False to turn them off
debug = True
#debug = False
#
print '================================================================================================================================================================= OS END'
#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Modified              : Ivan Nguyen
# Last updated          : 03-30-2022
#
def titleBlock(debug, TitleBlock,) :
    print ''
    print '================================================================================================= titleBlock START'
    #
    # Add USACE Logo, title block lines, and seal to TitleBlock
    TitleLines = [TitleLine1, TitleLine2, TitleLine3, TitleLine4]
    #
    outputDebug(debug, lineNo(), 'TitleLines = ', TitleLines)
    #
    # Add the USACE Logo to the TitleBlock
    Img = Image.getInstance(UsaceLogo)
    outputDebug(debug, lineNo(), 'Img = ', Img)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(Element.ALIGN_LEFT); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.NO_BORDER) #Cell.setBorder(Rectangle.BOX)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine1, Font1))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [2, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER) #Cell.setBorder(Rectangle.BOX)
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
    Cell.setBorder(Rectangle.NO_BORDER) #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine3 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER) #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)

    # Add TitleLine4 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine4 % CurDateTimeStrCST, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine4 % CurDateTimeStrCST, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER) #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER) #Cell.setBorder(Rectangle.BOX)
    Cell.setFixedHeight(4)
    TitleBlock.addCell(Cell)
    print '================================================================================================= titleBlock END'

    return TitleBlock
#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Modified              : Ivan Nguyen
# Last updated          : 03-30-2022
#
def table1Heading(debug, Table,) :
    print ''
    print '=================================================================================================table1Heading START'
    # Create Table1 Heading 
    #
    # Column 0 Heading
    #createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    #0
	
    #1
    CellData = Phrase(Chunk('River\nMile', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    
    CellData = Phrase(Chunk('Gage Station', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.5, 0.25, 1] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
    Cell = createCell(debug, CellData, 3, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color3, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','

     #4
    CellData = Phrase(Chunk('Stage\n(ft)', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #5
    CellData = Phrase(Chunk('24-hr\nChange (ft)', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #3
    CellData = Phrase(Chunk('Flood\nStage (ft)', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #2
    CellData = Phrase(Chunk('Gage\nZero (NAV88)', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    print '=================================================================================================table1Heading END'
    
    return Table
#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Modified              : Ivan Nguyen
# Last updated          : 03-30-2022
#
def table1Data(debug, Table, TableName, DataName, startTime, endTime, startSysTime, endSysTime, DbPathnameList) :
    print '=================================================================================================table1Data START'
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)
    #
    # Data Block Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    # CellPadding = [Top, Right, Bottom, Left]
    #
    if DataName == 'Data1' :
    	textString = "Selected River Gaging Stations as of 6:00 a.m. CST"
    	Cell = createCell(debug, Phrase(Chunk(textString, Font9)), TableLayoutDict[TableName]['RowSpan'],
                Table1Columns, Element.ALIGN_CENTER, TableLayoutDict[TableName]['VerticalAlignment'], [2, 2, 4, 2], TableLayoutDict[TableName]['BorderColors'],
                [0.25, 0.25, 0.25, 0.25], TableLayoutDict[TableName]['VariableBorders'], Color7) 
    	Table.addCell(Cell)
    	Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font9)), TableLayoutDict[TableName]['RowSpan'],
                Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [4, 2, 6, 4], TableLayoutDict[TableName]['BorderColors'],
                [0.25, 0.25, 0.25, 0.25], TableLayoutDict[TableName]['VariableBorders'], Color7)
    else :
        Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font9)), TableLayoutDict[TableName]['RowSpan'],
            Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [4, 2, 6, 4], TableLayoutDict[TableName]['BorderColors'],
            [0.25, 0.25, 0.25, 0.25], TableLayoutDict[TableName]['VariableBorders'], Color7)

    Table.addCell(Cell)

    # Add text to CsvData
    CellData = Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font5))

    # QUERY TO GET PROJECT GROUP TO DISPLAY STAGE 29
    PoolLakeLocation = retrieveGroup(debug,conn,'RDL_POOL_LAKE_ELEV_DISPLAY') 
    outputDebug(debug, lineNo(), 'PoolLakeLocation = ', str(PoolLakeLocation))

    # QUERY TO GET GAGES WITH LPMS DATA
    LPMSLocation = retrieveGroupLPMS(debug,conn) 
    outputDebug(debug, lineNo(), 'LPMSLocation = ', str(LPMSLocation))
           
    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        print '======================================================'
        outputDebug(debug, lineNo(), 'Location ID ============================================================ project = ', project, ' ==================================')
        PublicName = retrievePublicName(debug, conn, project)
        #PublicName = PublicName.replace(' & Reservoir', '')
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)

        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == 'Data%d' % NumberOfDataBlocks and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False

        # Reset TotalColSpan to 0
        TotalColSpan = 0

        for data in DataOrder :
            print '====================================================== data START'
            #
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)
            #
            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)
            #
            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
            TextFont2 = TableLayoutDict[TableName]['TextFont2']
            #
            if project in ['SYS'] :
                RowSpan = 3
            else :
                RowSpan = TableLayoutDict[TableName]['RowSpan']
            # 
            ColSpan = TableLayoutDict[TableName]['ColSpan']   
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding'] #[Top, Right, Bottom, Left]
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            #
			# 1 - RiverMile
            if data == 'RiverMile' :
                getRiverMile = retrieveRiverMile(debug,conn,project)
                outputDebug(debug, lineNo(), 'getRiverMile = ', str(getRiverMile))
                #stop
                if type(getRiverMile) == type('') : 
                    RivMile = float(getRiverMile)
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RivMile, TextFont))
                else :
                    CellData = Phrase(Chunk(Null, TextFont))
                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject or project == 'CEIA' : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
                    #BorderWidths = [0.25, 0.25, 1, 0.5] #[Top, Right, Bottom, Left]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width

            # 2 - PublicName
            elif data == 'PublicName' :
                if project in PoolLakeLocation:
                    #PublicName = PublicName + str('*')
                    PublicName = PublicName
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                CellPadding = [0, 2, 2, 7] #[Top, Right, Bottom, Left]#Indent the project names               
            
            # 3 - ElevDatum
            elif data == 'ElevDatum' :
                try :
                    CellData = Phrase(Chunk(Null, TextFont))
                    # todo: remove if statment below.
                    if project in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT'] : 
                        ElevationDatum = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif project in ['SYS'] :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
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

            # 4 - FloodStage
            elif data == 'FloodStage' :
                try :
                    MVSFloodStage = Null
                    CellData = Phrase(Chunk(Missing, TextFont))
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    MVSFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)
                    outputDebug(debug, lineNo(), 'Flood Stage Pathname = ', TscPathname, '\tMVSFloodStage = ', MVSFloodStage)
                    if MVSFloodStage != Null and MVSFloodStage != 'None' :
                        # Create a formatted string that will be added to the table
                        outputDebug(debug, lineNo(), 'MVSFloodStage = ', str(MVSFloodStage))
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MVSFloodStage, TextFont))
                    else:
                        CellData = Phrase(Chunk('', TextFont))
                except Exception, e :
                    outputDebug(debug, lineNo(), 'FloodStage Exception = ', str(e))

            # 5 - Stage
            elif data == 'Stage' :
                if project in PoolLakeLocation:
                    TscPathname = StageInst30min29 % project
                    outputDebug(debug, lineNo(), 'TscPathname_project = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime) 
                    if TscPathname == "Mel Price Pool-Mississippi.Stage.Inst.30Minutes.0.29":  
                       TscPathname = StageInst15min29 % project 
                       outputDebug(debug, lineNo(), 'TscPathname_mel_price = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime) 
                elif project in LPMSLocation:
                     TscPathname = StageInst2HoursLpmsRaw % project
                     outputDebug(debug, lineNo(), 'TscPathname_lpms = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime)
                else: 
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    outputDebug(debug, lineNo(), 'TscPathname_in_data_block = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime)
                    if TscPathname not in DbPathnameList:
                        TscPathname = StageInst15minRevLrgs % project
                        outputDebug(debug, lineNo(), 'TscPathname_not_in_data_block = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime)
                try :
                    Tsc = CwmsDb.get(TscPathname, startTime, endTime)
                    PrevStage = Tsc.values[-1] # Previous day's midnight value
                    Prev2xStage = Tsc.values[0] # 2 days previous midnight value
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                    outputDebug(debug, lineNo(), 'TscPathname = ', str(TscPathname))
                    #
                    getGageZero29 = retrieveGageZero29( debug,          # Set to True to print all debug statements
                                                        conn,           # 
                                                        project,        # Full name of time series container
                                                        )  
                    outputDebug(debug, lineNo(), 'project = ', project) 
                    outputDebug(debug, lineNo(), 'getGageZero29 = ', str(getGageZero29))                 
                    #
                    if PrevStage == Constants.UNDEFINED : raise ValueError('Missing Stage data for %s' % project)
                    elif Prev2xStage == Constants.UNDEFINED : Prev2xStage = Missing 		
                    #
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage) 
                    outputDebug(debug, lineNo(), 'PoolLakeLocation = ', str(PoolLakeLocation))
                    #
                    MVSFloodStage = retrieveLocationLevel2(debug,conn,project)
                    outputDebug(debug, lineNo(), 'MVSFloodStage = ', str(MVSFloodStage))  
                    #    
                    if project in PoolLakeLocation:
                        outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                        if len(str(MVSFloodStage)) > 0:
                            print 'MVSFloodStage = ' + str(MVSFloodStage) 
                            print 'getGageZero29 = ' + str(getGageZero29)
                            # TODOO Script do not like the statement below and will caused Exceptions
                            #print 'MVSFloodStage + getGageZero29 = ' + float(MVSFloodStage) + float(getGageZero29) 
                            if (float(PrevStage) >= (float(MVSFloodStage) + float(getGageZero29))): BackgroundColor = Color10 # Red
                            print "colorset = Color10 (project)" 
                        else : 
                            BackgroundColor = Color4
                            print "colorset = Color4 (project with no flood stage)"    
                    elif str(MVSFloodStage) =='':
                        outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)   
                        BackgroundColor = Color4
                        print "colorset = Color4 (white not a project)"
                    else:
                        outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                        if (float(PrevStage) >= float(MVSFloodStage)):
                            BackgroundColor = Color10
                            print "colorset = Color10 (red for regualr gage)"
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)

                    #if project in PoolLakeLocation:
                    #    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevStage, TextFont2))    
                    #else :
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevStage, TextFont))
                except :
                    PrevStage, Prev2xStage = Missing, Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevStage
                DataBlockDict['DataBlocks'][TableDataName][project][data + '2x'] = Prev2xStage
                      
            # 6 StageChange
            elif data == 'StageChange' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x'] == Missing :
                        raise ValueError('Cannot compute daily Stage change data for %s' % project)
            
                    DlyStageChange = DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] - DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x']
                    outputDebug(debug, lineNo(), 'DlyStageChange = ', str(DlyStageChange))
                    #
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyStageChange, TextFont))
                except :
                    DlyStageChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                
            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)
            #
            # Add data to CsvData. Break data loop if column span reaches the total number columns before each data piece has been added to that table
            outputDebug(debug, lineNo(), 'ColSpan = ', ColSpan)
            TotalColSpan += ColSpan
            outputDebug(debug, lineNo(), 'TotalColSpan = ', TotalColSpan)    
        #
        # Add Continued Heading for second page
        #
    print '=================================================================================================Data1_END'
    return Table
#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Modified              : Ivan Nguyen
# Last updated          : 03-30-2022
#
def bulletinFooter(debug, Footer) :
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
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Modified              : Ivan Nguyen
# Last updated          : 03-30-2022
#
def table1Footnote(debug, TableFootnote,) :
    # Add a blank line to the table footer to separate the footer from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
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
    Cell = createCell(debug, Phrase(Chunk('Bold = Stage NGVD29', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        3, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    return TableFootnote
#
#
try :    
    # Date and Time Window Info
    print ''
    print '=================================================================================================Main Script 1'
    CurDateTime = datetime.datetime.now()
    CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm
    ArchiveDateTimeStr  = CurDateTime.strftime('%d%m%Y') # Last updated time for bulletin formatted as dd-mm-yyyy
    if UseCurDate :
        Date = datetime.datetime.now() # Current date

        # convert Date to CST
        #if is_dst(str(Date)):
        #    Date = datetime.datetime.now() - datetime.timedelta(hours=-6)
        #else:
        #    Date = datetime.datetime.now() - datetime.timedelta(hours=-5)
    else :
        TimeObj = time.strptime(HistoricBulletinDate, '%d%b%Y %H%M')
        TimeObj = localtime(mktime(TimeObj)) # Convert TimeObj to local time so it includes the DST component
        Date    = datetime.datetime.fromtimestamp(mktime(TimeObj)) # Date is in UTC

    if is_dst(str(Date)):
        CurDateTimeStrCST = (CurDateTime + datetime.timedelta(hours=-6)).strftime('%m-%d-%Y %H:%M')
    else:
        CurDateTimeStrCST = (CurDateTime + datetime.timedelta(hours=-5)).strftime('%m-%d-%Y %H:%M')


    #DB Time
    StartTw             = Date - datetime.timedelta(2) # yesterday at 6am
    StartTwStr          = StartTw.strftime('%d%b%Y 0600') 
    EndTw               = Date - datetime.timedelta(1) # today at 6am
    EndTribTwStr        = Date
    EndTwStr            = EndTribTwStr.strftime('%d%b%Y 0600')
    
    # Mainstem 
    if is_dst(str(Date)):
       #DST had started (March) 	
       EndMainStem      = EndTribTwStr.strftime('%d%b%Y 0600')
       StartMainStem    = EndTw.strftime('%d%b%Y 0600')
    else:
       #DST has ended (in November)
       EndMainStem         = EndTribTwStr.strftime('%d%b%Y 0600')
       StartMainStem       = EndTw.strftime('%d%b%Y 0600')
       
    StartMainStemStor   = EndTw.strftime('%d%b%Y 0600')

    ProjectDateTimeStr  = CurDateTime.strftime('%m-%d-%Y 06:00') 
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr)
    outputDebug(debug, lineNo(), 'End of Time Window = ', EndTwStr)
    outputDebug(debug, lineNo(), 'Project Date and Time = ', ProjectDateTimeStr)
    #
    # Open database connection
    #
    CwmsDb = DBAPI.open()
    outputDebug(debug, lineNo(), 'CwmsDb = ', str(CwmsDb))
    CwmsDb.setTimeZone('US/Central')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('MVS')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()   # Create a java.sql.Connection
    outputDebug(debug, lineNo(), 'conn = ', str(conn))
    # Get list of pathnames in database
    DbPathnameList = CwmsDb.getPathnameList()
    outputDebug(debug, lineNo(), 'DbPathnameList = ', str(DbPathnameList))
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

    # BulletinFooter: Footer for the bulletin - Need for 2nd Page
    BulletinFooter2 = PdfPTable(FooterColumns)
    
    #
    # Specify column widths
    #
    # Title Block Columns
    TitleBlockColumnWidths = [10] * Table1Columns
    TitleBlockColumnWidths[0] = 12 # Adjust logo width 
    TitleBlockColumnWidths[-1] = 7 # Adjust seal width 
    TitleBlock.setWidths(TitleBlockColumnWidths)
    # Table Columns and Order of Variables for Table1
    DataOrder, ColumnWidths = [], []
    for column in range(Table1Columns) :
        # Column Key
        ColumnKey = 'Column%d' % column

        if column == 6 or column == 7 :
           for x in range(1, 2):
              DataOrder.append(TableLayoutDict['Table1'][ColumnKey][1]['Key'])
              ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey][1]['ColumnWidth'])
        else :
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
    print '=================================================================================================Main Script 2'
    NumberOfDataBlocks = len(DataBlockDict['DataBlocks'].keys())
    #NumberOfDataBlocks = 8
    for x in range(1, NumberOfDataBlocks + 1, 1) :
        DataBlock = 'Data%d' % x
        #if DataBlock == 'Data1' or DataBlock == 'Data2' or DataBlock == 'Data3' or DataBlock == 'Data4' or DataBlock == 'Data5' or DataBlock == 'Data6' or DataBlock == 'Data7' or DataBlock == 'Data8' :
        #if DataBlock == 'Data1':
        startTime = StartMainStem
        outputDebug(debug, lineNo(), 'startTime = ', startTime)
        endTime = EndMainStem
        outputDebug(debug, lineNo(), 'endTime = ', endTime)
        Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, StartMainStemStor, endTime, DbPathnameList)
        print '=================================================================================================Main Script 4 - For Every Basins'
    #
    # Create bulletin header that is repeated on each page
    #
    Table1.setHeaderRows(3)
    
    Table1Footnote = table1Footnote(debug, Table1Footnote)
    #
    # Create Pdf file and write tables to create bulletin
    #
    #filenames = [BulletinFilename]
    #
    filenames = [BulletinFilename, ArchiveBulletinFilename % ArchiveDateTimeStr]
    for filename in filenames :
        BulletinPdf = Document()
        Writer = PdfWriter.getInstance(BulletinPdf, FileOutputStream(filename))
        BulletinPdf.setPageSize(PageSize.LETTER) # Set the page size
        PageWidth = BulletinPdf.getPageSize().getWidth()
        BulletinPdf.setMargins(LeftMargin, RightMargin, TopMargin, BottomMargin) # Left, Right, Top, Bottom
        BulletinPdf.setMarginMirroring(True) 
        BulletinPdf.open()
        # Build a footer with page numbers and add to PDF. Only need to build it one time.
        if filename == filenames[0] :
            BulletinFooter = bulletinFooter(debug, BulletinFooter)
        BulletinFooter.setTotalWidth(PageWidth - 48) # Total width is 612 pixels (8.5 inches) minus the left and right margins (24 pixels each)
        BulletinFooter.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent())

        BulletinPdf.add(TitleBlock) # Add TitleBlock to the PDF
        BulletinPdf.add(Table1) # Add Table1 to the PDF

        # Need for second page Footer
        if filename == filenames[0] :
            BulletinFooter2 = bulletinFooter(debug, BulletinFooter2)
        BulletinFooter2.setTotalWidth(PageWidth - 48) # Total width is 612 pixels (8.5 inches) minus the left and right margins (24 pixels each)
        BulletinFooter2.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent())

        BulletinPdf.add(Table1Footnote) # Add Table1's footnotes
        BulletinPdf.close()
        Writer.close()
        #
#
#
finally :
    try : CwmsDb.done()
    except : pass
    try : conn.close()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass
    try : BulletinTsFile.close()
    except : pass
    try : BulletinProperties.close()
    except : pass
	
	
	
	
	
	
	
	
	
	
	
	
	
	