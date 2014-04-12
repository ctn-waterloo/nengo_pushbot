#include "tracks.h"

void c_main( void ) {
  // Set the system up
  address_t address = system_load_sram();
  data_system(region_start(1, address));
  data_get_keys(region_start(2, address));

  // Set up routing tables
  if(leadAp){
    system_lead_app_configured();
  }

  // Load core map
  system_load_core_map();

  // Setup timer tick, start
  spin1_set_timer_tick(g_tracks.machine_timestep);
  spin1_start();
}
