#ifndef __TRACKS_H__
#define __TRACKS_H__

#include "spin1_api.h"
#include "stdfix-full-iso.h"
#include "common-typedefs.h"

#include "nengo_typedefs.h"
#include "dimensional-io.h"

#include "ensemble-input.h"

/* Structs *******************************************************************/
/** \brief Shared tracks parameters.
 */
typedef struct tracks_parameters {
  uint machine_timestep;  //!< Machine timestep / useconds
  uint output_pause;      //!< Number of ticks between motor commands

  value_t *input;         //!< Input buffer
} tracks_parameters_t;

/* Parameters and Buffers ****************************************************/
extern tracks_parameters_t g_tracks;  //!< Global parameters

/* Functions *****************************************************************/
/**
 *\brief Initialise the tracks.
 */
void initialise_tracks(
  region_system_t *pars //!< Pointer to formatted system region
);

/**
 * \brief Filter the input values, scale and output to the motor when required.
 */
void tracks_update(uint arg0, uint arg1);

#endif
