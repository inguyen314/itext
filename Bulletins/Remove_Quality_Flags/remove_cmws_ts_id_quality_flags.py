# Set Quality Flag to 0 for a CWMS TS ID

from hec.script		                import MessageBox, Constants
import java
import time,calendar,datetime
from time				            import mktime
from hec.dssgui		                import ListSelection
from time				            import mktime
import inspect
import DBAPI
import os
import urllib
from hec.heclib.util	            import HecTime
from hec.hecmath		            import TimeSeriesMath
from hec.io			                import TimeSeriesContainer
from rma.services		            import ServiceLookup
from java.util			            import TimeZone
from hec.data.tx                    import QualityTx


try:
    CurDate = datetime.datetime.now() - datetime.timedelta(days=(32*365))
    #CurDate = '2017-12-31 23:59:59.000000'
    print 'CurDate = ' + str(CurDate)
    EndTwStr = CurDate.strftime('%d%b%Y %H%M')
    print 'EndTwStr = ' + EndTwStr

    StartTw  = datetime.datetime.now() - datetime.timedelta(days=(35*365)) # datetime.timedelta(days=(42*365)) = go back 42 years (1980)
    #StartTw  = '2015-01-01 01:01:01.000000'
    print 'StartTw = ' + str(StartTw)
    StartTwStr = StartTw.strftime('%d%b%Y %H%M')
    print 'StartTwStr = ' + StartTwStr
    #sys.exit()

    try :
        CwmsDb = DBAPI.open()
        if not CwmsDb : raise Exception
        CwmsDb.setTimeWindow(StartTwStr, EndTwStr)
        CwmsDb.setOfficeId('MVS')
        CwmsDb.setTimeZone('GMT')
        #conn = CwmsDb.getConnection()
    except :
        outputDebug(debug, lineNo(), 'Could not open DBI, exiting.')
        sys.exit(-1)


    #Data = ['Pacific-Meramec.Stage.Inst.15Minutes.0.lrgsShef-rev'] # STAGE REV and 29 GOES HERE

    Data = ['Sub-Casey Fork.Stage.Inst.30Minutes.0.lrgsShef-rev','Sub-Casey Fork.Stage.Inst.30Minutes.0.29'] # STAGE REV and 29 GOES HERE

    for x in Data:

        Tsc = CwmsDb.get(x)

        print "len(Tsc.values) = " + str(len(Tsc.values))

        for i in range(Tsc.numberValues) :

            # Write over to protected data
            CwmsDb.setOverrideProtection(True)

            # This will get all values from the database. Otherwise it will not get the null values
            CwmsDb.setTrimMissing(False)

            print "-----i------ start = " + str(Tsc.quality[i])

            # Remove protection flag
            Tsc.quality[i] = QualityTx.clearProtected_int(Tsc.quality[i])

            # force set quality to 0, not used
            #Tsc.quality[i] = 0

        
            print "-----i------ end = " + str(Tsc.quality[i])
            
        CwmsDb.put(Tsc)
        print 'EndTwStr = ' + EndTwStr
        print 'StartTwStr = ' + StartTwStr

        print 'CurDate = ' + str(CurDate)
        print 'StartTw = ' + str(StartTw)

finally :
    try : CwmsDb.done()
    except : pass
    #try : conn.close()
    #except : pass