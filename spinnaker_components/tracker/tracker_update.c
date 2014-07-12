#include "tracker.h"

ushort deltas[128][128];     //!< Pixel deltas
ushort * gaussian_time;      //!< Gaussian for time filtering - 16b fract
ushort gaussian_space[256];  //!< Gaussian for position filtering - 16b fract
uchar gaussian_time_length;  //!< Index of the position at which the Gaussian
                             //   for time effectively becomes zero

uchar pos_x;   //!< Current estimated x position (pixel space)
uchar pos_y;   //!< Current estimated y position (pixel space)

ushort r_adaptation; //!< Adaptation rate
ushort t_exp;  //!< Expected time delta

void spike_rx(uint key, uint payload) {
  // Get the x, y, p of the spike
  uchar x, y;
  bool p;
  x = (key & (0x7f << 7)) >> 7;
  y = key & 0x7f;
  p = key & 0x8000 >> 15;

  // If the spike was a down spike then ignore it
  if (!p)
    return;

  // Calculate the delta and store the last timestamp for the pixel
  ushort delta = payload - deltas[x][y];
  deltas[x][y] = payload;
  ushort t_deviation = delta - t_exp;

  // Determine the Manhattan distance between this point and the current best
  // estimated position.
  ushort displacement = (x > pos_x ? x - pos_x : pos_x - x) +
                        (y > pos_y ? y - pos_y : pos_y - y);

  // Get the certainty weights for time and displacement
  ushort wt = t_deviation > gaussian_time_length ?
              0 : gaussian_time[t_deviation];
  ushort wp = gaussian_space[displacement];

  // Calculate the new position for the x and y estimates
  // This is pretty obfuscated TODO Neaten up with clearer fix point
  uint sc1 = (((uint)r_adaptation) * (wt + wp)) >> 16;   // = eta * (wt + wp)
  pos_x = (uchar)((((0x10000 - sc1) * pos_x) + sc1 * x) >> 16);
  pos_y = (uchar)((((0x10000 - sc1) * pos_y) + sc1 * y) >> 16);
}
