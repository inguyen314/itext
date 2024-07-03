'''
Author: Ryan Larsen
Last Updated: 05-01-2017
Description: Creates a form for the reservoir bulletin that can be 
'''

from hec.script			import *
from hec.hecmath		import *
from hec.heclib.util	import *
from hec.io				import *
from javax.swing		import *
import DBAPI, datetime, inspect, time

'''
from decimal			import *
from hec.script			import *
from hec.hecmath		import *
from hec.heclib.util	import *
from hec.io				import *
from hec.script			import Constants
from hec.heclib.dss		import *
from hec.dataui.tx		import TsContainerDataSourceList
from hec.dataui.tx.awt	import VerifyDataDlg
from hec.dssgui			import ListSelection
from hec.dataTable		import *
from java.lang			import *
from java.awt			import BorderLayout, GridLayout, FlowLayout, Toolkit, GraphicsEnvironment, Rectangle, Color, Font
from java.awt.event		import ActionListener, FocusListener
from java.text			import SimpleDateFormat
from javax.swing		import *
from javax.swing.text	import DefaultStyledDocument, Style, StyleConstants, StyleContext, StyledDocument
from javax.swing.border	import EmptyBorder
from rma.swing			import DateChooser
from time				import mktime
import datetime, time, calendar, inspect, java, os, sys, traceback, javax.swing.JFrame, DBAPI, math
'''
# -------------------------------------------------------------------
# create Pdf Function	: Writes text to a .pdf file at a specified location
# Author/Editor			: Ryan Larsen
# Last updated			: 04-12-2016
# -------------------------------------------------------------------
def createPdf(	itextpdfDir,	# Directory of the itextpdf.jar file
				filename,		# Filename consists of the path and filename
				text			# Text that will be added to the PDF file
				) :

	# Add the itextpdfDir to the sys.path so it can be loaded
	if itextpdfDir not in sys.path : sys.path.insert(0, itextpdfDir)
	
	# Imports
	from com.itextpdf.text		import Document, DocumentException, Paragraph, Phrase, Font, FontFactory, PageSize
	from com.itextpdf.text.pdf	import PdfWriter, BaseFont
	from java.io				import FileOutputStream, IOException
	from java.util				import Set, TreeSet

	# Step 1: Create a blank document
	document = Document()
	document.setPageSize(PageSize.LETTER) # Set the page size
	document.setMargins(72, 72, 72, 72)
	document.setMarginMirroring(True)
	
	# Step 2: Use the PdfWriter to create the file with specifed filename and path
	PdfWriter.getInstance(document, FileOutputStream(filename))
	# Step 3: Open the .pdf file
	document.open()
	# Step 4: Add the text to the file, set the font and line spacing
	font = FontFactory.getFont(FontFactory.COURIER, 9)
	paragraph = Paragraph(text, font)
	paragraph.setLeading(0, 1.2) # Set the line spacing to 1.2x the font size
	document.add(paragraph)
	# Step 5: Close the file
	document.close()

# -------------------------------------------------------------------
# lineNo Function	: Retrieves the line number of the script.  Used when debugging
# Author/Editor		: Ryan Larsen
# Last updated		: 01-26-2016
# -------------------------------------------------------------------
def lineNo() :
	return inspect.currentframe().f_back.f_lineno

# -------------------------------------------------------------------
# outputDebug Function	: Debugging function that prints specified arguments
# Author/Editor			: Ryan Larsen
# Last updated			: 04-10-2017
# -------------------------------------------------------------------
def outputDebug(	*args
					) :
	ArgCount = len(args)
	if ArgCount < 2 :
		raise ValueError('Expected at least 2 arguments, got %d' % argCount)
	if type(args[0]) != type(True) :
		raise ValueError('Expected first argument to be either True or False')
	if type(args[1]) != type(1) :
		raise ValueError('Expected second argument to be line number')

	if args[0] == True: 
		DebugStatement = 'Debug Line %d   |\t' % args[1]
		for x in range(2, ArgCount, 1) :
			DebugStatement += str(args[x])
		print DebugStatement

