#!/bin/csh
# Script to extract CWMS data in SHEF format for external website
# Uses ExportSHEF program to create files in the $CWMS_HOME/Mainstem2SHEF directory
# Each basin has 4 basic lines to create a basin.shef file.
# To run the file manually enter "./Mainstem2SHEF.csh"
#
source /netapp/g7cwmspd/.cshrc
#
cd /netapp/g7cwmspd/cronjobs/Mainstem2SHEF

#
# MRBWM - Mainstem Data
#
# Mainstem
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_Mainstem.in \
OUT=MRBWM_Mainstem.shef \
LOG=MRBWM_Mainstem.log

# scp to nwo-wmlocal2 and nwk-wmlocal2
/bin/scp -rp /netapp/g7cwmspd/cronjobs/Mainstem2SHEF/MRBWM_Mainstem.shef `echo $LOCALZONE`:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Mainstem2SHEF/MRBWM_Mainstem.shef `echo $COOPLOCAL`:/netapp/g7cwmspd/mrads/db

