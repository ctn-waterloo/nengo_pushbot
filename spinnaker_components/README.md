Building Binaries for PushBot
=============================

To build the SpiNNaker binaries for nengo_pushbot you will need a developer
install of the nengo_spinnaker package from
https://github.com/ctn-waterloo/nengo_spinnaker.  Once this is available and
the build instructions in nengo_spinnaker have been followed the binaries can
be compiled by running:

	make SPINN_NENGO_DIRS=/path/to/nengo_spinnaker/spinnaker_components

For example:

	make SPINN_NENGO_DIRS=/home/andrew/nengo_spinnaker/spinnaker_components
