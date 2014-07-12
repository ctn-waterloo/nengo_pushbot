#include "spin1_api.h"
#include "common-impl.h"

#include "nengo-common.h"
#include "nengo_typedefs.h"

#include "tracker.h"

uint size_out;
uint *keys;
value_t *output_values, *transforms;

void tick(uint ticks, uint arg1) {
  use(arg1);
  if (simulation_ticks != UINT32_MAX && ticks >= simulation_ticks) {
    spin1_exit(0);
  }

  // Convert x, y position to S1615
  uint output_vals[3];
  output_vals[0] = (pos_x << 8) - (1 << 7);
  output_vals[1] = (pos_y << 8) - (1 << 7);
  output_vals[2] = 0;  // TODO Compute certainty

  // Apply all output transforms and transmit packets
  for (uint j = 0; j < size_out; j++) {
    output_values[j] = 0;
    for (uint k = 0; k < 3; k++)
      output_values[j] += transforms[j*3 + k] * output_vals[k];
  }
  for (int i = 0; i < 3; i++) {
    spin1_send_mc_packet(keys[i], bitsk(output_values[i]), WITH_PAYLOAD);
    spin1_delay_us(1);
  }
}

bool get_system_region(address_t addr) {
  // Copy in the rate of adaptation and the expected time delta
  r_adaptation = addr[0];
  t_exp = addr[1];
  return true;
}

bool get_output_keys(address_t addr) {
  size_out = addr[0];

  MALLOC_FAIL_FALSE(keys, size_out * sizeof(uint), "");
  MALLOC_FAIL_FALSE(output_values, size_out * sizeof(value_t), "");

  spin1_memcpy(keys, &addr[1], size_out * sizeof(uint));

  return true;
}

bool get_transforms(address_t addr) {
  MALLOC_FAIL_FALSE(transforms, size_out * sizeof(value_t) * 3, "");
  spin1_memcpy(transforms, addr, size_out * sizeof(value_t) * 3);

  return true;
}

bool get_space_gaussian(address_t addr) {
  spin1_memcpy(gaussian_space, addr, 256 * sizeof(value_t));
  return true;
}

bool get_time_gaussian(address_t addr) {
  MALLOC_FAIL_FALSE(gaussian_time, gaussian_time[0] * sizeof(value_t), "");
  gaussian_time_length = gaussian_time[0];
  spin1_memcpy(gaussian_time, addr, gaussian_time_length * sizeof(value_t));
  return true;
}

void c_main(void) {
  address_t addr = system_load_sram();
  if (leadAp) {
    system_lead_app_configured();
  }

  // Clear the pixel timestamps
  for (int i = 0; i < 128; i++)
    for (int j = 0; j < 128; j++)
      deltas[i][j] = 0;

  // Load in output keys, Gaussians and transforms
  if (!get_system_region(region_start(1, addr)) ||
      !get_output_keys(region_start(2, addr)) ||
      !get_transforms(region_start(3, addr)) ||
      !get_space_gaussian(region_start(4, addr)) ||
      !get_time_gaussian(region_start(5, addr))
     ) {
    return;
  }

  // Set up callbacks
  spin1_set_timer_tick(1000);
  spin1_callback_on(TIMER_TICK, tick, 1);
  spin1_callback_on(MCPL_PACKET_RECEIVED, spike_rx, -2);

  // Wait
  spin1_start(SYNC_WAIT);
}
