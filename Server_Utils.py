'''
Author: Ryan Larsen
Modified: Ivan Nguyen
Last Updated: 03-30-2022
Description: Contains functions used in scripts on the server
'''

from decimal                import Decimal
from hec.heclib.util        import HecTime
from hec.io                 import TimeSeriesContainer
from hec.script             import Constants, AxisMarker
from java.util              import Locale, Calendar, TimeZone
from com.itextpdf.text.pdf  import  PdfPCell, BaseFont
from java.text              import SimpleDateFormat
from hec.script.Constants   import TRUE, FALSE
import inspect, math

# createBlankTimeSeries Function : Create a blank time series for plotting purposes
# Author/Editor                  : Ryan Larsen
# Last updated                   : 12-19-2018

def createBlankTimeSeries(  debug, 
                            Pathname,       # Generic pathname
                            Units,          # Units of values
                            DatetimeObj,    # Datetime object
                            EndTwStr,       # String of the end of time window
                            ) : 
    PathnameParts = Pathname.split('.')
    Location = PathnameParts[0]
    Parameter = PathnameParts[1]
    TypeStr = PathnameParts[2]
    if TypeStr == 'Total' : Type = 'PER-CUM'
    elif TypeStr == 'Ave' : Type = 'PER-AVER'
    elif TypeStr == 'Inst' : Type = 'INST-VAL'
    IntervalStr = PathnameParts[3]
    if IntervalStr == '1Day' : Interval = 60 * 24
    elif IntervalStr == '~1Day' : Interval = 0
    elif IntervalStr == '1Hour' : Interval = 60
    elif IntervalStr == '15Minutes' : Interval = 15
    elif IntervalStr == '30Minutes' : Interval = 30
    Version = PathnameParts[-1]
    
    # Create times array
    HecTimeStartStr  = DatetimeObj.strftime('%d%b%Y ') + '2400'
    hecTime = HecTime(); hecTime.set(HecTimeStartStr)
    EndTime = HecTime(); EndTime.set(EndTwStr)
    times = [hecTime.value()]
    i = 0
    while times[-1] < EndTime.value() : 
        i += 1
        if i > 1000 : break
        hecTime.add(Interval)
        times.append(hecTime.value())

    Tsc = TimeSeriesContainer()                    
    Tsc.fullName       = Pathname
    Tsc.location       = Location
    Tsc.parameter      = Parameter
    Tsc.interval       = Interval
    Tsc.version        = Version
    Tsc.type           = Type
    Tsc.units          = Units
    values             = [Constants.UNDEFINED] * len(times)
    Tsc.times          = times
    Tsc.values         = values
    Tsc.quality        = [0] * len(values)
    Tsc.startTime      = times[0]
    Tsc.endTime        = times[-1]
    Tsc.numberValues   = len(values)
    
    return Tsc

# createPlot Function : Plot data with or without markers
# Author/Editor       : Ryan Larsen
# Last updated        : 12-10-2018

