'''
Author: Jessica Batterman and Ben Sterbenz
Last Updated: 8-17-2021
Description: Create the Omaha District Salt Creek Bulletin
'''

#
# Imports
#
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
import os, sys, inspect, datetime, time, DBAPI, java

# -------------------------------------------------------------------
# Import database pathnames and plotting functions
# -------------------------------------------------------------------
# Determine if OS is Windows or Unix. Use PC pathnames if OS is Windows
OsName = java.lang.System.getProperty("os.name").lower()
print 'OsName = ', OsName
if OsName[ : 7] == 'windows' : 
    # PC pathnames
    CronjobsDirectory = "C:\\Users\\G6EDXBWS\\Documents\\cronjobs\\" # Used in the properties file to create pathname for Seals and Symbols
    BulletinsDirectory = CronjobsDirectory + 'Bulletins\\'
    ScriptDirectory = BulletinsDirectory + 'NWO_Salts\\'
    BulletinFilename = BulletinsDirectory + 'NWO_Salts_Bulletin.pdf'
    CsvFilename = BulletinsDirectory + 'NWO_Salts_Bulletin.csv'
    BulletinPropertiesPathname = ScriptDirectory + 'NWO_Salts_Bulletin_Properties.txt'
else :
    # Server pathnames
    ScriptDirectory = os.path.dirname(os.path.realpath(__file__))
    PathList = ScriptDirectory.split('/')
    BulletinsDirectory = '/'.join(PathList[: -1]) + '/'
    CronjobsDirectory = '/'.join(PathList[: -2]) + '/'
    ScriptDirectory += '/'
    BulletinFilename = BulletinsDirectory + 'NWO_Salts_Bulletin.pdf'
    CsvFilename = BulletinsDirectory + 'NWO_Salts_Bulletin.csv'
    BulletinPropertiesPathname = ScriptDirectory + 'NWO_Salts_Bulletin_Properties.txt'    

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
##################################################################################################################################

#
# Functions
#

