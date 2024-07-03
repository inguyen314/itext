# name=|NWO Reservoir Bulletin|
# displayinmenu=true
# displaytouser=true
# displayinselector=true
'''
Author: Ryan Larsen
Last Updated: 04-19-2018
Description: Create the Division River Bulletin
'''

# PC pathnames
'''
iTextPdfPathname = "C:\\Local_Software\\CWMS\\v3.1.0.781\\CAVI\\jar\\sys\\iText-5.0.6.jar"#"D:\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\Bulletins\\itextpdf.jar"
BulletinFilename = "D:\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\Bulletins\\NWO_Reservoir\\MRBWM_River_Daily_iText.pdf"
BulletinTsFilePathname = "D:\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\Bulletins\\Bulletins_Time_Series.txt"
BulletinPropertiesPathname = "D:\\Projects\\HEC_DSSVue_Scripts\\MRBWM\\NWO-CWMS2_Scripts\\Bulletins\\NWO_Reservoir\\NWO_Reservoir_Bulletin_Properties_20180131.txt"
'''

#
# Imports
#
import os, sys, inspect, datetime, time, DBAPI
try : 
    if iTextPdfPathname not in sys.path : sys.path.append(iTextPdfPathname)
except : 
    pass
from com.itextpdf.text      import Document, DocumentException, Rectangle, Paragraph, Phrase, Chunk, Font, FontFactory, BaseColor, PageSize, Element, Image
from com.itextpdf.text.Font import FontFamily
from com.itextpdf.text.pdf  import PdfWriter, PdfPCell, PdfPTable, PdfPage, PdfName, PdfPageEventHelper, BaseFont
from hec.data.cwmsRating    import RatingSet
from hec.heclib.util        import HecTime
from hec.io                 import TimeSeriesContainer
from hec.script             import Constants, MessageBox
from java.awt.image         import BufferedImage
from java.io                import FileOutputStream, IOException
from java.lang              import System
from java.text              import NumberFormat
from java.util              import Locale
from time                   import mktime, localtime
from subprocess             import Popen

#
# File pathnames
#
BulletinScriptDirectory = os.path.dirname(os.path.realpath(__file__))
PathList = BulletinScriptDirectory.split('/')
HomeDirectory = '/'.join(PathList[: -1]) + '/'
BulletinScriptDirectory += '/'
BulletinFilename = HomeDirectory + 'MRBWM_River_Daily_iText.pdf'
BulletinTsFilePathname = HomeDirectory + 'Bulletins_Time_Series.txt'
BulletinPropertiesPathname = BulletinScriptDirectory + 'NWD_River_Properties.txt'
#
# Input
#
# Set debug = True to print all debug statements and = False to turn them off
debug = False

# Import variables in the time series and properties files
BulletinTsFile = open(BulletinTsFilePathname, "r"); exec(BulletinTsFile)
BulletinProperties = open(BulletinPropertiesPathname, "r"); exec(BulletinProperties)

##################################################################################################################################
#
# Functions
#

#
# bulletinFooter Function   : Creates a footer for the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def bulletinFooter( debug,  # Set to True to print all debug statements
                    Footer  # PdfPTable object
                    ) :
    # Add the footer image to the footer
    Img = Image.getInstance(FooterImage)
    Img.scalePercent(20)
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Img, TableLayoutDict['Table1']['RowSpan'], TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_LEFT, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Footer.addCell(Cell)

    # Add the page numbers to the footer
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('Page %d of 1' % Writer.getPageNumber(), TableLayoutDict['Table1']['TextFont'])), TableLayoutDict['Table1']['RowSpan'], 
        TableLayoutDict['Table1']['ColSpan'], TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], 
        TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], TableLayoutDict['Table1']['BorderWidths'], 
        TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Footer.addCell(Cell)
    
    return Footer

#
# createCell Function   : Creates a PdfPCell for tables
# Author/Editor         : Ryan Larsen
# Last updated          : 12-20-2017
#
def createCell( debug,                  # Set to True to print all debug statments
                CellData,               # Data that will appear within the cell
                RowSpan,                # Specifies number of rows information within cell will span
                ColSpan,                # Specifies number of columns information within cell will span
                HorizontalAlignment,    # Specifies horizontal alignment: ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT
                VerticalAlignment,      # Specifies vertical alignment: ALIGN_CENTER, ALIGN_TOP, ALIGN_BOTTOM
                CellPadding,            # List of cell padding around text: [Top, Right, Bottom, Left]
                BorderColors,           # List of border colors: [Top, Right, Bottom, Left]
                BorderWidths,           # List of border widths: [Top, Right, Bottom, Left]
                VariableBorders,        # Allows or denies variable borders: True, False
                BackgroundColor         # Color of cell background
                ) :
    Cell = PdfPCell(CellData)
    Cell.setRowspan(RowSpan); Cell.setColspan(ColSpan)
    Cell.setHorizontalAlignment(HorizontalAlignment); Cell.setVerticalAlignment(VerticalAlignment)
    Cell.setPaddingTop(CellPadding[0]); Cell.setPaddingRight(CellPadding[1]); Cell.setPaddingBottom(CellPadding[2]); Cell.setPaddingLeft(CellPadding[3])
    Cell.setBorderColorTop(BorderColors[0]); Cell.setBorderColorRight(BorderColors[1]); Cell.setBorderColorBottom(BorderColors[2]); Cell.setBorderColorLeft(BorderColors[3])
    Cell.setBorderWidthTop(BorderWidths[0]); Cell.setBorderWidthRight(BorderWidths[1]); Cell.setBorderWidthBottom(BorderWidths[2]); Cell.setBorderWidthLeft(BorderWidths[3])
    Cell.setUseVariableBorders(VariableBorders)
    Cell.setBackgroundColor(BackgroundColor)

    return Cell

