'''
Author: Ryan Larsen
Revised: Ryan Larsen
Last Updated: 09-05-2017
Description: Creates plots of gages in the Oahe-Bend reach used for ice determination. Runs on a cron on nwo-cwms2 g6cwmspd (script located in cronjobs)
'''

# -------------------------------------------------------------------
# Required imports
# -------------------------------------------------------------------
from hec.heclib.util        import HecTime
from hec.io                 import*
from hec.script             import *
from hec.script.Constants   import * # for TRUE & FALSE
import sys, time, DBAPI, os, inspect, datetime, math

# -------------------------------------------------------------------
# Input
# -------------------------------------------------------------------
# Set to True to turn on all print statements
debug = False

# List of locations to be included on plot
Locations = ['PIR', 'LFSD', 'IWSD', 'FISD']

# Plot info
PlotWidth= 975
PlotHeight = 735
PlotQuality = 100 # range of 0 (crappy) to 100 (great, but larger file)

# Dictionary of data
DataDict = {    'PIR'           :   {   'DbLocation'        :   'PIR-Pierre-Missouri',
                                        'CurveProperties'   :   {   'LineColor'         :   'blue',
                                                                    'LineStyle'         :   'Solid',
                                                                    'LineWidth'         :   1,
                                                                    'SymbolVisible'     :   Constants.FALSE,
                                                                    'SymbolType'        :   'Square',
                                                                    'SymbolSize'        :   7,
                                                                    'SymbolLineColor'   :   'blue',
                                                                    'SymbolFillColor'   :   'blue',
                                                                    'SymbolInterval'    :   0,
                                                                    'SymbolSkipCount'   :   0,
                                                                    'FirstSymbolOffset' :   0,
                                                                    'FillType'          :   'None',
                                                                    'FillColor'         :   'orange',
                                                                    'FillPattern'       :   'Solid',
                                                                    },
                                        'PpNotStage'        :   11.74, # Power plant notification stage (ft)
                                        'TargetStage'       :   12.24, # Target notification stage (ft)
                                        'CriticalStage'     :   13.24, # Critical notification stage (ft)
                                        'PlotTitle'         :   "Missouri River at Pierre, SD (RM 1066.5); datum = 1414.26'",
                                        },
                'LFSD'          :   {   'DbLocation'        :   'LFSD-Pierre-Missouri-LaFrambois_Isl',
                                        'CurveProperties'   :   {   'LineColor'         :   'blue',
                                                                    'LineStyle'         :   'Solid',
                                                                    'LineWidth'         :   1,
                                                                    'SymbolVisible'     :   Constants.FALSE,
                                                                    'SymbolType'        :   'Square',
                                                                    'SymbolSize'        :   7,
                                                                    'SymbolLineColor'   :   'blue',
                                                                    'SymbolFillColor'   :   'blue',
                                                                    'SymbolInterval'    :   0,
                                                                    'SymbolSkipCount'   :   0,
                                                                    'FirstSymbolOffset' :   0,
                                                                    'FillType'          :   'None',
                                                                    'FillColor'         :   'orange',
                                                                    'FillPattern'       :   'Solid',
                                                                    },
                                        'PpNotStage'        :   25.00, # Power plant notification stage (ft)
                                        'TargetStage'       :   26.00, # Target notification stage (ft)
                                        'CriticalStage'     :   26.50, # Critical notification stage (ft)
                                        'PlotTitle'         :   "Missouri River at LaFrambois Island, SD (RM 1064.8); datum = 1400.0'",
                                        },
                'IWSD'          :   {   'DbLocation'        :   'IWSD-Pierre-Missouri-Isaac_Walton',
                                        'CurveProperties'   :   {   'LineColor'         :   'blue',
                                                                    'LineStyle'         :   'Solid',
                                                                    'LineWidth'         :   1,
                                                                    'SymbolVisible'     :   Constants.FALSE,
                                                                    'SymbolType'        :   'Square',
                                                                    'SymbolSize'        :   7,
                                                                    'SymbolLineColor'   :   'blue',
                                                                    'SymbolFillColor'   :   'blue',
                                                                    'SymbolInterval'    :   0,
                                                                    'SymbolSkipCount'   :   0,
                                                                    'FirstSymbolOffset' :   0,
                                                                    'FillType'          :   'None',
                                                                    'FillColor'         :   'orange',
                                                                    'FillPattern'       :   'Solid',
                                                                    },
                                        'PpNotStage'        :   24.00, # Power plant notification stage (ft)
                                        'TargetStage'       :   25.30, # Target notification stage (ft)
                                        'CriticalStage'     :   25.50, # Critical notification stage (ft)
                                        'PlotTitle'         :   "Missouri River at Isaac Walton, SD (RM 1062.8); datum = 1400.0'",
                                        },
                'FISD'          :   {   'DbLocation'        :   'FISD-Pierre-Missouri-Farm_Island',
                                        'CurveProperties'   :   {   'LineColor'         :   'blue',
                                                                    'LineStyle'         :   'Solid',
                                                                    'LineWidth'         :   1,
                                                                    'SymbolVisible'     :   Constants.FALSE,
                                                                    'SymbolType'        :   'Square',
                                                                    'SymbolSize'        :   7,
                                                                    'SymbolLineColor'   :   'blue',
                                                                    'SymbolFillColor'   :   'blue',
                                                                    'SymbolInterval'    :   0,
                                                                    'SymbolSkipCount'   :   0,
                                                                    'FirstSymbolOffset' :   0,
                                                                    'FillType'          :   'None',
                                                                    'FillColor'         :   'orange',
                                                                    'FillPattern'       :   'Solid',
                                                                    },
                                        'PpNotStage'        :   23.00, # Power plant notification stage (ft)
                                        'TargetStage'       :   24.20, # Target notification stage (ft)
                                        'CriticalStage'     :   24.50, # Critical notification stage (ft)
                                        'PlotTitle'         :   "Missouri River at Farm Island, SD (RM 1059.8); datum = 1400.0'",
                                        },
                # Pathnames
                'StageInstHr'   :   '%s.Stage.Inst.1Hour.0.Combined-rev',
                # Filename
                'PlotFilename'  :   '/cwms/g7cwmspd/plotFiles/files/%sice.jpg'
                }

