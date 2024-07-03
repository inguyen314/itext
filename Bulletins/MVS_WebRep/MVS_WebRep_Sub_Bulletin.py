'''
Author: Scott Hoffman
Modified: Ivan Nguyen
Last Updated: 03-30-2022
Description: Create the MVS WebRep Bulletin
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
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = r'D:\Water Control\web\rebuild_internal_web\dev\cronjobs\\' # Used in the properties file to create pathname for Seals and Symbols
    BulletinsDirectory = CronjobsDirectory + 'Bulletins\\'
    ScriptDirectory = BulletinsDirectory + 'MVS_WebRep\\'
    BulletinFilename = BulletinsDirectory + 'MVS_WebRep_Sub_Bulletin.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'MVS_WebRep_Sub_Bulletin_Properties.txt'
else :
    # Server pathnames
    ScriptDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = ScriptDirectory.split('/')
    BulletinsDirectory = '/'.join(PathList[: -1]) + '/'
    CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
    ScriptDirectory += '/'
    BulletinFilename = BulletinsDirectory + 'MVS_WebRep_Sub_Bulletin.pdf'
    ArchiveBulletinFilename = BulletinsDirectory + 'MVS_WebRep_Sub_Bulletin_%s.pdf'
    BulletinPropertiesPathname = ScriptDirectory + 'MVS_WebRep_Sub_Bulletin_Properties.txt'    

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
print 'BulletinProperties = ' , BulletinPropertiesPathname

#NOTEE: Checking running on OS or Server 
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

# Import server utilities
import Server_Utils
reload(Server_Utils)
from Server_Utils import lineNo, outputDebug, retrieveCrest, retrieveCrestDate, retrieveNWSDay1, retrieveNWSDay2, retrieveNWSDay3, \
    retrieveNWSForecastDate, retrieveLocationLevel, retrieveRecordStage, retrieveRecordStageDate, retrievePublicName, retrieveElevatonDatum, \
    retrieveRiverMile, retrieveGroup, retrieveGroupLPMS, retrieveGageZero29, retrieveBasin, retrieveLocationID, createCell, is_dst, \
    checkTs, retrievePrecipLake, retrieveMidnightOutflow, retrieveEveningOutflow, retrieveRuleCurve, retrieveCrestLake, retrieveCrestDateLake

#
# Input
#
# Set debug = True to print all debug statements and = False to turn them off
debug = True
#debug = False
print '=================================================================================================OS_END'
##################################################################################################################################
# Functions
##################################################################################################################################
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Modified              : Ivan Nguyen
# Last updated          : 03-30-2022
#
print '=================================================================================================titleBlock'
def titleBlock(debug, TitleBlock,) :
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
    #Cell.setBorder(Rectangle.BOX)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine1, Font1))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [2, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.RIGHT)
    #Cell.setBorder(Rectangle.NO_BORDER)
    #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)

    #UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    
	# todo: check gage data date/time.
	# todo: check last update date/time.
	
    # Add the seal to the TitleBlock
    Img = Image.getInstance(Seal)
    
    #ImgScaledWidth = Img.getScaledWidth()
    #ImgScaledHeight = Img.getScaledHeight()
    #ImgPreferredHeight = 15.0
    #WidthScale = Img.getScaledHeight() / ImgPreferredHeight
    #Img.scaleAbsolute(Img.getScaledWidth() / WidthScale, ImgPreferredHeight)
    
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(TableLayoutDict['Table1']['HorizontalAlignment']); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.LEFT); Cell.setBorderColorLeft(Color1); Cell.setBorderWidthLeft(0.5)
    #Cell.setBorder(Rectangle.BOX); Cell.setBorderColorLeft(Color1); Cell.setBorderWidthLeft(1.5)
    Cell.setFixedHeight(60.)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine2 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine2, Font2))
    Cell = createCell(debug, Phrase(Chunk(TitleLine2, Font2)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)
    
    #UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    
    # Add TitleLine3 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)
    
    #UnformattedData = str(CellData[0]).replace(',', '') + ',\n'

    # Add TitleLine4 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font1))
    Cell = createCell(debug, Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 2, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    #Cell.setBorder(Rectangle.BOX)
    TitleBlock.addCell(Cell)
    
    #UnformattedData = str(CellData[0]).replace(',', '') + ',\n'

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font1)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    #Cell.setBorder(Rectangle.BOX)
    Cell.setFixedHeight(4)
    TitleBlock.addCell(Cell)

    return TitleBlock
#
# table1Heading Function    : Creates the heading for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
print '=================================================================================================table1Heading'
def table1Heading(debug, Table,) :
    # Create Table1 Heading 
    #
    # Column 0 Heading
    #createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    #0
	
    #1
    CellData = Phrase(Chunk('Lake', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    
    #2
    CellData = Phrase(Chunk('MidNight\nPool NGVD29', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.5, 0.25, 1] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #3
    CellData = Phrase(Chunk('24-hr\nChange', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #4-5
    CellData = Phrase(Chunk('Current Storage\nUtilized', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #6
    CellData = Phrase(Chunk('Precip\n(in.)', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #7
    CellData = Phrase(Chunk('Yesterday\nInflow (dsf)', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #8-9
    CellData = Phrase(Chunk('Controlled\nOutflow (cfs)', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #10
    CellData = Phrase(Chunk('Seasonal \nRule Curve', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #11-12
    CellData = Phrase(Chunk('Pool Forecast', TableLayoutDict['Table1']['TextFont2']))
    #BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #13
    CellData = Phrase(Chunk('Record\nLevel', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #14
    CellData = Phrase(Chunk('Record\n Date', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color11, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


# SUB HEADING

    #1
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    #2
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #3
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #4
    CellData = Phrase(Chunk('Consr', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #5
    CellData = Phrase(Chunk('Flood', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #6
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #7
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #8
    CellData = Phrase(Chunk('Midnight', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #9
    CellData = Phrase(Chunk('Evening', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #10
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


    #11
    CellData = Phrase(Chunk('Crest (ft)', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


     #12
    CellData = Phrase(Chunk('Date', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


     #13
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','


     #14
    CellData = Phrase(Chunk('  ', TableLayoutDict['Table1']['TextFont2']))
    BorderWidths = [0.25, 0.25, 0.25, 0.25]
    Cell = createCell(debug, CellData, 1, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding3'], [Color11, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color11)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    UnformattedData = str(CellData[0]).replace(',', '') + ','

    return Table

    

# table1Data Function   : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
print '=================================================================================================table1Data'
def table1Data(debug, Table, TableName, DataName, startTime, endTime, startSysTime, endSysTime, DbPathnameList) :
    print '=================================================================================================table1Data'
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)

# Data Block Heading
# createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
#CellPadding = [Top, Right, Bottom, Left]
    print '=================================================================================================Data1'

    # QUERY TO GET PROJECT GROUP TO DISPLAY STAGE 29
    GroupSet = retrieveGroup(debug,conn,'RDL_POOL_LAKE_ELEV_DISPLAY') 
    outputDebug(debug, lineNo(), 'GroupSet = ', str(GroupSet))

    # QUERY TO GET GAGES WITH LPMS DATA
    GroupSetLPMS = retrieveGroupLPMS(debug,conn) 
    outputDebug(debug, lineNo(), 'GroupSetLPMS = ', str(GroupSetLPMS))
           
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

        # Reset TotalColSpan to 0
        TotalColSpan = 0

        for data in DataOrder :
            print '==========================='

            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)

            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)

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
            
			# todo: move stage and 24hr stage next to gage station
			# 1 - RiverMile
            if data == 'RiverMile' :
                getRiverMile = retrieveRiverMile(debug,conn,project)
                #outputDebug(True, lineNo(), 'getRiverMile = ' , type(getRiverMile))
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
                    #BorderWidths = [0.25, 0.25, 0.25, 0.5] #[Top, Right, Bottom, Left]
                    
            # 2 - PublicName
            elif data == 'PublicName' :
                if project in GroupSet:
                    PublicName = PublicName + str('*')
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
                    CellData = Phrase(Chunk(Null, TextFont))
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    MVSFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)
                    outputDebug(debug, lineNo(), 'Flood Stage Pathname = ', TscPathname, '\tMVSFloodStage = ', MVSFloodStage)
                    if MVSFloodStage != Null and MVSFloodStage != 'None' :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MVSFloodStage, TextFont))
                    else:
                        CellData = Phrase(Chunk(Null, TextFont))
                except Exception, e :
                    outputDebug(debug, lineNo(), 'FloodStage Exception = ', str(e))


            # 4 - RecordStage
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


            # 4 - RecordStageDate
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


            # 5 - Stage
            elif data == 'Stage' :
                if project in GroupSet:
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
                    outputDebug(debug, lineNo(), 'project = ', project, '\tgetGageZero29 = ', str(getGageZero29))                 
                    
                    if PrevStage == Constants.UNDEFINED : raise ValueError('Missing Stage data for %s' % project)
                    elif Prev2xStage == Constants.UNDEFINED : Prev2xStage = Missing 		
                    
                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                    outputDebug(debug, lineNo(), 'Location ID ============================================================ project = ', project)
                    outputDebug(debug, lineNo(), 'GroupSet = ', str(GroupSet))


                    #TscPathname = DataBlockDict['DataBlocks'][TableDataName][FloodStage] % project
                    #MVSFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)                    
                    outputDebug(debug, lineNo(), 'MVSFloodStage = ')


                    #if project in GroupSet:
                    #    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                    #    if str(MVSFloodStage)!='--':
                    #        print 'MVSFloodStage = ' + str(MVSFloodStage)
                    #        print 'getGageZero29 = ' + getGageZero29
                    #        print 'MVSFloodStage + getGageZero29 = ' + str(MVSFloodStage + float(getGageZero29))
                    #        if (float(PrevStage) >= (float(MVSFloodStage) + float(getGageZero29))): BackgroundColor = Color10 # Red
                    #        print "colorset = Color10 (project)" 
                    #elif MVSFloodStage > 0:  
                    #    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)   
                    #    BackgroundColor = Color4
                    #    print "colorset = Color4 (white)"
                    #else:
                    #    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)
                    #    if (float(PrevStage) >= float(MVSFloodStage)):
                    #        BackgroundColor = Color10
                    #        print "colorset = Color10 (red)"









                    outputDebug(debug, lineNo(), 'PrevStage = ', PrevStage, '\tPrev2xStage = ', Prev2xStage)

                    #if project in GroupSet:
                    #    print "Project in GroupSet: " + project
                    #    print 'getGageZero29 = ' + getGageZero29
                    #    print 'MVSFloodStage = ' + str(MVSFloodStage)
                    #    print 'PrevStage = ' + str(PrevStage)
                    #    print 'PrevStage + getGageZero29 = ' + str(PrevStage + float(getGageZero29))
                    #    print 'MVSFloodStage + getGageZero29 = ' + str(MVSFloodStage + float(getGageZero29))
                    #    if str(MVSFloodStage)!='--':
                    #        if (float(PrevStage) >= (float(MVSFloodStage) + float(getGageZero29))): BackgroundColor = Color10 # Red
                    #        print "colorset = Color10 (project)"            
                    #elif str(MVSFloodStage) == '--': 
                    #    BackgroundColor = Color4
                    #    print "colorset = Color4 (white)" 
                    #else:
                    #    if (float(PrevStage) >= float(MVSFloodStage)): 
                    #        BackgroundColor = Color10
                    #        print "colorset = Color10 (red)"



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
                    
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyStageChange, TextFont))
                except :
                    DlyStageChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 4 - Precip Lake
            elif data == 'PrecipLake' :
                getPrecipLake = retrievePrecipLake(debug,conn,project)
                if getPrecipLake != None:
                    print 'getPrecipLake = ' + getPrecipLake
                    PrecipLake = float(getPrecipLake)
                    #PrecipLake = getPrecipLake
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrecipLake, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 4 - Midnight Outflow
            elif data == 'MidnightOutflow' :
                getMidnightOutflow = retrieveMidnightOutflow(debug,conn,project)
                if getMidnightOutflow != None:
                    print 'getMidnightOutflow = ' + getMidnightOutflow
                    MidnightOutflow = float(getMidnightOutflow)
                    #PrecipLake = getPrecipLake
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MidnightOutflow, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 4 - Evening Outflow
            elif data == 'EveningOutflow' :
                getEveningOutflow = retrieveEveningOutflow(debug,conn,project)
                if getEveningOutflow != None:
                    print 'getEveningOutflow = ' + getEveningOutflow
                    EveningOutflow = float(getEveningOutflow)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % EveningOutflow, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 4 - Rule Curve
            elif data == 'RuleCurve' :
                getRuleCurve = retrieveRuleCurve(debug,conn,project)
                if getRuleCurve != None:
                    print 'getRuleCurve = ' + getRuleCurve
                    RuleCurve = float(getRuleCurve)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RuleCurve, TextFont))
                else :
                    CellData = Phrase(Chunk(Missing, TextFont))


            # 4 - Crest
            elif data == 'CrestLake' :
                getCrestLake = retrieveCrestLake(debug,conn,project)
                if getCrestLake != None:
                    print 'getCrestLake = ' + str(getCrestLake)
                    CrestLake = float(getCrestLake)
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % CrestLake, TextFont))
                else :
                    CellData = Phrase(Chunk(Null, TextFont))


            # 4 - CrestDate
            elif data == 'CrestDateLake' :
                getCrestDateLake = retrieveCrestDateLake(debug,conn,project)  

                #print 'type = ' + type(getCrestDateLake)  

                if getCrestDateLake != None:
                    print 'getCrestDateLake = ' + getCrestDateLake
                if type(getCrestDateLake) == type('') : 
                    CrestDateLake = str(getCrestDateLake)
                    CellData = Phrase(Chunk(CrestDateLake, TextFont))
                else :
                    CellData = Phrase(Chunk(Null, TextFont))


            # 7  AirTempMax, AirTempMin, and Precip
            elif data == 'AirTempMax' or data == 'AirTempMin' or data == 'Precip' :
                if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' : 
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    if checkTs(TscPathname, conn) == 'true' :
                    #if TscPathname in DbPathnameList :
                        # Set database time zone to GMT-6 so met data can be retrieved
                        try :
                            Value = 0.
                            CellData = Phrase(Chunk(Missing, TextFont))
                            Tsc = CwmsDb.get(TscPathname, startTime, endTime)
                            if Tsc != Null :
                                Value = Tsc.values[-1]
                            else:
                                Value = round(Value, 0)
                                if Value > -60 :
                                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(Value)), TextFont))
                                else :
                                    CellData = Phrase(Chunk(Missing, TextFont))
                        except Exception, e :
                            print "AirTemp/Precip Exception = " + str(e)
                            CellData = Phrase(Chunk(Missing, TextFont))
                        
                        # Reset database time zone to US/Central
                        #CwmsDb.setTimeZone('US/Central')
                    else :
                        #Timeseries not found in the database, set value to Null
                        CellData = Phrase(Chunk(Null, TextFont))
                else :
                    CellData = Phrase(Chunk(Null, TextFont))	

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
print '=================================================================================================table1Data_END'
#
# bulletinFooter Function   : Creates a footer for the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
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
# table1Footnote Function   : Creates the footer for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
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
    Cell = createCell(debug, Phrase(Chunk('*Project Gage (Stage 29)', TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        3, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    return TableFootnote


##################################################################
# Main_Script
##################################################################


try :    
    # Date and Time Window Info
    print '=================================================================================================Main_Script'
    CurDateTime = datetime.datetime.now()
    CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm
    ArchiveDateTimeStr  = CurDateTime.strftime('%d%m%Y') # Last updated time for bulletin formatted as dd-mm-yyyy
    if UseCurDate :
        Date = datetime.datetime.now() # Current date
    else :
        TimeObj = time.strptime(HistoricBulletinDate, '%d%b%Y %H%M')
        TimeObj = localtime(mktime(TimeObj)) # Convert TimeObj to local time so it includes the DST component
        Date    = datetime.datetime.fromtimestamp(mktime(TimeObj))

    #DB Time
    StartTw             = Date - datetime.timedelta(2)
    StartTw             = StartTw - datetime.timedelta(hours=5)
    StartTwStr          = StartTw.strftime('%d%b%Y 0000') 

    EndTw               = Date - datetime.timedelta(1)
    EndTribTwStr        = Date
    EndTribTwStr        = EndTribTwStr - datetime.timedelta(hours=5)
    EndTwStr            = EndTribTwStr.strftime('%d%b%Y 0000')

    
    # Mainstem 
    if is_dst(str(Date)):
       #DST had started (March) 	
       EndMainStem      = EndTribTwStr.strftime('%d%b%Y 0000')
       StartMainStem    = EndTw.strftime('%d%b%Y 0000')
    else:
       #DST has ended (in November)
       EndMainStem         = EndTribTwStr.strftime('%d%b%Y 0000')
       StartMainStem       = EndTw.strftime('%d%b%Y 0000')
       
    StartMainStemStor   = EndTw.strftime('%d%b%Y 0000')

    ProjectDateTimeStr  = CurDateTime.strftime('%m-%d-%Y 00:00') 
    #
    # Print the Start and End Time Window here
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, '\tProject Date and Time = ', ProjectDateTimeStr)
    #
    # Open database connection
    #
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('US/Central')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('MVS')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()   # Create a java.sql.Connection
    # Get list of pathnames in database
    DbPathnameList = CwmsDb.getPathnameList()
    #
    # Print all the cwms_ts_id here
    #outputDebug(debug, lineNo(), 'DbPathnameList = ', str(DbPathnameList))
    #
    # Create tables with a finite number of columns that will be written to the pdf file
    #
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)
    #
    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)
    #
    # Table1Footnote: Contains the footnotes for Table1
    Table1Footnote = PdfPTable(Table1Columns)
    #
    # BulletinFooter: Footer for the bulletin
    BulletinFooter = PdfPTable(FooterColumns)
    #
    # Title Block Columns
    TitleBlockColumnWidths = [10] * Table1Columns
    TitleBlockColumnWidths[0] = 12 # Adjust logo width 
    TitleBlockColumnWidths[-1] = 7 # Adjust seal width 
    TitleBlock.setWidths(TitleBlockColumnWidths)
    print '=================================================================================================Main_Script_END1'
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
    print '=================================================================================================Main_Script_END2'
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
        print '=================================================================================================Main_Script_END3'
        Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, StartMainStemStor, endTime, DbPathnameList)
        print '=================================================================================================Main_Script_END4'
    #
    # Create bulletin header that is repeated on each page
    #
    Table1.setHeaderRows(3)
    #
    Table1Footnote = table1Footnote(debug, Table1Footnote)
    #
    # Create Pdf file and write tables to create bulletin
    #
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
        BulletinPdf.add(Table1Footnote) # Add Table1's footnotes
        BulletinPdf.close()
        Writer.close()
        #
        print '=================================================================================================Main_Script_END6'
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
  
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	