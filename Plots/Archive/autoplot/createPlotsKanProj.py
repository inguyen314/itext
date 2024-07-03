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
def plotData (dbi, qout1, qout2, qout3, qout4, titlename, width, height, jpgname, quality) :
#
	if debugOutput :
		print "Qout1		= %s" % qout1
		print "Qout2		= %s" % qout2
		print "Qout3		= %s" % qout3
		print "Qout4		= %s" % qout4
		print "Title 		= %s" % titlename
		print "Filename		= %s" % jpgname

# read the data from the CWMS Oracle database via the DBI from the ini data file
		qout1Data 	= dbi.get(qout1)
		qout2Data 	= dbi.get(qout2)
		qout3Data 	= dbi.get(qout3)
		qout4Data 	= dbi.get(qout4)
#
# get the data to be plotted		
		plot = Plot.newPlot()
		plot.setLocation(10000, 10000)
		plot.setSize(width, height)
#
		try :
			qout1DC = toLocalTime(qout1Data)
			qout2DC = toLocalTime(qout2Data)
			qout3DC = toLocalTime(qout3Data)
			qout4DC = toLocalTime(qout4Data)
		except :
			return
#
# define the plot layout
		layout = Plot.newPlotLayout()
		topView = layout.addViewport()
		topView.addCurve("Y1",qout1DC)	
		topView.addCurve("Y1",qout2DC)
		topView.addCurve("Y1",qout3DC)
		topView.addCurve("Y1",qout4DC)
		plot.configurePlotLayout(layout)
		plot.showPlot()
		plot.setLegendLabelText(qout1DC,"Clinton Lake")
		plot.setLegendLabelText(qout2DC,"Milford Lake")
		plot.setLegendLabelText(qout3DC,"Perry Lake")
		plot.setLegendLabelText(qout4DC,"Tuttle Creek Lake")
                plot.setLegendBackground("gray")
#
# set line color, style, width for time series ..... qout1Data
                lineColor1=plot.getCurve(qout1Data)
                lineColor1.setLineColor("black")
                lineColor1.setLineStyle("Solid")
                lineColor1.setLineWidth( 1. )
#
# set line color, style, width for time series ..... qout2Data
                lineColor2=plot.getCurve(qout2Data)
                lineColor2.setLineColor("blue")
                lineColor2.setLineStyle("Dash")
                lineColor2.setLineWidth( 2. )
#
# set line color, style, width for time series ..... qout3Data
                lineColor3=plot.getCurve(qout3Data)
                lineColor3.setLineColor("red")
                lineColor3.setLineStyle("Dot")
                lineColor3.setLineWidth( 2. )
#
# set line color, style, width for time series ..... qout4Data
                lineColor4=plot.getCurve(qout4Data)
                lineColor4.setLineColor("gray")
                lineColor4.setLineStyle("Dash Dot-Dot")
                lineColor4.setLineWidth( 2. )
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
officeID='NWDM'
iniFilename = "/cwms/g7cwmspd/plotFiles/plotDataKanProj.ini"
timeSpan    = 12 * 24 * 60 # minutes
timeSpanFcast=2 * 24 * 60 # minutes
plotWidth   = 640
plotHeight  = 480
plotQuality = 100 # range of 0 (crappy) to 100 (great, but larger file)
debugOutput = TRUE

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
		iniQout1 	= iniFile.readline().strip()
		iniQout2 	= iniFile.readline().strip()
		iniQout3 	= iniFile.readline().strip()
		iniQout4	= iniFile.readline().strip()
		iniTitle 	= iniFile.readline().strip()
		iniFname 	= iniFile.readline().strip()
		iniDummy 	= iniFile.readline().strip()
		if iniDummy == None :
			break
	except :
		break
	
	plotData(dbi, iniQout1, iniQout2, iniQout3, iniQout4, iniTitle, plotWidth, plotHeight, iniFname, plotQuality)

#
# clean up
#	
iniFile.close()
dbi.close()