# -------------------------------------------------------------------
# Classes
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------

#
# lineNo Function   : Retrieves the line number of the script.  Used when debugging
# Author/Editor     : Ryan Larsen
# Last updated      : 01-26-2016
#
def lineNo() :
    return inspect.currentframe().f_back.f_lineno

#
# outputDebug Function  : Debugging function that prints specified arguments
# Author/Editor         : Ryan Larsen
# Last updated          : 04-10-2017
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

#
# plotData Function : Plot retrieved data
# Author/Editor     : Ryan Larsen
# Last updated      : 09-05-2017
#
def plotData(   Db, 
                Location
                ) :
    # Read the data from the CWMS Oracle database via the DBI
    StageTsc = Db.get(DataDict['StageInstHr'] % DataDict[Location]['DbLocation'])

    try :
        stageDC = (StageTsc)
    except :
        return

    # Create plot
    plot = Plot.newPlot()
    layout = Plot.newPlotLayout()
    
    # Define the plot layout
    view = layout.addViewport()
    view.addCurve('Y1', stageDC)
    plot.configurePlotLayout(layout)
    plot.showPlot()

    # Set curve properties
    curve = plot.getCurve(StageTsc)
    curve.setLineColor(DataDict[Location]['CurveProperties']['LineColor'])
    curve.setLineStyle(DataDict[Location]['CurveProperties']['LineStyle'])
    curve.setLineWidth(DataDict[Location]['CurveProperties']['LineWidth'])

    # Customize the plot
    viewport = plot.getViewport(0)
    
    # Increase Y1 scale if needed
    yaxis = viewport.getAxis('Y1')
    yaxisScaleMax = yaxis.getScaleMax()
    yaxisScaleMin = yaxis.getScaleMin()
    yaxisMajorTic = yaxis.getMajorTic()
    outputDebug(debug, lineNo(), Location, '\tInitial Values: MajorTic = ', yaxisMajorTic, '\tyaxis scale max = ', yaxisScaleMax, '\tyaxis scale min = ', yaxisScaleMin)
    MaxValue = max(DataDict[location]['CriticalStage'], max(StageTsc.values))
    if yaxisMajorTic < 1. : 
        maxscale = math.ceil((MaxValue + yaxisMajorTic) * yaxisMajorTic) / yaxisMajorTic
        minscale = math.ceil(yaxisScaleMin - yaxisMajorTic) - yaxisMajorTic
    else :
        maxscale = math.ceil((MaxValue + yaxisMajorTic) / yaxisMajorTic) * yaxisMajorTic
        minscale = math.ceil(yaxisScaleMin - yaxisMajorTic)
    outputDebug(debug, lineNo(), Location, '\tFirst Values: MajorTic = ', yaxisMajorTic, '\tyaxis scale max = ', yaxisScaleMax, '\tyaxis scale min = ', yaxisScaleMin,
        '\tmaxscale = ', maxscale, '\tminscale = ', minscale)

    yaxis.setScaleLimits(minscale, maxscale)

    # Loop until yaxisMajorTic does not change
    for x in range(5) :
        # Check if MajorTic changed
        newYaxisMajorTic = yaxis.getMajorTic()
        if yaxisMajorTic == newYaxisMajorTic : break
        else : yaxisMajorTic = newYaxisMajorTic
        
        MaxValue = max(DataDict[location]['CriticalStage'], max(StageTsc.values))
        if yaxisMajorTic < 1. : 
            maxscale = math.ceil((MaxValue + yaxisMajorTic) * yaxisMajorTic) / yaxisMajorTic
            minscale = math.ceil(yaxisScaleMin - yaxisMajorTic) - yaxisMajorTic
        else :
            maxscale = math.ceil((MaxValue + yaxisMajorTic) / yaxisMajorTic) * yaxisMajorTic
            minscale = math.ceil(yaxisScaleMin - yaxisMajorTic)
        yaxis.setScaleLimits(minscale, maxscale)
        
    outputDebug(debug, lineNo(), Location, '\tFinal Values: MajorTic = ', yaxisMajorTic, '\tyaxis scale max = ', yaxisScaleMax, '\tyaxis scale min = ', yaxisScaleMin,
        '\tmaxscale = ', maxscale, '\tminscale = ', minscale)

    #
    # Define the marker lines
    #
    # Power Plant Stage
    PowerPlantMarker = AxisMarker()
    PowerPlantMarker.axis = 'Y1'
    PowerPlantMarker.value = str(DataDict[location]['PpNotStage'])
    PowerPlantMarker.labelText = 'PowerPlant Notification Elevation'
    PowerPlantMarker.labelFont = 'Arial,Plain,12'
    PowerPlantMarker.labelColor = 'red'
    PowerPlantMarker.labelPosition = 'above'
    PowerPlantMarker.lineColor = 'red'
    PowerPlantMarker.lineStyle = 'Dash Dot'
    viewport.addAxisMarker(PowerPlantMarker)

    # Target Stage
    TargetMarker = AxisMarker()
    TargetMarker.axis = 'Y1'
    TargetMarker.value = str(DataDict[location]['TargetStage'])
    TargetMarker.labelText = 'Target Elevation'
    TargetMarker.labelFont = 'Arial,Plain,12'
    TargetMarker.labelColor = 'magenta'
    TargetMarker.labelPosition = 'above'
    TargetMarker.lineColor = 'magenta'
    TargetMarker.lineStyle = 'Dash Dot'
    viewport.addAxisMarker(TargetMarker)

    # Critical Stage
    CriticalMarker = AxisMarker()
    CriticalMarker.axis = 'Y1'
    CriticalMarker.value = str(DataDict[location]['CriticalStage'])
    CriticalMarker.labelText = 'Critical Elevation'
    CriticalMarker.labelFont = 'Arial,Plain,12'
    CriticalMarker.labelColor = 'cyan'
    CriticalMarker.labelPosition = 'above'
    CriticalMarker.lineColor = 'cyan'
    CriticalMarker.lineStyle = 'Dash Dot'
    viewport.addAxisMarker(CriticalMarker)

    # Plot Title
    title = plot.getPlotTitle()
    title.setForeground('darkblue')
    title.setFontFamily('Arial')
    title.setFontStyle('Normal')
    title.setFontSize(20)
    title.setText(DataDict[location]['PlotTitle'])
    title.setDrawTitleOn()
    plot.setSize(PlotWidth, PlotHeight)
    
    return plot

