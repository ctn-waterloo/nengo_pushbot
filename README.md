nengo_pushbot
=============

Nengo hooks for controlling Jorg Conradt's pushbots

Compiling SpiNNaker Components
------------------------------

To compile the SpiNNaker components you will require a copy of the latest
SpiNNaker (103) release, and
[nengo_spinnaker](https://github.com/ctn-waterloo/nengo_spinnaker).

If `$SPINN103_DIR` is the location of your SpiNNaker package and 
`$SPINN103_NENGO_DIR` is the location of your nengo_spinnaker package you need
to:

 1. `cd ${SPINN103_DIR}/spinnaker_tools; source ./setup`
 1. `cd ${SPINN103_NENGO_DIR}; source ./setup`
 1. `cd ${PUSHBOT_DIR}/spinnaker_components; make`
