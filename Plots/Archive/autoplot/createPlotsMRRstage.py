from hec.script import *
from hec.script.Constants import *   # for TRUE & FALSE
from hec.heclib.util import HecTime
import sys, time
import DBAPI
from hec.io import*

#----------------------------------------------------------#
# define a function to adjust retrieved data to local time # from M. Perryman 8/2/07
#----------------------------------------------------------#
def toLocalTime(tsc) :
# get the local time zone offset from UTC in minutes
	tzOffset = -time.timezone / 60
# use the startTime to determine offset of entire time series container
	hecTime = HecTime()
	hecTime.set(tsc.startTime)
	if time.localtime(hecTime.getTimeInMillis() / 1000)[-1] :
# startTime is in daylight savings time
		tzOffset += 60
# adjust the times
	tsc.startTime 	+= tzOffset
	tsc.endTime	+= tzOffset
	for i in range(len(tsc.times)) :
		tsc.times[i] += tzOffset
	return tsc
	
#-----------------------------------------#
# define a function to generate the plots #
#-----------------------------------------#
def plotData (dbi, stage, titlename, width, height, jpgname, quality) :

	if debugOutput :
		print "Stage 		= %s" % stage
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname
#
# read the data from the CWMS Oracle database via the DBI from the ini data file
		stageData = dbi.get(stage)
# define the plot, add data, etc.		
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
		try :
			plot.addData(stageData)
		except :
			return
		plot.showPlot()
#
# set line color, style, width for time series stage
                lineColor1=plot.getCurve(stageData)
                lineColor1.setLineColor("red")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 1. )
#                lineColor1.setSymbolsVisible(TRUE)
#                lineColor1.setSymbolsAutoInterval(FALSE)
#                lineColor1.setSymbolInterval(24)
#                lineColor1.setSymbolLineColor("red")
#                lineColor1.setSymbolType("Open Diamond")
#                lineColor1.setSymbolSize( 10. )
#
# customize the first graph on the plot (first line in the ini data file) ... stage ... viewport0		
		viewport0=plot.getViewport(0)
# customize the y axis label
		yaxislabel=viewport0.getAxisLabel("Y1")
		yaxislabel.setForeground("red")	
		yaxislabel.setFont("Arial,Normal,20")	
#
# customize the title of the plot (fourth line in the ini data file)
		title=plot.getPlotTitle()
                title.setForeground("darkblue")
                title.setFontFamily("Arial")
                title.setFontStyle("Normal")
                title.setFontSize(20)
                title.setText ( titlename )
                title.setDrawTitleOn()

# resizing plots - per Mike Perryman email 3/3/17 so plot title is correct

		size = plot.getSize()
		plot.setSize(size.width-1,size.height-1)
		plot.setSize(size.width, size.height)
#
		fileName = '%s.jpg' % jpgname
		plot.saveToJpeg (fileName, quality)
		
#
# program information
#
dbiName     = "foo"
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataMRRstage.ini"
timeSpan    = 18 * 24 * 60 # minutes
timeSpanFcast=2 * 24 * 60 # minutes
plotWidth   = 640
plotHeight  = 480
plotQuality = 100 # range of 0 (crappy) to 100 (great, but larger file)
debugOutput = TRUE
officeID='NWDM'

#
# initialize variables
#
if debugOutput :
	print "Using time span of %d minutes (%f hours, or %f days)" % (timeSpan, timeSpan / 60, timeSpan / 60 / 24)
hecTime = HecTime()
hecTime.setTimeInMillis(long(time.time() * 1000))
endTime = hecTime.dateAndTime(4).replace(",",  "").replace(":",  "")
hecTime.add(timeSpanFcast)
endTime = hecTime.dateAndTime(4).replace(",",  "").replace(":",  "")
hecTime.subtract(timeSpan)
startTime = hecTime.dateAndTime(4).replace(",",  "").replace(":",  "")
if debugOutput :
	print "Time window = %s --> %s" % (startTime, endTime)

if debugOutput :
	print "Opening DBI %s" % dbiName
try :
	dbi = DBAPI.open()
	if not dbi : raise Exception

	dbi.setTimeWindow(startTime, endTime)
	dbi.setOfficeId(officeID)
        dbi.setTimeZone('US/Central')

except :
	print "Could not open DBI %s, exiting." % dbiName
	sys.exit(-1)

if debugOutput :
	print "Opening ini file %s" % iniFilename
try :
	iniFile = open(iniFilename, "r")
except :
	print "Could not open ini file %s, exiting." % iniFilename
	try    : dbi.close()
	except : pass
	sys.exit(-1)
	

#
# start looping through the ini file.  read each line for stage, then station1, then
# title and filename.  then call the plotting routine using the oracle paths, title and filename
# to plot as arguments
#
# note: the while loop ends with the 'break' statement when readline read til it sees "end"
#
while 1 :
	try :	
		iniStage 	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	
	plotData(dbi, iniStage, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
