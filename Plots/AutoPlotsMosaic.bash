#!/bin/bash
. /wm/nwo/g7cwpa30/.bashrc
echo ...
echo 'Starting MosaicPlots at:' `date`
echo ...
DISPLAY=:1;export DISPLAY
echo $DISPLAY
cd /wm/nwo/g7cwpa30/cronjobs/Plots

# Mosaic scripts
PirGagesMosaic.script
echo 'finished PirGagesMosaic'
BisGagesMosaic.script
echo 'finished BisGagesMosaic'
CorpsGagesMosaic.script
echo 'finished CorpsGagesMosaic'
CorpsGagesMosaic2.script
echo 'finished CorpsGagesMosaic2'

#
# Move files to web and to local zone MRADS cwmspixel directory for displaying by viewpix
#
echo 'Moving files to web server.'
# Location of images
cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWO
/bin/scp -p corpsgages*.jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs

cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/NWD
/bin/scp -p bisgages.jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs

cd /wm/nwo/g7cwpa30/cronjobs/Plots/Images/MRBWM
/bin/scp -p pirgages.jpg d1wm1a93@140.194.46.137:/web/www.nwd-mr.usace.army.mil/htdocs/rcc/plots/jpegs
echo ...
echo 'Finished MosaicPlots at:' `date`
echo ...
