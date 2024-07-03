# name=NWO_Res_Elev_RawRev_Plots
# displayinmenu=false
# displaytouser=false
# displayinselector=false
'''

Author: Ryan Larsen
Revised: Ryan Larsen
Last Updated: 01-25-2018
Description: Creates elevation plots for all tributary projects in the Missouri River Basin. Runs on a cron on nwo-cwms2 g7cwmspd (script located in cronjobs)
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
Locations = ['BECR', 'CHFI', 'COLD', 'PA11', 'PA16', 'PA18', 'PA20', 'SC02', 'SC04', 'SC08', 'SC09', 
            'SC10', 'SC12', 'SC13', 'SC14', 'SC17', 'SC18', 'BOHA', 'CHCR', 'COTT', 'PIST', 'BOYN', 'CAFE', 'GLEN', 'JATO', 'PACA', 'SHHI',
            'YETL', 'CLCA', 'HEBU', 'KEYO', 'TIBR']

# Plot info
PlotWidth= 975
PlotHeight = 735
PlotQuality = 100 # range of 0 (crappy) to 100 (great, but larger file)

# Dictionary of data
DataDict = {	 'BECR'              :	{	'DbLocation'        :   'BECR-Bear_Creek_Dam-Bear',
                                            'PlotTitle'         :   'Bear Creek Dam on Bear Creek, Denver Metro, CO',
                                            },
                'CHFI'              :	{	'DbLocation'        :   'CHFI-Chatfield_Dam-South_Platte',
                                            'PlotTitle'         :   'Chatfield Dam on South Platte River, Denver Metro, CO',
                                            },
                'COLD'              :	{	'DbLocation'        :   'COLD-Coldbrook_Dam-Cold_Br',
                                            'PlotTitle'         :   'Cold Brook Dam on Cold Brook, Hot Springs, SD',
                                            },
                'PA11'              :	{	'DbLocation'        :   'PA11-Papio_Cr_Dam_11-Cunningham_Lake',
                                            'PlotTitle'         :   'Cunningham Lake / Papio Dam 11, Omaha, NE',
                                            },
                'PA16'              :	{	'DbLocation'        :   'PA16-Papio_Cr_Dam_16-Stand_Bear_Lake',
                                            'PlotTitle'         :   'Standing Bear Lake / Papio Dam 16, Omaha, NE',
                                            },
                'PA18'              :	{	'DbLocation'        :   'PA18-Papio_Cr_Dam_18-Zorinsky_Lake',
                                            'PlotTitle'         :   'Zorinksy Lake / Papio Dam 18, Omaha, NE',
                                            },
                'PA20'              :	{	'DbLocation'        :   'PA20-Papio_Cr_Dam_20-Wehrspann_Lake',
                                            'PlotTitle'         :   'Wehrspann Lake / Papio Dam 20, Omaha Metro, NE',
                                            },
                'SC02'              :	{	'DbLocation'        :   'SC02-Salt_Cr_Dam_2-Olive_Creek_Lake',
                                            'PlotTitle'         :   'Olive Branch Creek / Salt Cr Dam 2, Lincoln, NE',
                                            },
                'SC04'              :	{	'DbLocation'        :   'SC04-Salt_Cr_Dam_4-Blue_Stem_Lake',
                                            'PlotTitle'         :   'Blue Stem Lake / Salt Cr Dam 4, Lincoln, NE',
                                            },
                'SC08'              :	{	'DbLocation'        :   'SC08-Salt_Cr_Dam_8-Wagon_Train_Lake',
                                            'PlotTitle'         :   'Wagon Train Lake / Salt Cr Dam 8, Lincoln, NE',
                                            },
                'SC09'              :	{	'DbLocation'        :   'SC09-Salt_Cr_Dam_9-Stagecoach_Lake',
                                            'PlotTitle'         :   'Stagecoach Lake / Salt Cr Dam 9, Lincoln, NE',
                                            },
                'SC10'              :	{	'DbLocation'        :   'SC10-Salt_Cr_Dam_10-Yankee_Hill_Lake',
                                            'PlotTitle'         :   'Yankee Hill Lake / Salt Cr Dam 10, Lincoln, NE',
                                            },
                'SC12'              :	{	'DbLocation'        :   'SC12-Salt_Cr_Dam_12-Conestoga_Lake',
                                            'PlotTitle'         :   'Conestoga Lake / Salt Cr Dam 12, Lincoln, NE',
                                            },
                'SC13'              :	{	'DbLocation'        :   'SC13-Salt_Cr_Dam_13-Twin_Lakes',
                                            'PlotTitle'         :   'Twin Lakes / Salt Cr Dam 13, Lincoln, NE',
                                            },
                'SC14'              :	{	'DbLocation'        :   'SC14-Salt_Cr_Dam_14-Pawnee_Lake',
                                            'PlotTitle'         :   'Pawnee Lake / Salt Cr Dam 14, Lincoln, NE',
                                            },
                'SC17'              :	{	'DbLocation'        :   'SC17-Salt_Cr_Dam_17-Holmes_Lake',
                                            'PlotTitle'         :   'Holmes Lake / Salt Cr Dam 17, Lincoln, NE',
                                            },
                'SC18'              :	{	'DbLocation'        :   'SC18-Salt_Cr_Dam_18-Branched_Oak_Lake',
                                            'PlotTitle'         :   'Branched Oak Lake / Salt Cr Dam 18, Lincoln, NE',
                                            },
                'BOHA'              :	{	'DbLocation'        :   'BOHA-Bowman_Haley_Dam-Grand',
                                            'PlotTitle'         :   'Bowman-Haley Dam on Grand River, Bowman, ND',
                                            },
                'CHCR'              :	{	'DbLocation'        :   'CHCR-Cherry_Creek_Dam-Cherry',
                                            'PlotTitle'         :   'Cherry Creek Dam on Cherry Creek, Denver Metro, CO',
                                            },
                'COTT'              :	{	'DbLocation'        :   'COTT-Cottonwood_Dam-Cottonwood_Spr',
                                            'PlotTitle'         :   'Cottonwood Springs Dam on Cottonwood Spring, Hot Springs, SD',
                                            },
                'PIST'              :	{	'DbLocation'        :   'PIST-Pipestem_Dam-Pipestem',
                                            'PlotTitle'         :   'Pipestem Dam on Pipestem Creek, Jamestown, ND',
                                            },
                'BOYN'              :	{	'DbLocation'        :   'BOYN-Boysen_Dam-Wind',
                                            'PlotTitle'         :   'Boysen Dam on Wind River, WY',
                                            },
                'CAFE'              :	{	'DbLocation'        :   'CAFE-Canyon_Ferry_Dam-Missouri',
                                            'PlotTitle'         :   'Canyon Ferry Dam on Missouri River, MT',
                                            },
                'GLEN'              :	{	'DbLocation'        :   'GLEN-Glendo_Dam-North_Platte',
                                            'PlotTitle'         :   'Glendo Dam on North Platte River, WY',
                                            },
                'JATO'              :	{	'DbLocation'        :   'JATO-Jamestown_Dam-James',
                                            'PlotTitle'         :   'Jamestown Dam on James River, Jamestown, ND',
                                            },
                'PACA'              :	{	'DbLocation'        :   'PACA-Pactola_Dam-Rapid',
                                            'PlotTitle'         :   'Pactola Dam on Rapid Creek, outside Rapid City, SD',
                                            },
                'SHHI'              :	{	'DbLocation'        :   'SHHI-Shadehill_Dam-Grand',
                                            'PlotTitle'         :   'Shadehill Dam on Grand River, SD',
                                            },
                'YETL'              :	{	'DbLocation'        :   'YETL-Yellowtail_Dam-Bighorn_Lake',
                                            'PlotTitle'         :   'Yellowtail Dam on Bighorn River, MT',
                                            },
                'BUBI'              :	{	'DbLocation'        :   'BUBI-Buffalo_Bill_Dam-Shoshone',
                                            'PlotTitle'         :   'Buffalo Bill Reservoir on Shoshone River, Cody, WY',
                                            },
                'CLCA'              :	{	'DbLocation'        :   'CLCA-Clark_Canyon_Dam-Red_Rock',
                                            'PlotTitle'         :   'Clark Canyon Dam on Red Rock River, MT',
                                            },
                'HEBU'              :	{	'DbLocation'        :   'HEBU-Heart_Butte_Dam-Heart',
                                            'PlotTitle'         :   'Heart Butte Dam on Heart River, ND',
                                            },
                'KEYO'              :	{	'DbLocation'        :   'KEYO-Keyhole_Dam-Belle_Fourche',
                                            'PlotTitle'         :   'Keyhole Dam on Belle Fourche River, WY',
                                            },
                'TIBR'              :	{	'DbLocation'        :   'TIBR-Tiber_Dam-Marias',
                                            'PlotTitle'         :   'Tiber Dam on Marias River, MT',
                                            },
                'CurveProperties'	:   {   'LineColor'         :   'red',
                                            'LineStyle'         :   'Solid',
                                            'LineWidth'         :   1,
                                            'SymbolVisible'     :   Constants.FALSE,
                                            'SymbolType'        :   'Square',
                                            'SymbolSize'        :   7,
                                            'SymbolLineColor'   :   'blue',
                                            'SymbolFillColor'   :   'blue',
                                            'SymbolInterval'    :   0,
                                            'SymbolSkipCount'   :   0,
                                            'FirstSymbolOffset'	:   0,
                                            'FillType'          :   'None',
                                            'FillColor'         :   'orange',
                                            'FillPattern'       :   'Solid',
                                            },
                'TitleProperties'   :	{   'Font'            	:    'Arial',
                                            'FontColor'        	:    'black',
                                            'FontStyle'        	:    'Normal',
                                            'FontSize'			:    20
                                            },
                # Pathnames
                'ElevInstHrRev'		:   '%s.Elev.Inst.1Hour.0.Combined-rev',
                'ElevInstHrRaw'    :   '%s.Elev.Inst.1Hour.0.Combined-raw',
                # Filename
                'PlotFilename'		:   '/netapp/g7cwmspd/plotFiles/files/%s3.jpg'
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
    RevOnlyLocations = ['TIBR']
    try : 
        ElevRev = Db.read(DataDict['ElevInstHrRev'] % DataDict[Location]['DbLocation'])
        ElevTscRev = ElevRev.getData()
        # Locations in list do not have a raw time series
        if Location not in RevOnlyLocations :
            ElevRaw = Db.read(DataDict['ElevInstHrRaw'] % DataDict[Location]['DbLocation'])
            ElevTscRaw = ElevRaw.getData()
    except : 
        raise ValueError
    
    #
    # Create plot
    #
    plot = Plot.newPlot()
    layout = Plot.newPlotLayout()
    
    # Define the plot layout
    view = layout.addViewport()
    if Location not in RevOnlyLocations :
        view.addCurve('Y1', ElevTscRaw)
    view.addCurve('Y1',ElevTscRev)
    plot.configurePlotLayout(layout)
    plot.showPlot()
    
    # Set curve properties
    if Location not in RevOnlyLocations :
        curve1 = plot.getCurve(ElevTscRaw)
        curve1.setLineColor(DataDict['CurveProperties']['LineColor'])
        curve1.setLineStyle(DataDict['CurveProperties']['LineStyle'])
        curve1.setLineWidth(DataDict['CurveProperties']['LineWidth'])
    curve2 = plot.getCurve(ElevTscRev)
    curve2.setLineColor(DataDict['CurveProperties']['LineColor'])
    curve2.setLineStyle(DataDict['CurveProperties']['LineStyle'])
    curve2.setLineWidth(DataDict['CurveProperties']['LineWidth'])
    
    #
    # Customize the plot
    #
    viewport = plot.getViewport(0)

    # Set Y1 scale
    yaxis = viewport.getAxis('Y1')
    yaxisScaleMax = yaxis.getScaleMax()
    yaxisScaleMin = yaxis.getScaleMin()
    yaxisMajorTic = yaxis.getMajorTic()
    CombinedTscValues = ElevTscRev.values
    if Location not in RevOnlyLocations :
        for value in ElevTscRaw.values :
            CombinedTscValues.append(value)
    # Substitute missing values with maximum value. This is only for scaling purposes. Plots will still contain all of the data
    TscValues = [max(CombinedTscValues) if x == Constants.UNDEFINED else x for x in CombinedTscValues]
    MaxValue = max(TscValues)
    MinValue = min(TscValues)
    outputDebug(debug, lineNo(), Location, '\tInitial Values: MajorTic = ', yaxisMajorTic, '\tyaxis scale max = ', yaxisScaleMax, '\tyaxis scale min = ', yaxisScaleMin,
            '\tMax Value = ', MaxValue, '\tMin Value = ', MinValue)
    maxscale = int(MaxValue)
    i = 1
    outputDebug(debug, lineNo(), 'maxscale = ', maxscale)
    while maxscale < (MaxValue + yaxisMajorTic) :
        maxscale += yaxisMajorTic
        outputDebug(debug, lineNo(), 'Increase maxscale: ', maxscale)
        i += 1
        if i > 1000 : 
            outputDebug(debug, lineNo(), 'Break initial maxscale loop')
            break
    
    minscale = math.ceil(MinValue)
    i = 1
    while minscale > (MinValue - yaxisMajorTic) :
        minscale -= yaxisMajorTic
        i += 1
        if i > 1000 : 
            outputDebug(debug, lineNo(), 'Break initial minscale loop')
            break
    outputDebug(debug, lineNo(), Location, '\tFirst Values: MajorTic = ', yaxisMajorTic, '\tyaxis scale max = ', yaxisScaleMax, '\tyaxis scale min = ', yaxisScaleMin,
        '\tmaxscale = ', maxscale, '\tminscale = ', minscale)
    
    yaxis.setScaleLimits(minscale, maxscale)

    # Loop until yaxisMajorTic does not change
    for x in range(5) :
        # Check if MajorTic changed
        newYaxisMajorTic = yaxis.getMajorTic()
        outputDebug(debug, lineNo(), 'newYaxisMajorTic = ', newYaxisMajorTic, '\tyaxisMajorTic = ', yaxisMajorTic)
        if yaxisMajorTic == newYaxisMajorTic or newYaxisMajorTic < 0.1 : break
        else : yaxisMajorTic = newYaxisMajorTic
        
        MaxValue = max(TscValues)
        MinValue = min(TscValues)
        maxscale = int(MaxValue)
        outputDebug(debug, lineNo(), 'maxscale = ', maxscale, '\tMaxValue = ', MaxValue)
        i = 1
        while maxscale < (MaxValue + yaxisMajorTic) :
            maxscale += yaxisMajorTic
            i += 1
            if i > 1000 : 
                outputDebug(debug, lineNo(), 'Break maxscale loop')
                break
        
        minscale = math.ceil(MinValue)
        i = 1
        outputDebug(debug, lineNo(), 'minscale = ', minscale, '\tMinValue = ', MinValue)
        while minscale > (MinValue - yaxisMajorTic) :
            minscale -= yaxisMajorTic
            i += 1
            if i > 1000 : 
                outputDebug(debug, lineNo(), 'Break minscale loop')
                break
        outputDebug(debug, lineNo(), 'Final minscale = ', minscale, '\tFinal maxscale = ', maxscale)
        yaxis.setScaleLimits(minscale, maxscale)

    # Set Y1 label. In CWMS v3.0.3.50, axis label randomly does not appear correctly. Use this to correctly label axis
    yaxis.setLabel('%s (%s)' % (ElevTscRev.parameter, ElevTscRev.units))
        
    # Plot Title
    title = plot.getPlotTitle()
    title.setForeground(DataDict['TitleProperties']['FontColor'])
    title.setFontFamily(DataDict['TitleProperties']['Font'])
    title.setFontStyle(DataDict['TitleProperties']['FontStyle'])
    title.setFontSize(DataDict['TitleProperties']['FontSize'])
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
    Lookback    = 16 # Number of days to lookback and set the start of the time window
    CurDate     = datetime.datetime.now() # Current date
    EndTwStr    = CurDate.strftime('%d%b%Y %H%M')
    StartTw     = CurDate - datetime.timedelta(Lookback)
    StartTwStr  = StartTw.strftime('%d%b%Y %H%M')
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
        try :
            outputDebug(True, lineNo(), 'Creating plot for %s' % location)
            plot = plotData(Db, location)
        
            # Save plot file
            plot.saveToJpeg (DataDict['PlotFilename'] % location.lower(), PlotQuality)
            
            # Close plot
            plot.close()
            outputDebug(True, lineNo(), '%s Plot closed' % location)
        except :
            outputDebug(True, lineNo(), 'Could not create %s plot' % location)
            # 
            # Close plot
            #
            try : 
                outputDebug(True, lineNo(), '%s Plot closed' % location)
                plot.close()
            except : pass
finally :
    #
    # Close database connection
    #
    try : 
        outputDebug(True, lineNo(), 'Database connection closed')
        Db.done()
    except : pass