#
# lineNo Function   : Retrieves the line number of the script.  Used when debugging
# Author/Editor     : Ryan Larsen
# Last updated      : 12-09-2016
#
def lineNo() :
    return inspect.currentframe().f_back.f_lineno

#
# outputDebug Function  : Debugging function that prints specified arguments
# Author/Editor         : Ryan Larsen
# Last updated          : 03-27-2017
#
def outputDebug(    *args
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
###########################################################################################
#
# retrieveElevatonDatum Function : Retrieves Elevation datum
# Author/Editor                  : Scott Hoffman
# Last updated                   : 06-25-2018
#
def retrieveElevatonDatum(debug,        # Set to True to print all debug statements
                        conn,           #
                        BaseLocation,   # Full name of time series container
                        ) :
    try :
        stmt = conn.prepareStatement('''
                                    select distinct
                                    bl.elevation as base_location_elevation
                                    from cwms_v_loc loc
                                    inner join cwms_v_loc bl on bl.base_location_code = loc.base_location_code
                                        and bl.db_office_id = loc.db_office_id
                                        and bl.unit_system = loc.unit_system
                                    where loc.UNIT_SYSTEM = 'EN'
                                        and loc.db_office_id = :1
                                        and bl.location_id = :2
                                    ''')
        stmt.setString(1, 'NWDM')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()

        while rs.next() :
            ElevationDatum = str(rs.getString(1))
            break
    finally :
        stmt.close()
        rs.close()
	#print "Got ElevDatum: " + str(ElevationDatum)  
    return ElevationDatum
##############################################################################################
#
# retrievePublicName Function    : Retrieves reservoir zone data
# Author/Editor                  : Ryan Larsen
# Last updated                   : 01-30-2018
#
def retrievePublicName( debug,          # Set to True to print all debug statements
                        conn,           # 
                        BaseLocation,   # Full name of time series container
                        ) :
    try :
        stmt = conn.prepareStatement('''
                                    select distinct
                                    bl.public_name as base_location_public_name
                                    from cwms_v_loc loc 
                                    inner join cwms_v_loc bl on bl.base_location_code = loc.base_location_code
                                        and bl.db_office_id = loc.db_office_id 
                                        and bl.unit_system = loc.unit_system
                                    where loc.UNIT_SYSTEM = 'EN' 
                                        and loc.db_office_id = :1 
                                        and bl.location_id = :2
                                    ''')   
        stmt.setString(1, 'NWDM')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()
        
        while rs.next() : 
            PublicName = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()

    return PublicName
#################################################################################################
#
# checkTs Function    : Check if the TS is in the database
# Author/Editor       : Scott Hoffman
#
def checkTs(timeseries,
            conn,) :
    try :
       stmt = conn.createStatement()
       #check if timeseries exist in DB
       sql = "select * from CWMS_20.av_cwms_ts_id where cwms_ts_id='" + timeseries + "'"
       #print "sql: " + sql		
       rset = stmt.executeQuery(sql)
       if rset.next() :
          #Found timeseries
          flag = 'true'
       else :
          flag = 'false'
          #print "\nTimeseries not found in the database: " + timeseries
    finally :
       stmt.close()
       rset.close()
    return flag
################################################################################################
#
# retrieveLocationLevel Function    : Retrieves reservoir zone data
# Author/Editor                     : Mike Perryman
# Last updated                      : 05-01-2017
#
def retrieveLocationLevel(  debug,          # Set to True to print all debug statements
                            conn,           # 
                            CwmsDb,         # DBAPI connection
                            TscFullName,    # Full name of time series container
                            ) :
    CurDate         = datetime.datetime.now() # Current date
    StartTimeStr    = CurDate.strftime('%d%b%Y ') + '0000' # Start date formatted as ddmmmyyy 0000
    EndTimeStr      = CurDate.strftime('%d%b%Y ') + '0000' # End date formatted as ddmmmyyy 0000

    level_1a = TimeSeriesContainer()
    level_1a_parts = TscFullName.split('.')
    level_1aId_parts = level_1a_parts[:]
    level_1aId = '.'.join(level_1aId_parts)
    #outputDebug(True, lineNo(), 'level_1a_parts = ', level_1a_parts, '\tlevel_1aId_parts = ', level_1aId_parts, '\n\t\tlevel_1aId = ', level_1aId) 
    
    level_1a.fullName  = TscFullName
    level_1a.location  = level_1a_parts[0]
    level_1a.parameter = level_1a_parts[1]
    level_1a.interval  = 0
    level_1a.version   = level_1a_parts[-1]
    if level_1a_parts[1] == 'Stor' : level_1a.units = 'ac-ft'
    elif level_1a_parts[1] == 'Elev' : level_1a.units = 'ft'
    elif level_1a_parts[1] == 'Flow' : level_1a.units = 'cfs'
    elif level_1a_parts[1] == 'Stage' : level_1a.units = 'ft'
    level_1a.type      = 'INST-VAL'
    
    try :
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
	#stmt.setString(2, 'ft')	
        stmt.setString(3, StartTimeStr)
        stmt.setString(4, EndTimeStr)
        stmt.setString(5, CwmsDb.getTimeZoneName())
        rs = stmt.executeQuery()
        while rs.next() : 
            LocationLevel = rs.getDouble(2)
            break
    finally :
        stmt.close()
        rs.close()
    
    return LocationLevel
###################################################################################################
#
# table1Data Function   : Creates the Data1 block for Table1 in the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def table1Data( debug,      # Set to True to print all debug statements
                Table,      # PdfPTable object
                TableName,  # String name for the table
                DataName,    # String name for data section of table
		startTime,
		endTime,
		startSysTime,
		endSysTime
                ) :
    # Create name for TableData
    TableDataName = '%s%s' % (TableName, DataName)
    # Data Block Heading
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    if DataName == 'Data1' or DataName == 'Data3':
        Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font9)), TableLayoutDict[TableName]['RowSpan'], 
            Table1Columns, Element.ALIGN_CENTER, TableLayoutDict[TableName]['VerticalAlignment'], [1, 2, 1, 3], TableLayoutDict[TableName]['BorderColors'], 
            [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
    elif DataName == 'Data4' :
	textString = "Selected River Gaging Stations as of 6:00 a.m."
	Cell = createCell(debug, Phrase(Chunk(textString, Font9)), TableLayoutDict[TableName]['RowSpan'],
            Table1Columns, Element.ALIGN_CENTER, TableLayoutDict[TableName]['VerticalAlignment'], [1, 2, 1, 3], TableLayoutDict[TableName]['BorderColors'],
            [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7) 
	Table.addCell(Cell)
	textString = "Yellowstone River"
	Cell = createCell(debug, Phrase(Chunk(textString, Font9)), TableLayoutDict[TableName]['RowSpan'],
            Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [1, 2, 1, 3], TableLayoutDict[TableName]['BorderColors'],
            [0.5, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
    else :
        Cell = createCell(debug, Phrase(Chunk(DataBlockDict['DataBlocks'][TableDataName]['Heading'], Font9)), TableLayoutDict[TableName]['RowSpan'],
            Table1Columns, Element.ALIGN_LEFT, TableLayoutDict[TableName]['VerticalAlignment'], [1, 2, 1, 3], TableLayoutDict[TableName]['BorderColors'],
            [0.25, 1, 0.25, 1], TableLayoutDict[TableName]['VariableBorders'], Color7)
    Table.addCell(Cell)

    # Data
    for project in DataBlockDict['DataBlocks'][TableDataName]['ProjectList'] :

        # Retrieve Public Name and store it to the DataBlockDict
        PublicName = LocationDict[project]['BulletinName']
        outputDebug(debug, lineNo(), 'Creating %s row' % PublicName)
        
        # If adding the last project in the last data block, create a trigger to use a thick bottom border
        if DataName == DataBlocks[-1] and project == DataBlockDict['DataBlocks'][TableDataName]['ProjectList'][-1] :
            LastProject = True
        else : LastProject = False

        for data in DataOrder :
            outputDebug(debug, lineNo(), 'Adding %s to the row' % data)
            # Create a variable within the DataDict. This will allow the user to store all data to a dictionary and access the variables throughout
            #   the script
            DataBlockDict['DataBlocks'][TableDataName].setdefault(project, {}).setdefault(data, None)

            # Get column number
            ColumnKey = 'Column%d' % DataOrder.index(data)

            # Default cell properties. If there is a special case, the properties will be changed.
            TextFont = TableLayoutDict[TableName]['TextFont']
	    if project in ['SYS'] :
		RowSpan = 3;
            else :
                RowSpan = TableLayoutDict[TableName]['RowSpan']; 
             
            ColSpan = TableLayoutDict[TableName]['ColSpan']   
            HorizontalAlignment = TableLayoutDict[TableName]['HorizontalAlignment']; VerticalAlignment = TableLayoutDict[TableName]['VerticalAlignment']
            #CellPadding = TableLayoutDict[TableName]['CellPadding']
	    CellPadding = [0, 2, 1, 3] #[Top, Right, Bottom, Left]
            BorderColors = TableLayoutDict[TableName]['BorderColors']
            BorderWidths = TableLayoutDict[TableName]['BorderWidths']
            VariableBorders = TableLayoutDict[TableName]['VariableBorders']
            BackgroundColor = TableLayoutDict[TableName]['BackgroundColor']
            
            # 0 - Project Bulletin Name
            if data == 'PublicName' :
                # Create a formatted string that will be added to the table
                CellData = Phrase(Chunk(PublicName, TextFont))
                # Change default cell properties
                HorizontalAlignment = Element.ALIGN_LEFT
                BorderColors = [Color2, Color3, Color2, Color2]
                CellPadding = [1, 2, 1, 7] #[Top, Right, Bottom, Left]#Indent the project names               
		if LastProject : BorderWidths = [0.25, 0.25, 1, 1] #[Top, Right, Bottom, Left]
		else : BorderWidths = [0.25, 0.25, 0.25, 1] #[Top, Right, Bottom, Left]
            # 1 - River Mile
            elif data == 'RiverMile' :
                try :
                    if project not in ['SYS'] : 
                        RivMile = LocationDict[project]['RiverMile']
                        # Create a formatted string that will be added to the table
			CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % RivMile, TextFont))
                    else :
			CellData = Phrase(Chunk(Null, TextFont))

                except Exception, e :
                    print "River Mile Exception = " + str(e) 
                    RivMile = Missing
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

		#if project not in ['SYS'] :
                   # Store value to DataDict
                   #DataBlockDict['DataBlocks'][TableDataName][project][data] = RivMile 

                # Change default cell properties
                BorderColors = [Color2, Color2, Color2, Color3]
            # 2 - elevation datum
            elif data == 'ElevDatum' :
                try :
	 	    CellData = Phrase(Chunk(Null, TextFont))
                    if project in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT'] : 
                        ElevationDatum = Null
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Null, TextFont))
		    elif project in ['SYS'] :
			CellData = Phrase(Chunk(Null, TextFont))
                    else :
			#Get the Elvation Datum
			ElevationDatum = retrieveElevatonDatum(debug, conn, project)
			#print "ElevationDatum: " + str(ElevationDatum)
                        
                        # Create a formatted string that will be added to the table
			if ElevationDatum == Null or ElevationDatum == 'None' :
			   CellData = Phrase(Chunk(Null, TextFont))
			else :
			   CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % float(ElevationDatum), TextFont))
			#print "CellData: " + str(CellData) 

		except Exception, e :
                    print "Elevation Datum Exception = " + str(e)	
                    # Create a formatted string that will be added to the table
                    CellData = Phrase(Chunk(Missing, TextFont))

            # 3 - Flood Stage
            elif data == 'FloodStage' :
                try :
                    CellData = Phrase(Chunk(Missing, TextFont))
		    if project in ['SYS', 'FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT', 'CAFE', 'HAST', 'BAGL'] :
                        CellData = Phrase(Chunk(Null, TextFont)) 
                    else :
			id = str(LocationDict[project]['DbLocation']).split("-")
			TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % id[0] 
			#print "floodstag TscPathname: " + str(TscPathname)
		        NwsFloodStage = retrieveLocationLevel(debug, conn, CwmsDb, TscPathname)
                        #print TscPathname, " |FS| " , NwsFloodStage
                            
			if NwsFloodStage != Null or NwsFloodStage != 'None' :
                            # Create a formatted string that will be added to the table
		            CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % NwsFloodStage, TextFont))
			else:
			    CellData = Phrase(Chunk(Missing, TextFont))
		except Exception, e :
                    print "FloodStage Exception = " + str(e)

             # 4 - Elevation
            elif data == 'Elevation' :
		if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
		   TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']	
		   #print "TscPathname elev: " + str(TscPathname) + " " + data 
		   if checkTs(TscPathname, conn) == 'true' or project in ['CAFE'] :
		      if project not in ['SYS'] :
                         try :
		             if project in ['CAFE'] : 
		   	        Ts = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
			        Ts = Ts.replace("Combined-rev", "usbr-rev")
				Tsc = CwmsDb.get(Ts, startTime, endTime)
			     elif project in ['HAST', 'BAGL'] :
				Ts = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
				Tsc = CwmsDb.get(Ts, startTime, endTime)
		             else : 
			        Tsc = CwmsDb.read(DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']).getData()
			  	
                             PrevElev = Tsc.values[-1] # Previous day's midnight value
                             Prev2xElev = Tsc.values[0] # 2 days previous midnight value
			     #print "PrevElev: " + str(PrevElev) + str(project)
			     #print "Prev2xElev: " + str(Prev2xElev)
                    
		             # If previous day's value is missing raise an exception and using the missing value
                             if PrevElev == Constants.UNDEFINED : raise ValueError 
                             elif Prev2xElev == Constants.UNDEFINED : Prev2xElev = Missing 
		    
		             # Create a formatted string that will be added to the table
                             CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % PrevElev, TextFont))

                         except Exception, e :
		            print "Elevation Exception = " + str(e)
                            PrevElev, Prev2xElev = Missing, Missing
                            # Create a formatted string that will be added to the table
                            CellData = Phrase(Chunk(Missing, TextFont))

                         # Store value to DataDict
                         outputDebug(debug, lineNo(), 'Set %s %s = ' % (project, data), PrevElev)
                         DataBlockDict['DataBlocks'][TableDataName][project][data] = PrevElev
                         DataBlockDict['DataBlocks'][TableDataName][project][data + '2x'] = Prev2xElev
		   else :
                     #None, set value to Null
                     CellData = Phrase(Chunk(Missing, TextFont))
		else :
                   #None, set value to Null
                   CellData = Phrase(Chunk(Null, TextFont))

            # 5 Daily elevation change
            elif data == 'ElevChange' :
                   try :
                       if project in ['SYS'] :
			  CellData = Phrase(Chunk('System Storage \n Storage Change \n Daily Generation', TextFont))
                          HorizontalAlignment = Element.ALIGN_RIGHT
                          ColSpan = 2
                       else :
                           if DataBlockDict['DataBlocks'][TableDataName][project]['Elevation'] == Missing or \
                               DataBlockDict['DataBlocks'][TableDataName][project]['Elevation2x'] == Missing :
                               raise ValueError
				
                           DlyElevChange = DataBlockDict['DataBlocks'][TableDataName][project]['Elevation'] - DataBlockDict['DataBlocks'][TableDataName][project]['Elevation2x']

                           # Create a formatted string that will be added to the table
                           CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % DlyElevChange, TextFont))
		   except Exception, e :
		       print "ElevChange Exception = " + str(e)	
                       DlyElevChange = Missing
                       # Create a formatted string that will be added to the table
                       CellData = Phrase(Chunk(Missing, TextFont))

            # 6 Storage, Inflow, Energy, and Flow Total
            elif data == 'FlowIn' or data == 'Storage' :
               if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
                TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
                if project in ['CAFE'] and data == 'FlowIn' :
                   TscPathname = TscPathname.replace("Ave.1Day.1Day.Combined-rev", "Inst.1Day.0.usbr-rev")
                elif  project in ['CAFE'] and data == 'Storage' :
                   TscPathname = TscPathname.replace("Combined-rev", "usbr-rev")
                if checkTs(TscPathname, conn) == 'true' :
		    #print 'Valid Flow/Storage Timeseries: ' + TscPathname + " " + data
                    try :
                            if project in ['SYS'] :
                                if data == 'Storage' :
                                    tscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
				    Tsc = CwmsDb.get(tscPathname, startTime, endTime)
                                    Value = Tsc.values[0]
                                    Value = round(Value, 0)
                                    PrevStor = Value
                                    Value = Value/1000
                                    CellData =  Chunk(TableLayoutDict[TableName][ColumnKey][1]['Format'].format(int(Value)), TextFont)

                                    tscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
				    Tsc2 = CwmsDb.get(tscPathname, startSysTime, endSysTime)
                                    Value2 = Tsc2.values[0]
			 	    #print "Value2: " + str(Value2)
                                    Value2 = round(Value2, 0)
                                    Value2 = (PrevStor - Value2)/1000
                                    CellData2 =  Chunk(TableLayoutDict[TableName][ColumnKey][1]['Format'].format(int(Value2)), TextFont)

                                    tscPathname = tscPathname.replace("Stor.Inst.~1Day.0", "Energy.Total.~1Day.1Day")
				    Tsc3 = CwmsDb.get(tscPathname, startTime, endTime)
                                    Value3 = Tsc3.values[-1]
                                    Value3 = round(Value3, 0)
                                    CellData3 =  Chunk(TableLayoutDict[TableName][ColumnKey][1]['Format'].format(int(Value3)), TextFont)
                                    CellData = Phrase(str(CellData) + '\n' + str(CellData2) + '\n' + str(CellData3), TextFont)
                                else :
                                    Value = 0.
                                    CellData = Phrase(Chunk(Missing, TextFont))
                            else : #All Other projects
				Tsc = CwmsDb.get(TscPathname, startTime, endTime)

                                if data == 'FlowIn' and project in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT','CAFE', 'HAST', 'BAGL'] :
                                   TscPathname2 = TscPathname.replace("Flow-In", "Flow-Total")
				   Tsc2 = CwmsDb.get(TscPathname2, startTime, endTime)
                                   Value2 = Tsc2.values[-1]
                                   Value2 = round(Value2, 0)
                                elif data == 'Storage' and project in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT', 'HAST', 'BAGL'] :
				   if project in ['HAST']:	
				      TscPathname2 = TscPathname.replace("Stor.Inst.1Day.0", "Energy-Total_Generation.Total.1Day.1Day")
                                      Tsc2 = CwmsDb.get(TscPathname2, startTime, endTime)
                                      Value2 = Tsc2.values[-1]
                                      Value2 = round(Value2, 0) 	
				   else :
                                      TscPathname2 = TscPathname.replace("Stor.Inst.~1Day.0", "Energy.Total.~1Day.1Day")
				      Tsc2 = CwmsDb.get(TscPathname2, startTime, endTime)
                                      Value2 = Tsc2.values[-1]
                                      Value2 = round(Value2, 0)
				elif data == 'Storage' and project in ['CAFE', 'BAGL'] :#Only a storage value no energy for 2 projects
				   Tsc2 = CwmsDb.get(TscPathname, startTime, endTime)
				   Value2 = Tsc2.values[-1]/1000
				   Value2 = round(Value2, 0)

                                if Tsc != Null and not project in ['WSN', 'PONE', 'BLNE', 'JEFM' ] :
                                   Value = Tsc.values[-1]
                                   if data == 'Storage' :
                                      Value = Tsc.values[-1]/1000
                                   Value = round(Value, 0)
				else :
				   Value = Null


                                # If value is missing raise an exception and using the missing value
                                if Value == Constants.UNDEFINED : raise ValueError

                                # Create a formatted string that will be added to the table
                                if Value == Null :
                                    CellData = Phrase(Chunk(Null, TextFont))
                                else :
                                  if (data == 'FlowIn' or data == 'Storage') and project in ['FTPK', 'GARR', 'OAHE', 'BEND', 'FTRA', 'GAPT','CAFE', 'HAST', 'BAGL'] :

				     #Check for valid values FlowIn or Storage
				     if int(Value) >= 0 :  		
                                        CellData = Chunk(TableLayoutDict[TableName][ColumnKey][1]['Format'].format(int(Value)), TextFont)
				     else :
					CellData = Chunk(Missing, TextFont)

				     #Check for valid values Storage or Energy
				     if int(Value2) >= 0 : 
					if (data == 'Storage') and project in ['BAGL', 'CAFE']:
					   cellx = '%s' % ('--')
					   CellData2 = Chunk(cellx)
					else:
                                           CellData2 = Chunk(TableLayoutDict[TableName][ColumnKey][2]['Format'].format(int(Value2)), TextFont)
				     else :
					CellData2 = Chunk(Missing, TextFont)

				     #Combine the 2 cells of data
				     CellData3 = Chunk('/')
				     cellInfo = '%s%s%s' % (CellData, CellData3, CellData2)
				     CellData = Phrase(cellInfo, TextFont)
                                  else :
                                     if data == 'FlowIn' :
                                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey][1]['Format'].format(int(Value)), TextFont)) #formatting, comma separator
                                     else :
                                        CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(Value)), TextFont))

                    except Exception, e :
                        print "Flow/Storage Exception = " + str(e) +  " -  " + project
                        Value = Missing
                        # Create a formatted string that will be added to the table
                        CellData = Phrase(Chunk(Missing, TextFont))
                else :
                   #Timeseries not found in the database, set value to Null
                   CellData = Phrase(Chunk(Null, TextFont))
               else :
		  if project in ['SYS'] and data == 'FlowIn' :
		     ColSpan = 0
		  else :
                   #None, set value to Null
                   CellData = Phrase(Chunk(Null, TextFont))	

	       # 7  AirTempMax, AirTempMin, and Precip
            elif data == 'AirTempMax' or data == 'AirTempMin' or data == 'Precip' :
               if str(DataBlockDict['DataBlocks'][TableDataName][data]) != 'None' :
                  TscPathname = DataBlockDict['DataBlocks'][TableDataName][data] % LocationDict[project]['DbLocation']
                  if checkTs(TscPathname, conn) == 'true' :
                      try :
                          Value = 0.
                          CellData = Phrase(Chunk(Missing, TextFont))
			  Tsc = CwmsDb.get(TscPathname, startTime, endTime)
                          #print "air/precip Tsc value= " + str(Tsc.values[-1])

                          if Tsc != Null :
                              Value = Tsc.values[-1]

                          if project in ['CAFE'] and data == 'Precip' :
			     CellData = Phrase(Chunk(Null, TextFont))
                          elif project in ['CAFE', 'BAGL', 'HAST' ] and (data == 'AirTempMax' or data == 'AirTempMin') :
                             CellData = Phrase(Chunk(Null, TextFont))
                          elif data == 'Precip' :
			     if float(Value) > -1 :
                                CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'] % float(Value), TextFont))
			     else :
				CellData = Phrase(Chunk(Missing, TextFont))	
                          else:
                             Value = round(Value, 0)
			     if Value > -60 :
                                CellData = Phrase(Chunk(TableLayoutDict[TableName][ColumnKey]['Format'].format(int(Value)), TextFont))
			     else :
				CellData = Phrase(Chunk(Missing, TextFont))

                      except Exception, e :
                         print "AirTemp/Precip Exception = " + str(e)
                         CellData = Phrase(Chunk(Missing, TextFont))
                  else :
                     #Timeseries not found in the database, set value to Null
                    CellData = Phrase(Chunk(Null, TextFont))
	       else :
                   #Precip set to None
		    if project in ['SYS'] and data == 'Precip':
                        CellData = Phrase(Chunk('KAF\nKAF\nMwh', TextFont))
			HorizontalAlignment = Element.ALIGN_LEFT 
                    else :	
                        CellData = Phrase(Chunk(Null, TextFont))	

	    if project in ['SYS'] and data == 'FlowIn' :
		print "SYS project has no Flow-In values."
	    else : 
	       if data == 'AirTempMin' and not LastProject :
	 	   BorderWidths = [0.25, 1, 0.25, 0.25] #[Top, Right, Bottom, Left] 
	       elif data == 'AirTempMin' and LastProject :
		   BorderWidths = [0.25, 1, 1, 0.25] #[Top, Right, Bottom, Left]

	       if LastProject and data != 'AirTempMin' and data != 'PublicName' : BorderWidths = [0.25, 0.25, 1, 0.25] #[Top, Right, Bottom, Left]
               Cell = createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
               Table.addCell(Cell)

    return Table	
