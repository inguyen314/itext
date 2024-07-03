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
def plotData (dbi, obsFlow, measFlow, usgsFlow, fuiFlow, titlename, width, height, jpgname, quality) :

	if debugOutput :
		print "Observed Flow	= %s" % obsFlow
		print "USGS Measure	= %s" % measFlow
		print "USGS Flow	= %s" % usgsFlow
		print "FUI Forecast	= %s" % fuiFlow
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname
#
# read the data from the CWMS Oracle database via the DBI from the ini data file
		obsFlowData 	= dbi.get(obsFlow)
		measFlowData 	= dbi.get(measFlow)
		usgsFlowData 	= dbi.get(usgsFlow)
		fuiFlowData 	= dbi.get(fuiFlow)
#
# get the data to be plotted		
		numlines = 6
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
#
		try :
			obsFlowDC = toLocalTime(obsFlowData.getData())
			usgsFlowDC = toLocalTime(usgsFlowData.getData())
			fuiFlowDC = toLocalTime(fuiFlowData.getData())
			try :
				measFlowDC = toLocalTime(measFlowData.getData())
			except :
				print "no USGS measurements in lookback time window"
				numlines = 5
		except :
			return
#
# define the plot layout
		layout = Plot.newPlotLayout()
		view = layout.addViewport(100)
		view.addCurve("Y1",obsFlowDC)	
		if numlines <> 5 :
			view.addCurve("Y1",measFlowDC)
		view.addCurve("Y1",usgsFlowDC)
		view.addCurve("Y1",fuiFlowDC)
		plot.configurePlotLayout(layout)
		plot.showPlot()
		plot.setLegendLabelText(obsFlowDC,"COE Calculated Flow")
		if numlines <> 5 :
			plot.setLegendLabelText(measFlowDC,"USGS Measured Flow")
		plot.setLegendLabelText(usgsFlowDC,"USGS Calculated Flow")
#		plot.setLegendLabelText(fuiFlowDC,"COE FUI Forecast")
		plot.setLegendBackground("gray")
#
# set line color, style, width for time series ..... COE calculated hourly flow
                lineColor1=plot.getCurve(obsFlowData)
                lineColor1.setLineColor("red")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 2. )
#
# set line color, style, width for time series ..... USGS measured flow
		if numlines <> 5 :
                	lineColor2=plot.getCurve(measFlowData)
                	lineColor2.setLineColor("white")
                	lineColor2.setLineStyle("Solid")
                	lineColor2.setLineWidth( 1. )
                	lineColor2.setSymbolsVisible(TRUE)
                	lineColor2.setSymbolsAutoInterval(FALSE)
                	lineColor2.setSymbolInterval(1)
                	lineColor2.setSymbolLineColor("black")
                	lineColor2.setSymbolType("Open Triangle")
                	lineColor2.setSymbolSize( 12. )
#
# set line color, style, width for time series ..... USGS calculated flow
                lineColor3=plot.getCurve(usgsFlowData)
                lineColor3.setLineColor("green")
                lineColor3.setLineStyle("Solid")
                lineColor3.setLineWidth( 1. )
#
# set line color, style, width for time series ..... COE FUI forecasted flow
                lineColor4=plot.getCurve(fuiFlowData)
                lineColor4.setLineColor("blue")
                lineColor4.setLineStyle("Dash")
                lineColor4.setLineWidth( 1. ) 
#
# customize the first graph on the plot (all 4 flows) ... viewport0		
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
dbiName     = "foo"
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataMRRfcastDENE.ini"
timeSpan    = 25 * 24 * 60 # minutes
timeSpanFcast=12 * 24 * 60 # minutes
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
	dbi =DBAPI.open()
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
		iniObsFlow 	= iniFile.readline().strip()
		iniMeasFlow 	= iniFile.readline().strip()
		iniUsgsFlow 	= iniFile.readline().strip()
		iniFuiFlow 	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	
	plotData(dbi, iniObsFlow, iniMeasFlow, iniUsgsFlow, iniFuiFlow, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
