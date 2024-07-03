from hec.script import *
from hec.script.Constants import *   # for TRUE & FALSE
from hec.heclib.util import HecTime
import sys, time
import DBAPI

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
def plotData (dbi, elev, inflow, release, titlename, width, height, jpgname, quality) :

	if debugOutput :
		print "Elev 		= %s" % elev
		print "Inflow		= %s" % inflow
		print "Release		= %s" % release
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname
#
# read the data from the CWMS Oracle database via the DBI from the ini data file
		elevData 	= dbi.get(elev)
		inflowData 	= dbi.get(inflow)
		releaseData 	= dbi.get(release)
#
# get the data to be plotted		
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
#
		try :
			elevDC = toLocalTime(elevData)
			inflowDC = toLocalTime(inflowData)
			releaseDC = toLocalTime(releaseData)
		except :
			return
#
# define the plot layout
		layout = Plot.newPlotLayout()
		topView = layout.addViewport(40.)
		bottomView = layout.addViewport(40.)
		topView.addCurve("Y1",elevDC)	
		bottomView.addCurve("Y1",inflowDC)	
		bottomView.addCurve("Y1",releaseDC)	
		plot.configurePlotLayout(layout)
		plot.showPlot()
		plot.setLegendLabelText(inflowDC,"Average Daily Inflow")
		plot.setLegendLabelText(elevDC,"Reservoir Elevation")
		plot.setLegendBackground("gray")
#
# set line color, style, width for time series ..... elev
                lineColor1=plot.getCurve(elevData)
                lineColor1.setLineColor("green")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 1. )
#               lineColor1.setSymbolsVisible(TRUE)
#               lineColor1.setSymbolsAutoInterval(FALSE)
#               lineColor1.setSymbolInterval(24)
#               lineColor1.setSymbolLineColor("green")
#               lineColor1.setSymbolType("Open Triangle")
#               lineColor1.setSymbolSize( 8. )
#
# set line color, style, width for time series ..... inflow
                lineColor2=plot.getCurve(inflowData)
                lineColor2.setLineColor("blue")
                lineColor2.setLineStyle("Solid")
                lineColor2.setLineWidth( 2. )
#               lineColor2.setSymbolsVisible(TRUE)
#               lineColor2.setSymbolsAutoInterval(FALSE)
#               lineColor2.setSymbolInterval(1)
#               lineColor2.setSymbolLineColor("blue")
#               lineColor2.setSymbolType("Open Circle")
#               lineColor2.setSymbolSize( 8. )
#
# set line color, style, width for time series ..... release
                lineColor3=plot.getCurve(releaseData)
                lineColor3.setLineColor("magenta")
                lineColor3.setLineStyle("Solid")
                lineColor3.setLineWidth( 2. )
#               lineColor3.setSymbolsVisible(TRUE)
#	        lineColor3.setSymbolsAutoInterval(FALSE)
#     	        lineColor3.setSymbolInterval(1)
#               lineColor3.setSymbolLineColor("magenta")
#               lineColor3.setSymbolType("X")
#               lineColor3.setSymbolSize( 8. ) 
#
# customize the first graph on the plot (elev) ... viewport0		
		viewport0=plot.getViewport(0)
#
# customize the left y axis label on viewport0
		yaxislabel=viewport0.getAxisLabel("Y1")
		yaxislabel.setForeground("red")	
		yaxislabel.setFont("Arial,Normal,20")	
#
# customize the second graph on the plot (#elev,# inflow and release) ... viewport1
		viewport1=plot.getViewport(1)
#
# customize the left y axis label on viewport1
		yaxislabel=viewport1.getAxisLabel("Y1")
		yaxislabel.setForeground("blue")	
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
		
# Suggestion from Mike Perryman (March 3, 2017) - to see if we can get label correct
		size = plot.getSize()
		plot.setSize(size.width-1, size.height-1)
		plot.setSize(size.width, size.height)

		fileName = '%s.jpg' % jpgname
		plot.saveToJpeg (fileName, quality)
#		plot.saveToPng (fileName)	
#
# program information
#
dbiName     = "foo"
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataMRRres4.ini"
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
        dbi.setTimeWindow(startTime, endTime)
        dbi.setOfficeId(officeID)
        dbi.setTimeZone('US/Central')
	#if not dbi : raise Exception
	#dbi.setTimeWindow(startTime, endTime)
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
		iniElev 	= iniFile.readline().strip()
		iniInflow 	= iniFile.readline().strip()
		iniRelease 	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	
	plotData(dbi, iniElev, iniInflow, iniRelease, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
