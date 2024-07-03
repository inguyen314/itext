#!/bin/csh
# Script to extract CWMS data in SHEF format for external website
# Uses ExportSHEF program to create files in the $CWMS_HOME/Fcst2SHEF directory
# Each basin has 4 basic lines to create a basin.shef file.
# To run the file manually enter "./Fcst2SHEF.csh"
#
source /netapp/g7cwmspd/.cshrc
#
cd /netapp/g7cwmspd/cronjobs/Fcst2SHEF

#
# MRBWM - Three Week Forecast
#
# Fort Peck
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_TW_Release_FTPK.in \
OUT=MRBWM_TW_Release_FTPK.shef \
LOG=MRBWM_TW_Release_FTPK.log
# Garrison
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_TW_Release_GARR.in \
OUT=MRBWM_TW_Release_GARR.shef \
LOG=MRBWM_TW_Release_GARR.log
# Oahe
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_TW_Release_OAHE.in \
OUT=MRBWM_TW_Release_OAHE.shef \
LOG=MRBWM_TW_Release_OAHE.log
# Big Bend
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_TW_Release_BEND.in \
OUT=MRBWM_TW_Release_BEND.shef \
LOG=MRBWM_TW_Release_BEND.log
# Fort Randall
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_TW_Release_FTRA.in \
OUT=MRBWM_TW_Release_FTRA.shef \
LOG=MRBWM_TW_Release_FTRA.log
# Gavins Point
$CWMS_EXE/bin/ExportSHEF \
IN=MRBWM_TW_Release_GAPT.in \
OUT=MRBWM_TW_Release_GAPT.shef \
LOG=MRBWM_TW_Release_GAPT.log

# scp to nwo-wmlocal2
#cd /netapp/g7cwmspd/cronjobs/Fcst2SHEF
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_FTPK.shef nwo-wmlocal2:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_GARR.shef nwo-wmlocal2:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_OAHE.shef nwo-wmlocal2:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_BEND.shef nwo-wmlocal2:/netapp/g7cwmspd/mrads/db
/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_FTRA.shef nwo-wmlocal2:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_GAPT.shef nwo-wmlocal2:/netapp/g7cwmspd/mrads/db
#
# cp to nwk-wmlocal2.nwk for COOP
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_FTPK.shef nwk-wmlocal2.nwk:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_GARR.shef nwk-wmlocal2.nwk:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_OAHE.shef nwk-wmlocal2.nwk:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_BEND.shef nwk-wmlocal2.nwk:/netapp/g7cwmspd/mrads/db
/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_FTRA.shef nwk-wmlocal2.nwk:/netapp/g7cwmspd/mrads/db
#/bin/scp -rp /netapp/g7cwmspd/cronjobs/Fcst2SHEF/MRBWM_TW_Release_GAPT.shef nwk-wmlocal2.nwk:/netapp/g7cwmspd/mrads/db

