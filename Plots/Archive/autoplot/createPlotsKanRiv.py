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
def plotData (dbi, flow1, flow2, flow3, flow4, flow5, titlename, width, height, jpgname, quality) :
#
	if debugOutput :
		print "Flow1 		= %s" % flow1
		print "Flow2 		= %s" % flow2
		print "Flow3 		= %s" % flow3
		print "Flow4 		= %s" % flow4
		print "Flow5 		= %s" % flow5
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname

# read the data from the CWMS Oracle database via the DBI from the ini data file
		flow1Data 	= dbi.get(flow1)
		flow2Data 	= dbi.get(flow2)
		flow3Data 	= dbi.get(flow3)
		flow4Data 	= dbi.get(flow4)
		flow5Data 	= dbi.get(flow5)
#
# get the data to be plotted		
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
#
		try :
			flow1DC = toLocalTime(flow1Data)
			flow2DC = toLocalTime(flow2Data)
			flow3DC = toLocalTime(flow3Data)
			flow4DC = toLocalTime(flow4Data)
			flow5DC = toLocalTime(flow5Data)
		except :
			return
#
# define the plot layout
		layout = Plot.newPlotLayout()
		topView = layout.addViewport()
		topView.addCurve("Y1",flow1DC)	
		topView.addCurve("Y1",flow2DC)
		topView.addCurve("Y1",flow3DC)	
		topView.addCurve("Y1",flow4DC)		
		topView.addCurve("Y1",flow5DC)
		plot.configurePlotLayout(layout)
		plot.showPlot()
		plot.setLegendLabelText(flow1DC,"Ft. Riley-Kansas")
		plot.setLegendLabelText(flow2DC,"Wamego-Kansas")
		plot.setLegendLabelText(flow3DC,"Topeka-Kansas")
		plot.setLegendLabelText(flow4DC,"Lecompton-Kansas")
		plot.setLegendLabelText(flow5DC,"DeSoto-Kansas")
                plot.setLegendBackground("gray")
#
# set line color, style, width for time series ..... flow1Data
                lineColor1=plot.getCurve(flow1Data)
                lineColor1.setLineColor("black")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 1. )
#
# set line color, style, width for time series ..... flow2Data
                lineColor2=plot.getCurve(flow2Data)
                lineColor2.setLineColor("blue")
                lineColor2.setLineStyle("Dash")
                lineColor2.setLineWidth( 2. )
#
# set line color, style, width for time series ..... flow3Data
                lineColor3=plot.getCurve(flow3Data)
                lineColor3.setLineColor("red")
                lineColor3.setLineStyle("Dot")
                lineColor3.setLineWidth( 2. )
#
# set line color, style, width for time series ..... flow4Data
                lineColor4=plot.getCurve(flow4Data)
                lineColor4.setLineColor("gray")
                lineColor4.setLineStyle("Dash Dot")
                lineColor4.setLineWidth( 2. )
#
# set line color, style, width for time series ..... flow5Data
                lineColor5=plot.getCurve(flow5Data)
                lineColor5.setLineColor("black")
                lineColor5.setLineStyle("Dash Dot-Dot")
                lineColor5.setLineWidth( 2. )
#
# customize the first graph on the plot (elev) ... viewport0		
		viewport0=plot.getViewport(0)
#
# customize the left y axis label on viewport0
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
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataKanRiv.ini"
timeSpan    = 12 * 24 * 60 # minutes
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
		iniFlow1 	= iniFile.readline().strip()
		iniFlow2 	= iniFile.readline().strip()
		iniFlow3 	= iniFile.readline().strip()
		iniFlow4 	= iniFile.readline().strip()
		iniFlow5 	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	
	plotData(dbi, iniFlow1, iniFlow2, iniFlow3, iniFlow4, iniFlow5, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