#
# createCell Function   : Creates a PdfPCell for tables
# Author/Editor         : Ryan Larsen and Ben Sterbenz
# Last updated          : 8-17-2021
#
def createCell( debug,                  # Set to True to print all debug statements
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
    CellData = Phrase(Chunk('Project', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [1, 0.5, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1-4 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Project Information', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 4, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color3], 
        [1, 0.5, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 5-9 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Current Data', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 5, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color3], 
        [1, 0.5, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 10-12 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Occupied Storage', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [1, 1, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData
    
    # Blank Column 0 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk(' ', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 1], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1-2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Elevations (ft)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 2, 
        Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], 
        [Color2, Color2, Color2, Color3], [0.25, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3-4 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Cumulative Stor (ac-ft)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 2, 
        Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 5 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Elev\n(ft)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [0.25, 0.25, 0.25, 0.5], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 6 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Daily Elev Change (ft)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 7 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Storage\n(ac-ft)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 8 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Inflow\n(cfs)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 9 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Release\n(cfs)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 10 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('MP\n(%)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, 
        TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], [0.25, 0.25, 0.25, 0.5], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 11 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('FC\n(ac-ft)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 12 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('FC\n(%)', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, 2, TableLayoutDict['Table1']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        [0.25, 1, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData

    # Column 1 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('MP', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color3], [0.25, 0.25, 0.25, 0.5], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('FC', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('MP', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 4 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('FC', TableLayoutDict['Table1']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], 
        [Color2, Color3, Color2, Color2], [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table1']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ',\n'
    CsvData += UnformattedData

    return Table, CsvData

#
# table2Heading Function    : Creates the heading for Table2 in the bulletin
# Author/Editor             : Jessica Batterman
# Last updated              : 12-03-2020
#
def table2Heading(  debug,  # Set to True to print all debug statements
                    Table,  # PdfPTable object
                    CsvData # Csv data
                    ) :
    #
    # Create Table2 Heading 
    #
    # Column 0-2 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Streamgage', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [1, 0.5, 0.25, 1], TableLayoutDict['Table2']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3-5 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Current Data', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], [Color2, Color3, Color2, Color3], 
        [1, 0.5, 0.25, 0.5], TableLayoutDict['Table2']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 6-9 Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('NWS Flood Stages', Font3))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], 4, Element.ALIGN_CENTER, 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [1, 1, 0.25, 0.5], TableLayoutDict['Table2']['VariableBorders'], Color5)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData
    
    # Column 0 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Name', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], Element.ALIGN_LEFT, 
        Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 0.25, 0.25, 1], TableLayoutDict['Table2']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 1 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Map \nLabel', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], 
        [Color2, Color2, Color2, Color2], [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], 
        Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    '''# Column 2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Map \nLocation', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData'''

    # Column 2 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Stage \n(ft)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [0.25, 0.25, 0.25, 0.5], TableLayoutDict['Table2']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 3 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Daily Stage \nChange (ft)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 0.25, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 4 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Flow \n(cfs)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color3, Color2, Color2], 
        [0.25, 0.5, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], Color6)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 5 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Action \n(ft)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color3], 
        [0.25, 0.25, 0.25, 0.5], TableLayoutDict['Table2']['VariableBorders'], Color11)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 6 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Minor \n(ft)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 0.25, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], Color13)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 7 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Moderate \n(ft)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 0.25, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], Color12)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    # Column 8 Sub-Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    CellData = Phrase(Chunk('Major \n(ft)', TableLayoutDict['Table2']['TextFont']))
    Cell = createCell(debug, CellData, TableLayoutDict['Table2']['RowSpan'], TableLayoutDict['Table2']['ColSpan'], 
        Element.ALIGN_CENTER, Element.ALIGN_BOTTOM, TableLayoutDict['Table2']['CellPadding'], [Color2, Color2, Color2, Color2], 
        [0.25, 1, 0.25, 0.25], TableLayoutDict['Table2']['VariableBorders'], Color14)
    Table.addCell(Cell)
    # Add data to CsvData.
    UnformattedData = str(CellData[0]).replace(',', '') + ','
    CsvData += UnformattedData

    return Table, CsvData
    
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

    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        PublicName = retrievePublicName(debug, conn, project)
        if project in [ 'SC02', 'SC09', 'SC12', 'SC14' ]:
            append = '*'
            BulletinName = PublicName.replace(' & Reservoir', '')
            BulletinName += append
        else: BulletinName = PublicName.replace(' & Reservoir', '')
        outputDebug(debug, lineNo(), 'Creating %s row' % BulletinName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == DataBlocks[-1] and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False
        
        # Reset TotalColSpan to 0
        TotalColSpan = 0
        
        for data in DataOrder1 :
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)

            # Get column number
            ColumnKey = 'Column%d' % DataOrder1.index(data)

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
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(BulletinName, TextFont))
                
                # Store value to DataDict
                DataBlockDict['DataBlocks'][TableDataName][project][data] = BulletinName

                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 1]
                else : BorderWidths = [0.25, 0.5, 0.25, 1]
                CellPadding = [0, 2, 2, 3]                
            # MP elevation
            elif data == 'TopOfConsZoneElev' :
                try :
                    if project in [ 'SC02', 'SC09', 'SC12', 'SC14' ]:
                        ElevZoneFullName = TopOfInactZone % project
                            # Create a formatted string that will be added to the table
                            # Retrieve reservoir elevation zone value. Section 7 and Corps projects have varying names. First try the TopOfJointZone. Then try
                            #   the TopOfConsZone. Then try the TopOfInactZone if the project is in a specific list. If that does not work, raise an 
                            #   exception so the value is shown as missing.
                        try :
                            MpElevZone = retrieveLocationLevel(debug, conn, CwmsDb, ElevZoneFullName)
                            outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)
                        except :
                            
                            raise ValueError
                            
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MpElevZone, TextFont))
                    else:
                        ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                        
                            # Retrieve reservoir elevation zone value. Section 7 and Corps projects have varying names. First try the TopOfJointZone. Then try
                            #   the TopOfConsZone. Then try the TopOfInactZone if the project is in a specific list. If that does not work, raise an 
                            #   exception so the value is shown as missing.
                        try :
                            MpElevZone = retrieveLocationLevel(debug, conn, CwmsDb, ElevZoneFullName)
                            outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)
                        except :
                            try :
                                ElevZoneFullName = TopOfConsZone % project
                                MpElevZone = retrieveLocationLevel(debug, conn, CwmsDb, ElevZoneFullName)
                                outputDebug(debug, lineNo(), '%s Mp Elev Zone = ' % ElevZoneFullName, MpElevZone)
                            except :
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
                    ElevZoneFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    
                    # Retrieve reservoir elevation zone value
                    FcElevZone = retrieveLocationLevel(debug, conn, CwmsDb, ElevZoneFullName)
                    
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
                    if MpElevZone == Null :
                        MpStorZone = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(MpStorZone, TextFont))
                    elif MpElevZone == Missing :
                        raise ValueError
                    else :
                        # Rate the elevation value
                        System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                            #   CCP currently uses (11-17-2017) and seems to work the fastest
                        ElevStorPdc = RatingSet.fromDatabase(conn, DataBlockDict['DataBlocks'][TableDataName]['RatingCurve'] % project)
                        PdcTime = int(TimeSinceEpoch * 1000) # Time used for retrieving the Pdc storage curves
                        ElevStorPdc.setDefaultValueTime(PdcTime)
                        MpStorZone = ElevStorPdc.rate(MpElevZone)
                        MpStorZone = round(MpStorZone, 0)
                        
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(MpStorZone)), TextFont))
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
                    if FcElevZone == Null :
                        FcStorZone = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
                    elif FcElevZone == Missing :
                        raise ValueError
                    else :
                        # Rate the elevation value
                        System.setProperty('hec.data.cwmsRating.RatingSet.databaseLoadMethod', 'reference') # Load methods can be 'eager', 'lazy', or 'reference'. 'reference' is what 
                                                                                                            #   CCP currently uses (11-17-2017) and seems to work the fastest
                        ElevStorPdc = RatingSet.fromDatabase(conn, DataBlockDict['DataBlocks'][TableDataName]['RatingCurve'] % project)
                        PdcTime = int(TimeSinceEpoch * 1000) # Time used for retrieving the Pdc storage curves
                        ElevStorPdc.setDefaultValueTime(PdcTime)
                        FcStorZone = ElevStorPdc.rate(FcElevZone)
                        FcStorZone = round(FcStorZone, 0)
                        
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(FcStorZone)), TextFont))
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
                    Tsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName][data] % project).getData()
                    PrevElev = Tsc.values[-1] # Previous day's midnight value
                    Prev2xElev = Tsc.values[0] # 2 days previous midnight value
                    
                    # If previous day's value is missing raise an exception and using the missing value
                    if PrevElev == Constants.UNDEFINED : raise ValueError
                    elif Prev2xElev == Constants.UNDEFINED : Prev2xElev = Missing
                    
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

                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.5]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
            # Daily elevation change
            elif data == 'ElevChange' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['Elevation'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['Elevation2x'] == Missing :
                        raise ValueError

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
                    DlyElevChange = Missing
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
                    CwmsDb.setTimeZone('Etc/GMT+6')
                            
                    TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    Tsc = CwmsDb.get(TscPathname, TrimTwStr, EndTwStr) # Use TrimTwStr for daily data. Some daily data is ~1Day which won't return missing values
                                                                       #    since they are irregular time series. By using TrimTwStr, only 1 value will be returned
                    Value = Tsc.values[-1]
                    Value = round(Value, 0)
                    
                    # Reset database time zone to US/Central
                    CwmsDb.setTimeZone('US/Central')
                    
                    # If value is missing raise an exception and using the missing value
                    if Value == Constants.UNDEFINED : raise ValueError

                    # Create a formatted string that will be added to the table
                    if Value == Null : CellData = Phrase(Chunk(Null, TextFont))
                    else :  CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(Value)), TextFont)) # Uses Java formatting to get the 1000s comma separator
                except :
                    Value = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), Value)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = Value

                # Change default cell properties
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
                if data == 'FlowTotal' :
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
                        if DataBlockDict['DataBlocks'][TableDataName][project]['Storage'] == Missing : 
                            raise ValueError
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
                        if DataBlockDict['DataBlocks'][TableDataName][project]['Storage'] == Missing : 
                            raise ValueError
                        
                        else : 
                            FcStor = DataBlockDict['DataBlocks'][TableDataName][project]['Storage'] - DataBlockDict['DataBlocks'][TableDataName][project]['TopOfConsZoneStor']
    
                        if FcStor < 0. : FcStor = 0.
    
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(FcStor)), TextFont)) # Uses Java formatting to get the 1000s comma separator
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
                        elif DataBlockDict['DataBlocks'][TableDataName]['GreenStor'] < FcStorPercent : BackgroundColor = Color8 # Green
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

            # Add data to CsvData. Break data loop if column span reaches the total number columns before each data piece has been added to that table
            outputDebug(debug, lineNo(), 'ColSpan = ', ColSpan)
            TotalColSpan += ColSpan
            UnformattedData = str(CellData[0]).replace(',', '')
            CsvData += UnformattedData
            CsvData += ','
            outputDebug(debug, lineNo(), 'TotalColSpan = ', TotalColSpan)
            if TotalColSpan == Table.getNumberOfColumns() :
                CsvData += '\n'
                break
            
    return Table, CsvData

