# name=CroncompareFlows
# displayinmenu=false
# displaytouser=false
# displayinselector=false
from java.text          import SimpleDateFormat
import time,calendar
from hec.script import *
from hec.heclib.dss import *
from hec.hecmath import *
from hec.heclib.util import *
from hec.io import*
#from hec.dataTable import *
import java
import sys
#from hec.dataTable import *
import DBAPI
from hec.script.Constants import TRUE, FALSE
from datetime import datetime, timedelta





month = datetime.today().month
if month == 10 or month == 11 or month == 12:
	yeare = datetime.today().year+1
	years = datetime.today().year
	yearss = datetime.today().year-1

	yearsend  =[yeare,years]
	yearsstart=[years,yearss]

else:
	yeare = datetime.today().year
	years = datetime.today().year-1
	yearss = datetime.today().year-2	

	yearsend  =[yeare,years]
	yearsstart=[years,yearss]


print years
print yeare

startTime  = datetime(year=years, month=11, day=1, hour=0, minute=0)

endTime    = datetime(year=yeare, month=03, day=1, hour=0, minute=0)

timeFormat = "%d%b%Y %H%M"



db = DBAPI.open()
db.setTimeZone("US/Central")

'''
plot = Plot.newPlot()
plot.setLocation(0,0)

layout=Plot.newPlotLayout()

plot.configurePlotLayout(layout)
#plot.setSize(1200, 1000)
topView = layout.addViewport(100.)
'''
ykn= 'YKN-Yankton-Missouri'
sux = 'SUX-Sioux_City-Missouri'
dene = 'DENE-Decatur-Missouri'
oma = 'OMA-Omaha-Missouri'
ncne = 'NCNE-Nebraska_City-Missouri'
rune = 'RUNE-Rulo-Missouri'
stj = 'STJ-St_Joseph-Missouri'
mkc = 'MKC-Kansas_City-Missouri'
wvmo = 'WVMO-Waverly-Missouri'
bnmo = 'BNMO-Boonville-Missouri'
hemo = 'HEMO-Hermann-Missouri'
gapt = 'GAPT-Gavins_Point_Dam-Missouri'

group = [hemo,bnmo,wvmo,mkc,stj,rune,ncne,oma,dene,sux,ykn,gapt]
#dlnm = addNote()
#(year1,year2,year3,year4,year5,year6,year7,year8,new)= dlnm.checkNotes()
#print year1,year2,year3,year4,year5,year6,year7,year8,new
t=1
for tsid2 in group:
	tsid = tsid2
	shortname = tsid[:4]
	shortname = shortname.replace("-","")
	shortname = shortname.lower()
	print shortname
	startTime  = datetime(year=years, month=11, day=1, hour=0, minute=0)
	endTime    = datetime(year=yeare, month=03, day=1, hour=0, minute=0)

	t = t+1

	plot = Plot.newPlot(tsid2)
	plot.setLocation(0,0)
	
	layout=Plot.newPlotLayout()
	
	plot.configurePlotLayout(layout)
	#plot.setSize(1200, 1000)
	topView = layout.addViewport(100.)

	for i in range(0,len(yearsend)):
		print "i is %d " % i
		print startTime.strftime(timeFormat)
		print endTime.strftime(timeFormat)
		db.setTimeWindow(startTime.strftime(timeFormat),endTime.strftime(timeFormat))
		
		if tsid != 'GAPT-Gavins_Point_Dam-Missouri':
		
			tsm = db.read(tsid+".Flow.Inst.1Hour.0.Combined-rev")
			tsm2 = db.read(tsid + ".Stage.Inst.1Hour.0.Combined-rev")


			tmp=(yeare-yearsend[i])
			print "tmp is %d" % tmp
			if tmp : tsm = tsm.shiftInTime("%dYY" % tmp)
			
			if tmp : tsm2 = tsm2.shiftInTime("%dYY" % tmp)
			tsc = tsm.getData()
			tsc2 = tsm2.getData()
			str=''
			str+=startTime.strftime("%b %Y")
			str+= '-'
			str+= endTime.strftime("%b %Y")
			tsc.version = str
			tsc2.version = str
			
			plot.addData(tsc)
			plot.addData(tsc2)
			topView.addCurve("Y1", tsc)
			tmp2=i+1
			
			print tmp2
			tmp3=len(yearsend)
			print "tmp3 %d " % tmp3
			if tmp2 < tmp3 :
			         startTime = startTime.replace(year=yearsstart[i+1])
			         endTime = endTime.replace(year=yearsend[i+1]);
			
			         print startTime
			         print endTime
		else:
			tsm = db.read(tsid+".Flow-Total.Ave.1Day.1Day.mrrppcs-rev")
		
		
			tmp=(yeare-yearsend[i])
			print "tmp is %d" % tmp
			if tmp : tsm = tsm.shiftInTime("%dYY" % tmp)
			

			tsc = tsm.getData()

			str=''
			str+=startTime.strftime("%b %Y")
			str+= '-'
			str+= endTime.strftime("%b %Y")
			tsc.version = str

			
			plot.addData(tsc)

			topView.addCurve("Y1", tsc)
			tmp2=i+1
			
			print tmp2
			tmp3=len(yearsend)
			print "tmp3 %d " % tmp3
			if tmp2 < tmp3 :
			         startTime = startTime.replace(year=yearsstart[i+1])
			         endTime = endTime.replace(year=yearsend[i+1]);
			
			         print startTime
			         print endTime
           





	plot.showPlot()				

	plotlocation = "/usr1/g7cwmspd/plotFiles/files/" + shortname + "comp"
	print plotlocation
	plot.saveToJpeg(plotlocation)
	plot.close()		
'''

	print startTime
	print endTime
	db.setTimeWindow(startTime.strftime(timeFormat),endTime.strftime(timeFormat))
	tsm3 = db.read(tsid+".Flow.Inst.1Hour.0.Combined-rev")
	tsm3.setLocation(tsid2+" "+eachstr)
	tsm4 = db.read(tsid+".Stage.Inst.1Hour.0.Combined-rev")
	tsm4.setLocation(tsid2+" "+eachstr)
	#tsm3.setPathname('//'+name+"/Depth-SWE/1Day/"+eachstr+"/")
	tsm3 = tsm3.shiftInTime("%dYY" % yearDelta)
	tsc3 = tsm3.getData()

	tsm4 = tsm4.shiftInTime("%dYY" % yearDelta)
	tsc4 = tsm4.getData()
	plot.addData(tsc3)
	plot.addData(tsc4)
	topView.addCurve("Y1",tsc3)
'''
	



	
