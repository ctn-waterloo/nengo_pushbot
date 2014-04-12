/**
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
 * 
 * \addtogroup tracks
 * @{
 */

#include "tracks.h"

#ifndef __TRACKS_INPUT_H__
#define __TRACKS_INPUT_H__

/* Buffers and parameters ****************************************************/
extern filtered_input_buffer_t *gfib_input;  //!< Input buffer

/* Functions *****************************************************************/

/**
 * \brief Initialise the input system
 * \param pars Formatted system region
 */
value_t* initialise_input(region_system_t *pars);

/**
 * \brief Handle an incoming dimensional value.
 * \param key Multicast key associated with the dimension
 * \param payload Partial value of the dimension to be accumulated
 *
 * Each arriving multicast packet contains a part of the value for a given
 * dimension for the given timestep.  On receipt of a packet the input
 * dimension referred to is taken from the bottom nibble of the key and the
 * value of the payload is added to the accumulator for this dimension.
 */
void incoming_dimension_value_callback(uint key, uint payload);

/**
 * \brief Handle the buffering and filtering of input
 *
 * Filter the inputs and set the accumulators to zero.
 */
static inline void input_filter_step( void ) {
  input_buffer_step(gfib_input);
}

#endif

/** @} */
