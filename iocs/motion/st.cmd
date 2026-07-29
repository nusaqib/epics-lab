# -----------------------------------------------------------------------
# ioc-motion — motion axis simulation IOC
# -----------------------------------------------------------------------

## Identify this IOC to RecSync/ChannelFinder (sent by reccaster)
epicsEnvSet("IOCNAME", "${IOC_NAME}")

dbLoadDatabase("/opt/epics/ioc/dbd/labioc.dbd")
labioc_registerRecordDeviceDriver(pdbbase)

## Device simulation database
dbLoadRecords("/config/db/motion.db", "P=${IOC_PREFIX}")

## IOC health / statistics PVs
dbLoadRecords("/opt/epics/modules/iocStats/db/iocAdminSoft.db", "IOC=${IOC_PREFIX}:IOC")

## CA access security: open read/write with write trapping (caPutLog)
asSetFilename("/common/lab.acf")

## Autosave
set_savefile_path("/autosave")
set_requestfile_path("/config/req")
save_restoreSet_DatedBackupFiles(0)
save_restoreSet_NumSeqFiles(3)
save_restoreSet_SeqPeriodInSeconds(600)
set_pass0_restoreFile("motion_settings.sav")
set_pass1_restoreFile("motion_settings.sav")

iocInit()

## Forward trapped CA puts to the central caputlog server
caPutLogInit("${CAPUTLOG_ADDR}", 1)

create_monitor_set("motion_settings.req", 30, "P=${IOC_PREFIX}")