#
# table2Data Function   : Creates the Data1 block for Table2 in the bulletin
# Author/Editor         : Jessica Batterman
# Last updated          : 12-07-2020
#
def table2Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName,   # String name for data section of table
                CsvData,    # Csv data   
                ) :
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)

    # Set variable x = 0 to use as an index for arrays in Table2 properties
    x = 0

    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :
        # Retrieve Public Name and store it to the DataBlockDict
        BulletinName = retrievePublicName(debug, conn, project)
        outputDebug(debug, lineNo(), 'Creating %s row' % BulletinName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == DataBlocks[-1] and project == 'ALNE' :
            LastProject = True
        else : LastProject = False
        
        # Reset TotalColSpan to 0
        TotalColSpan = 0
        
        for data in DataOrder2 :
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)

            # Get column number
            ColumnKey = 'Column%d' % DataOrder2.index(data)

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
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(BulletinName, TextFont))
                
                # Store value to DataDict
                DataBlockDict['DataBlocks'][TableDataName][project][data] = BulletinName

                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color2, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 1]
                else : BorderWidths = [0.25, 0.25, 0.25, 1]
                CellPadding = [0, 2, 2, 3]                

            # Project Base Location
            elif data == 'BaseLocation' :
                try :
                    Label = DataBlockDict['DataBlocks'][TableDataName][data][x]
                    
                    outputDebug(debug, lineNo(), '%s Base Location = ' % project, Label)

                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Label, TextFont))
                    
                except :
                    Label = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                
                # Store value to DataDict
                DataBlockDict['DataBlocks'][TableDataName][project][data] = Label
                
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_CENTER
                BorderColors = [Color2, Color2, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 0.25]
                else : BorderWidths = [0.25, 0.5, 0.25, 0.25]

            # Project Map Location
            elif data == 'RelativeLocation' :
                try :
                    MapLoc = DataBlockDict['DataBlocks'][TableDataName][data][x]
                    
                    outputDebug(debug, lineNo(), '%s Map Location = ' % project, MapLoc)
                    
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(MapLoc, TextFont))
                    
                except :
                    MapLoc = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                    
                # Store value to DataDict
                DataBlockDict['DataBlocks'][TableDataName][project][data] = MapLoc
                
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_CENTER
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 0.25]
                else : BorderWidths = [0.25, 0.5, 0.25, 0.25]
                
            # Current Stage
            elif data == 'Stage' :
                try :
                    Tsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName][data] % project).getData()
                    PrevSt = Tsc.values[-1] # Previous day's midnight value
                    Prev2xSt = Tsc.values[0] # 2 days previous midnight value
                
                    # If previous day's value is missing raise an exception and using the missing value
                    if PrevSt == Constants.UNDEFINED : raise ValueError
                    elif Prev2xSt == Constants.UNDEFINED : Prev2xSt = Missing

                    # Pull NWS flood levels and Max of Record to compare to current stage
                    try :
                        ActionStage = retrieveLocationLevel(debug, conn, CwmsDb, DataBlockDict['DataBlocks'][TableDataName]['StageNwsActionElev'] % project)
                    except : ActionStage = Missing
                    try :
                        MinorStage = retrieveLocationLevel(debug, conn, CwmsDb, DataBlockDict['DataBlocks'][TableDataName]['StageNwsFloodElev'] % project)
                    except : MinorStage = Missing
                    try :
                        ModerateStage = retrieveLocationLevel(debug, conn, CwmsDb, DataBlockDict['DataBlocks'][TableDataName]['StageNwsModFloodElev'] % project)
                    except : ModerateStage = Missing
                    try :
                        MajorStage = retrieveLocationLevel(debug, conn, CwmsDb, DataBlockDict['DataBlocks'][TableDataName]['StageNwsMajFloodElev'] % project)
                    except : MajorStage = Missing
                    try :
                        MaxRecord = retrieveLocationLevel(debug, conn, CwmsDb, StageMaxOfRecord % project)
                    except : MaxRecord = Missing
                    
                    # Format cell to match NWS flood stage level it is in, if needed
                    if PrevSt > ActionStage : BackgroundColor = Color11 # Yellow
                    if PrevSt > MinorStage : BackgroundColor = Color13 # Orange
                    if PrevSt > ModerateStage : BackgroundColor = Color12 # Red
                    if PrevSt > MajorStage : BackgroundColor = Color14 # Purple

                    # Create a formatted string that will be added to the table
                    if PrevSt > MaxRecord :
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevSt + '*', TextFont))
                    else :
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevSt, TextFont))
                    
                except :
                    PrevSt, Prev2xSt = Missing, Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                    
                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevSt)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevSt
                DataBlockDict['DataBlocks'][TableDataName][project][data + '2x'] = Prev2xSt

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.5]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.5]

            # Stage Change
            elif data == 'StageChange' :
                try :
                    if DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] == Missing or \
                        DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x'] == Missing :
                        raise ValueError

                    DlyStChange = DataBlockDict['DataBlocks'][TableDataName][project]['Stage'] - DataBlockDict['DataBlocks'][TableDataName][project]['Stage2x']

                    # Format the value. If the daily stage change is greater than 1.0 foot, bold the font and set the background color to red
                    if DlyStChange > 1. :
                        # Change default cell properties
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyStChange, Font5))
                        BackgroundColor = Color10 # Red
                    else :
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyStChange, TextFont))
                        
                except :
                    DlyStChange = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), DlyStChange)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = DlyStChange

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25]

            # Current Flow
            elif data == 'Flow' :
                # First try grabbing version Raw-CODWR.  If ts doesn't exist, use Best-NWDM
                try :
                    FlowTsFullName = DataBlockDict['DataBlocks'][TableDataName][data] % project
                    FlowTsValid = FlowTsFullName in CwmsDb.getPathnameList()
                    if FlowTsValid == 0 :
                        FlowTsFullName = FlowInstHourBestNwdm % project
                    Tsc = CwmsDb.read(FlowTsFullName).getData()
                    PrevFlow = Tsc.values[-1] # Previous day's midnight value
                    
                    # If previous day's value is missing raise an exception and using the missing value
                    if PrevFlow == Constants.UNDEFINED : raise ValueError 
                    
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(PrevFlow)), TextFont)) # Uses Java formatting to get the 1000s comma separator
                    
                except :
                    PrevFlow = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                    
                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevFlow)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevFlow
                
                # Change default cell properties
                BorderColors = [Color2, Color3, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.5, 1, 0.25]
                else : BorderWidths = [0.25, 0.5, 0.25, 0.25]

            # NWS Action Stage
            elif data == 'StageNwsActionElev' :
                if project in ['PCCO'] :
                    ActionStage = Null
                    # Create a formatted string that will be added to the table
                    CellData =Phrase(Chunk(Null, TextFont))
                elif ActionStage == Missing :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                else :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % ActionStage, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), ActionStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = ActionStage

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.5]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.5]
                
            # NWS Minor Flood Stage
            elif data == 'StageNwsFloodElev' :
                if project in ['PCCO'] :
                    MinorStage = Null
                    # Create a formatted string that will be added to the table
                    CellData =Phrase(Chunk(Null, TextFont))
                elif MinorStage == Missing :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                else :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MinorStage, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), MinorStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = MinorStage

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25]
                
            # NWS Moderate Flood Stage
            elif data == 'StageNwsModFloodElev' :
                if project in ['ACNE', 'SLNE'] :
                    ModerateStage = Null
                    # Create a formatted string that will be added to the table
                    CellData =Phrase(Chunk(Null, TextFont))
                elif ModerateStage == Missing :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                else :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % ModerateStage, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), ModerateStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = ModerateStage

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 0.25, 1, 0.25]
                else : BorderWidths = [0.25, 0.25, 0.25, 0.25]
                
            # NWS Major Flood Stage
            elif data == 'StageNwsMajFloodElev' :
                if project in ['ACNE', 'AWNE', 'SLNE'] :
                    MajorStage = Null
                    # Create a formatted string that will be added to the table
                    CellData =Phrase(Chunk(Null, TextFont))
                elif MajorStage == Missing :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))
                else :
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % MajorStage, TextFont))

                # Store value to DataDict
                outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), MajorStage)
                DataBlockDict['DataBlocks'][TableDataName][project][data] = MajorStage

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color2]
                if LastProject : BorderWidths = [0.25, 1, 1, 0.25]
                else : BorderWidths = [0.25, 1, 0.25, 0.25]
                
            # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
            Table.addCell(Cell)

            # Add data to CsvData. Break data loop if column span reaches the total number columns before each data piece has been added to that table
            outputDebug(debug, lineNo(), 'ColSpan = ', ColSpan)
            TotalColSpan += ColSpan
            UnformattedData = str(CellData[0]).replace(',', '')
            CsvData += UnformattedData
            CsvData += ','
            outputDebug(debug, lineNo(), 'TotalColSpan = ', TotalColSpan)
            if TotalColSpan == Table.getNumberOfColumns() :
                CsvData += '\n'
                break
                    
        # Increase variable x to use as an index for other arrays in Table2 properties
        x = x + 1

    return Table, CsvData

