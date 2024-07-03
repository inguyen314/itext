#!/bin/bash
. /wm/nwo/g7cwpa30/.bashrc
echo ...
echo 'Starting NWDM Plots at:' `date`
echo ...
DISPLAY=:1;export DISPLAY
echo $DISPLAY
cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWD
rm *jpg
cd /wm/nwo/g7cwpa30/cronjobs/Plots

# Run each script below to generate plots
jython Reservoir_NwdmElev_Plots.py
jython River_NwdmStage_Plots.py
jython River_NwdmStageFlow_Plots.py
jython River_NwdmMoRivKanFlow_Plots.py
jython Snowpack_NwdmSnotel_Plots.py
jython UmrbNetwork_NwdmHydroMet_Plots.py
jython UmrbNetwork_NwdmMet_Plots.py
jython UmrbNetwork_NwdmSoilMoisture_Plots.py
jython UmrbNetwork_NwdmSoilTemperature_Plots.py

#
# Move files to web and to local zone MRADS cwmspixel directory for displaying by viewpix
#
echo 'Moving files to web server.'
# Location of images
cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWD
/bin/scp -p *jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs
echo ...
echo 'Finished NWDM Plots at:' `date`
echo ...
