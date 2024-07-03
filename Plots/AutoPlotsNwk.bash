#!/bin/bash
. /wm/nwo/g7cwpa30/.bashrc
echo ...
echo 'Starting NWK Plots at:' `date`
echo ...
DISPLAY=:1;export DISPLAY
echo $DISPLAY

cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWK
rm *.jpg

cd /wm/nwo/g7cwpa30/cronjobs/Plots

# Run each script below to generate plots
jython Reservoir_NwkElevInflowOutflowPrecipStorZones_Plots.py
jython Reservoir_NwkKanProjFlow_Plots.py
jython River_NwkKrftFlow_Plots.py

#
# Move files to web and to local zone MRADS cwmspixel directory for displaying by viewpix
#
echo 'Moving files to web server.'
# Change directory to the location of images
cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWK
/bin/scp -p *jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs

echo ...
echo 'Finished NWK Plots at:' `date`
echo ...