#
# table3Data Function   : Creates the Data1 block for Table3 in the bulletin
# Author/Editor         : Jessica Batterman
# Last updated          : 12-08-2020
#
def table3Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName,   # String name for data section of table
                CsvData,    # Csv data   
                ) :
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)
    
    
    # Add Table3 Image
    Img = Image.getInstance(Table3Image)
    Img.scalePercent(8.5)
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Img, 60, 3, Element.ALIGN_CENTER, 
        TableLayoutDict['Table3']['VerticalAlignment'], TableLayoutDict['Table3']['CellPadding'], TableLayoutDict['Table3']['BorderColors'], 
        TableLayoutDict['Table3']['BorderWidths'], TableLayoutDict['Table3']['VariableBorders'], TableLayoutDict['Table3']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
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

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('MP = Multipurpose', Font6)), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('FC = Flood Control', Font6)), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)
    
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('-- = N/A Data', Font6)), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('M = Missing Data', Font6)), TableLayoutDict['Table1']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('All project elevations are reported in local project datums.', 
        Font6)), TableLayoutDict['Table1']['RowSpan'], 5, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)
    
    Cell = createCell(debug, Phrase(Chunk('* = Project has no Designated Multipurpose Zone, Sediment Zone is Displayed.', 
        Font6)), TableLayoutDict['Table1']['RowSpan'], 7, Element.ALIGN_LEFT, TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # Add a blank line to the table footer to separate the footer from Table2
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font6)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(10)
    TableFootnote.addCell(Cell)

    return TableFootnote

