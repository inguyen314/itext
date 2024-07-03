# name=SnotelPlots-cron
# displayinmenu=false
# displaytouser=false
# displayinselector=false
#Snotel Plotting Script
#Runs in a cron on nwo-cwms2 g6cwmspd (script located in cronjobs)
#
#Jessica Branigan
#
#Version 2.1 written Dec 2014
###Changes: Written to generate plots automatically for website viewing
####Plots are generated with 30-yr, current year, and last year
#
#

#imports all classes (may not all be necessary, copied from Alex's scripts)
from hec.script import *
from hec.heclib.dss import *
from hec.heclib.util import HecTime
import java
#import org.free.*
import time,calendar
from javax.swing import *
from java.lang import *
from hec.hecmath import *
from hec.heclib.util import *
from hec.io import*
from java.awt           import BorderLayout,GridLayout, FlowLayout, Toolkit
from java.awt.event     import ActionListener
from javax.swing.border import EmptyBorder
import sys
from hec.dataTable import *
from rma.swing          import DateChooser
import DBAPI
from hec.script.Constants import TRUE, FALSE
from datetime import datetime, timedelta


#Defines array of basin names
basinNames = ["BOYN-Basin","CAFE-Basin","CAFE-blw_Canyon_Ferry","CAFE-Gallatin","CAFE-Jefferson","CAFE-Madison","CHFI-South_Platte","CHFI-Upper_South_Platte","CLCA-Basin","GLEN-Alcova_to_Glendo","GLEN-Basin","GLEN-Laramie","GLEN-Sweetwater","GLEN-Upper_North_Platte","KEYO-blw_Keyhole","MRB-Basin","PACA-Rapid","PRB-Basin","SJMU-Basin","TIBR-Basin","YELL-Powder","YELL-Tongue","YELL-Upper_Yellowstone","YETL-Basin","YETL-Bighorn","YETL-Shoshone","FTPK-Basin","FTPK-bl_7000","FTPK-7000_to_8500","FTPK-ab_8500","GARR-Basin","GARR-bl_7000","GARR-7000_to_8500","GARR-ab_8500"]

#Opens and defines database
db = DBAPI.open()
db.setTimeZone("US/Central")
officeID = 'NWDM'
db.setOfficeId(officeID)

#Sets up time series IDs, time windows, and plots for each basin
for i in basinNames :

	#Defines time series for each basin plot
	tsid = str(i + ".Depth-Snow-WE.Inst.1Day.0.NRCS_Snotel")
	tsid30yr = str(i + ".Depth-Snow-WE.Inst.1Day.0.NRCS_Snotel_1981-2010")

	#Defines time windows
	today = datetime.today()
	month = datetime.today().month
	currentYear = datetime.today().year
	timeFormat = "%d%b%Y %H%M"

	#Sets current and last year's time window
	if month == 10 or month == 11 or month == 12 :
		startDateCurrent = today.replace(month = 10, day = 1, hour = 0, minute = 0)
		endDateCurrent = today.replace(year = currentYear + 1, month = 10, day = 1, hour = 0, minute = 0)
	
		startDateLast = today.replace(year = currentYear - 1, month = 10, day = 1, hour = 0, minute = 0)
		endDateLast = today.replace(year = currentYear, month = 10, day = 1, hour = 0, minute = 0)
	else :
		startDateCurrent = today.replace(year = currentYear - 1, month = 10, day = 1, hour = 0, minute = 0)
		endDateCurrent = today.replace(year = currentYear, month = 10, day = 1, hour = 0, minute = 0)
	
		startDateLast = today.replace(year = currentYear - 2, month = 10, day = 1, hour = 0, minute = 0)
		endDateLast = today.replace(year = currentYear - 1, month = 10, day = 1, hour = 0, minute = 0)

	#Sets 30-yr average time window (uses set dates so don't have to worry about copying ts each year)
	startDate30yr = today.replace(year = 2012, month = 10, day = 1, hour = 0, minute = 0)
	endDate30yr = today.replace(year = 2013, month = 10, day = 1, hour = 0, minute = 0)

	#Defines plot and plot layout
	plot = Plot.newPlot(i + " SWE Comparison Plot")
	layout = Plot.newPlotLayout()
	plot.configurePlotLayout(layout)

	#Sets plot size so that title shows up correctly instead of squished
	#size = plot.getSize()
	#plot.setSize(size.width-1, size.height-1)
	#plot.setSize(size.width, size.height)

	#Defines viewport (since just one, it takes up 100% of the plot) and plot properties
	viewport = layout.addViewport(100)


	#Sets time window for current year and reads time series into a time series container
	db.setTimeWindow(startDateCurrent.strftime(timeFormat), endDateCurrent.strftime(timeFormat))
	tscCurrent = db.read(tsid)

	#Adds data to plot (no need to shift since current time window)
	tscCurrent2 = tscCurrent.getData()
	if month == 10 or month == 11 or month == 12 :
		tscCurrent2.version = str(currentYear + 1)
	else :
		tscCurrent2.version = str(currentYear)
	plot.addData(tscCurrent2)
	viewport.addCurve("Y1",tscCurrent2)


	#Sets time window for 30-yr average and reads time series into a time series container
	db.setTimeWindow(startDate30yr.strftime(timeFormat), endDate30yr.strftime(timeFormat))
	tsc30yr = db.read(tsid30yr)
	
	#Defines the number of years to shift the time series to current dates, and shifts data
	if month == 10 or month == 11 or month == 12 :
		yearShift = (currentYear - 2012)
	else :
		yearShift = (currentYear - 2013)
	tsc30yr = tsc30yr.shiftInTime("%dYY" % yearShift)
	
	#Pulls the data from the db for the time series
	tsc30yr2 = tsc30yr.getData()

	#Adds the data to the plot
	plot.addData(tsc30yr2)
	viewport.addCurve("Y1",tsc30yr2)


	#Sets time window for last year and reads time series into a time series container
	db.setTimeWindow(startDateLast.strftime(timeFormat), endDateLast.strftime(timeFormat))
	tscLast = db.read(tsid)
	
	#Shifts data
	yearShift = 1
	tscLast = tscLast.shiftInTime("%dYY" % yearShift)
	
	#Adds data to plot
	tscLast2 = tscLast.getData()
	if month == 10 or month == 11 or month == 12 :
		tscLast2.version = str(currentYear)
	else :
		tscLast2.version = str(currentYear - 1)
	plot.addData(tscLast2)
	viewport.addCurve("Y1",tscLast2)

	#Shows plot
	plot.showPlot()
        plot.getPlotTitle().setDrawTitleOn()	

        plot.setPlotTitleText(i + " SWE Comparison Plot\nSource Data: NRCS ")

	#Sets plot size so that title shows up correctly instead of squished
        size = plot.getSize()
        plot.setSize(size.width-1, size.height-1)
        plot.setSize(size.width, size.height)

        #plot.setPlotTitleText(i + " SWE Comparison Plot\nSource Data: NRCS ")

	#saves plot image
	i = i.lower()
	plot.saveToJpeg("/netapp/g6cwmspd/cronjobs/snotelplots/" + i + ".jpg")
	#plot.saveToJpeg("/netapp/g7cwmspd/plotFiles/files/" + i + ".jpg")

#Closes CWMS database
db.close()