#
# table1Heading Function    : Creates the heading for Table1 in the bulletin
# Author/Editor             : Ryan Larsen
# Last updated              : 12-12-2017
#
def table1Heading(  debug,  # Set to True to print all debug statements
                    Table  # PdfPTable object
                    ) :
    #
    # Create Table1 Heading 
    #
    # Column 0 Heading
    #createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    #0
    CellData = Phrase(Chunk('STATION', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 1] #[Top, Right, Bottom, Left]
    Cell = createCell(debug,CellData, 3, TableLayoutDict['Table1']['ColSpan'], Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color3, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #1
    CellData = Phrase(Chunk('Miles above\nMissouri R\nMouth (1960)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #2
    CellData = Phrase(Chunk('Elev\nDatum\n(ft msl)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #3
    CellData = Phrase(Chunk('Flood\nStage\n(feet)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #4
    CellData = Phrase(Chunk('Gage\nReading\n(feet)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #5
    CellData = Phrase(Chunk('24-Hr\nChange\n(feet)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #6
    CellData = Phrase(Chunk('Estimated\nDischarge\nIn/Out(cfs)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #7
    CellData = Phrase(Chunk('Actual\nStor/Gen\n(KAF/Mwh)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #8
    CellData = Phrase(Chunk('24-Hr\nPrecip\n(in)', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 0.25, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 1, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    #9
    CellData = Phrase(Chunk('Air Temp\n(deg F)\nHi  |  Lo', TableLayoutDict['Table1']['TextFont']))
    BorderWidths = [1, 1, 0.25, 0.25] #[Top, Right, Bottom, Left]
    Cell = createCell(debug, CellData, 3, 2, Element.ALIGN_CENTER, 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], [Color2, Color2, Color2, Color2], 
        BorderWidths, TableLayoutDict['Table1']['VariableBorders'], Color6)
    Cell.setFixedHeight(25)
    Table.addCell(Cell)
    return Table

#
# titleBlock Function   : Creates the title block for the bulletin
# Author/Editor         : Ryan Larsen
# Last updated          : 12-12-2017
#
def titleBlock( debug,      # Set to True to print all debug statements
                TitleBlock  # PdfPTable object
                ) :
    #
    # Add USACE Logo, title block lines, and seal to TitleBlock
    #
    TitleLines = [TitleLine1, TitleLine2, TitleLine3, TitleLine4]
    
    # Add the USACE Logo to the TitleBlock
    Img = Image.getInstance(UsaceLogo)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(Element.ALIGN_LEFT); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(60)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine1 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine1, Font15)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [1, 5, 1, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    
    # Add the seal to the TitleBlock
    Img = Image.getInstance(Seal)
    Cell = PdfPCell(Img, 1)
    Cell.setRowspan(len(TitleLines))
    Cell.setHorizontalAlignment(TableLayoutDict['Table1']['HorizontalAlignment']); Cell.setVerticalAlignment(TableLayoutDict['Table1']['VerticalAlignment'])
    Cell.setPaddingTop(2); Cell.setPaddingRight(2); Cell.setPaddingBottom(2); Cell.setPaddingLeft(2)
    Cell.setBorder(Rectangle.LEFT); Cell.setBorderColorLeft(Color1); Cell.setBorderWidthLeft(0.5)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine2 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine2, Font25)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 1, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)
    
    # Add TitleLine3 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine3 % ProjectDateTimeStr, Font15)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 1, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)

    # Add TitleLine4 to the TitleBlock
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk(TitleLine4 % CurDateTimeStr, Font15)), TableLayoutDict['Table1']['RowSpan'], Table1Columns - 2, 
        TableLayoutDict['Table1']['HorizontalAlignment'], TableLayoutDict['Table1']['VerticalAlignment'], [0, 5, 1, 2], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    TitleBlock.addCell(Cell)

    # Add a blank line to the TitleBlock to separate the TitleBlock from the table
    # createCell(debug, CellData, RowSpan, ColSpan, HorizontalAlignment, VerticalAlignment, CellPadding, BorderColors, BorderWidths, VariableBorders, BackgroundColor)
    Cell = createCell(debug, Phrase(Chunk('', Font15)), TableLayoutDict['Table1']['RowSpan'], Table1Columns, TableLayoutDict['Table1']['HorizontalAlignment'], 
        TableLayoutDict['Table1']['VerticalAlignment'], TableLayoutDict['Table1']['CellPadding'], TableLayoutDict['Table1']['BorderColors'], 
        TableLayoutDict['Table1']['BorderWidths'], TableLayoutDict['Table1']['VariableBorders'], TableLayoutDict['Table1']['BackgroundColor'])
    Cell.setBorder(Rectangle.NO_BORDER)
    Cell.setFixedHeight(4)
    TitleBlock.addCell(Cell)

    return TitleBlock

##################################################################
# Main Script
##################################################################
try :    
    #
    # Date and Time Window Info
    #
    CurDateTime = datetime.datetime.now()
    CurDateTimeStr  = CurDateTime.strftime('%m-%d-%Y %H:%M') # Last updated time for bulletin formatted as mm-dd-yyyy hhmm
    if UseCurDate :
        Date = datetime.datetime.now() # Current date
    else :
        TimeObj = time.strptime(HistoricBulletinDate, '%d%b%Y %H%M')
        TimeObj = localtime(mktime(TimeObj)) # Convert TimeObj to local time so it includes the DST component
        Date    = datetime.datetime.fromtimestamp(mktime(TimeObj))

    StartTw             = Date - datetime.timedelta(2)
    StartTwStr          = StartTw.strftime('%d%b%Y 2400') # Start of time window for the database formatted as ddmmmyyyy 2400
    EndTribTwStr        = Date
    TrimTribTwStr       = EndTribTwStr.strftime('%d%b%Y 0100')
    EndTw               = Date - datetime.timedelta(1)
    EndTribTw           = Date - datetime.timedelta(2)
    TrimTwStr           = EndTw.strftime('%d%b%Y 0100') # Trimmed time window for the database formatted as ddmmmyyyy 0100. Used for daily time series
    TribTrimTwStr       = EndTribTw.strftime('%d%b%Y 0100') # Trimmed time window for the database formatted as ddmmmyyyy 0100. Used for daily time series
    TrimTw7Str          = EndTribTwStr.strftime('%d%b%Y 0700') # Trimmed time window for the database formatted as ddmmmyyyy 0600. Used for daily time series
    EndTwStr            = EndTw.strftime('%d%b%Y 2400') # End of time window for the database formatted as ddmmmyyyy 2400
    EndTwStr2           = Date.strftime('%d%b%Y 0100') # End of time window for the database formatted as ddmmmyyyy 2400
    SysEndTwStr         = EndTribTw.strftime('%d%b%Y 2400') # End of time window for the database formatted as ddmmmyyyy 2400
    ProjectDateTimeStr  = EndTw.strftime('%m-%d-%Y 24:00') # Project date and time for bulletin formatted as mm-dd-yyyy 2400
    outputDebug(debug, lineNo(), 'Start of Time Window = ', StartTwStr, '\tEnd of Time Window = ', EndTwStr, 
        '\tProject Date and Time = ', ProjectDateTimeStr)
    
    #
    # Open database connection
    #
    CwmsDb = DBAPI.open()
    CwmsDb.setTimeZone('US/Central')
    CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
    CwmsDb.setOfficeId('NWDM')
    CwmsDb.setTrimMissing(False)
    conn = CwmsDb.getConnection()# Create a java.sql.Connection

    # 
    # Retrieve public names for all projects shown in bulletin. Remove 'Reservoir' from public name for spacing purposes
    #
    locations = LocationDict.keys()
    for location in locations :
        PublicName = retrievePublicName(debug, conn, location)
	if PublicName.find(" & Reservoir") != -1: 
            BulletinName = PublicName.replace(' & Reservoir', '')
	elif PublicName.find("Missouri R at") != -1:
	    BulletinName = PublicName.replace('Missouri R at ', '')
	elif PublicName.find("Missouri River at") != -1:
	    BulletinName = PublicName.replace('Missouri River at ', '')
	elif PublicName.find("Yellowstone R at") != -1:
	    BulletinName = PublicName.replace('Yellowstone R at ', '')
	elif PublicName.find("Yellowstone River nr") != -1:
	    BulletinName = PublicName.replace('Yellowstone River nr ', '')
	elif PublicName.find("Yellowstone R nr") != -1:
            BulletinName = PublicName.replace('Yellowstone R nr ', '')
	elif PublicName.find("Yellowstone at") != -1:
            BulletinName = PublicName.replace('Yellowstone at ', '')
	elif PublicName.find("Gasconade R nr") != -1:
           BulletinName = PublicName.replace('Gasconade R nr ', '')
	elif PublicName.find("Osage River bl") != -1:
           BulletinName = PublicName.replace('Osage River bl ', '')
	elif PublicName.find("Grand River near") != -1:
           BulletinName = PublicName.replace('Grand River near ', '')
	elif PublicName.find("Kansas River at") != -1:
           BulletinName = PublicName.replace('Kansas River at ', '')
	elif PublicName.find("Platte River at") != -1:
           BulletinName = PublicName.replace('Platte River at', '')
	elif PublicName.find("Big Sioux River at ") != -1:
           BulletinName = PublicName.replace('Big Sioux River at', '')
	elif PublicName.find("James River near") != -1:
           BulletinName = PublicName.replace('James River near ', '')
	elif PublicName.find("STL-St_Louis-Missouri") != -1:
           BulletinName = PublicName.replace('STL-St_Louis-Missouri', 'St. Louis, MO')
	elif PublicName.find("BIL") != -1:
           BulletinName = PublicName.replace('BIL', 'Billings, MT ')
	else :
	    BulletinName = PublicName
        #if location == 'COTT' : BulletinName = PublicName.replace(' & Res', '')
        LocationDict[location].setdefault('PublicName', PublicName)
        LocationDict[location].setdefault('BulletinName', BulletinName)
    
    #
    # Create tables with a finite number of columns that will be written to the pdf file
    #
    # TitleBlock: Contains the title block for the bulletin
    TitleBlock = PdfPTable(Table1Columns)
    
    # Table1: Contains all data and data headings
    Table1 = PdfPTable(Table1Columns)

    # Table1Footnote: Contains the footnotes for Table1
    Table1Footnote = PdfPTable(Table1Columns)

    # BulletinFooter: Footer for the bulletin
    BulletinFooter = PdfPTable(FooterColumns)
    
    #
    # Specify column widths
    #
    # Title Block Columns
    TitleBlockColumnWidths = [10] * Table1Columns
    TitleBlockColumnWidths[0] = 25
    TitleBlockColumnWidths[-1] = 17
    TitleBlock.setWidths(TitleBlockColumnWidths)
    
    # Table Columns and Order of Variables for Table1
    DataOrder, ColumnWidths = [], []
    for column in range(Table1Columns) :
        # Column Key
        ColumnKey = 'Column%d' % column

        if column == 6 or column == 7 :
           for x in range(1, 2):
              DataOrder.append(TableLayoutDict['Table1'][ColumnKey][1]['Key'])
              ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey][1]['ColumnWidth'])
        else :
            DataOrder.append(TableLayoutDict['Table1'][ColumnKey]['Key'])
            ColumnWidths.append(TableLayoutDict['Table1'][ColumnKey]['ColumnWidth'])
    Table1.setWidths(ColumnWidths)
    
    #
    # Add data to Title Block that will be at the top of the bulletin
    #
    TitleBlock = titleBlock(debug, TitleBlock)

    #
    # Add data to the heading for Table1
    #
    Table1 = table1Heading(debug, Table1)

    #
    # Add data to the data blocks for Table1
    #
    DataBlocks = ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8', 'Data9', 'Data10', 'Data11', 'Data12', 'Data13', 'Data14', 'Data15', 'Data16', 'Data17', 'Data18', 'Data19']

    for DataBlock in DataBlocks :
	if DataBlock == 'Data1' or DataBlock == 'Data2':
	   startTime = TrimTwStr
	   endTime = EndTwStr
           Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, TribTrimTwStr, SysEndTwStr)
	elif DataBlock == 'Data3' :
	   startTime = TrimTwStr
           endTime = EndTwStr2
           Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, TribTrimTwStr, SysEndTwStr)
        else :
	   startTime = TrimTribTwStr
           endTime = TrimTw7Str
	   Table1 = table1Data(debug, Table1, 'Table1', DataBlock, startTime, endTime, '', '') 

	#print "startTime: " + str(startTime) + "  " + str(endTime) + "  " + str(DataBlock)

    #
    # Create Pdf file and write tables to create bulletin
    #
    BulletinPdf = Document()
    Writer = PdfWriter.getInstance(BulletinPdf, FileOutputStream(BulletinFilename))
    BulletinPdf.setPageSize(PageSize.LETTER) # Set the page size
    BulletinPdf.setMargins(LeftMargin, RightMargin, TopMargin, BottomMargin) # Left, Right, Top, Bottom
    BulletinPdf.setMarginMirroring(True) 
    BulletinPdf.open()
    BulletinPdf.add(TitleBlock) # Add TitleBlock to the PDF
    BulletinPdf.add(Table1) # Add Table1 to the PDF
    BulletinPdf.add(Table1Footnote) # Add Table1's footnotes
    BulletinFooter.setTotalWidth(612 - 48) # Total width is 612 pixels (8.5 inches) minus the left and right margins (24 pixels each)
    # Build a footer with page numbers and add to PDF
    BulletinFooter = bulletinFooter(debug, BulletinFooter)
    BulletinFooter.writeSelectedRows(0, -1, 24, 36, Writer.getDirectContent())

finally :
    try : CwmsDb.done()
    except : pass
    try : conn.done()
    except : pass
    try : BulletinPdf.close()
    except : pass
    try : Writer.close()
    except : pass


