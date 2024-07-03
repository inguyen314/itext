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
def plotData (dbi, Flow, FlowD1, FlowD3, FlowD5, FlowD7, titlename, width, height, jpgname, quality) :

	if debugOutput :
		print "Flow-River	= %s" % Flow
		print "Flow-D1		= %s" % FlowD1
		print "Flow-D3		= %s" % FlowD3
		print "Flow-D5		= %s" % FlowD5
		print "Flow-D7		= %s" % FlowD7
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname
#
# read the data from the CWMS Oracle database via the DBI from the ini data file
		FlowData 	= dbi.get(Flow)
		FlowD1Data 	= dbi.get(FlowD1)
		FlowD3Data 	= dbi.get(FlowD3)
		FlowD5Data 	= dbi.get(FlowD5)
		FlowD7Data 	= dbi.get(FlowD7)
#
# get the data to be plotted		
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
		flowDC = toLocalTime(FlowData)
		flowD1DC = toLocalTime(FlowD1Data)
		flowD3DC = toLocalTime(FlowD3Data)
		flowD5DC = toLocalTime(FlowD5Data)
		flowD7DC = toLocalTime(FlowD7Data)
#
# define the plot layout
		layout = Plot.newPlotLayout()
		view = layout.addViewport(100)
		view.addCurve("Y1",flowDC)
		view.addCurve("Y1",flowD1DC)
		view.addCurve("Y1",flowD3DC)
		view.addCurve("Y1",flowD5DC)
		view.addCurve("Y1",flowD7DC)
		plot.configurePlotLayout(layout)
		plot.showPlot()
		plot.setLegendLabelText(flowDC,"Actual Flow")
		plot.setLegendLabelText(flowD1DC,"Forecast - Day 1")
		plot.setLegendLabelText(flowD3DC,"Forecast - Day 3")
		plot.setLegendLabelText(flowD5DC,"Forecast - Day 5")
		plot.setLegendLabelText(flowD7DC,"Forecast - Day 7")
#		plot.setLegendBackground("gray")
#
# set line color, style, width for time series ..... Actual Flow
                lineColor1=plot.getCurve(FlowData)
                lineColor1.setLineColor("red")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 2. )
#
# set line color, style, width for time series ..... FUI Forecasted Flow - yesterday's run
                lineColor2=plot.getCurve(FlowD1Data)
                lineColor2.setLineColor("magenta")
                lineColor2.setLineStyle("Solid")
                lineColor2.setLineWidth( 1. )
#
# set line color, style, width for time series ..... FUI Forecasted Flow - run 3 days ago
                lineColor3=plot.getCurve(FlowD3Data)
                lineColor3.setLineColor("green")
                lineColor3.setLineStyle("Solid")
                lineColor3.setLineWidth( 1. )
#
# set line color, style, width for time series ..... FUI Forecasted Flow - run 5 days ago
                lineColor4=plot.getCurve(FlowD5Data)
                lineColor4.setLineColor("black")
                lineColor4.setLineStyle("Dash")
                lineColor4.setLineWidth( 2. ) 
#
# set line color, style, width for time series ..... FUI Forecasted Flow - run 7 days ago
                lineColor5=plot.getCurve(FlowD7Data)
                lineColor5.setLineColor("blue")
                lineColor5.setLineStyle("Dash")
                lineColor5.setLineWidth( 2. ) 
#
# customize the first graph on the plot (all 5 flows) ... viewport0		
		viewport0=plot.getViewport(0)
#
# customize the left y axis label on viewport0
		yaxislabel=viewport0.getAxisLabel("Y1")
		yaxislabel.setForeground("black")	
		yaxislabel.setFont("Arial,Normal,20")	
#
# customize the title of the plot (sixth line in the ini data file)
		title=plot.getPlotTitle()	
		title.setForeground("darkblue")	
		title.setFontFamily("Courier")
		title.setFontStyle("Bold")
		title.setFontSize(24)
		title.setText ( titlename )	
		title.setDrawTitleOn()
		
		fileName = '%s.jpg' % jpgname
		plot.saveToJpeg (fileName, quality)
		
#
# program information
#
dbiName     = "fooo"
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataMRRcheckFUI.ini"
timeSpan    = 25 * 24 * 60 # minutes
timeSpanFcast= 14 * 24 * 60 # minutes
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
		iniFlow 	= iniFile.readline().strip()
		iniFlowD1 	= iniFile.readline().strip()
		iniFlowD3 	= iniFile.readline().strip()
		iniFlowD5 	= iniFile.readline().strip()
		iniFlowD7 	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	
	plotData(dbi, iniFlow, iniFlowD1, iniFlowD3, iniFlowD5, iniFlowD7, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