def createPlot( debug,               # Set to True or False to print debug statements
                CwmsDb,              # CWMS database connection
                Location,            # DCP ID of location
                plot,                # Plot
                layout,              # Plot layout
                ViewportLayoutsInfo, # Lists of ViewportLayouts, time series, and axis for each curve
                LocationProperties,  # Properties of locations
                CurveProperties,     # Properties of curves in the plot
                MarkerProperties,    # Properties of markers in the plot
                PlotProperties,      # Properties of plot
                ) :
    # Define the plot layout
    for x in range(len(ViewportLayoutsInfo)) :
        ViewportLayoutsInfo[x][0].addCurve(ViewportLayoutsInfo[x][2], ViewportLayoutsInfo[x][1])

    plot.configurePlotLayout(layout)
    plot.showPlot()
    
    # Set curve and symbol properties
    for x in range(len(ViewportLayoutsInfo)) :
        TscParts = ViewportLayoutsInfo[x][1].fullName.split('.')
        CurvePropertyKey = ViewportLayoutsInfo[x][3]

        if CurvePropertyKey is not None :
            curve = plot.getCurve(ViewportLayoutsInfo[x][1])
            curve.setLineColor(CurveProperties[CurvePropertyKey][0])
            curve.setLineStyle(CurveProperties[CurvePropertyKey][1])
            curve.setLineWidth(CurveProperties[CurvePropertyKey][2])
            curve.setFillType(CurveProperties[CurvePropertyKey][3])
            curve.setFillColor(CurveProperties[CurvePropertyKey][4])
            curve.setFillPattern(CurveProperties[CurvePropertyKey][5])
            curve.setSymbolsVisible(CurveProperties[CurvePropertyKey][6])
            curve.setSymbolType(CurveProperties[CurvePropertyKey][7])
            curve.setSymbolSize(CurveProperties[CurvePropertyKey][8])
            curve.setSymbolLineColor(CurveProperties[CurvePropertyKey][9])
            curve.setSymbolFillColor(CurveProperties[CurvePropertyKey][10])
            curve.setSymbolInterval(CurveProperties[CurvePropertyKey][11])
            curve.setSymbolSkipCount(CurveProperties[CurvePropertyKey][12])
            curve.setFirstSymbolOffset(CurveProperties[CurvePropertyKey][13])
    
    # Calculate min and max of each curve for each viewport. Viewport scales will automatically be set to the same scale if the same data type is 
    #    displayed on separate viewports. Need to include min and max values for the same data type in each viewport
    MinMaxDict = {}
    for x in range(len(ViewportLayoutsInfo)) :
        TimeSeriesParameter = ViewportLayoutsInfo[x][1].parameter
        TimeSeriesSubParameter = ViewportLayoutsInfo[x][1].subParameter
        outputDebug(debug, lineNo(), 'Time series: %s' % ViewportLayoutsInfo[x][1].fullName)
        InitialTscValues = ViewportLayoutsInfo[x][1].values
        outputDebug(debug, lineNo(), 'IntitialTscValues = ', InitialTscValues)
        # Substitute missing values with maximum value. This is only for scaling purposes. Plots will still contain all of the data
        if InitialTscValues == None or len(InitialTscValues) == 0 or all(x == Constants.UNDEFINED for x in InitialTscValues) == True :
            TscValues = [0.0, 0.5]
        else :
            TscValues = [max(InitialTscValues) if y == Constants.UNDEFINED else y for y in InitialTscValues]

        # Calculate min and max for curve
        MinValue = min(TscValues)
        MaxValue = max(TscValues)
        
        # Save min and max to dictionary
        Viewport = plot.getViewport(ViewportLayoutsInfo[x][1])
        ViewportName = Viewport.getName()
        
        try : 
            # Append min and max values to dictionary
            MinMaxDict[ViewportName][ViewportLayoutsInfo[x][2]]['MinValues'].append(MinValue)
            MinMaxDict[ViewportName][ViewportLayoutsInfo[x][2]]['MaxValues'].append(MaxValue)
        except : 
            # Add min and max values to dictionary
            outputDebug(debug, lineNo(), 'AxisName = ', ViewportLayoutsInfo[x][2])
            MinMaxDict.setdefault(ViewportName, {}).setdefault(ViewportLayoutsInfo[x][2], {}).setdefault('MinValues', [MinValue])
            MinMaxDict.setdefault(ViewportName, {}).setdefault(ViewportLayoutsInfo[x][2], {}).setdefault('MaxValues', [MaxValue])

            # Add viewports to dictionary
            MinMaxDict[ViewportName].setdefault('Viewport', Viewport)
        outputDebug(debug, lineNo(), 'ViewportName = ', ViewportName, '  MinValues = ', MinMaxDict[ViewportName][ViewportLayoutsInfo[x][2]]['MinValues'], 
                    '  MaxValues = ', MinMaxDict[ViewportName][ViewportLayoutsInfo[x][2]]['MaxValues'])
        
        for y in range(len(ViewportLayoutsInfo)) :
            OtherViewport = plot.getViewport(ViewportLayoutsInfo[y][1])
            OtherViewportName = OtherViewport.getName()
            if OtherViewportName != ViewportName :
                OtherTimeSeriesParameter = ViewportLayoutsInfo[y][1].parameter
                OtherTimeSeriesSubParameter = ViewportLayoutsInfo[y][1].subParameter
                
                if OtherTimeSeriesParameter == TimeSeriesParameter and OtherTimeSeriesSubParameter == TimeSeriesSubParameter :
                    outputDebug(debug, lineNo(), 'Parameter is in another viewport. Add values to %s' % OtherViewportName)
                    try : 
                        # Append min and max values to dictionary
                        MinMaxDict[OtherViewportName][ViewportLayoutsInfo[y][2]]['MinValues'].append(MinValue)
                        MinMaxDict[OtherViewportName][ViewportLayoutsInfo[y][2]]['MaxValues'].append(MaxValue)
                    except : 
                        # Add min and max values to dictionary
                        outputDebug(debug, lineNo(), 'AxisName = ', ViewportLayoutsInfo[y][2])
                        MinMaxDict.setdefault(OtherViewportName, {}).setdefault(ViewportLayoutsInfo[y][2], {}).setdefault('MinValues', [MinValue])
                        MinMaxDict.setdefault(OtherViewportName, {}).setdefault(ViewportLayoutsInfo[y][2], {}).setdefault('MaxValues', [MaxValue])
            
                        # Add viewports to dictionary
                        MinMaxDict[OtherViewportName].setdefault('Viewport', OtherViewport)
                    outputDebug(debug, lineNo(), 'OtherViewportName = ', OtherViewportName, '  MinValues = ', MinMaxDict[OtherViewportName][ViewportLayoutsInfo[y][2]]['MinValues'], 
                                '  MaxValues = ', MinMaxDict[OtherViewportName][ViewportLayoutsInfo[y][2]]['MaxValues'])
    
    # Set axis label. When running on the server, the units are sometimes left off the axis label.
    for x in range(len(ViewportLayoutsInfo)) :
        Viewport = plot.getViewport(ViewportLayoutsInfo[x][1])
        Y1Axis = Viewport.getAxis('Y1')
        if Y1Axis != None and ViewportLayoutsInfo[x][2] == 'Y1' : 
            if ViewportLayoutsInfo[x][1].parameter == '%' : Y1Axis.setLabel('%s (%s)' % (ViewportLayoutsInfo[x][1].subParameter, ViewportLayoutsInfo[x][1].units))
            else :Y1Axis.setLabel('%s (%s)' % (ViewportLayoutsInfo[x][1].parameter, ViewportLayoutsInfo[x][1].units))
        Y2Axis = Viewport.getAxis('Y2')
        if Y2Axis != None and ViewportLayoutsInfo[x][2] == 'Y2' : 
            if ViewportLayoutsInfo[x][1].parameter == '%' : Y2Axis.setLabel('%s (%s)' % (ViewportLayoutsInfo[x][1].subParameter, ViewportLayoutsInfo[x][1].units))
            else :Y2Axis.setLabel('%s (%s)' % (ViewportLayoutsInfo[x][1].parameter, ViewportLayoutsInfo[x][1].units))

    # Define the axis markers
    MarkerKeys = MarkerProperties.keys()
    for key in MarkerKeys :
        if MarkerProperties[key][0] and MarkerProperties[key][2] != None :
            marker = AxisMarker()
            outputDebug(debug, lineNo(), 'Marker Value = ', MarkerProperties[key][2])
            marker.value = '%s' % MarkerProperties[key][2]
            Viewport = plot.getViewport(MarkerProperties[key][3])
            ViewportName = Viewport.getName()
            marker.labelText = MarkerProperties[key][4]
            marker.labelFont = MarkerProperties[key][5]
            marker.axis = MarkerProperties[key][6]
            marker.labelAlignment = MarkerProperties[key][7]
            marker.labelPosition = MarkerProperties[key][8]
            marker.labelColor = MarkerProperties[key][9]
            marker.lineStyle = MarkerProperties[key][10]
            marker.lineColor = MarkerProperties[key][11]
            marker.lineWidth = MarkerProperties[key][12]
            Viewport.addAxisMarker(marker)
            
            # Determine which axis the marker is applied to
            for x in range(len(ViewportLayoutsInfo)) :
                TscFullName = ViewportLayoutsInfo[x][1].fullName
                if MarkerProperties[key][3].fullName == TscFullName : 
                    AxisName = ViewportLayoutsInfo[x][2]
                    outputDebug(debug, lineNo(), 'AxisName = ', AxisName)
                
            # Add markers to min and max values so the auto scaling with include the values only if marker is on Y axis
            if MarkerProperties[key][6] == 'Y1' or MarkerProperties[key][6] == 'Y2' : 
                MinMaxDict[ViewportName][AxisName]['MinValues'].append(float(MarkerProperties[key][2]))
                MinMaxDict[ViewportName][AxisName]['MaxValues'].append(float(MarkerProperties[key][2]))
    
    # Adjust scales to fit data. Normally this is done automatically when a plot is generated with CWMS. However, the auto-scaling does not always give a scale that fits
    #    the data correctly. Sometimes the scaling is too tight to the data so some curves are difficult to read or the axis markers are not shown on 
    #    the plot. The logic below, will scale the Y axes so the data is visible.
    ViewportKeys = MinMaxDict.keys()
    for key in ViewportKeys :
        Viewport = MinMaxDict[key]['Viewport']
        
        # Set yaxis scale
        AxesList = MinMaxDict[key].keys()[1 :] # The first key is 'Viewport'. Only want the axes
        for axis in AxesList :
            outputDebug(debug, lineNo(), 'ViewportName = ', key, '  Axis = ', axis)
            MaxValue = max(MinMaxDict[key][axis]['MaxValues'])
            MinValue = min(MinMaxDict[key][axis]['MinValues'])
            NumberOfTics = 5.
            YAxisMajorTic = (MaxValue - MinValue) / NumberOfTics
            if YAxisMajorTic == 0. : YAxisMajorTic = 0.05
            elif YAxisMajorTic < 0.1 : YAxisMajorTic = round(YAxisMajorTic, 2)
            elif YAxisMajorTic < 1. : YAxisMajorTic = round(YAxisMajorTic, 1)
            elif YAxisMajorTic < 10. : YAxisMajorTic = round(YAxisMajorTic, 0)
            elif YAxisMajorTic < 100. : YAxisMajorTic = round(YAxisMajorTic, -1)
            elif YAxisMajorTic < 1000. : YAxisMajorTic = round(YAxisMajorTic, -2)
            elif YAxisMajorTic < 10000. : YAxisMajorTic = round(YAxisMajorTic, -3)
            elif YAxisMajorTic < 100000. : YAxisMajorTic = round(YAxisMajorTic, -4)

            # Axis display digits
            if (YAxisMajorTic - int(YAxisMajorTic)) == 0.0 : YAxisDigits = 0
            elif (YAxisMajorTic - int(YAxisMajorTic)) < 0.1 : YAxisDigits = 2
            elif (YAxisMajorTic - int(YAxisMajorTic)) < 1. : YAxisDigits = 1
                        
            if YAxisMajorTic == 0. : YAxisMajorTic = 0.05 # Double check rounded values are not 0 
            maxscale = int(MaxValue / YAxisMajorTic) * YAxisMajorTic + YAxisMajorTic
            minscale = int(MinValue / YAxisMajorTic) * YAxisMajorTic - YAxisMajorTic
            
            if abs(maxscale - MaxValue) < (YAxisMajorTic / 2.) : maxscale += YAxisMajorTic
            if abs(minscale - MinValue) < (YAxisMajorTic / 2.) : minscale -= YAxisMajorTic
            
            YAxis = Viewport.getAxis(axis)
            YAxis.setScaleLimits(minscale, maxscale)
            YAxis.setViewLimits(minscale, maxscale)
            YAxis.setMajorTicInterval(YAxisMajorTic)
            YAxis.setMaximumFactionDigits(YAxisDigits)
            outputDebug(debug, lineNo(), 'MaxValue = ', MaxValue, '  MinValue = ', MinValue, '  YAxisMajorTic = ', YAxisMajorTic, 
                        '  maxscale = ', maxscale, '  minscale = ', minscale)
            YAxisScaleMax = YAxis.getScaleMax()
            YAxisScaleMin = YAxis.getScaleMin()
            YAxisMajorTic = YAxis.getMajorTic()
            outputDebug(debug, lineNo(), Location, '\tFinal minscale = ', minscale, '\tYAxis scale max = ', YAxisScaleMax, '\tYAxis scale min = ', YAxisScaleMin,
                '\tFinal maxscale = ', maxscale, '\tFinal YAxis Major Tic = ', YAxisMajorTic)
         
    # Plot Title
    title = plot.getPlotTitle()
    title.setForeground(PlotProperties['FontColor'])
    title.setFontFamily(PlotProperties['Font'])
    title.setFontStyle(PlotProperties['FontStyle'])
    title.setFontSize(PlotProperties['FontSize'])
    title.setText(LocationProperties[Location]['PlotTitle'])
    title.setDrawTitleOn()
    plot.setSize(PlotProperties['PlotWidth'], PlotProperties['PlotHeight'])
    
    return plot