#
# table2Footnote Function   : Creates the footer for Table2 in the bulletin
# Author/Editor             : Jessica Batterman
# Last updated              : 12-03-2020
#
def table2Footnote( debug,          # Set to True to print all debug statements
                    TableFootnote,  # PdfPTable object
                    ) :

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('-- = N/A Data',  Font6)), TableLayoutDict['Table2']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('M = Missing Data',  Font6)), TableLayoutDict['Table2']['RowSpan'], 
        2, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('* Stage value is above the Maximum of Record.',  Font6)), TableLayoutDict['Table2']['RowSpan'], 
        6, Element.ALIGN_LEFT, TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TableFootnote.addCell(Cell)

    # Add a blank line to the table footer to separate the footer from Table3
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font6)), TableLayoutDict['Table2']['RowSpan'], Table2Columns, TableLayoutDict['Table2']['HorizontalAlignment'], 
        TableLayoutDict['Table2']['VerticalAlignment'], TableLayoutDict['Table2']['CellPadding'], TableLayoutDict['Table2']['BorderColors'], 
        TableLayoutDict['Table2']['BorderWidths'], TableLayoutDict['Table2']['VariableBorders'], TableLayoutDict['Table2']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(10)
    TableFootnote.addCell(Cell)

    return TableFootnote

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

