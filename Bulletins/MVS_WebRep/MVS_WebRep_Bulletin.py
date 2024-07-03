# --------------------------------------------------------------------------------------------------------------------------------------
# Required Imports
# --------------------------------------------------------------------------------------------------------------------------------------
from ast import IsNot
from operator import is_not
from com.itextpdf.text                          import Document, DocumentException, Rectangle, Paragraph, Phrase, Chunk, Font, FontFactory, BaseColor, PageSize, Element, Image
from com.itextpdf.text.Font                     import FontFamily
from com.itextpdf.text.pdf                      import PdfWriter, PdfPCell, PdfPTable, PdfPage, PdfName, PdfPageEventHelper, BaseFont
from hec.data.cwmsRating                        import RatingSet
from hec.heclib.util                            import HecTime
from hec.io                                     import TimeSeriesContainer
from hec.script                                 import Constants, MessageBox
from java.awt.image                             import BufferedImage
from java.io                                    import FileOutputStream, IOException
from java.lang                                  import System
from java.text                                  import NumberFormat
from java.util                                  import Locale, Calendar, TimeZone
from time                                       import mktime, localtime
from subprocess                                 import Popen
import java.lang
import os, sys, inspect, datetime, time, DBAPI

# --------------------------------------------------------------------------------------------------------------------------------------
# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
# --------------------------------------------------------------------------------------------------------------------------------------
print '=== Determine if OS is Windows or Unix ==='

OsName = java.lang.System.getProperty("os.name").lower()

print 'OS is Windows or Unix = ', OsName


# If OS is PC, else UNIX Server
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = r'D:\Water Control\web\rebuild_internal_web\dev\cronjobs\\' 
    # Used in the properties file to create pathname for Seals and Symbols
    BulletinsDirectory = CronjobsDirectory + 'Bulletins\\'
    ScriptDirectory = BulletinsDirectory + 'MVS_WebRep\\'
    BulletinFilename = BulletinsDirectory + 'MVS_WebRep_Bulletin.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'MVS_WebRep_Bulletin_Properties.txt'
else :
    # Server pathnames
    ScriptDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = ScriptDirectory.split('/')
    BulletinsDirectory = '/'.join(PathList[: -1]) + '/'
    CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
    ScriptDirectory += '/'
    BulletinFilename = BulletinsDirectory + 'MVS_WebRep_Bulletin.pdf'
    ArchiveBulletinFilename = BulletinsDirectory + 'MVS_WebRep_Bulletin_%s.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'MVS_WebRep_Bulletin_Properties.txt' 


#'\t' in '\tBulletinPropertiesPathname = ' is a tab
print 'BulletinsDirectory = ', BulletinsDirectory
print 'ScriptDirectory = ', ScriptDirectory
print 'BulletinFilename = ', BulletinFilename
print 'BulletinPropertiesPathname = ', BulletinPropertiesPathname

# Setup Pathnames for Unix Server ***
if CronjobsDirectory not in sys.path : sys.path.append(CronjobsDirectory)
if BulletinsDirectory not in sys.path : sys.path.append(BulletinsDirectory)
if ScriptDirectory not in sys.path : sys.path.append(ScriptDirectory)

# --------------------------------------------------------------------------------------------------------------------------------------
# Load DatabasePathnames.txt (One level above at "Bulletins" Folder) and BulletinProperties.txt (Same folder "MVS_Webrep")
# --------------------------------------------------------------------------------------------------------------------------------------
print 'BulletinPropertiesPathname = ' , BulletinPropertiesPathname
while True :
    errorMessage = None
    # Build Pathname for DatabasePathnames.txt
    DatabasePathnamesFile = os.path.join(CronjobsDirectory, "DatabasePathnames.txt")
    print 'DatabasePathnamesFile = ' + str(DatabasePathnamesFile)

    # ***
    if not os.path.exists(DatabasePathnamesFile) :
        errorMessage = "DatabasePathnames.txt does not exist: %s" % DatabasePathnamesFile
    with open(DatabasePathnamesFile, "r") as f : exec(f.read())
    break
# ***
if errorMessage :
    print "ERROR : " + errorMessage
BulletinProperties = open(BulletinPropertiesPathname, "r"); exec(BulletinProperties)

# --------------------------------------------------------------------------------------------------------------------------------------
# Import Query Functions From Server_Utils.py (One level above at "Bulletins" Folder)
# --------------------------------------------------------------------------------------------------------------------------------------
from Server_Utils import lineNo, outputDebug, retrieveCrest, retrieveCrestDate, retrieveNWSDay1, retrieveNWSDay2, retrieveNWSDay3, \
    retrieveNWSForecastDate, retrieveLocationLevel, retrieveRecordStage, retrieveRecordStageDate, retrievePublicName, \
    retrieveElevatonDatum, retrieveRiverMile, retrieveGroup, retrieveGroupLPMS, retrieveGageZero29, retrieveBasin, retrieveLocationID, \
    createCell, is_dst, checkTs, retrieveNWSDay1Date, retrieveNWSDay2Date, retrieveNWSDay3Date, retrievePrecipLake, retrieveMidnight,\
    retrieveEveningOutflow, retrieveRuleCurve, retrieveCrestLake, retrieveCrestLakeDate, retrieveYesterdayInflow, retrieveLakeMeta,\
    retrieveStorageLake, retrieveTopBottomLake, retrieveLocationLevel2

# --------------------------------------------------------------------------------------------------------------------------------------
# Set debug = True to print all debug statements and = False to turn them off
# --------------------------------------------------------------------------------------------------------------------------------------
debug = True
#debug = False

print '=========================================================== OS END'

