#include "spin1_api.h"
#include "spin1_api_params.h"
#include "common-impl.h"
#include "nengo-common.h"
#include "nengo_typedefs.h"

/* Implementation of ``A Miniature Low-Power Sensor System for Real Time 2D
 * Visual Tracking of LED Markers'' Muller & Conradt, 2011.  Output appropriate
 * for driving Nengo executables on SpiNNaker.
 */

/* Enable the below line to build in debug mode.
 * You should then load the produced APLX to a spin5 board with the ybug
 * commands:
 *
 * > iptag .
 * > app_load nengo_pushbot/binaries/pushbot_alm_tracker_simple.aplx 0.0.0.0 1 30
 *
 * View the output (x, y) estimate using Tubotron or similar.
 */
#define DEBUG_RETINA true

// Defines for resolution, etc.
// Downsampling to 64x64 to save memory, eventually could use DMA to store
// the last spike times to allow for full 128x128 or bigger, or store 2 byte
// timestamps, not sure.
#define X_RESOLUTION 64
#define X_RESOLUTION_SHIFT (16 - 6)  // 16 - log_2(64)
#define Y_RESOLUTION 64
#define Y_RESOLUTION_SHIFT (16 - 6)  // As above

static inline uint abs(int val)
{
  if (val >= 0)
    return val;
  else
    return (uint)(-val);
}

/* System state for the tracker */
typedef struct _tracker_t {
  value_t x, y;     //!< Current estimates of position
  uint good_events; //!< Horrible metric of confidence from Python code
  uint count;       //!< Count of events for the current time period

  uint* last_spikes;  //!< Last spikes at pixels
  uint  t_exp;        //!< Expected period us

  value_t* w_t;  //!< Weighting for time delta
  uint w_t_max;  //!< Maximum t_D with weight
  value_t* w_p;  //!< Weighting for position delta
  value_t  eta;  //!< eta weighting factor
} tracker_t;