# -------------------------------------------------------------------
# reservoirBulletin Function	: Creates the bulletin form that will be written to a .pdf file
# Author/Editor					: Ryan Larsen
# Last updated					: 05-01-2017
# -------------------------------------------------------------------
def reservoirBulletin(	debug,		# Set to True to print all debug statements
						DataDict	# Dictionary of all data
						) :
	ReservoirBulletinForm = '''\
                             U.S. Army Corps of Engineers
                                 Missouri River Basin

          FTPK         GARR         OAHE         BEND         FTRA         GAPT
 Time Power  Spill Power  Spill Power  Spill Power  Spill Power  Spill Power  Spill
------------------------------------------------------------------------------------
	'''
	
	return ReservoirBulletinForm

# -------------------------------------------------------------------
# retrieveReservoirZone Function	: Retrieves reservoir zone data
# Author/Editor						: Mike Perryman
# Last updated						: 05-01-2017
# -------------------------------------------------------------------
def retrieveReservoirZone(	debug,			# Set to True to print all debug statements
							TscFullName,	# Full name of time series container
							) :
	CurDate			= datetime.datetime.now() # Current date
	StartTimeStr	= CurDate.strftime('%d%b%Y ') + '0000' # Start date formatted as ddmmmyyy 0000
	EndTimeStr		= CurDate.strftime('%d%b%Y ') + '0000' # End date formatted as ddmmmyyy 0000

	level_1a = TimeSeriesContainer()
	level_1a_parts = TscFullName.split('.')
	level_1aId_parts = level_1a_parts[:]
	del level_1aId_parts[3]
	level_1aId = '.'.join(level_1aId_parts)
	outputDebug(debug, lineNo(), 'level_1a_parts = ', level_1a_parts, '\tlevel_1aId_parts = ', level_1aId_parts, 
		'\n\t\tlevel_1aId = ', level_1aId)
	
	level_1a.fullName  = TscFullName
	level_1a.location  = level_1a_parts[0]
	level_1a.parameter = level_1a_parts[1]
	level_1a.interval  = 0
	level_1a.version   = level_1a_parts[-1]
	if level_1a_parts[1] == 'Stor' : level_1a.units = 'ac-ft'
	elif level_1a_parts[1] == 'Elev' : level_1a.units = 'ft'
	level_1a.type      = 'INST-VAL'
	
	conn = Db.getConnection()
	stmt = conn.prepareStatement('''
	                      select * from table(cwms_level.retrieve_location_level_values(
	                      p_location_level_id => :1,
	                      p_level_units       => :2,
	                      p_start_time        => to_date(:3, 'ddmonyyyy hh24mi'),
	                      p_end_time          => to_date(:4, 'ddmonyyyy hh24mi'),
	                      p_timezone_id       => :5))
	                ''')   
	stmt.setString(1, level_1aId)
	stmt.setString(2, level_1a.units)
	stmt.setString(3, StartTimeStr)
	stmt.setString(4, EndTimeStr)
	stmt.setString(5, Db.getTimeZoneName())
	rs = stmt.executeQuery()
	
	while rs.next() : 
		return rs.getDouble(2)

