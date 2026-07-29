TOP=../..
include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

# Generic soft IOC used by every instance in this repo. Instance-specific
# databases and st.cmd are mounted into the container at /config.
PROD_IOC = labioc

# labioc.dbd will be created and installed
DBD += labioc.dbd

# Base records and IOC shell
labioc_DBD += base.dbd

# PVA server + QSRV: serve every record over PV Access as well as Channel
# Access. PVAServerRegister.dbd provides the hook that actually starts the
# PVA server at iocInit (same combination softIocPVA uses).
labioc_DBD += PVAServerRegister.dbd
labioc_DBD += qsrv.dbd

# IOC health/statistics PVs
labioc_DBD += devIocStats.dbd

# Autosave/restore of operator settings
labioc_DBD += asSupport.dbd

# RecSync client: registers all records with ChannelFinder via recceiver
labioc_DBD += reccaster.dbd

# caPutLog: log trapped CA writes to the central caputlog server
labioc_DBD += caPutLog.dbd

# labioc_registerRecordDeviceDriver.cpp derives from Makefile
labioc_SRCS += labioc_registerRecordDeviceDriver.cpp
labioc_SRCS_DEFAULT += labiocMain.cpp

labioc_LIBS += devIocStats
labioc_LIBS += autosave
labioc_LIBS += reccaster
labioc_LIBS += caPutLog
labioc_LIBS += qsrv
labioc_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
labioc_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE
