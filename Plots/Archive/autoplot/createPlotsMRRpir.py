from hec.script import *
from hec.script.Constants import *   # for TRUE & FALSE
from hec.heclib.util import HecTime
import sys, time
import DBAPI
from hec.io import*


#-----------------------------------------#
# define a function to generate the plots #
#-----------------------------------------#
def plotData (dbi, stage, ppnot, targel, critel, titlename, width, height, jpgname, quality) :

	if debugOutput :
		print "Stage 		= %s" % stage
		print "PP Notify	= %s" % ppnot
		print "Target Elev	= %s" % targel
		print "Critical Elev	= %s" % critel
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname
#
# read the data from the CWMS Oracle database via the DBI from the ini data file
		stageData 	= dbi.get(stage)
#
# get the data to be plotted		
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
#
		try :
			#stageDC = stageData
		except :
			return
#
# define the plot layout
		layout = Plot.newPlotLayout()
		view = layout.addViewport(100)
		view.addCurve("Y1",stageDC)	
		plot.configurePlotLayout(layout)
		plot.showPlot()
#
# set line color, style, width for time series ..... stage
                lineColor1=plot.getCurve(stageData)
                lineColor1.setLineColor("blue")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 1. )
                lineColor1.setSymbolsVisible(TRUE)
                lineColor1.setSymbolsAutoInterval(FALSE)
                lineColor1.setSymbolInterval(24)
                lineColor1.setSymbolLineColor("blue")
                lineColor1.setSymbolType("Open Circle")
                lineColor1.setSymbolSize( 8. )
#
# customize the plot 	
		viewport0=plot.getViewport(0)
#
# customize the left y axis label on viewport0 ..... stage
		yaxis = viewport0.getAxis("Y1")
		yaxis.setScaleLimits(4.,14.)
		yaxislabel=viewport0.getAxisLabel("Y1")
		yaxislabel.setForeground("blue")	
		yaxislabel.setFont("Arial,Normal,20")	
#
# define the marker lines ... PowerPlant notification elevation as listed in ini data file - second line 
		marker1=AxisMarker()
		marker1.axis = "Y2"
		marker1.value = ppnot
		marker1.labelText = "PowerPlant Notification Elevation (11.74 ft)"
		marker1.labelColor = "orange"
		marker1.labelPosition = "above"
		marker1.lineColor = "orange"
		marker1.lineStyle = "Dash Dot"
		viewport0.addAxisMarker(marker1)
#
# define the marker lines ... Target elevation as listed in ini data file - third line 
		marker2=AxisMarker()
		marker2.axis = "Y2"
		marker2.value = targel
		marker2.labelText = "Target Elevation (12.24 ft)"
		marker2.labelColor = "magenta"
		marker2.labelPosition = "above"
		marker2.lineColor = "magenta"
		marker2.lineStyle = "Dash Dot"
		viewport0.addAxisMarker(marker2)
#
# define the marker lines ... Critical elevation as listed in the ini data file - fourth line 
		marker3=AxisMarker()
		marker3.axis = "Y2"
		marker3.value = critel
		marker3.labelText = "Critical Elevation (13.24 ft)"
		marker3.labelColor = "cyan"
		marker3.labelPosition = "above"
		marker3.lineColor = "cyan"
		marker3.lineStyle = "Dash Dot"
		viewport0.addAxisMarker(marker3)
#
# customize the right y axis label on viewport0 ..... elevation in feet msl
		yaxis = viewport0.getAxis("Y2")
#		yaxis.setScaleLimits(1418.26,1428.26)
		yaxislabel=viewport0.getAxisLabel("Y2")
#		yaxislabel.setForeground("red")	
#		yaxislabel.setFont("Arial,Normal,20")	
#		yaxislabel.setText("Elevation in feet, msl")	
#
# customize the title of the plot (fifth line in the ini data file)
		title=plot.getPlotTitle()	
		title.setForeground("darkblue")	
		title.setFontFamily("Arial")
		title.setFontStyle("Normal")
		title.setFontSize(20)
		title.setText ( titlename )	
		title.setDrawTitleOn()
		
		fileName = '%s.jpg' % jpgname
		plot.saveToJpeg (fileName, quality)
		
#
# program information
#
dbiName     = "foo"
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataMRRpir.ini"
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
		iniPPnot 	= iniFile.readline().strip()
		iniTargel 	= iniFile.readline().strip()
		iniCritel 	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	dbi.setTimeWindow(startTime, endTime)
        dbi.setOfficeId(officeID)
        dbi.setTimeZone('US/Central')
	print startTime
	print endTime
	plotData(dbi, iniStage, iniPPnot, iniTargel, iniCritel, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