#
# Main script
#
try : 
	#
	# Global variables
	#
	global Db
	
	#
	# Input data
	#
	debug = True
	
	# Bulletin variables
	HourlyVariables = ['ElevInstHr']
	DailyVariables = ['StorInstDay', 'FlowInAveDay', 'FlowTotalAveDay']
	
	# Bulletin location DCP Ids
	DcpIds = ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT', 'SYS']
	
	# Data dictionary
	DataDict =	{	'FTPK'				:	{	'Location'				: 'FTPK-Fort_Peck_Dam-Missouri',
												'StorInstDay'			: None,
												'FlowInAveDay'			: None,
												'FlowTotalAveDay'		: None,
												'MidnightElev'			: None,
												'DailyElevChange'		: None,
												'TopOfConservationElev'	: None,
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeElev'	: None,
												'TopOfMultipurposeStor'	: None,
												},
					'GARR'				:	{	'Location'				: 'GARR-Garrison_Dam-Missouri',
												'StorInstDay'			: None,
												'FlowInAveDay'			: None,
												'FlowTotalAveDay'		: None,
												'MidnightElev'			: None,
												'DailyElevChange'		: None,
												'TopOfConservationElev'	: None,
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeElev'	: None,
												'TopOfMultipurposeStor'	: None,
												},
					'OAHE'				:	{	'Location'				: 'OAHE-Oahe_Dam-Missouri',
												'StorInstDay'			: None,
												'FlowInAveDay'			: None,
												'FlowTotalAveDay'		: None,
												'MidnightElev'			: None,
												'DailyElevChange'		: None,
												'TopOfConservationElev'	: None,
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeElev'	: None,
												'TopOfMultipurposeStor'	: None,
												},
					'BEND'				:	{	'Location'				: 'BEND-Big_Bend_Dam-Missouri',
												'StorInstDay'			: None,
												'FlowInAveDay'			: None,
												'FlowTotalAveDay'		: None,
												'MidnightElev'			: None,
												'DailyElevChange'		: None,
												'TopOfConservationElev'	: None,
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeElev'	: None,
												'TopOfMultipurposeStor'	: None,
												},
					'FTRA'				:	{	'Location'				: 'FTRA-Fort_Randall_Dam-Missouri',
												'StorInstDay'			: None,
												'FlowInAveDay'			: None,
												'FlowTotalAveDay'		: None,
												'MidnightElev'			: None,
												'DailyElevChange'		: None,
												'TopOfConservationElev'	: None,
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeElev'	: None,
												'TopOfMultipurposeStor'	: None,
												},
					'GAPT'				:	{	'Location'				: 'GAPT-Gavins_Point_Dam-Missouri',
												'StorInstDay'			: None,
												'FlowInAveDay'			: None,
												'FlowTotalAveDay'		: None,
												'MidnightElev'			: None,
												'DailyElevChange'		: None,
												'TopOfConservationElev'	: None,
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeElev'	: None,
												'TopOfMultipurposeStor'	: None,
												},
					'SYS'				:	{	'Location'				: 'SYS-Missouri_River_Mainstem',
												'TopOfConservationStor'	: None,
												'TopOfMultipurposeStor'	: None,
												'StorInstDay'			: None,
												},
					'ElevInstHr'		: '%s.Elev.Inst.1Hour.0.mrrppcs-rev',
					'StorInstDay'		: '%s.Stor.Inst.~1Day.0.mrrppcs-rev',
					'FlowInAveDay'		: '%s.Flow-In.Ave.~1Day.1Day.mrrppcs-rev',
					'FlowTotalAveDay'	: '%s.Flow-Total.Ave.~1Day.1Day.mrrppcs-rev',
					'TopOfConservation'	: '%s.Elev.Inst.0.0.Top of Conservation',
					'TopOfMultipurpose'	: '%s.Elev.Inst.0.0.Top of Multipurpose',
					'StorCurve'			: '%s.Elev-Estimated;Stor.USGS-EXSA.Production',
					'CFStoACRE-FT'		: 86400.0/43560.0,
					'ACRE-FTtoCFS'		: 43560.0/86400.0
					}
	#
	# Date and time data
	#
	CurDate			= datetime.datetime.now() # Current date
	DbStartTw		= CurDate - datetime.timedelta(2) # Database start of time window
	DbStartTwStr	= DbStartTw.strftime('%d%b%Y ') + '2400' 
	DbEndTw			= CurDate - datetime.timedelta(1) # Database end of time window
	DbEndTwStr		= DbEndTw.strftime('%d%b%Y ') + '2400' 
	PdcTime			= int(time.time() * 1000) # Time used for retrieving the PDC storage and area curves
	
	#
	# Open the CWMS database and set the timezone, time window, and officeID
	#
	Db = DBAPI.open()
	Db.setTimeZone('US/Central') # Set timezone.  This timezone will adjust for DST
	Db.setTimeWindow(DbStartTwStr, DbEndTwStr)
	Db.setOfficeId('NWDM')

	#
	# Retrieve data from database and calculate other variables
	#
	for DcpId in DcpIds :
		if DcpId == 'SYS' :
			# System storage data
			DataDict[DcpId]['TopOfConservationStor'] = DataDict['FTPK']['TopOfConservationStor'] + \
					DataDict['GARR']['TopOfConservationStor'] + DataDict['OAHE']['TopOfConservationStor'] + \
					DataDict['BEND']['TopOfConservationStor'] + DataDict['FTRA']['TopOfConservationStor'] + \
					DataDict['GAPT']['TopOfConservationStor']

			DataDict[DcpId]['TopOfMultipurposeStor'] = DataDict['FTPK']['TopOfMultipurposeStor'] + \
					DataDict['GARR']['TopOfMultipurposeStor'] + DataDict['OAHE']['TopOfMultipurposeStor'] + \
					DataDict['BEND']['TopOfMultipurposeStor'] + DataDict['FTRA']['TopOfMultipurposeStor'] + \
					DataDict['GAPT']['TopOfMultipurposeStor']
			outputDebug(debug, lineNo(), '%s Top of Conservation Storage = %.0f ac-ft' % (DcpId, DataDict[DcpId]['TopOfConservationStor']),
				'\t%s Top of Multipurpose Storage = %.0f ac-ft' % (DcpId, DataDict[DcpId]['TopOfMultipurposeStor']))
		else :
			# Retrieve the elevation-storage curve
			StorCurvePdc = Db.read(DataDict['StorCurve'] % DataDict[DcpId]['Location'])
			# Set time associated with AreaCurvePdc and StorCurvePdc curves so data an be accessed
			StorCurvePdc.setDefaultValueTime(PdcTime)
			
			# Reservoir zone data
			DataDict[DcpId]['TopOfConservationElev'] = retrieveReservoirZone(debug, DataDict['TopOfConservation'] % DataDict[DcpId]['Location'])
			DataDict[DcpId]['TopOfConservationStor'] = StorCurvePdc.rate(DataDict[DcpId]['TopOfConservationElev'])
			DataDict[DcpId]['TopOfMultipurposeElev'] = retrieveReservoirZone(debug, DataDict['TopOfMultipurpose'] % DataDict[DcpId]['Location'])
			DataDict[DcpId]['TopOfMultipurposeStor'] = StorCurvePdc.rate(DataDict[DcpId]['TopOfMultipurposeElev'])
			outputDebug(debug, lineNo(), '%s Top of Conservation Elevation = %.2f ft' % (DcpId, DataDict[DcpId]['TopOfConservationElev']),
				'\t%s Top of Conservation Storage = %.0f ac-ft' % (DcpId, DataDict[DcpId]['TopOfConservationStor']))
		
		# Hourly variables
		for variable in HourlyVariables :
			try :
				outputDebug(debug, lineNo(), 'Processing %s at %s' % (variable, DcpId))
				if variable == 'ElevInstHr' : 
					Hm = Db.read(DataDict[variable] % DataDict[DcpId]['Location'])
					Hm = Hm.extractTimeSeriesDataForTimeSpecification('TIME', '2400', True, 0, True)
					Tsc = Hm.getData()
					for x in range(len(Tsc.times)) :
						hecTime = HecTime(); hecTime.set(Tsc.times[x])
						outputDebug(debug, lineNo(), hecTime.dateAndTime(4), ' ', Tsc.values[x])
					
					DataDict[DcpId]['MidnightElev'] = Tsc.values[-1]
					DataDict[DcpId]['DailyElevChange'] = Tsc.values[-1] - Tsc.values[0]
					outputDebug(debug, lineNo(), '%s Daily Elevation Change = %.2f ft' % (DcpId, DataDict[DcpId]['DailyElevChange']))
			except :
				outputDebug(debug, lineNo(), '%s does not exist at %s' % (variable, DcpId))
		
		# Daily variables
		for variable in DailyVariables : 
			try : 
				outputDebug(debug, lineNo(), 'Processing %s at %s' % (variable, DcpId))
				Tsc = Db.get(DataDict[variable] % DataDict[DcpId]['Location'])
				DataDict[DcpId][variable] = Tsc.values[-1]
				outputDebug(debug, lineNo(), '%s %s = %.0f %s' % (DcpId, variable, DataDict[DcpId][variable], Tsc.units))
			except :
				outputDebug(debug, lineNo(), '%s does not exist at %s' % (variable, DcpId))

	#
	# Create Reservoir Bulletin form
	#
	ReservoirBulletinForm = reservoirBulletin(debug, DataDict)
	print ReservoirBulletinForm

	#
	# Create pdf
	#
	createPdf(	'C:/Local_Software/CWMS/v3.0.3.50/common/jar/itextpdf.jar', 
				'C:/Users/G6EDXRJL/Desktop/ReservoirBulletin.pdf', 
				ReservoirBulletinForm
				)
finally :
	try : Db.done()
	except : pass