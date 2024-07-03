#!/bin/bash
. /wm/nwo/g7cwpa30/.bashrc
echo ...
echo 'Starting NWO Plots at:' `date`
echo ...

DISPLAY=:1;export DISPLAY
echo $DISPLAY

cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWO/
rm *.jpg

cd /wm/nwo/g7cwpa30/cronjobs/Plots

# Run each script below to generate plots
jython Reservoir_NwoElevInflowOutflowPrecipStorZones_Plots.py
jython Reservoir_NwoPrecip_Plots.py
jython Reservoir_NwoElevInflowOutflow6Hr_Plots.py
jython Reservoir_NwoElevPrecip_Plots.py
jython Reservoir_NWOSC12_Geotech.py 
jython Reservoir_NwoCorpsOwnedRaw_Plots.py
jython Reservoir_NwoRawRevElev_Plots.py
jython Reservoir_NwoRawRevRadarElev_Plots.py

#
# Move files to web and to local zone MRADS cwmspixel directory for displaying by viewpix
#
echo 'Moving files to web server.'
# Location of images
cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWO/
/bin/scp -p *jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs

echo ...
echo 'Finished NWO Plots at:' `date`
echo ...