# lineNo Function   : Retrieves the line number of the script.  Used when debugging
# Author/Editor     : Ryan Larsen
# Last updated      : 01-26-2016

def lineNo() :
    return inspect.currentframe().f_back.f_lineno

# outputDebug Function  : Debugging function that prints specified arguments
# Author/Editor         : Ryan Larsen
# Last updated          : 04-10-2017

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

#########################################################################
# Webrep Report
#########################################################################

def retrieveElevatonDatum( debug,                   # Set to True to print all debug statements
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
        stmt.setString(1, 'MVS')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()

        while rs.next() :
            ElevationDatum = str(rs.getString(1))
            break
    finally :
        try :
            stmt.close()
            rs.close()
        except :
            pass
    return ElevationDatum


def retrieveLocationLevel( debug,                   # Set to True to print all debug statements
                            conn,           # SQL connection
                            CwmsDb,         # DBAPI connection
                            TscFullName,    # Full name of time series container
                            ) :
    import datetime
    print '================= Server_Utils START'
    outputDebug(debug, lineNo(), 'conn = ', str(conn) )
    outputDebug(debug, lineNo(), 'cwmsdb = ', str(CwmsDb))
    outputDebug(debug, lineNo(), 'tscpathname = ', str(TscFullName))

    CurDate         = datetime.datetime.now() # Current date
    StartTimeStr    = CurDate.strftime('%d%b%Y ') + '0000' # Start date formatted as ddmmmyyy 0000
    EndTimeStr      = CurDate.strftime('%d%b%Y ') + '0000' # End date formatted as ddmmmyyy 0000

    level_1a = TimeSeriesContainer()
    level_1a_parts = TscFullName.split('.')
    level_1aId_parts = level_1a_parts[:]
    level_1aId = '.'.join(level_1aId_parts)  
    outputDebug(debug, lineNo(), 'level_1a_parts = ', level_1a_parts, '\tlevel_1aId_parts = ', level_1aId_parts, '\tlevel_1aId = ', level_1aId)
    level_1a.fullName  = TscFullName
    level_1a.location  = level_1a_parts[0]
    level_1a.parameter = level_1a_parts[1]
    level_1a.interval  = 0
    level_1a.version   = level_1a_parts[-1]
    if level_1a_parts[1] == 'Stor' : level_1a.units = 'ac-ft'
    elif level_1a_parts[1] == 'Elev' or level_1a_parts[1] == 'Stage' : level_1a.units = 'ft'
    elif level_1a_parts[1] == 'Flow' : level_1a.units = 'cfs'
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
        
    outputDebug(debug, lineNo(), 'LocationLevel = ', LocationLevel)
    print '================= Server_Utils END'
    return LocationLevel


def retrieveRecordStage( debug,                     # Set to True to print all debug statements
                           conn,           # SQL connection
                           CwmsDb,         # DBAPI connection
                           TscFullName,    # Full name of time series container
                           ) :
    import datetime
    
    outputDebug(debug, lineNo(), 'conn = ', str(conn) )
    outputDebug(debug, lineNo(), 'cwmsdb = ', str(CwmsDb))
    outputDebug(debug, lineNo(), 'tscpathname = ', str(TscFullName))

    CurDate         = datetime.datetime.now() # Current date
    StartTimeStr    = CurDate.strftime('%d%b%Y ') + '0000' # Start date formatted as ddmmmyyy 0000
    EndTimeStr      = CurDate.strftime('%d%b%Y ') + '0000' # End date formatted as ddmmmyyy 0000

    level_1a = TimeSeriesContainer()
    level_1a_parts = TscFullName.split('.')
    level_1aId_parts = level_1a_parts[:]
    level_1aId = '.'.join(level_1aId_parts)
    print '===========================Server_Utils'  
    outputDebug(debug, lineNo(), 'level_1a_parts = ', level_1a_parts, '\tlevel_1aId_parts = ', level_1aId_parts, '\tlevel_1aId = ', level_1aId)
    level_1a.fullName  = TscFullName
    level_1a.location  = level_1a_parts[0]
    level_1a.parameter = level_1a_parts[1]
    level_1a.interval  = 0
    level_1a.version   = level_1a_parts[-1]
    if level_1a_parts[1] == 'Stor' : level_1a.units = 'ac-ft'
    elif level_1a_parts[1] == 'Elev' or level_1a_parts[1] == 'Stage' : level_1a.units = 'ft'
    elif level_1a_parts[1] == 'Flow' : level_1a.units = 'cfs'
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
        stmt.setString(3, StartTimeStr)
        stmt.setString(4, EndTimeStr)
        stmt.setString(5, CwmsDb.getTimeZoneName())
        rs = stmt.executeQuery()
        
        while rs.next() : 
            RecordStage = rs.getDouble(2)
            break
    finally :
        stmt.close()
        rs.close()
        
    outputDebug(debug, lineNo(), 'RecordStage = ', RecordStage)
    return RecordStage


def retrieveRecordStageDate ( debug,                # Set to True to print all debug statements
                                conn,           # 
                                BaseLocation,   # Full name of time series container
                                ) :
    try :
        level_date = None
        stmt = conn.prepareStatement('''
                                    select to_char(level_date, 'MM-DD-YY') as level_date 
                                    from CWMS_20.AV_LOCATION_LEVEL where specified_level_id = 'Record Stage' and location_id = :1 and unit_system = 'EN' 
                                    FETCH FIRST 1 ROWS ONLY
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        
        while rs.next() : 
            level_date = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()

    return level_date


def retrieveLongName( debug,                        # Set to True to print all debug statements
                        conn,           # 
                        BaseLocation,   # Full name of time series container
                        ) :
    try :
        stmt = conn.prepareStatement('''
                                    select distinct
                                    bl.long_name as base_location_long_name
                                    from cwms_v_loc loc 
                                    inner join cwms_v_loc bl on bl.base_location_code = loc.base_location_code
                                        and bl.db_office_id = loc.db_office_id 
                                        and bl.unit_system = loc.unit_system
                                    where loc.UNIT_SYSTEM = 'EN' 
                                        and loc.db_office_id = :1 
                                        and bl.location_id = :2
                                    ''')   
        stmt.setString(1, 'MVS')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()
        
        while rs.next() : 
            LongName = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    
    return LongName


def retrievePublicName( debug,                      # Set to True to print all debug statements
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
        stmt.setString(1, 'MVS')
        stmt.setString(2, BaseLocation)
        rs = stmt.executeQuery()
        
        while rs.next() : 
            PublicName = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    
    return PublicName


def retrieveRiverMile( debug,                       # Set to True to print all debug statements
                        conn,           # 
                        BaseLocation,   # Full name of time series container
                        ) :
    try :
        stmt = conn.prepareStatement('''
                                    select station from CWMS_20.AV_STREAM_LOCATION where location_id = :1 and unit_system = 'EN' and db_office_id = :2
                                    ''')   
        stmt.setString(1, BaseLocation)
        stmt.setString(2, 'MVS')
        rs = stmt.executeQuery()
        
        while rs.next() : 
            StationName = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    
    return StationName


def retrieveCrest( debug,                           # Set to True to print all debug statements
                     conn,           # 
                     BaseLocation,   # Full name of time series container
                     ) :
    try :
        Crest = None
        stmt = conn.prepareStatement('''
                                    select value
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FX' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'ft'
                                    and (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) > to_date(to_char(current_date, 'mm-dd-yyyy hh24:mi') ,'mm-dd-yyyy hh24:mi')
                                    order by data_entry_date desc
                                    fetch first 1 rows only
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            Crest = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Crest


def retrieveCrestDate( debug,                       # Set to True to print all debug statements
                         conn,           # 
                         BaseLocation,   # Full name of time series container
                         ) :
    try :
        CrestDate=None
        stmt = conn.prepareStatement('''
                                    select to_char(date_time,'mm/dd am') as date_time
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FX' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'ft'
                                    and (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) > to_date(to_char(current_date, 'mm-dd-yyyy hh24:mi') ,'mm-dd-yyyy hh24:mi')
                                    order by data_entry_date desc
                                    fetch first 1 rows only
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            CrestDate = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    return CrestDate


def retrieveNWSDay1( debug,                         # Set to True to print all debug statements
                       conn,           # 
                       BaseLocation,   # Full name of time series container
                       ) :
    try :
        Day1 = None
        stmt = conn.prepareStatement('''
                                    select value from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '1' day
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            #Day1 = str(rs.getString(1))
            Day1 = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Day1


def retrieveNWSDay1Date( debug,                     # Set to True to print all debug statements
                           conn,                    # 
                           ) :
    try :
        Day1Date = None
        stmt = conn.prepareStatement('''
                                    select to_char(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT' ), 'mm-dd') as date_time
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like 'St Louis-Mississippi' || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '1' day
                                    ''')   
        rs = stmt.executeQuery()
        while rs.next() : 
            Day1Date = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Day1Date


def retrieveNWSForecastDate( debug,                 # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        NWSForecastDate=None
        stmt = conn.prepareStatement('''
                                    select to_char(data_entry_date, 'MM-DD-YYYY hh24:mi') as data_entry_date
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '1' day
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            NWSForecastDate = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    return NWSForecastDate


def retrieveNWSDay2( debug,                         # Set to True to print all debug statements
                       conn,                        # 
                       BaseLocation,                # Full name of time series container
                       ) :
    try :
        Day2 = None
        stmt = conn.prepareStatement('''
                                    select value from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '2' day
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        #Day1 = ''
        while rs.next() : 
            #Day1 = str(rs.getString(1))
            Day2 = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Day2


def retrieveNWSDay2Date( debug,                     # Set to True to print all debug statements
                           conn,                    # 
                           ) :
    try :
        Day2Date = None
        stmt = conn.prepareStatement('''
                                    select to_char(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT' ), 'mm-dd') as date_time
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like 'St Louis-Mississippi' || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '2' day
                                    ''')   
        rs = stmt.executeQuery()
        while rs.next() : 
            Day2Date = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Day2Date


def retrieveNWSDay3( debug,                         # Set to True to print all debug statements
                       conn,                        # 
                       BaseLocation,                # Full name of time series container
                       ) :
    try :
        Day3 = None
        stmt = conn.prepareStatement('''
                                    select value from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '3' day
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            #Day1 = str(rs.getString(1))
            Day3 = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Day3


def retrieveNWSDay3Date( debug,                     # Set to True to print all debug statements
                           conn,                    # 
                           ) :
    try :
        Day3Date = None
        stmt = conn.prepareStatement('''
                                    select to_char(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT' ), 'mm-dd') as date_time
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Stage.Inst.6Hours.0.RVFShef-FF' 
                                    and cwms_ts_id like 'St Louis-Mississippi' || '%'
                                    and unit_id = 'ft'
                                    and date_time = to_date( to_char(current_date, 'mm-dd-yyyy') || '12:00' ,'mm-dd-yyyy hh24:mi') + interval '1' day
                                    ''')   
        rs = stmt.executeQuery()
        while rs.next() : 
            Day3Date = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Day3Date


def retrieveGroup( debug,                           # Set to True to print all debug statements
                     conn,                          # 
                     CategoryId,                    # Full name of time series container
                     ) :
    try :
        stmt = conn.prepareStatement('''
                                    select location_id from CWMS_20.AV_LOC_GRP_ASSGN where category_id = :1
                                    ''')   
        stmt.setString(1, CategoryId)
        rs = stmt.executeQuery()
        groupList = []
        while rs.next() : 
            groupList.append(str(rs.getString(1)))
    finally :
        stmt.close()
        rs.close()
    
    return groupList


def retrieveGroupLPMS( debug,                       # Set to True to print all debug statements
                         conn,                      # 
                         ) :
    try :
        stmt = conn.prepareStatement('''
                                    select location_id from cwms_v_ts_id where cwms_ts_id like '%Stage.Inst.~2Hours.0.lpmsShef-raw'
                                    ''')   
        rs = stmt.executeQuery()
        groupListLPMS = []
        while rs.next() : 
            #StationName = str(rs.getString(1))
            groupListLPMS.append(str(rs.getString(1)))
            #break 
    finally :
        stmt.close()
        rs.close()
    
    return groupListLPMS


def retrieveGageZero29( debug,                      # Set to True to print all debug statements
                          conn,                     # 
                          BaseLocation,             # Full name of time series container
                          ) :
    try :
        stmt = conn.prepareStatement('''
                                    select constant_level from CWMS_20.AV_LOCATION_LEVEL where location_level_id = :1 || '.Height.Inst.0.NGVD29' and unit_system = 'EN'
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        GageZero29 = ''
        while rs.next() : 
            #StationName = str(rs.getString(1))
            GageZero29 = rs.getString(1)
            #break 
    finally :
        stmt.close()
        rs.close()
    
    return GageZero29


def retrieveBasin( debug,                           # Set to True to print all debug statements
                     conn,                          #
                     ) :
    try :
        stmt = conn.prepareStatement('''
                                    select distinct group_id as basin from CWMS_V_LOC_GRP_ASSGN where category_id = 'RDL_Basins'
                                    ''')   
        rs = stmt.executeQuery()
        Basin = []
        while rs.next() :
            Basin.append(str(rs.getString(1)))
    finally :
        stmt.close()
        rs.close()
    return Basin


def retrieveLocationID( debug,                      # Set to True to print all debug statements
                          conn,                     # 
                          Basin,                    # Full name of time series container
                          ) :
    try :
        stmt = conn.prepareStatement('''
                                    select location_id  from CWMS_V_LOC_GRP_ASSGN where category_id = 'RDL_Basins' and location_id in (select location_id from CWMS_V_LOC_GRP_ASSGN where category_id = 'RDL_River_Reservoir' and group_id = 'ALL') and group_id = :1 order by location_id asc
                                    ''')   
        stmt.setString(1, Basin)
        rs = stmt.executeQuery()
        LocationID = []
        while rs.next() : 
            LocationID.append(str(rs.getString(1)))
            #LocationID = rs.getString(1)

    finally :
        stmt.close()
        rs.close()
    return LocationID


def retrieveLocationLevel2( debug,                  # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        Level = ''
        stmt = conn.prepareStatement('''
                                    select constant_level from CWMS_20.AV_LOCATION_LEVEL
                                    where specified_level_id = 'Flood' and location_id = :1 and unit_system = 'EN'
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        
        while rs.next() : 
            Level = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    
    return Level

#########################################################################
# Webrep Sub Report
#########################################################################

def retrieveYesterdayInflow( debug,                 # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        YesterdayInflow = None
        stmt = conn.prepareStatement('''
                                    select value
                                    from cwms_v_tsv_dqu 
                                    where cwms_ts_id like '%Flow-In.Ave.~1Day.1Day.lakerep-rev' 
                                    and cwms_ts_id like :1 || '%'
                                    and unit_id = 'cfs'
                                    and (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi')  - interval '1' day
                                    order by data_entry_date desc
                                    fetch first 1 rows only
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            YesterdayInflow = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return YesterdayInflow


def retrieveLakeMeta( debug,                        # Set to True to print all debug statements
                         conn,                      # 
                         ) :
    try :
        stmt = conn.prepareStatement('''
                                    with cte_data as (
                                    select location_id
                                        ,specified_level_id
                                        ,constant_level
                                        ,level_unit 
                                    from CWMS_20.AV_LOCATION_LEVEL 
                                    where location_id in ('Carlyle Lk', 'Mark Twain Lk', 'Rend Lk', 'Lk Shelbyville', 'Wappapello Lk')
                                    and level_unit in ('ac-ft')
                                    and unit_system = 'EN'
                                    and specified_level_id in ('Top of Conservation','Bottom of Conservation', 'Top of Flood', 'Bottom of Flood')),

                                    cte_new_data as (
                                    select 
                                        case
                                            when location_id = 'Lk Shelbyville' then 'Lk Shelbyville-Kaskaskia'
                                            when location_id = 'Wappapello Lk' then 'Wappapello Lk-St Francis'
                                            when location_id = 'Rend Lk' then 'Rend Lk-Big Muddy'
                                            when location_id = 'Mark Twain Lk' then 'Mark Twain Lk-Salt'
                                            when location_id = 'Carlyle Lk' then 'Carlyle Lk-Kaskaskia'
                                            else 'na'
                                        end as location_id
                                        ,specified_level_id
                                        ,constant_level
                                        ,level_unit 
                                    from cte_data)
                                    select location_id
                                        ,specified_level_id
                                        ,constant_level
                                        ,level_unit
                                    from cte_new_data
                                    where location_id = :1
                                    ''')   
        rs = stmt.executeQuery()
        LakeMeta = []
        while rs.next() :
            LakeMeta.append(str(rs.getString(1)))
    finally :
        stmt.close()
        rs.close()
    return LakeMeta


def retrieveCrestLake( debug,                       # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        CrestLake = None
        CrestOption = None
        stmt = conn.prepareStatement('''
                                    with cte_data as (
                                        select 
                                            case
                                            when lake = 'SHELBYVILLE' then 'Lk Shelbyville-Kaskaskia'
                                            when lake = 'WAPPAPELLO' then 'Wappapello Lk-St Francis'
                                            when lake = 'REND' then 'Rend Lk-Big Muddy'
                                            when lake = 'MT' then 'Mark Twain Lk-Salt'
                                            when lake = 'CARLYLE' then 'Carlyle Lk-Kaskaskia'
                                                else 'na'
                                            end as project_id,
                                            crest, 
                                            (cwms_util.change_timezone(crst_dt, 'UTC', 'CST6CDT')) as crst_dt, 
                                            (cwms_util.change_timezone(data_entry_dt, 'UTC', 'CST6CDT')) as data_entry_dt, 
                                            opt
                                        from wm_mvs_lake.crst_fcst
                                        where (cwms_util.change_timezone(data_entry_dt, 'UTC', 'CST6CDT')) = to_date(to_char(current_date, 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '0' day
                                        order by project_id
                                        )
                                    select cte_data.crest, cte_data.opt
                                    from cte_data
                                    where cte_data.project_id = :1
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            CrestLake = rs.getString(1)
            CrestOption = rs.getString(2)
            break 
    finally :
        stmt.close()
        rs.close()
    return CrestLake, CrestOption


def retrieveCrestLakeDate( debug,                   # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        CrestDateLake=None
        stmt = conn.prepareStatement('''
                                    with cte_data as (
                                    select 
                                        case
                                        when lake = 'SHELBYVILLE' then 'Lk Shelbyville-Kaskaskia'
                                        when lake = 'WAPPAPELLO' then 'Wappapello Lk-St Francis'
                                        when lake = 'REND' then 'Rend Lk-Big Muddy'
                                        when lake = 'MT' then 'Mark Twain Lk-Salt'
                                        when lake = 'CARLYLE' then 'Carlyle Lk-Kaskaskia'
                                            else 'na'
                                        end as project_id,
                                        crest, 
                                        --(cwms_util.change_timezone(crst_dt, 'UTC', 'CST6CDT')) as crst_dt, 
                                        crst_dt,
                                        --'05-18-2002' as crst_dt,  
                                        (cwms_util.change_timezone(data_entry_dt, 'UTC', 'CST6CDT')) as data_entry_dt, 
                                        opt
                                    from wm_mvs_lake.crst_fcst
                                    where (cwms_util.change_timezone(data_entry_dt, 'UTC', 'CST6CDT')) = to_date(to_char(current_date, 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '0' day
                                    order by project_id
                                    )
                                select to_char(cte_data.crst_dt,'mm-dd am') as crest_date
                                from cte_data
                                where cte_data.project_id = :1
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            CrestDateLake = str(rs.getString(1))
            break 
    finally :
        stmt.close()
        rs.close()
    return CrestDateLake


def retrieveProjectId( debug,                       # Set to True to print all debug statements
                         conn,                      #
                         ) :
    try :
        stmt = conn.prepareStatement('''
                                    select location_id as project_id
                                    from cwms_v_loc_grp_assgn
                                    where category_id = 'RDL_Project_Types' and group_id = 'Lake'
                                    order by location_id asc
                                    ''')   
        rs = stmt.executeQuery()
        ProjectId = []
        while rs.next() :
            ProjectId.append(str(rs.getString(1)))
    finally :
        stmt.close()
        rs.close()
    return ProjectId


def retrievePrecipLake( debug,                      # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        Precip = None
        stmt = conn.prepareStatement('''
                                    select value from CWMS_20.AV_TSV_DQU_30D
                                    where cwms_ts_id = :1 || '.Precip.Total.~1Day.1Day.lakerep-rev'
                                    and (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi')
                                    and unit_id = 'ft'
                                    order by date_time desc
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            #Precip = str(rs.getString(1))
            Precip = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Precip


def retrieveMidnight( debug,                        # Set to True to print all debug statementsretrieveEveningOutflow
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        Midnight = None
        stmt = conn.prepareStatement('''
                                    with cte_rend as (
                                    select 'Rend Lk-Big Muddy' as project_id 
                                    ,(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) as date_time
                                    ,round(q_tom, -1) as midnight_outflow_rend
                                    from wm_mvs_lake.rend_flow
                                    where cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT') >= to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '1' day
                                    ),
                                    cte_wappapello as (
                                    select 'Wappapello Lk-St Francis' as project_id
                                        ,(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) as date_time
                                        ,q as midnight_outflow_wappapello
                                    from wm_mvs_lake.wappapello_gate
                                    where cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT') = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '1' day
                                    ),
                                    cte_shelbyville as (
                                    select 'Lk Shelbyville-Kaskaskia' as project_id 
                                        ,(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) as date_time
                                        ,q as midnight_outflow_shelbyville
                                    from wm_mvs_lake.shelbyville_gate
                                    where cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT') = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '1' day
                                    ),
                                    cte_carlyle as (
                                    select 'Carlyle Lk-Kaskaskia' as project_id 
                                        ,(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) as date_time
                                        ,q as midnight_outflow_carlyle
                                    from wm_mvs_lake.carlyle_gate
                                    where cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT') = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '1' day
                                    ),
                                    cte_mark_twain as (
                                    select 
                                        case
                                            when lake = 'MT' then 'Mark Twain Lk-Salt'
                                        end as project_id
                                        ,(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) as date_time
                                        ,outflow as midnight_outflow_mark_twain
                                        --,(cwms_util.change_timezone(fcst_date, 'UTC', 'CST6CDT')) as fcst_date
                                        --,inflow
                                        --,lev
                                        --,src
                                    from wm_mvs_lake.qlev_fcst
                                    where (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '1' day 
                                    and (cwms_util.change_timezone(fcst_date, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '0' day
                                    and lake = 'MT'
                                    order by project_id asc
                                    ),
                                    cte_all_data as (
                                        select project_id, date_time, midnight_outflow_rend as midnight from cte_rend
                                        union all
                                        select project_id, date_time, midnight_outflow_wappapello as midnight from cte_wappapello
                                        union all
                                        select project_id, date_time, midnight_outflow_shelbyville as midnight from cte_shelbyville
                                        union all    
                                        select project_id, date_time, midnight_outflow_carlyle as midnight from cte_carlyle
                                        union all
                                        select project_id, date_time, midnight_outflow_mark_twain as midnight from cte_mark_twain
                                    )
                                    select midnight 
                                    from cte_all_data
                                    where project_id = :1
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            Midnight = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Midnight


def retrieveEveningOutflow( debug,                  # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        EveningOutflow = None
        stmt = conn.prepareStatement('''
                                    with cte_evening_outflow as (
                                    select 
                                        case
                                            when lake = 'SHELBYVILLE' then 'Lk Shelbyville-Kaskaskia'
                                            when lake = 'WAPPAPELLO' then 'Wappapello Lk-St Francis'
                                            when lake = 'REND' then 'Rend Lk-Big Muddy'
                                            when lake = 'MT' then 'Mark Twain Lk-Salt'
                                            when lake = 'CARLYLE' then 'Carlyle Lk-Kaskaskia'
                                            else 'na'
                                        end as project_id
                                        ,(cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) as date_time
                                        ,outflow
                                        ,(cwms_util.change_timezone(fcst_date, 'UTC', 'CST6CDT')) as fcst_date
                                        ,inflow
                                        ,lev
                                        ,src
                                    from wm_mvs_lake.qlev_fcst
                                    where (cwms_util.change_timezone(fcst_date, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '0' day 
                                    and (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi') - interval '0' day
                                    order by project_id asc)

                                    select outflow 
                                    from cte_evening_outflow
                                    where project_id = :1
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            EveningOutflow = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return EveningOutflow


def retrieveRuleCurve( debug,                       # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        RuleCurve = None 
        stmt = conn.prepareStatement('''
                                    with cte_rule_curve as (
                                    select 
                                        case
                                            when lake = 'SHELBYVILLE' then 'Lk Shelbyville-Kaskaskia'
                                            when lake = 'WAPPAPELLO' then 'Wappapello Lk-St Francis'
                                            when lake = 'REND' then 'Rend Lk-Big Muddy'
                                            when lake = 'MT' then 'Mark Twain Lk-Salt'
                                            when lake = 'CARLYLE' then 'Carlyle Lk-Kaskaskia'
                                            else 'na'
                                        end as project_id,
                                        lev,
                                        dt_s,
                                        dt_e
                                    from wm_mvs_lake.rule_curve
                                    where current_date > to_date(dt_s, 'mm-dd hh24:mi')
                                    and current_date < to_date(dt_e, 'mm-dd hh24:mi')) 
                                    select cast(lev as number) as lev
                                    from cte_rule_curve
                                    where project_id = :1
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            RuleCurve = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()

    return RuleCurve


def retrieveStorageLake( debug,                     # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        Storage = None
        stmt = conn.prepareStatement('''
                                    select value 
                                    from CWMS_20.AV_TSV_DQU
                                    where cwms_ts_id = :1 || '.Stor.Inst.30Minutes.0.RatingCOE'
                                    --and (cwms_util.change_timezone(date_time, 'UTC', 'CST6CDT')) = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi')
                                    and date_time = to_date(to_char((cwms_util.change_timezone(sysdate, 'UTC', 'CST6CDT')), 'mm-dd-yyyy') || '00:00' ,'mm-dd-yyyy hh24:mi')
                                    and unit_id = 'ac-ft'
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            Storage = rs.getString(1)
            break 
    finally :
        stmt.close()
        rs.close()
    return Storage


def retrieveTopBottomLake( debug,                   # Set to True to print all debug statements
                        conn,                       # 
                        BaseLocation,               # Full name of time series container
                        ) :
    try :
        TOC = None
        BOC = None
        TOF = None
        BOF = None
        stmt = conn.prepareStatement('''
                                    with cte_data as (
                                    select location_id
                                        ,specified_level_id
                                        ,constant_level
                                        ,level_unit 
                                    from CWMS_20.AV_LOCATION_LEVEL 
                                    where location_id in ('Carlyle Lk', 'Mark Twain Lk', 'Rend Lk', 'Lk Shelbyville', 'Wappapello Lk')
                                    and level_unit in ('ac-ft')
                                    and unit_system = 'EN'
                                    and specified_level_id in ('Top of Conservation','Bottom of Conservation', 'Top of Flood', 'Bottom of Flood')),

                                    cte_new_data as (
                                    select 
                                        case
                                            when location_id = 'Lk Shelbyville' then 'Lk Shelbyville-Kaskaskia'
                                            when location_id = 'Wappapello Lk' then 'Wappapello Lk-St Francis'
                                            when location_id = 'Rend Lk' then 'Rend Lk-Big Muddy'
                                            when location_id = 'Mark Twain Lk' then 'Mark Twain Lk-Salt'
                                            when location_id = 'Carlyle Lk' then 'Carlyle Lk-Kaskaskia'
                                            else 'na'
                                        end as location_id
                                        ,specified_level_id
                                        ,constant_level
                                        ,level_unit 
                                    from cte_data)
                                    select toc.constant_level as TOC
                                        ,boc.constant_level  as BOC
                                        ,tof.constant_level as TOF
                                        ,bof.constant_level as BOF
                                    from cte_new_data toc
                                        left outer join (
                                        select location_id ,specified_level_id ,constant_level ,level_unit 
                                        from cte_new_data 
                                        where specified_level_id = 'Bottom of Conservation' ) boc
                                        on toc.location_id = boc.location_id 
                                            left outer join (
                                            select location_id ,specified_level_id ,constant_level ,level_unit 
                                            from cte_new_data 
                                            where specified_level_id = 'Top of Flood' ) tof
                                            on toc.location_id = tof.location_id 
                                                left outer join (
                                                select location_id ,specified_level_id ,constant_level ,level_unit 
                                                from cte_new_data 
                                                where specified_level_id = 'Bottom of Flood' ) bof
                                                on toc.location_id = bof.location_id 
                                    where toc.location_id = :1 and toc.specified_level_id = 'Top of Conservation'
                                    ''')   
        stmt.setString(1, BaseLocation)
        rs = stmt.executeQuery()
        while rs.next() : 
            TOC = rs.getString(1)
            BOC = rs.getString(2)
            TOF = rs.getString(3)
            BOF = rs.getString(4)
            break 
    finally :
        stmt.close()
        rs.close()
    return TOC, BOC, TOF, BOF

# checkTs Function    : Check if the TS is in the database
# Author/Editor       : Scott Hoffman

def checkTs(timeseries,
            conn,) :
    try :
        #stmt = conn.createStatement()
        #check if timeseries exist in DB
        #sql = "select * from CWMS_20.av_cwms_ts_id where cwms_ts_id='" + timeseries + "'"
        #rset = stmt.executeQuery(sql)
        string = "select * from CWMS_20.av_cwms_ts_id where cwms_ts_id='" + timeseries + "'"
        stmt = conn.prepareStatement(string)
        rset = stmt.executeQuery()
        if rset.next() :
            #Found timeseries
            flag = 'true'
        else :
            flag = 'false'
    finally :
        try : stmt.close()
        except : pass
        try : rset.close()
        except : pass
    return flag

# Check DST Function

def is_dst(dayTime):
    
    # example:  2018-06-15 15:09:46
    sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
    date = sdf.parseObject(dayTime)
    cal = Calendar.getInstance(TimeZone.getTimeZone("UTC"))
    cal.setTime(date)
    # checking day light
    timezoneone = TimeZone.getDefault()
    day = cal.getTime()

    return timezoneone.inDaylightTime(day) 

# createCell Function   : Creates a PdfPCell for tables
# Author/Editor         : Ryan Larsen
# Last updated          : 12-20-2017

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