# -------------------------------------------------------------------
# Main Script
# -------------------------------------------------------------------
try :
    #
    # Date and time
    #
    Lookback = 5 # Number of days to lookback and set the start of the time window
    CurDate = datetime.datetime.now() # Current date
    EndTwStr = CurDate.strftime('%d%b%Y %H%M')
    StartTw = CurDate - datetime.timedelta(Lookback)
    StartTwStr = StartTw.strftime('%d%b%Y %H%M')
    outputDebug(debug, lineNo(), 'Time window = %s -- %s' % (StartTwStr, EndTwStr))
    try :
        Db = DBAPI.open()
        if not Db : raise Exception
        Db.setTimeWindow(StartTwStr, EndTwStr)
        Db.setOfficeId('NWDM')
        Db.setTimeZone('US/Central')
    except :
        outputDebug(debug, lineNo(), 'Could not open DBI, exiting.')
        sys.exit(-1)
    
    # Add data and format plot
    for location in Locations :
        plot = plotData(Db, location)

        # Save plot file
        plot.saveToJpeg (DataDict['PlotFilename'] % location.lower(), PlotQuality)
        
        # Close plot
        plot.close()
finally :
    #
    # Close databse connection
    #
    try : 
        outputDebug(True, lineNo(), 'Database connection closed')
        Db.done()
    except : pass
    # 
    # Close plot
    #
    try : 
        outputDebug(True, lineNo(), 'Plot closed')
        plot.close()
    except : pass