##################################################################################################################################
##################################################################################################################################

#
# Main Script
#
try :
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

        StartTw             = Date - datetime.timedelta(2)
        StartTwStr          = StartTw.strftime('%d%b%Y 2400') # Start of time window for the database formatted as ddmmmyyyy 2400
        EndTw               = Date - datetime.timedelta(1)
        TrimTwStr           = EndTw.strftime('%d%b%Y 0100') # Trimmed time window for the database formatted as ddmmmyyyy 0100. Used for daily time series
        EndTwStr            = EndTw.strftime('%d%b%Y 2400') # End of time window for the database formatted as ddmmmyyyy 2400
        ProjectDateTimeStr  = CurDateTime.strftime('%m-%d-%Y 00:00') # Project date and time for bulletin formatted as mm-dd-yyyy 2400
        TimeSinceEpoch      = mktime(TimeObj) # Time object used for ratings
        outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, 
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

        # Table1Footnote: Contains the footnotes for Table1
        Table1Footnote = PdfPTable(Table1Columns)

        # Table2: Contains all data and data headings
        Table2 = PdfPTable(Table2Columns)

        # Table2Footnote: Contains the footnotes for Table2
        Table2Footnote = PdfPTable(Table2Columns)

        # Table3: Contains all data and data headings
        Table3 = PdfPTable(Table3Columns)

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
        DataOrder1, DataOrder2, DataOrder3, Table1ColumnWidths, Table2ColumnWidths, Table3ColumnWidths = [], [], [], [], [], []
        for column in range(Table1Columns) :
            # Column Key
            ColumnKey = 'Column%d' % column
            
            DataOrder1.append(TableLayoutDict['Table1'][ColumnKey]['Key'])
            Table1ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey]['ColumnWidth'])

        for column in range(Table2Columns) :
            # Column Key
            ColumnKey = 'Column%d' % column
            
            DataOrder2.append(TableLayoutDict['Table2'][ColumnKey]['Key'])
            Table2ColumnWidths.append(TableLayoutDict['Table2'][ColumnKey]['ColumnWidth'])

        Table3ColumnWidths.append(131)
        Table3ColumnWidths.append(15)
        for column in range(Table3Columns - 2) :
            # Column Key
            ColumnKey = 'Column%d' % column
            
            DataOrder3.append(TableLayoutDict['Table3'][ColumnKey]['Key'])
            Table3ColumnWidths.append(TableLayoutDict['Table3'][ColumnKey]['ColumnWidth'])
            
        Table1.setWidths(Table1ColumnWidths)
        Table2.setWidths(Table2ColumnWidths)
        Table3.setWidths(Table3ColumnWidths)

        # Table1Footnote Columns
        Table1Footnote.setWidths([10] * Table1Columns)

        # Table2Footnote Columns
        Table2Footnote.setWidths([10] * Table2Columns)

        # BulletinFooter Columns
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
        DataBlocks = ['Data1']
        for DataBlock in DataBlocks :
            Table1, CsvData = table1Data(debug, Table1, 'Table1', DataBlock, CsvData)

        #
        # Add data to the table footnotes for Table1
        #
        Table1Footnote = table1Footnote(debug, Table1Footnote)

        #
        # Add data to the heading for Table2
        #
        Table2, CsvData = table2Heading(debug, Table2, CsvData)

        #
        # Add data to the data blocks for Table2
        #
        DataBlocks = ['Data1']
        for DataBlock in DataBlocks :
            Table2, CsvData = table2Data(debug, Table2, 'Table2', DataBlock, CsvData)

        #
        # Add data to the table footnotes for Table2
        #
        Table2Footnote = table2Footnote(debug, Table2Footnote)

        #
        # Add data to the data blocks for Table3
        #
        DataBlocks = ['Data1']
        for DataBlock in DataBlocks :
            Table3, CsvData = table3Data(debug, Table3, 'Table3', DataBlock, CsvData)

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
        BulletinPdf.add(Table2) # Add Table2 to the PDF
        BulletinPdf.add(Table2Footnote) # Add Table2's footnotes
        BulletinPdf.add(Table3) # Add Table3 to the PDF
        BulletinFooter.setTotalWidth(612 - 48) # Total width is 612 pixels (8.5 inches) minus the left and right margins (24 pixels each)
        # Build a footer with page numbers and add to PDF
        BulletinFooter = bulletinFooter(debug, BulletinFooter)
        BulletinFooter.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent())
            
        # 
        # Create csv file
        #
        CsvFile = open(CsvFilename, 'w')
        CsvFile.write(CsvData)
    except Exception, e : 
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
    except java.lang.Exception, e : 
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
finally :
    try : CwmsDb.done()
    except : pass
    try : conn.close()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass
    try : CsvFile.close()
    except : pass
    try : BulletinTsFile.close()
    except : pass
    try : BulletinProperties.close()
    except : pass
