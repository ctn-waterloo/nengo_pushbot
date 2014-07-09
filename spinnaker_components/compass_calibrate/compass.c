#include "spin1_api.h"
#include "common-impl.h"

#include "nengo-common.h"
#include "nengo_typedefs.h"

typedef struct _key_id_t {
  uint dimension:2;
  uint sensor:5;
  uint index:4;
  uint header:21;
} key_id_t;

// Compass data
value_t compass_data[3], compass_max[3], compass_min[3];
value_t *output, *transform;

// Output keys
uint * keys;
uint size_out;

void mc_receive(uint key, uint payload) {
  // Assert that this packet relates to compass data
  key_id_t * info;
  info = (key_id_t *) &key;

  if (info->sensor == 9) {
    // Update the stored max and min values if required
    compass_max[info->dimension] =
      (compass_max[info->dimension] > kbits(payload) ?
       compass_max[info->dimension] : kbits(payload));
    compass_min[info->dimension] =
      (compass_min[info->dimension] < kbits(payload) ?
       compass_min[info->dimension] : kbits(payload));

    // Determine the range for the values
    value_t range = compass_max[info->dimension] -
                    compass_min[info->dimension];

    if ((uint) bitsk(range) > 0) {
      value_t c__ = 1. / range;
      compass_data[info->dimension] =
        (((kbits(payload) - compass_min[info->dimension]) * c__) - 0.5k) * 2.0k;
    }
  }
}

void tick(uint ticks, uint arg1) {
  use(arg1);

  if (simulation_ticks != UINT32_MAX && ticks >= simulation_ticks) {
    spin1_exit(0);
  }

  // Perform the transform and then output each MC packet
  for (uint j = 0; j < size_out; j++) {
    output[j] = 0;

    for (uint k = 0; k < 3; k++) {
      output[j] += transform[j*3 + k] * compass_data[k];
    }
  }

  for(uint d = 0; d < size_out; d++) {
    spin1_send_mc_packet(keys[d], bitsk(output[d]), WITH_PAYLOAD);
    spin1_delay_us(1);
  }
}

bool get_data(address_t addr) {
  size_out = region_start(1, addr)[0];
  io_printf(IO_BUF, "Size out = %d\n", size_out);

  // Get transforms
  MALLOC_FAIL_FALSE(output, size_out * sizeof(value_t), "Transform");
  MALLOC_FAIL_FALSE(transform, 3 * size_out * sizeof(value_t), "Transform");
  spin1_memcpy(transform, region_start(3, addr),
               3 * size_out * sizeof(value_t));

  io_printf(IO_BUF, "Transform = [");
  for (uint i = 0; i < size_out; i++) {
    for (uint j = 0; j < 3; j++) {
      io_printf(IO_BUF, "%k ", transform[i*3 + j]);
    }
    io_printf(IO_BUF, "\n             ");
  }
  io_printf(IO_BUF, "\r]\n");

  // Get keys
  MALLOC_FAIL_FALSE(keys, size_out * sizeof(uint), "Keys");
  spin1_memcpy(keys, region_start(2, addr), size_out * sizeof(uint));

  for (uint i = 0; i < size_out; i++) {
    io_printf(IO_BUF, "Key[%d] = 0x%08x\n", i, keys[i]);
  }

  return true;
}

void c_main(void) {
  address_t addr = system_load_sram();
  if (leadAp) {
    system_lead_app_configured();
  }

  if (!get_data(addr)) {
    return;
  }

  // Set up the callbacks
  spin1_set_timer_tick(1000);
  spin1_callback_on(TIMER_TICK, tick, 2);
  spin1_callback_on(MCPL_PACKET_RECEIVED, mc_receive, -1);

  spin1_start(SYNC_WAIT);
}
