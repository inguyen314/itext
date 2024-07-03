# -------------------------------------------------------------------
# Required imports
# -------------------------------------------------------------------
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



CurDateTime = datetime.datetime.now()

print 'CurDateTime = ' + str(CurDateTime)

CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm

print 'CurDateTimeStr = ' + str(CurDateTimeStr)

ArchiveDateTimeStr  = CurDateTime.strftime('%d%m%Y') # Last updated time for bulletin formatted as dd-mm-yyyy

print 'ArchiveDateTimeStr = ' + str(ArchiveDateTimeStr)


Date = datetime.datetime.now() # Current date
print 'Date = ' + str(Date)

StartTw             = Date - datetime.timedelta(2) # datetime.timedelta(2) = minus two days
print 'StartTw = ' + str(StartTw)
StartTw             = StartTw - datetime.timedelta(hours=5) # Minus 5 Hours from StartTw
print 'StartTw = ' + str(StartTw)
StartTwStr          = StartTw.strftime('%d%b%Y 0600') # Hard Coded Time to 0600 Format 21Aug2022 0600
print 'StartTwStr = ' + str(StartTwStr)

EndTw               = Date - datetime.timedelta(1)
print 'EndTw = ' + str(EndTw)
EndTribTwStr        = Date
print 'EndTribTwStr = ' + str(EndTribTwStr)
EndTribTwStr        = EndTribTwStr - datetime.timedelta(hours=5)
print 'EndTribTwStr = ' + str(EndTribTwStr)
EndTwStr            = EndTribTwStr.strftime('%d%b%Y 0600')
print 'EndTwStr = ' + str(EndTwStr)



