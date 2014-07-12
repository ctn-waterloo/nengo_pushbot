# SpiNNaker Nengo Pushbot Integration
# ----------------------------------------------------------------------------
# Authors:
#  Andrew Mundy <mundya@cs.man.ac.uk>
#  Terry Stewart
# ----------------------------------------------------------------------------
# Code derived from Andrew Rowley, University of Manchester

APPS = compass_calibrate countspikes tracker
APP_OUTPUT_DIR = $(PWD)/../nengo_pushbot/binaries
COMPLETE_SOURCE = ./*/*.c ./*/*.h

all :
	for a in $(APPS); do ( cd $$a; "$(MAKE)"  ) || exit $$?; done

docs : ${COMPLETE_SOURCE}
	doxygen

clean :
	for a in $(APPS); do ( cd $$a; "$(MAKE)" clean  ) || exit $$?; done
	rm -rf ./docs/
