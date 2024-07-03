#!/bin/bash
. /wm/nwo/g7cwpa30/.bashrc
echo ...
echo 'Starting MRBWM Plots at:' `date`
echo ...
DISPLAY=:1;export DISPLAY
echo $DISPLAY

cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/MRBWM
rm *.jpg

cd /wm/nwo/g7cwpa30/cronjobs/Plots

# Run each script below to generate plots
jython Reservoir_MrbwmElevInflowOutflow_Plots.py
jython Reservoir_MrbwmElevInflowOutflowZones_Plots.py
jython Reservoir_MrbwmMinElevInflowOutflowPrecipStor_Plots.py
jython River_MrbwmPirGagesStage_Plots.py
jython River_MrbwmGrftFlow_Plots.py
jython River_MrbwmCompareStageFlow_Plots.py

#
# Move files to web and to local zone MRADS cwmspixel directory for displaying by viewpix
#
echo 'Moving files to web server.'
# Location of images
cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/MRBWM
/bin/scp -p *jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs
echo ...
echo 'Finished MRBWM Plots at:' `date`
echo ...
