# -----------------------------------------------------------------------
# ioc-cryo — cryogenics simulation IOC
# Runs the generic `labioc` binary; IOC_PREFIX comes from the container env.
# -----------------------------------------------------------------------

## Identify this IOC to RecSync/ChannelFinder (sent by reccaster)
epicsEnvSet("IOCNAME", "${IOC_NAME}")

dbLoadDatabase("/opt/epics/ioc/dbd/labioc.dbd")
labioc_registerRecordDeviceDriver(pdbbase)

## Device simulation database
dbLoadRecords("/config/db/cryo.db", "P=${IOC_PREFIX}")

## IOC health / statistics PVs ($(IOC_PREFIX):IOC:HEARTBEAT etc.)
dbLoadRecords("/opt/epics/modules/iocStats/db/iocAdminSoft.db", "IOC=${IOC_PREFIX}:IOC")

## CA access security: open read/write with write trapping (caPutLog)
asSetFilename("/common/lab.acf")

## Autosave: restore operator settings across restarts
set_savefile_path("/autosave")
set_requestfile_path("/config/req")
save_restoreSet_DatedBackupFiles(0)
save_restoreSet_NumSeqFiles(3)
save_restoreSet_SeqPeriodInSeconds(600)
set_pass0_restoreFile("cryo_settings.sav")
set_pass1_restoreFile("cryo_settings.sav")

iocInit()

## Forward trapped CA puts to the central caputlog server
caPutLogInit("${CAPUTLOG_ADDR}", 1)

## Save operator settings every 30 s (on change)
create_monitor_set("cryo_settings.req", 30, "P=${IOC_PREFIX}")
