#include "spin1_api.h"
#include "common-impl.h"

#include "nengo-common.h"
#include "nengo_typedefs.h"

value_t *transform; //!< Output transform (Dx1 matrix)
uint *keys;         //!< Output keys

typedef struct _spike_counter_system_t {
  uint min_x, min_y, max_x, max_y;  //!< Top left and bottom right corners
  uint count;                       //!< Count of spikes within the region
  uint size_out;                    //!< Size out of the countspikes item
} spike_counter_system_t;
spike_counter_system_t g_system;


void mc_receive(uint key, uint payload) {
  // Get the x, y, polarity of the spike
  uint x = (payload & 0x0000ffff);
  uint y = (payload & 0x7fff0000) >> 16;
  bool p = (payload & 0x80000000) >> 31;

  // If the spike is within the region we care about then increase the count
  if (g_system.min_x <= x && g_system.min_y <= y &&
      x < g_system.max_x && y < g_system.max_y) {
    g_system.count++;
  }
}


void tick(uint ticks, uint arg1) {
  use(arg1);

  if (simulation_ticks != UINT32_MAX && ticks >= simulation_ticks) {
    spin1_exit(0);
  }

  // Apply the output transform to the count data and transmit
  value_t count = kbits(g_system.count << 15);

  for (uint i = 0; i < g_system.size_out; i++) {
    spin1_send_mc_packet(keys[i], bitsk(count * transform[i]),
                         WITH_PAYLOAD);
    spin1_delay_us(1);
  }

  // Zero the count
  g_system.count = 0;
}


bool get_data(address_t addr) {
  // Read in the system values (region values)
  g_system.min_x = region_start(1, addr)[0];
  g_system.min_y = region_start(1, addr)[1];
  g_system.max_x = region_start(1, addr)[2];
  g_system.max_y = region_start(1, addr)[3];

  io_printf(IO_BUF, "(%3d, %3d) to (%3d, %3d)\n",
            g_system.min_x, g_system.min_y,
            g_system.max_x, g_system.max_y);

  // Read in the transform and output keys
  g_system.size_out = region_start(2, addr)[0];
  MALLOC_FAIL_FALSE(transform, g_system.size_out * sizeof(value_t), "");
  MALLOC_FAIL_FALSE(keys, g_system.size_out * sizeof(uint), "");

  spin1_memcpy(transform, &region_start(2, addr)[1],
               g_system.size_out * sizeof(value_t));
  spin1_memcpy(keys, &region_start(3, addr)[1],
               g_system.size_out * sizeof(uint));

  for (uint i = 0; i < g_system.size_out; i++) {
    io_printf(IO_BUF, "[%d] = %k, Key = 0x%08x\n",
              i, transform[i], keys[i]);
  }

  return true;
}


void c_main(void) {
  address_t addr = system_load_sram();
  if (leadAp) {
    system_lead_app_configured();
  }

  // Read in the region values and the transform to apply to the output
  if (!get_data(addr))
    return;

  // Prepare callbacks and synchronise
  spin1_callback_on(MCPL_PACKET_RECEIVED, mc_receive, -1);
  spin1_callback_on(TIMER_TICK, tick, 2);
  spin1_set_timer_tick(1000);
  spin1_start(SYNC_WAIT);
}