##################################################################################################################################
# Functions
##################################################################################################################################
#
# titleBlock Function       : Creates the title block for the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 05-03-2023
#
def titleBlock( debug,      # Set to True to print all debug statements
                TitleBlock  # PdfPTable object
              ) :

    print '=========================================================== titleBlock START'
    
    # Add USACE Logo, title block lines, and seal to TitleBlock

    # TitleLine1 to TitleLine4 Located in the MVS_WebRep_Bulletin_Properties.txt File
    TitleLines = [TitleLine1, TitleLine2, TitleLine3, TitleLine4]

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)

    # Add USACE Logo to TitleBlock
    Img = Image.getInstance(UsaceLogo)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(Element.ALIGN_LEFT); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to TitleBlock
    CellData = Phrase(Chunk(TitleLine1, Font1))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [2, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    
    # Add the Seal to the TitleBlock
    Img = Image.getInstance(Seal)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(TableLayoutDict['Table1']['HorizontalAlignment']); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.LEFT); Cell.setBorderColorLeft(Color1); Cell.setBorderWidthLeft(0.5)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine2 to the TitleBlock
    CellData = Phrase(Chunk(TitleLine2, Font2))
    Cell = createCell(debug, Phrase(Chunk(TitleLine2, Font2)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    
    # Add TitleLine3 to the TitleBlock
    CellData = Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'

    # Add TitleLine4 to the TitleBlock
    CellData = Phrase(Chunk(TitleLine4 % CurDateTimeStrCST, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine4 % CurDateTimeStrCST, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TitleBlock.addCell(Cell)

    print '=========================================================== titleBlock END'

    return TitleBlock
#
# table1Heading Function    : Creates the title block for the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 05-03-2023
#
def table1Heading(debug, Table,) :
    print '=========================================================== table1Heading'
    # Create Table1 Heading 
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    # [Top, Right, Bottom, Left]

    # Query to Get NWS Date
    #
    NWSDay1Date = retrieveNWSDay1Date(debug, conn) 
    outputDebug(debug, lineNo(), 'NWSDay1Date = ', str(NWSDay1Date))
    #
    NWSDay2Date = retrieveNWSDay2Date(debug, conn) 
    outputDebug(debug, lineNo(), 'NWSDay2Date = ', str(NWSDay2Date))
    #
    NWSDay3Date = retrieveNWSDay3Date(debug, conn) 
    outputDebug(debug, lineNo(), 'NWSDay3Date = ', str(NWSDay3Date))

    # Table Heading Note
    Cell = createCell(debug, Phrase(Chunk('NOTE: ALL WATER LEVELS GIVEN IN STAGE, UNLESS INDICATED (GAGE ZERO + STAGE = ELEVATION \n FORECASTS INCLUDE OBSERVED PRECIP UP TO 6AM TODAY + EXPECTED PRECIP TO 6AM TOMORROW ONLY.', Font8)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignmentLeft'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)

    # Setup tabel1 heading row 1 of 3

    # 1
    CellData = Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    
    # 2
    CellData = Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 3
    CellData = Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 4
    CellData = Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 5-10
    CellData = Phrase(Chunk('National Weather Service River Forecast', TableLayoutDict['Table1']['TextFont3']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 6, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 11
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 12
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 13
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 14
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # Setup tabel1 heading row 2 of 3

    # Column 1 Heading
    CellData = Phrase(Chunk('River\nMile', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 2 Heading
    CellData = Phrase(Chunk('Gage\nStation', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 3 Heading
    CellData = Phrase(Chunk('6am Levels\n(ft)', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 4 Heading
    CellData = Phrase(Chunk('24-hr\nChange (ft)', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 5-7 Heading
    CellData = Phrase(Chunk('Next 3 Days', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 8 Heading
    CellData = Phrase(Chunk('Forecast\nDate', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 9 Heading
    CellData = Phrase(Chunk('Crest', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 10 Heading
    CellData = Phrase(Chunk('Crest\nDate', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 11 Heading
    CellData = Phrase(Chunk('Flood\nLevel', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 12 Heading
    CellData = Phrase(Chunk('Gage\nZero', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 13 Heading
    CellData = Phrase(Chunk('Record\nLevel', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 14 Heading
    CellData = Phrase(Chunk('Record\n Date', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # Setup tabel1 heading row 3 of 3

    # Column 1 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 2 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 3 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 4 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 5 Sub Sub Heading
    CellData = Phrase(Chunk(NWSDay1Date, TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 6 Sub Sub Heading
    CellData = Phrase(Chunk(NWSDay2Date, TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 7 Sub Sub Heading
    CellData = Phrase(Chunk(NWSDay3Date, TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 8 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 9 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 10 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 11 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 12 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 13 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Column 14 Sub Sub Heading
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    print '=========================================================== table1Heading END'

    return Table
#
# table2Heading Function    : Creates the title block for the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 03-30-2022
#
def table2Heading(debug, Table,) :
    print '=========================================================== table2Heading'
    # Create Table2 Heading 
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    # [Top, Right, Bottom, Left]
    
    # Setup tabel1 heading row 1 of 2

    # 01
    CellData = Phrase(Chunk('Lake', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    
    # 02
    CellData = Phrase(Chunk('MidNight Pool', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, TableLayoutDict['Table2']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignmentBottom'], TableLayoutDict['Table2']['CellPadding1'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 03
    CellData = Phrase(Chunk('24-hr\nChange', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 04 - 05
    CellData = Phrase(Chunk('Current Storage\nUtilized', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 06
    CellData = Phrase(Chunk('Precip\n(in.)', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 07
    CellData = Phrase(Chunk('Yesterday\nInflow (dsf)', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 08 - 09
    CellData = Phrase(Chunk('Controlled\nOutflow (cfs)', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 10
    CellData = Phrase(Chunk('Seasonal \nRule', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignmentBottom'], TableLayoutDict['Table2']['CellPadding1'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 11 - 12
    CellData = Phrase(Chunk('Pool Forecast', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 13
    CellData = Phrase(Chunk('Record\nLevel', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 14
    CellData = Phrase(Chunk('Record\n Date', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # Setup tabel1 heading row 2 of 2

    # 01
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    # 02
    CellData = Phrase(Chunk('Level (Stage)', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignmentTop'], TableLayoutDict['Table2']['CellPadding1'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 03
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 04
    CellData = Phrase(Chunk('Consr', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 05
    CellData = Phrase(Chunk('Flood', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 06
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 07
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 08
    CellData = Phrase(Chunk('Midnight', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 09
    CellData = Phrase(Chunk('Evening', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 10
    CellData = Phrase(Chunk('Curve\n(ft.)', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignmentTop'], TableLayoutDict['Table2']['CellPadding1'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 11
    CellData = Phrase(Chunk('Crest', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 12
    CellData = Phrase(Chunk('Date', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 13
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    # 14
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table2']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table2']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    print '=========================================================== table1Heading END'

    return Table
#
# table1Data Function       : Creates the title block for the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 03-30-2022
#
def table1Data(debug, Table, TableName, DataName, startTime, endTime, startSysTime, endSysTime, DbPathnameList) :
    print ''
    print '================================================================================================= table1Data START'
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)
    #
    # Data Block Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    # CellPadding = [Top, Right, Bottom, Left]
    #
    if DataName == 'Data1' :
    	textString = "Selected River Gaging Stations as of 06:00 a.m. CST"
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
    GroupSetLPMS = retrieveGroupLPMS(debug,conn) 
    outputDebug(debug, lineNo(), 'GroupSetLPMS = ', str(GroupSetLPMS))
           
    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        outputDebug(debug, lineNo(), 'Location ID ============================================================================================== project = ', project, ' ==================================')
        PublicName = retrievePublicName(debug, conn, project)
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border [?]
        if DataName == 'Data%d' % NumberOfDataBlocks and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False

        # Reset TotalColSpan to 0
        TotalColSpan = 0

        for data in DataOrder :
            print '====================================================== data START'
            
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)

            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)
            
            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)
            outputDebug(debug, lineNo(), 'ColumnKey = ', str(ColumnKey))
            
            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
            TextFont4 = TableLayoutDict[TableName]['TextFont4']
            if project in ['SYS'] :
                RowSpan = 3
            else :
                RowSpan = TableLayoutDict[TableName]['RowSpan']
            
            ColSpan = TableLayoutDict[TableName]['ColSpan']   
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding'] #[Top, Right, Bottom, Left]
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
			# 01 - RiverMile
            if data == 'RiverMile' :
                getRiverMile = retrieveRiverMile(debug,conn,project)
                outputDebug(debug, lineNo(), 'getRiverMile = ', str(getRiverMile))
                
                if type(getRiverMile) == type('') : 
                    RiverMile = float(getRiverMile)
                    outputDebug(debug, lineNo(), 'RiverMile = ', str(RiverMile))
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RiverMile, TextFont))
                else :
                    CellData = Phrase(Chunk(Null, TextFont))
                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject or project == 'CEIA' : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]


            # 02 - PublicName
            elif data == 'PublicName' :
                if project in PoolLakeLocation:
                    #PublicName = PublicName + str('*') 
                    PublicName = PublicName
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color2, Color2, Color2]
                CellPadding = [0, 2, 2, 7] #[Top, Right, Bottom, Left] #Indent the project names               
            

            # 03 - Stage
            elif data == 'Stage' :
                if_project = False
                if project in PoolLakeLocation:
                    if_project = True
                    TscPathname = StageInst30min29 % project
                    outputDebug(debug, lineNo(), 'TscPathname_project = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime) 
                    if TscPathname == "Mel Price Pool-Mississippi.Stage.Inst.30Minutes.0.29":  
                       TscPathname = StageInst15min29 % project 
                       outputDebug(debug, lineNo(), 'TscPathname_mel_price = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime) 
                elif project in GroupSetLPMS:
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
                    
                    getGageZero29 = retrieveGageZero29( debug,          # Set to True to print all debug statements
                                                        conn,           # 
                                                        project,        # Full name of time series container
                                                        )  
                    outputDebug(debug, lineNo(), 'project = ', project) 
                    outputDebug(debug, lineNo(), 'getGageZero29 = ', str(getGageZero29))                 
                    
                    if PrevStage == Constants.UNDEFINED : raise ValueError('Missing Stage data for %s' % project)
                    elif Prev2xStage == Constants.UNDEFINED : Prev2xStage = Missing 		
                    
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage) 
                    outputDebug(debug, lineNo(), 'PoolLakeLocation = ', str(PoolLakeLocation))
                    
                    MVSFloodStage = retrieveLocationLevel2(debug,conn,project)
                    outputDebug(debug, lineNo(), 'MVSFloodStage = ', str(MVSFloodStage))  
                      
                    if project in PoolLakeLocation:
                        outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                        TextFont = FontBold
                        if len(str(MVSFloodStage)) > 0:
                            print 'MVSFloodStage = ' + str(MVSFloodStage) 
                            print 'getGageZero29 = ' + str(getGageZero29)
                            # if (float(PrevStage) >= (float(MVSFloodStage) + float(getGageZero29))): BackgroundColor = Color10 # BackgroundColor = Red
                            if (float(PrevStage) >= (float(MVSFloodStage) + float(getGageZero29))): TextFont = FontBoldRed # TextFont = Red
                        else : 
                            BackgroundColor = Color4   
                    elif str(MVSFloodStage) =='':
                        outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)   
                        BackgroundColor = Color4
                    else:
                        outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                        if (float(PrevStage) >= float(MVSFloodStage)):
                            #BackgroundColor = Color10 # BackgroundColor = Red
                            TextFont = Font10 # TextFont = Red
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevStage, TextFont))
                except :
                    PrevStage, Prev2xStage = Missing, Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevStage
                DataBlockDict['DataBlocks'][TableDataName][project][data + '2x'] = Prev2xStage


            # 04 StageChange
            elif data == 'StageChange' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x'] == Missing :
                        raise ValueError('Cannot compute daily Stage change data for %s' % project)
            
                    DlyStageChange = DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] - DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x']
                    
                    if DlyStageChange < 0 :
                        #BackgroundColor = Color10 # Change Background Color to RED
                        #TextFont = Font10 # Change Font Color to RED
                        TextFont = Font8 # Change Font Color to BLACK
                    else :
                        #BackgroundColor = Color4 # Change Background Color to WHITE
                         TextFont = Font8 # Change Font Color to BLACK

                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyStageChange, TextFont))
                except :
                    DlyStageChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 05 - NWSDay1
            elif data == 'NWSDay1' :
                getNWSDay1 = retrieveNWSDay1(debug,conn,project)
                outputDebug(debug, lineNo(), 'getNWSDay1 = ', str(getNWSDay1))

                if getNWSDay1 != None:
                    NWSDay1 = float(getNWSDay1)
                    outputDebug(debug, lineNo(), 'NWSDay1 = ', str(NWSDay1))
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % NWSDay1, TextFont))
                else :
                    CellData = Phrase(Chunk('', TextFont)) 
                BorderColors = [Color2, Color2, Color2, Color3]


            # 06 - NWSDay2
            elif data == 'NWSDay2' :
                getNWSDay2 = retrieveNWSDay2(debug,conn,project)
                outputDebug(debug, lineNo(), 'getNWSDay2 = ', str(getNWSDay2))

                if getNWSDay2 != None:
                    NWSDay2 = float(getNWSDay2)
                    outputDebug(debug, lineNo(), 'NWSDay2 = ', str(NWSDay2))
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % NWSDay2, TextFont))
                else :
                    CellData = Phrase(Chunk('', TextFont))


            # 07 - NWSDay3
            elif data == 'NWSDay3' :
                getNWSDay3 = retrieveNWSDay3(debug,conn,project)
                outputDebug(debug, lineNo(), 'getNWSDay3 = ', str(getNWSDay3))

                if getNWSDay3 != None:
                    NWSDay3 = float(getNWSDay3)
                    outputDebug(debug, lineNo(), 'NWSDay3 = ', str(NWSDay3))
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % NWSDay3, TextFont))
                else :
                    CellData = Phrase(Chunk('', TextFont))


            # 08 - NWSForecastDate
            elif data == 'NWSForecastDate' :
                getNWSForecastDate = retrieveNWSForecastDate(debug,conn,project) 
                outputDebug(debug, lineNo(), 'getNWSForecastDate = ', str(getNWSForecastDate))

                if getNWSForecastDate != None:
                    CellData = Phrase(Chunk(getNWSForecastDate, TextFont))
                else :
                    CellData = Phrase(Chunk('', TextFont))


            # 09 - Crest
            elif data == 'Crest' :
                getCrest = retrieveCrest(debug,conn,project)
                outputDebug(debug, lineNo(), 'getCrest = ', str(getCrest))

                if getCrest != None:
                    Crest = float(getCrest)
                    outputDebug(debug, lineNo(), 'Crest = ', str(Crest))
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Crest, TextFont))
                else :
                    CellData = Phrase(Chunk('', TextFont))
                

            # 10 - CrestDate
            elif data == 'CrestDate' :
                getCrestDate = retrieveCrestDate(debug,conn,project)  
                outputDebug(debug, lineNo(), 'getCrestDate = ', str(getCrestDate))  

                if getCrestDate != None:
                    outputDebug(debug, lineNo(), 'getCrestDate = ', str(getCrestDate)) 
                if type(getCrestDate) == type('') : 
                    CrestDate = str(getCrestDate)
                    outputDebug(debug, lineNo(), 'CrestDate = ', str(CrestDate)) 
                    CellData = Phrase(Chunk(CrestDate, TextFont))
                else :
                    CellData = Phrase(Chunk('', TextFont))
                BorderColors = [Color2, Color2, Color2, Color2]


            # 11 - FloodStage
            elif data == 'FloodStage' :
                try :
                    MVSFloodStage = Null
                    CellData = Phrase(Chunk('', TextFont))
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    MVSFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)
                    outputDebug(debug, lineNo(), 'Flood Stage Pathname = ', TscPathname, '\tMVSFloodStage = ', MVSFloodStage)
                    
                    if MVSFloodStage != Null and MVSFloodStage != 'None' :
                        if MVSFloodStage > 900 :
                            CellData = Phrase(Chunk('', TextFont))
                        else :
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MVSFloodStage, TextFont))
                    else:
                        CellData = Phrase(Chunk('', TextFont))
                    BorderColors = [Color2, Color2, Color2, Color3]
                except Exception, e :
                    outputDebug(debug, lineNo(), 'FloodStage Exception = ', str(e))
                    BorderColors = [Color2, Color2, Color2, Color3]

              
            # 12 - ElevDatum
            elif data == 'ElevDatum' :
                try :
                    CellData = Phrase(Chunk(Null, TextFont))
                    # [?]
                    if project in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT'] : 
                        ElevationDatum = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif project in ['SYS'] :
                        CellData = Phrase(Chunk(Null, TextFont))
                    else :
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


            # 13 - RecordStage
            elif data == 'RecordStage' :
                try :
                    MVSRecordStage = Null
                    CellData = Phrase(Chunk(Missing, TextFont))
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    MVSRecordStage = retrieveRecordStage(debug, conn, CwmsDb, TscPathname)
                    outputDebug(debug, lineNo(), 'TscPathname = ', str(TscPathname))
                    outputDebug(debug, lineNo(), 'MVSFloodStage = ', str(MVSFloodStage))
                    outputDebug(debug, lineNo(), 'MVSRecordStage = ', str(MVSRecordStage))

                    if MVSRecordStage != Null and MVSRecordStage != 'None' :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MVSRecordStage, TextFont))
                    else:
                        #CellData = Phrase(Chunk(Missing, TextFont))
                        CellData = Phrase(Chunk(Missing, TextFont))
                except Exception, e :
                    outputDebug(debug, lineNo(), 'RecordStage Exception = ', str(e))


            # 14 - RecordStageDate
            elif data == 'RecordStageDate' :
                getRecordStageDate = retrieveRecordStageDate(debug,conn,project)
                if getRecordStageDate != None:
                    print 'getRecordStageDate = ' + getRecordStageDate
                if type(getRecordStageDate) == type('') : 
                    RecordStageDate = str(getRecordStageDate)
                    #CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RecordStageDate, TextFont))
                    CellData = Phrase(Chunk(RecordStageDate, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))
                # Change default cell properties
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastProject or project == 'CEIA' : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
                    #BorderWidths = [0.25, 0.25, 1, 0.5] #[Top, Right, Bottom, Left]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width


            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)

            # Add data to CsvData. Break data loop if column span reaches the total number columns before each data piece has been added to that table
            outputDebug(debug, lineNo(), 'ColSpan = ', ColSpan)
            TotalColSpan += ColSpan
            UnformattedData = str(CellData[0]).replace(',', '')
            outputDebug(debug, lineNo(), 'TotalColSpan = ', TotalColSpan)
            print '==========================='    
        #
        # Add Continued Heading for second page
        #
    print '=================================================================================================Data1_END'
    return Table
#
# table2Data Function       : Creates the title block for the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 03-30-2022
#
def table2Data(debug, Table, TableName, DataName, startTime, endTime, startSysTime, endSysTime, DbPathnameList) :
    print '=================================================================================================table2Data'
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)

# Data Block Heading
# createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
#CellPadding = [Top, Right, Bottom, Left]
    print '=================================================================================================Data2' + TableDataName
     

    # QUERY TO GET PROJECT GROUP TO DISPLAY STAGE 29
    PoolLakeLocation = retrieveGroup(debug,conn,'RDL_POOL_LAKE_ELEV_DISPLAY') 
    outputDebug(debug, lineNo(), 'PoolLakeLocation = ', str(PoolLakeLocation))


    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        outputDebug(debug, lineNo(), 'Location ID ============================================================ project = ', project)
        PublicName = retrievePublicName(debug, conn, project)
        ###PublicName = PublicName.replace(' & Reservoir', '')
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == 'Data%d' % NumberOfDataBlocks and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False
        #
        # Reset TotalColSpan to 0
        TotalColSpan = 0
        #
        for data in DataOrder :
            print '==========================='

            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            # The script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)
            #
            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)
            #
            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
            if project in ['SYS'] :
                RowSpan = 3
            else :
                RowSpan = TableLayoutDict[TableName]['RowSpan']
            ColSpan = TableLayoutDict[TableName]['ColSpan']   
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            CellPadding = TableLayoutDict[TableName]['CellPadding'] #[Top, Right, Bottom, Left]
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
                    
            # 1 - PublicName
            if data == 'PublicName' :
                if project in PoolLakeLocation:
                    #PublicName = PublicName + str('*')
                    PublicName = PublicName
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                CellPadding = [0, 2, 2, 7] #[Top, Right, Bottom, Left]#Indent the project names               


            # 2 - Stage
            elif data == 'Stage' :
                if project in PoolLakeLocation:
                    TscPathname = StageInst30min29 % project
                    outputDebug(debug, lineNo(), 'TscPathname_project = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime) 
                    if TscPathname == "Mel Price Pool-Mississippi.Stage.Inst.30Minutes.0.29":  
                       TscPathname = StageInst15min29 % project 
                       outputDebug(debug, lineNo(), 'TscPathname_mel_price = ', TscPathname, '\tstartTime = ', startTime, '\tendTime = ', endTime) 
                elif project in GroupSetLPMS:
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

                    #TextFont = FontBold

                    getGageZero29 = retrieveGageZero29( debug,          # Set to True to print all debug statements
                                                        conn,           # 
                                                        project,        # Full name of time series container
                                                        )  
                    outputDebug(debug, lineNo(), 'project = ', project, '\tgetGageZero29 = ', str(getGageZero29))                 
                    
                    if PrevStage == Constants.UNDEFINED : raise ValueError('Missing Stage data for %s' % project)
                    elif Prev2xStage == Constants.UNDEFINED : Prev2xStage = Missing 		
                    
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                    outputDebug(debug, lineNo(), 'Location ID ============================================================ project = ', project)
                    outputDebug(debug, lineNo(), 'PoolLakeLocation = ', str(PoolLakeLocation))

                    #TscPathname = DataBlockDict['DataBlocks'][TableDataName][FloodStage] % project
                    #MVSFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)                    
                    outputDebug(debug, lineNo(), 'MVSFloodStage = ')

                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)

                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevStage, TextFont))
                except :
                    PrevStage, Prev2xStage = Missing, Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
    
                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevStage
                DataBlockDict['DataBlocks'][TableDataName][project][data + '2x'] = Prev2xStage


            # 3 StageChange
            elif data == 'StageChange' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x'] == Missing :
                        raise ValueError('Cannot compute daily Stage change data for %s' % project)
            
                    DlyStageChange = DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] - DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x']

                    if DlyStageChange < 0 :
                        #TextFont = Font10 # Change Font Color to RED
                        TextFont = Font8 # Change Font Color to BLACK
                    else :
                        TextFont = Font8 # Change Font Color to BLACK

                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyStageChange, TextFont))
                except :
                    DlyStageChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 4 Consr - Current Storage Utilized 
            elif data == 'Consr' :
                getStorage = retrieveStorageLake(debug,conn,project)
                getTOC, getBOC, getTOF, getBOF = retrieveTopBottomLake(debug,conn,project)

                Storage = float(getStorage)
                TOC = float(getTOC)
                BOC = float(getBOC)
                outputDebug(debug, lineNo(), 'getStorage = ', str(getStorage))
                outputDebug(debug, lineNo(), 'getTOC = ', str(getTOC))
                outputDebug(debug, lineNo(), 'getBOC = ', str(getBOC))

                if Storage>0.0 and TOC>0.0 and BOC>=0.0:
                    if Storage < BOC:
                        Consr = 0.00 
                    elif Storage > TOC:
                        Consr = 100.00
                    elif Storage <= TOC:
                        Consr = (((Storage - BOC)/(TOC - BOC))*100)
                    outputDebug(debug, lineNo(), 'Consr = ', str(Consr))
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Consr, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 5 Flood - Current Storage Utilized 
            elif data == 'Flood' :
                getStorage = retrieveStorageLake(debug,conn,project)
                getTOC, getBOC, getTOF, getBOF = retrieveTopBottomLake(debug,conn,project)

                Storage = float(getStorage)
                TOF = float(getTOF)
                BOF = float(getBOF)

                outputDebug(debug, lineNo(), 'getStorage = ', str(getStorage))
                outputDebug(debug, lineNo(), 'getTOC = ', str(getTOF))
                outputDebug(debug, lineNo(), 'getBOC = ', str(getBOF))

                if Storage>0.0 and TOF>0.0 and BOF>0.0:

                    if Storage < BOF:
                        Flood = 0.00 
                    elif Storage > TOF:
                        Flood = 100.00
                    elif Storage <= TOF:
                        Flood = (((Storage - BOF)/(TOF - BOF))*100)

                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % Flood, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 6 - Precip Lake
            elif data == 'PrecipLake' :
                getPrecipLake = retrievePrecipLake(debug,conn,project)
                if getPrecipLake != None:
                    print 'getPrecipLake = ' + getPrecipLake
                    PrecipLake = float(getPrecipLake)
                    #PrecipLake = getPrecipLake
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrecipLake, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 7 Yesterday Inflow 
            elif data == 'YesterdayInflow' :
                getYesterdayInflow = retrieveYesterdayInflow(debug,conn,project)
                if getYesterdayInflow != None:
                    print 'getPrecipLake = ' + getYesterdayInflow
                    YesterdayInflow = float(getYesterdayInflow)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % YesterdayInflow, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 8 - Midnight
            elif data == 'MidnightOutflow' :
                getMidnightOutflow = retrieveMidnight(debug,conn,project)
                if getMidnightOutflow != None:
                    print 'getMidnightOutflow = ' + getMidnightOutflow
                    MidnightOutflow = float(getMidnightOutflow)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MidnightOutflow, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 9 - Evening Outflow
            elif data == 'EveningOutflow' :
                getEveningOutflow = retrieveEveningOutflow(debug,conn,project)
                if getEveningOutflow != None:
                    print 'getEveningOutflow = ' + getEveningOutflow
                    EveningOutflow = float(getEveningOutflow)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % EveningOutflow, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 10 - Rule Curve
            elif data == 'RuleCurve' :
                getRuleCurve = retrieveRuleCurve(debug,conn,project)
                if getRuleCurve != None:
                    print 'getRuleCurve = ' + getRuleCurve
                    RuleCurve = float(getRuleCurve)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RuleCurve, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 11 - Crest
            elif data == 'CrestLake' :
                getCrestLake, getCrestOption = retrieveCrestLake(debug,conn,project)
                if getCrestOption != None:
                    print 'getCrestLake = ' + str(getCrestLake)
                    print 'getCrestOption = ' + str(getCrestOption)
                    if getCrestOption == "CG":
                        CrestOption = "Cresting"
                    else:
                        CrestOption = str(getCrestOption) + " " + str(getCrestLake)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % CrestOption, TextFont))
                else :
                    CellData = Phrase(Chunk(' ', TextFont))


            # 12 - CrestDate
            elif data == 'CrestDateLake' :
                getCrestDateLake = retrieveCrestLakeDate(debug,conn,project)  
                if getCrestDateLake is not None:
                    print 'getCrestDateLake = ' + getCrestDateLake
                #if type(getCrestDateLake) == type('') : 
                    CrestDateLake = str(getCrestDateLake)
                    CellData = Phrase(Chunk(CrestDateLake, TextFont))
                else :
                    CellData = Phrase(Chunk(' ', TextFont))


            # 13 - RecordStage
            elif data == 'RecordStage' :
                try :
                    MVSRecordStage = Null
                    #CellData = Phrase(Chunk(Missing, TextFont))
                    CellData = Phrase(Chunk(Null, TextFont))
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    MVSRecordStage = retrieveRecordStage(debug, conn, CwmsDb, TscPathname)
                    outputDebug(debug, lineNo(), 'RecordStage Pathname = ', TscPathname, '\tMVSRecordStage = ', MVSRecordStage)
                    if MVSRecordStage != Null and MVSRecordStage != 'None' :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MVSRecordStage, TextFont))
                    else:
                        #CellData = Phrase(Chunk(Missing, TextFont))
                        CellData = Phrase(Chunk(Null, TextFont))
                except Exception, e :
                    outputDebug(debug, lineNo(), 'RecordStage Exception = ', str(e))


            # 14 - RecordStageDate
            elif data == 'RecordStageDate' :
                getRecordStageDate = retrieveRecordStageDate(debug,conn,project)
                if getRecordStageDate != None:
                    print 'getRecordStageDate = ' + getRecordStageDate
                if type(getRecordStageDate) == type('') : 
                    RecordStageDate = str(getRecordStageDate)
                    #CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RecordStageDate, TextFont))
                    CellData = Phrase(Chunk(RecordStageDate, TextFont))
                else :
                    CellData = Phrase(Chunk(Null, TextFont))
                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject or project == 'CEIA' : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width
                    #BorderWidths = [0.25, 0.25, 1, 0.5] #[Top, Right, Bottom, Left]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left] IVAN NGUYEN: use same border width


            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)

            # Add data to CsvData. Break data loop if column span reaches the total number columns before each data piece has been added to that table
            outputDebug(debug, lineNo(), 'ColSpan = ', ColSpan)
            TotalColSpan += ColSpan
            UnformattedData = str(CellData[0]).replace(',', '')
            outputDebug(debug, lineNo(), 'TotalColSpan = ', TotalColSpan)
            print '==========================='    
        #
        # Add Continued Heading for second page
        #
    print '=================================================================================================Data2_END'
    return Table
#
# bulletinFooter Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 12-12-2017
#
def bulletinFooter(debug, Footer) :
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(8)
    Footer.addCell(Cell)
    #
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
# table1Footnote Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 12-12-2017
#
def table1Footnote(debug, TableFootnote,) :
    # Add a blank line to the table footer to separate the footer from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    
    # ColSpan in createCell MUST BE EQUAL to Table1Columns in Properties.txt file

    print "table1Footnote begin" 
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('-- = N/A Data', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        5, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('M = Missing Data', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        5, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Bold (Project Gage NGVD29)', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        4, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TableFootnote.addCell(Cell)

    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TableFootnote.addCell(Cell)

    print "table1Footnote end" 
    return TableFootnote
#
# table2Footnote Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 12-12-2017
#
def table2Footnote(debug, TableFootnote,) :
    # Add a blank line to the table footer to separate the footer from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table2']['RowSpan'], Table2Columns, TableLayoutDict['Table2']['HorizontalAlignment'], 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TableFootnote.addCell(Cell)

    # LINE 1
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Lake level and discharges in red/bold exceed arbitrary impact levels', TableLayoutDict['Table2']['TextFont'])), TableLayoutDict['Table2']['RowSpan'], 
        6, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('M = Missing Data', TableLayoutDict['Table2']['TextFont'])), TableLayoutDict['Table2']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Lake Record Levels in Stage NAV 88', TableLayoutDict['Table2']['TextFont'])), TableLayoutDict['Table2']['RowSpan'], 
        4, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('-- = N/A Data', TableLayoutDict['Table2']['TextFont'])), TableLayoutDict['Table2']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

   

    return TableFootnote
#
try :   
    # -------------------------------------------------------------------
    # Date and Time Window Info
    # -------------------------------------------------------------------
    print ''
    print '================================================================================================= Main Script 1'
    CurDateTime = datetime.datetime.now() # Time in UTC with format = 2022-08-23 22:21:03.607000
    CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm (08-23-2022 22:21)
    ArchiveDateTimeStr  = CurDateTime.strftime('%d%m%Y') # Last updated time for bulletin formatted as ddmmyyyy (23082022)

    # Setup Date and Time to Run Historical WebRep Report
    if UseCurDate :
        Date = datetime.datetime.now() # Current date, Time in UTC with format = 2022-08-23 22:21:03.607000
    else :
        TimeObj = time.strptime(HistoricBulletinDate, '%d%b%Y %H%M') 
        TimeObj = localtime(mktime(TimeObj)) # Convert TimeObj to local time so it includes the DST component
        Date    = datetime.datetime.fromtimestamp(mktime(TimeObj))

    # For the Last Updated in the Title Block
    if is_dst(str(Date)):
        CurDateTimeStrCST = (CurDateTime + datetime.timedelta(hours=-6)).strftime('%m-%d-%Y %H:%M')
        outputDebug(debug, lineNo(), 'CurDateTimeStrCST = ', str(CurDateTimeStrCST))
    else:
        CurDateTimeStrCST = (CurDateTime + datetime.timedelta(hours=-5)).strftime('%m-%d-%Y %H:%M')
        outputDebug(debug, lineNo(), 'CurDateTimeStrCST = ', str(CurDateTimeStrCST))


    #Database Time
    StartTw             = Date - datetime.timedelta(1) # datetime.timedelta(2) = minus two days = 2022-08-21 22:39:04.362000

    EndTw               = Date - datetime.timedelta(0) # 2022-08-22 22:39:04.362000
    EndTribTwStr        = Date # 2022-08-23 22:39:04.362000
    
    # Mainstem Report
    if is_dst(str(Date)):
       #DST had started (March) 
       StartTw             = StartTw - datetime.timedelta(hours=5) # Minus 5 Hours from StartTw = 2022-08-21 17:39:04.362000
       EndTribTwStr        = EndTribTwStr - datetime.timedelta(hours=5) #2022-08-23 17:39:04.362000
       EndMainStem         = EndTribTwStr.strftime('%d%b%Y 0600')
       outputDebug(debug, lineNo(), 'EndMainStem = ', str(EndMainStem))
       StartMainStem       = StartTw.strftime('%d%b%Y 0600')
       outputDebug(debug, lineNo(), 'StartMainStem = ', str(StartMainStem))
    else:
       #DST has ended (in November)
       StartTw             = StartTw - datetime.timedelta(hours=6) # Minus 5 Hours from StartTw = 2022-08-21 17:39:04.362000
       EndTribTwStr        = EndTribTwStr - datetime.timedelta(hours=6) #2022-08-23 17:39:04.362000
       EndMainStem         = EndTribTwStr.strftime('%d%b%Y 0600')
       outputDebug(debug, lineNo(), 'EndMainStem = ', str(EndMainStem))
       StartMainStem       = StartTw.strftime('%d%b%Y 0600')
       outputDebug(debug, lineNo(), 'StartMainStem = ', str(StartMainStem))

    StartTwStr          = StartTw.strftime('%d%b%Y 0600') # Hard Coded Time to 0600 Format = 21Aug2022 0600
    outputDebug(debug, lineNo(), 'StartTwStr = ', str(StartTwStr))
    EndTwStr            = EndTribTwStr.strftime('%d%b%Y 0600') #23Aug2022 0600
    outputDebug(debug, lineNo(), 'EndTwStr = ', str(EndTwStr))

    ProjectDate = CurDateTime- datetime.timedelta(hours=5) 

    StartMainStemStor   = ProjectDate.strftime('%d%b%Y 0600')
    outputDebug(debug, lineNo(), 'StartMainStemStor = ', str(StartMainStemStor))

    ProjectDateTimeStr  = ProjectDate.strftime('%m-%d-%Y 06:00') 
    outputDebug(debug, lineNo(), 'ProjectDateTimeStr = ', str(ProjectDateTimeStr))

    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, '\tProject Date and Time = ', ProjectDateTimeStr)
    
    # -------------------------------------------------------------------
    # Open database connection
    # -------------------------------------------------------------------
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('US/Central')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('MVS')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()   # Create a java.sql.Connection
    # Get list of pathnames in database
    DbPathnameList = CwmsDb.getPathnameList()
    #outputDebug(debug, lineNo(), 'DbPathnameList = ', str(DbPathnameList)) # Large outputDebug

    # -------------------------------------------------------------------
    # Create tables with a finite number of columns that will be written to the pdf file
    # -------------------------------------------------------------------
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)

    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)

    # Table1Footnote: Contains the footnotes for Table1
    Table1Footnote = PdfPTable(Table1Columns)

    # BulletinFooter: Footer for the bulletin
    BulletinFooter = PdfPTable(FooterColumns)
    BulletinFooter2 = PdfPTable(FooterColumns) # There are two pages in this report
    
    # Specify column widths
    
    # Title Block Columns

    # Adjust the LOGO size here

    TitleBlockColumnWidths = [8] * Table1Columns
    TitleBlockColumnWidths[0] = 25 # Adjust logo width 
    TitleBlockColumnWidths[-1] = 17 # Adjust seal width 
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
    # Table1Footnote Columns
    Table1Footnote.setWidths([10] * Table1Columns)
    # Table1Footnote Columns
    BulletinFooter.setWidths([10] * FooterColumns)
    
    # Add data to Title Block that will be at the top of the bulletin
    
    TitleBlock = titleBlock(debug, TitleBlock)
    
    # Add data to the heading for Table1
    
    Table1 = table1Heading(debug, Table1)
    
    # Add data to the data blocks for Table1

    #NumberOfDataBlocks = len(DataBlockDict['DataBlocks'].keys())
    print '================================================================================================= Main Script DataBlocks 1'
    NumberOfDataBlocks = 8
    for x in range(1, NumberOfDataBlocks + 1, 1) :
        DataBlock = 'Data%d' % x
        startTime = StartMainStem
        outputDebug(debug, lineNo(), 'startTime = ', startTime)
        endTime = EndMainStem
        outputDebug(debug, lineNo(), 'endTime = ', endTime)
        Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, StartMainStemStor, endTime, DbPathnameList)
    
    # Create bulletin header that is repeated on each page
    
    Table1.setHeaderRows(3)
    
    Table1Footnote = table1Footnote(debug, Table1Footnote)
    
    # Create Pdf file and write tables to create bulletin
    
    print '=================================================================================================Main_Script_END5'
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

        ######################################################################
        # Second Table Start and End Time
        ######################################################################

        #DB Time For Pool Elev, Delta 1 Instead of 2
        StartTwStr          = StartTw.strftime('%d%b%Y 0000') 
        outputDebug(debug, lineNo(), 'StartTwStr = ', str(StartTwStr))

        EndTwStr            = EndTribTwStr.strftime('%d%b%Y 0000')
        outputDebug(debug, lineNo(), 'EndTwStr = ', str(EndTwStr))
        
        StartMainStemStor   = ProjectDate.strftime('%d%b%Y 0000') # ProjectDate setup in Main Script Above
        outputDebug(debug, lineNo(), 'StartMainStemStor = ', str(StartMainStemStor))

        ProjectDateTimeStr  = ProjectDate.strftime('%m-%d-%Y 00:00') 
        outputDebug(debug, lineNo(), 'ProjectDateTimeStr = ', str(ProjectDateTimeStr))

        # Table1: Contains all data and data headings
        Table2 = PdfPTable(Table2Columns)

        # Table1Footnote: Contains the footnotes for Table1
        Table2Footnote = PdfPTable(Table2Columns)
        DataOrder, ColumnWidths = [], []
        for column in range(Table2Columns) :
            # Column Key
            ColumnKey = 'Column%d' % column

            DataOrder.append(TableLayoutDict['Table2'][ColumnKey]['Key'])
            ColumnWidths.append(TableLayoutDict['Table2'][ColumnKey]['ColumnWidth'])
        Table2.setWidths(ColumnWidths)

        # Table2Footnote Columns
        Table2Footnote.setWidths([10] * Table2Columns)
        # Add data to the heading for Table1
        Table2 = table2Heading(debug, Table2)
        #
        DataBlocks = ['Data1']
        for DataBlock in DataBlocks :
            startTime = StartTwStr
            outputDebug(debug, lineNo(), 'startTime = ', startTime)
            endTime = EndTwStr
            outputDebug(debug, lineNo(), 'endTime = ', endTime)
            Table2 = table2Data(debug, Table2, 'Table2', DataBlock, startTime, endTime, StartMainStemStor, endTime, DbPathnameList)
        #
        # Create bulletin header that is repeated on each page
        #
        #Table2.setHeaderRows(3)
        #
        Table2Footnote = table2Footnote(debug, Table2Footnote)
        #
        # Create Pdf file and write tables to create bulletin

        ######################################################################
        # Second table end
        ######################################################################


        ######################################################################
        # Second table end
        ######################################################################
        BulletinPdf.add(Table2) # Add Table2 to the PDF
        BulletinPdf.add(Table2Footnote) # Add Table1's footnotes
        ######################################################################
        # Second table end
        ######################################################################


        BulletinPdf.close()
        Writer.close()
        print '=================================================================================================Main_Script_END6'
#
# try Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 12-12-2017
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
#
# finally Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen/Scott Hoffman
# Modified                  : Ivan Nguyen
# Last updated              : 12-12-2017
#