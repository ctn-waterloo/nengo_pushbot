/*
 * Tracks - Input
 * --------------
 * Structures and functions to deal with arriving multicast packets (input).
 *
 * Authors:
 *   - Andrew Mundy <mundya@cs.man.ac.uk>
 *   - Terry Stewart
 * 
 * Copyright:
 *   - Advanced Processor Technologies, School of Computer Science,
 *      University of Manchester
 *   - Computational Neuroscience Research Group, Centre for
 *      Theoretical Neuroscience, University of Waterloo
 */

#include "tracks-input.h"

// Globals
filtered_input_buffer_t *gfib_input;

value_t* initialise_input(region_system_t *pars){
  // Buffer initialisation
  gfib_input = input_buffer_initialise(2);
  gfib_input->filter = pars->filter;
  gfib_input->n_filter = pars->filter_complement;

  // Set up the multicast callback
  spin1_callback_on(
    MCPL_PACKET_RECEIVED, incoming_dimension_value_callback, -1
  );

  // Return the input (to the encoders) buffer
  return gfib_input->filtered;
}

// Incoming spike callback
void incoming_dimension_value_callback( uint key, uint payload )
{
  uint dimension = key & 0x0000000f;
  gfib_input->accumulator[ dimension ] += kbits( payload );
}
