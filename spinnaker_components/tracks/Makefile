# SpiNNaker Nengo Pushbot Integration
# Tracks Component
# ----------------------------------------------------------------------------
# Authors:
#  Andrew Mundy <mundya@cs.man.ac.uk>
#  Terry Stewart
#
# April 2014
# ----------------------------------------------------------------------------

APP = nengo_pushbot_tracks
SOURCES = tracks-main.c ${SPINN_NENGO_DIRS}/ensemble/ensemble-input.c
OBJECTS = $(SOURCES:.c=.o)

CFLAGS += -I $(SPINN_NENGO_DIRS)/ensemble/

include ../Makefile.depend
