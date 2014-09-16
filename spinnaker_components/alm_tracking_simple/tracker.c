#include "tracker.h"

tracker_t g_tracker;

void retina_update(uint key, uint timestamp);
bool provide_debug_values();

/** Spike received, schedule callback for processing */
void mcpl_received(uint key, uint payload)
{
  // Ignore down spikes
  if ((key & 0x1000) == 0)
    return;

  spin1_schedule_callback(retina_update, key, payload, 1);
}

/** Process retina spike */
void retina_update(uint key, uint timestamp)
{
  // Extract event x and event y from the key
  uint x = (0xfc0 & key) >> 6;
  uint y = (0x03f & key);

  // Calculate the delta, store the timestamp
  int t_delta = (int)g_tracker.t_exp -
                ((int)g_tracker.last_spikes[x*Y_RESOLUTION + y] -
                 (int)timestamp);
  g_tracker.last_spikes[x*Y_RESOLUTION + y] = timestamp;

  t_delta = abs(t_delta);
  if ((uint) t_delta >= g_tracker.w_t_max)
    return;

  // Calculate x and y as accums
  value_t ex = kbits(x << X_RESOLUTION_SHIFT) - 1k;
  value_t ey = kbits(y << Y_RESOLUTION_SHIFT) - 1k;

  // Calculate the distance between the current and best position
  int p_delta_x = bitsk(g_tracker.x + 1k) >> X_RESOLUTION_SHIFT;
  int p_delta_y = bitsk(g_tracker.y + 1k) >> Y_RESOLUTION_SHIFT;
  uint p_delta = abs(p_delta_x - x) + abs(p_delta_y - y);

  // Calculate the new x and y positions
  value_t _p = g_tracker.eta * (g_tracker.w_t[t_delta] +
                                g_tracker.w_p[p_delta]);
  g_tracker.x = (1k - _p)*g_tracker.x + _p*ex;
  g_tracker.y = (1k - _p)*g_tracker.y + _p*ey;

  // Modify the confidence
  g_tracker.count++;

  if (g_tracker.w_t[t_delta] > 0.5k && g_tracker.w_p[p_delta] > 0.5k)
  {
    g_tracker.good_events++;
  }
}

/** Output current estimate */
void tick(uint ticks, uint arg1)
{
  use(ticks);
  use(arg1);

  // Calculate the confidence
  value_t confidence;
  if (g_tracker.count == 0 || g_tracker.good_events == 0)
  {
    confidence = 0k;
  }
  else
  {
    confidence = ((value_t)g_tracker.good_events) / ((value_t)g_tracker.count);
  }

#ifndef DEBUG_RETINA
  // Transmit multicast packet

  // Apply the output transform
#else
  // Output to IO_STD
  io_printf(IO_STD, "x = %.3k, y=%.3k, c=%.3k\n",
            g_tracker.x, g_tracker.y, confidence);
#endif

  g_tracker.good_events = 0;
  g_tracker.count = 0;
}

void c_main(void)
{
  // Initialise the last used times
  debug("Zeroing last spike tracker.");
  g_tracker.last_spikes = spin1_malloc(
      X_RESOLUTION*Y_RESOLUTION*sizeof(uint32_t));
  for (uint i = 0; i < X_RESOLUTION; i++) {
    for (uint j = 0; j < Y_RESOLUTION; j++) {
      g_tracker.last_spikes[i*Y_RESOLUTION + j] = 0;
    }
  }

  g_tracker.count = g_tracker.good_events = 0;

#ifndef DEBUG_RETINA
  address_t address = system_load_sram();
  if (leadAp)
  {
    system_lead_app_configured();
  }

  // Load in the position delta Gaussian
  g_tracker.w_p = spin1_malloc((X_RESOLUTION + Y_RESOLUTION)*sizeof(value_t));
  if (g_tracker.w_p == NULL)
  {
    debug("Failed to malloc space for g_tracker.w_p.");
    return;
  }
  spin1_memcpy(g_tracker.w_p, region_start(2, address),
               (X_RESOLUTION + Y_RESOLUTION)*sizeof(value_t));

  // Load in the time delta Gaussian
  system_region_t* sys_region = (system_region_t*) region_start(1, address);
  g_tracker.w_t_max = sys_region->w_t_max;
  g_tracker.w_t = spin1_malloc(sys_region->w_t_max * sizeof(value_t));
  if (g_tracker.w_t == NULL)
  {
    debug("Failed to malloc space for g_tracker.w_t.");
    return;
  }
  spin1_memcpy(g_tracker.w_t, region_start(3, address),
               sys_region->w_t_max * sizeof(value_t));

  // Set the t_exp and eta values
  g_tracker.t_exp = sys_region->t_exp;
  g_tracker.eta = sys_region->eta;

  // Initialise the callbacks for spike events and timer ticks
  debug("Setting up callbacks.");
  spin1_callback_on(MCPL_PACKET_RECEIVED, mcpl_received, -1);
  spin1_callback_on(TIMER_TICK, tick, 2);

  spin1_set_timer_tick(1000);
  spin1_start(SYNC_WAIT);
#else
  debug("Setting up dummy routes.");
  // Set up routes to/from the retina
  rtr_mc_set(1, 0x10000000, 0xfffffc00, 1 << SOUTH_WEST);
  rtr_mc_set(2, 0xfefff800, 0xfefff800, spin1_get_core_id() << 7);

  // Enable data streaming from the retina
  debug("Enabling retina data streaming.");
  spin1_send_mc_packet(0x10000000 | 1, (4 << 29) | (2 << 26), WITH_PAYLOAD);

  // Provide sample values for important settings
  debug("Providing sample data values.");
  g_tracker.eta = 0.3k;
  g_tracker.t_exp = 746;
  if (!provide_debug_values())
    return;

  // Initialise the callbacks for spike events and timer ticks
  debug("Setting up callbacks.");
  spin1_callback_on(MCPL_PACKET_RECEIVED, mcpl_received, -1);
  spin1_callback_on(TIMER_TICK, tick, 2);

  // Start
  spin1_set_timer_tick(1000);
  spin1_start(SYNC_NOWAIT);
#endif
}

bool provide_debug_values()
{
  // ***YUCK!***
  MALLOC_FAIL_FALSE(g_tracker.w_p,
                    (X_RESOLUTION+Y_RESOLUTION)*sizeof(uint32_t),
                    "");
  g_tracker.w_p[  0] = kbits(0x00008000);
  g_tracker.w_p[  1] = kbits(0x00007fed);
  g_tracker.w_p[  2] = kbits(0x00007fb7);
  g_tracker.w_p[  3] = kbits(0x00007f5c);
  g_tracker.w_p[  4] = kbits(0x00007ede);
  g_tracker.w_p[  5] = kbits(0x00007e3c);
  g_tracker.w_p[  6] = kbits(0x00007d77);
  g_tracker.w_p[  7] = kbits(0x00007c90);
  g_tracker.w_p[  8] = kbits(0x00007b87);
  g_tracker.w_p[  9] = kbits(0x00007a5e);
  g_tracker.w_p[ 10] = kbits(0x00007915);
  g_tracker.w_p[ 11] = kbits(0x000077ad);
  g_tracker.w_p[ 12] = kbits(0x00007628);
  g_tracker.w_p[ 13] = kbits(0x00007487);
  g_tracker.w_p[ 14] = kbits(0x000072cb);
  g_tracker.w_p[ 15] = kbits(0x000070f5);
  g_tracker.w_p[ 16] = kbits(0x00006f07);
  g_tracker.w_p[ 17] = kbits(0x00006d03);
  g_tracker.w_p[ 18] = kbits(0x00006aea);
  g_tracker.w_p[ 19] = kbits(0x000068bd);
  g_tracker.w_p[ 20] = kbits(0x0000667e);
  g_tracker.w_p[ 21] = kbits(0x0000642f);
  g_tracker.w_p[ 22] = kbits(0x000061d2);
  g_tracker.w_p[ 23] = kbits(0x00005f67);
  g_tracker.w_p[ 24] = kbits(0x00005cf2);
  g_tracker.w_p[ 25] = kbits(0x00005a73);
  g_tracker.w_p[ 26] = kbits(0x000057ec);
  g_tracker.w_p[ 27] = kbits(0x0000555f);
  g_tracker.w_p[ 28] = kbits(0x000052cd);
  g_tracker.w_p[ 29] = kbits(0x00005039);
  g_tracker.w_p[ 30] = kbits(0x00004da2);
  g_tracker.w_p[ 31] = kbits(0x00004b0c);
  g_tracker.w_p[ 32] = kbits(0x00004877);
  g_tracker.w_p[ 33] = kbits(0x000045e5);
  g_tracker.w_p[ 34] = kbits(0x00004357);
  g_tracker.w_p[ 35] = kbits(0x000040cf);
  g_tracker.w_p[ 36] = kbits(0x00003e4d);
  g_tracker.w_p[ 37] = kbits(0x00003bd3);
  g_tracker.w_p[ 38] = kbits(0x00003962);
  g_tracker.w_p[ 39] = kbits(0x000036fb);
  g_tracker.w_p[ 40] = kbits(0x0000349f);
  g_tracker.w_p[ 41] = kbits(0x0000324e);
  g_tracker.w_p[ 42] = kbits(0x0000300a);
  g_tracker.w_p[ 43] = kbits(0x00002dd2);
  g_tracker.w_p[ 44] = kbits(0x00002ba9);
  g_tracker.w_p[ 45] = kbits(0x0000298e);
  g_tracker.w_p[ 46] = kbits(0x00002781);
  g_tracker.w_p[ 47] = kbits(0x00002584);
  g_tracker.w_p[ 48] = kbits(0x00002396);
  g_tracker.w_p[ 49] = kbits(0x000021b8);
  g_tracker.w_p[ 50] = kbits(0x00001fea);
  g_tracker.w_p[ 51] = kbits(0x00001e2c);
  g_tracker.w_p[ 52] = kbits(0x00001c7f);
  g_tracker.w_p[ 53] = kbits(0x00001ae1);
  g_tracker.w_p[ 54] = kbits(0x00001954);
  g_tracker.w_p[ 55] = kbits(0x000017d7);
  g_tracker.w_p[ 56] = kbits(0x0000166a);
  g_tracker.w_p[ 57] = kbits(0x0000150d);
  g_tracker.w_p[ 58] = kbits(0x000013bf);
  g_tracker.w_p[ 59] = kbits(0x00001281);
  g_tracker.w_p[ 60] = kbits(0x00001152);
  g_tracker.w_p[ 61] = kbits(0x00001032);
  g_tracker.w_p[ 62] = kbits(0x00000f20);
  g_tracker.w_p[ 63] = kbits(0x00000e1c);
  g_tracker.w_p[ 64] = kbits(0x00000d26);
  g_tracker.w_p[ 65] = kbits(0x00000c3d);
  g_tracker.w_p[ 66] = kbits(0x00000b61);
  g_tracker.w_p[ 67] = kbits(0x00000a92);
  g_tracker.w_p[ 68] = kbits(0x000009ce);
  g_tracker.w_p[ 69] = kbits(0x00000916);
  g_tracker.w_p[ 70] = kbits(0x00000869);
  g_tracker.w_p[ 71] = kbits(0x000007c7);
  g_tracker.w_p[ 72] = kbits(0x0000072f);
  g_tracker.w_p[ 73] = kbits(0x000006a1);
  g_tracker.w_p[ 74] = kbits(0x0000061b);
  g_tracker.w_p[ 75] = kbits(0x0000059f);
  g_tracker.w_p[ 76] = kbits(0x0000052b);
  g_tracker.w_p[ 77] = kbits(0x000004bf);
  g_tracker.w_p[ 78] = kbits(0x0000045b);
  g_tracker.w_p[ 79] = kbits(0x000003fe);
  g_tracker.w_p[ 80] = kbits(0x000003a8);
  g_tracker.w_p[ 81] = kbits(0x00000357);
  g_tracker.w_p[ 82] = kbits(0x0000030d);
  g_tracker.w_p[ 83] = kbits(0x000002c9);
  g_tracker.w_p[ 84] = kbits(0x0000028a);
  g_tracker.w_p[ 85] = kbits(0x0000024f);
  g_tracker.w_p[ 86] = kbits(0x0000021a);
  g_tracker.w_p[ 87] = kbits(0x000001e8);
  g_tracker.w_p[ 88] = kbits(0x000001bb);
  g_tracker.w_p[ 89] = kbits(0x00000192);
  g_tracker.w_p[ 90] = kbits(0x0000016c);
  g_tracker.w_p[ 91] = kbits(0x00000149);
  g_tracker.w_p[ 92] = kbits(0x00000129);
  g_tracker.w_p[ 93] = kbits(0x0000010c);
  g_tracker.w_p[ 94] = kbits(0x000000f1);
  g_tracker.w_p[ 95] = kbits(0x000000d9);
  g_tracker.w_p[ 96] = kbits(0x000000c3);
  g_tracker.w_p[ 97] = kbits(0x000000af);
  g_tracker.w_p[ 98] = kbits(0x0000009d);
  g_tracker.w_p[ 99] = kbits(0x0000008d);
  g_tracker.w_p[100] = kbits(0x0000007e);
  g_tracker.w_p[101] = kbits(0x00000071);
  g_tracker.w_p[102] = kbits(0x00000065);
  g_tracker.w_p[103] = kbits(0x0000005a);
  g_tracker.w_p[104] = kbits(0x00000050);
  g_tracker.w_p[105] = kbits(0x00000047);
  g_tracker.w_p[106] = kbits(0x0000003f);
  g_tracker.w_p[107] = kbits(0x00000038);
  g_tracker.w_p[108] = kbits(0x00000032);
  g_tracker.w_p[109] = kbits(0x0000002c);
  g_tracker.w_p[110] = kbits(0x00000027);
  g_tracker.w_p[111] = kbits(0x00000022);
  g_tracker.w_p[112] = kbits(0x0000001e);
  g_tracker.w_p[113] = kbits(0x0000001b);
  g_tracker.w_p[114] = kbits(0x00000017);
  g_tracker.w_p[115] = kbits(0x00000015);
  g_tracker.w_p[116] = kbits(0x00000012);
  g_tracker.w_p[117] = kbits(0x00000010);
  g_tracker.w_p[118] = kbits(0x0000000e);
  g_tracker.w_p[119] = kbits(0x0000000c);
  g_tracker.w_p[120] = kbits(0x0000000a);
  g_tracker.w_p[121] = kbits(0x00000009);
  g_tracker.w_p[122] = kbits(0x00000008);
  g_tracker.w_p[123] = kbits(0x00000007);
  g_tracker.w_p[124] = kbits(0x00000006);
  g_tracker.w_p[125] = kbits(0x00000005);
  g_tracker.w_p[126] = kbits(0x00000004);
  g_tracker.w_p[127] = kbits(0x00000004);

  // Time based Gaussian
  MALLOC_FAIL_FALSE(g_tracker.w_t, sizeof(value_t) * 457, "");
  g_tracker.w_t_max = 457;
  g_tracker.w_t[   0] = kbits(0x00008000);
  g_tracker.w_t[   1] = kbits(0x00007ffe);
  g_tracker.w_t[   2] = kbits(0x00007ff9);
  g_tracker.w_t[   3] = kbits(0x00007ff1);
  g_tracker.w_t[   4] = kbits(0x00007fe5);
  g_tracker.w_t[   5] = kbits(0x00007fd7);
  g_tracker.w_t[   6] = kbits(0x00007fc5);
  g_tracker.w_t[   7] = kbits(0x00007faf);
  g_tracker.w_t[   8] = kbits(0x00007f97);
  g_tracker.w_t[   9] = kbits(0x00007f7b);
  g_tracker.w_t[  10] = kbits(0x00007f5c);
  g_tracker.w_t[  11] = kbits(0x00007f3a);
  g_tracker.w_t[  12] = kbits(0x00007f14);
  g_tracker.w_t[  13] = kbits(0x00007eec);
  g_tracker.w_t[  14] = kbits(0x00007ec0);
  g_tracker.w_t[  15] = kbits(0x00007e91);
  g_tracker.w_t[  16] = kbits(0x00007e5f);
  g_tracker.w_t[  17] = kbits(0x00007e29);
  g_tracker.w_t[  18] = kbits(0x00007df1);
  g_tracker.w_t[  19] = kbits(0x00007db5);
  g_tracker.w_t[  20] = kbits(0x00007d77);
  g_tracker.w_t[  21] = kbits(0x00007d35);
  g_tracker.w_t[  22] = kbits(0x00007cf0);
  g_tracker.w_t[  23] = kbits(0x00007ca8);
  g_tracker.w_t[  24] = kbits(0x00007c5d);
  g_tracker.w_t[  25] = kbits(0x00007c0f);
  g_tracker.w_t[  26] = kbits(0x00007bbe);
  g_tracker.w_t[  27] = kbits(0x00007b6b);
  g_tracker.w_t[  28] = kbits(0x00007b14);
  g_tracker.w_t[  29] = kbits(0x00007aba);
  g_tracker.w_t[  30] = kbits(0x00007a5e);
  g_tracker.w_t[  31] = kbits(0x000079fe);
  g_tracker.w_t[  32] = kbits(0x0000799c);
  g_tracker.w_t[  33] = kbits(0x00007937);
  g_tracker.w_t[  34] = kbits(0x000078cf);
  g_tracker.w_t[  35] = kbits(0x00007865);
  g_tracker.w_t[  36] = kbits(0x000077f7);
  g_tracker.w_t[  37] = kbits(0x00007788);
  g_tracker.w_t[  38] = kbits(0x00007715);
  g_tracker.w_t[  39] = kbits(0x000076a0);
  g_tracker.w_t[  40] = kbits(0x00007628);
  g_tracker.w_t[  41] = kbits(0x000075ae);
  g_tracker.w_t[  42] = kbits(0x00007531);
  g_tracker.w_t[  43] = kbits(0x000074b2);
  g_tracker.w_t[  44] = kbits(0x00007430);
  g_tracker.w_t[  45] = kbits(0x000073ac);
  g_tracker.w_t[  46] = kbits(0x00007326);
  g_tracker.w_t[  47] = kbits(0x0000729d);
  g_tracker.w_t[  48] = kbits(0x00007212);
  g_tracker.w_t[  49] = kbits(0x00007185);
  g_tracker.w_t[  50] = kbits(0x000070f5);
  g_tracker.w_t[  51] = kbits(0x00007063);
  g_tracker.w_t[  52] = kbits(0x00006fd0);
  g_tracker.w_t[  53] = kbits(0x00006f3a);
  g_tracker.w_t[  54] = kbits(0x00006ea2);
  g_tracker.w_t[  55] = kbits(0x00006e08);
  g_tracker.w_t[  56] = kbits(0x00006d6c);
  g_tracker.w_t[  57] = kbits(0x00006cce);
  g_tracker.w_t[  58] = kbits(0x00006c2f);
  g_tracker.w_t[  59] = kbits(0x00006b8d);
  g_tracker.w_t[  60] = kbits(0x00006aea);
  g_tracker.w_t[  61] = kbits(0x00006a45);
  g_tracker.w_t[  62] = kbits(0x0000699e);
  g_tracker.w_t[  63] = kbits(0x000068f5);
  g_tracker.w_t[  64] = kbits(0x0000684b);
  g_tracker.w_t[  65] = kbits(0x000067a0);
  g_tracker.w_t[  66] = kbits(0x000066f2);
  g_tracker.w_t[  67] = kbits(0x00006644);
  g_tracker.w_t[  68] = kbits(0x00006594);
  g_tracker.w_t[  69] = kbits(0x000064e2);
  g_tracker.w_t[  70] = kbits(0x0000642f);
  g_tracker.w_t[  71] = kbits(0x0000637b);
  g_tracker.w_t[  72] = kbits(0x000062c6);
  g_tracker.w_t[  73] = kbits(0x0000620f);
  g_tracker.w_t[  74] = kbits(0x00006157);
  g_tracker.w_t[  75] = kbits(0x0000609e);
  g_tracker.w_t[  76] = kbits(0x00005fe4);
  g_tracker.w_t[  77] = kbits(0x00005f29);
  g_tracker.w_t[  78] = kbits(0x00005e6d);
  g_tracker.w_t[  79] = kbits(0x00005db0);
  g_tracker.w_t[  80] = kbits(0x00005cf2);
  g_tracker.w_t[  81] = kbits(0x00005c33);
  g_tracker.w_t[  82] = kbits(0x00005b74);
  g_tracker.w_t[  83] = kbits(0x00005ab3);
  g_tracker.w_t[  84] = kbits(0x000059f2);
  g_tracker.w_t[  85] = kbits(0x00005930);
  g_tracker.w_t[  86] = kbits(0x0000586e);
  g_tracker.w_t[  87] = kbits(0x000057ab);
  g_tracker.w_t[  88] = kbits(0x000056e8);
  g_tracker.w_t[  89] = kbits(0x00005623);
  g_tracker.w_t[  90] = kbits(0x0000555f);
  g_tracker.w_t[  91] = kbits(0x0000549a);
  g_tracker.w_t[  92] = kbits(0x000053d5);
  g_tracker.w_t[  93] = kbits(0x0000530f);
  g_tracker.w_t[  94] = kbits(0x00005249);
  g_tracker.w_t[  95] = kbits(0x00005183);
  g_tracker.w_t[  96] = kbits(0x000050bd);
  g_tracker.w_t[  97] = kbits(0x00004ff6);
  g_tracker.w_t[  98] = kbits(0x00004f30);
  g_tracker.w_t[  99] = kbits(0x00004e69);
  g_tracker.w_t[ 100] = kbits(0x00004da2);
  g_tracker.w_t[ 101] = kbits(0x00004cdc);
  g_tracker.w_t[ 102] = kbits(0x00004c15);
  g_tracker.w_t[ 103] = kbits(0x00004b4e);
  g_tracker.w_t[ 104] = kbits(0x00004a88);
  g_tracker.w_t[ 105] = kbits(0x000049c1);
  g_tracker.w_t[ 106] = kbits(0x000048fb);
  g_tracker.w_t[ 107] = kbits(0x00004835);
  g_tracker.w_t[ 108] = kbits(0x00004770);
  g_tracker.w_t[ 109] = kbits(0x000046aa);
  g_tracker.w_t[ 110] = kbits(0x000045e5);
  g_tracker.w_t[ 111] = kbits(0x00004521);
  g_tracker.w_t[ 112] = kbits(0x0000445c);
  g_tracker.w_t[ 113] = kbits(0x00004399);
  g_tracker.w_t[ 114] = kbits(0x000042d5);
  g_tracker.w_t[ 115] = kbits(0x00004213);
  g_tracker.w_t[ 116] = kbits(0x00004150);
  g_tracker.w_t[ 117] = kbits(0x0000408f);
  g_tracker.w_t[ 118] = kbits(0x00003fce);
  g_tracker.w_t[ 119] = kbits(0x00003f0d);
  g_tracker.w_t[ 120] = kbits(0x00003e4d);
  g_tracker.w_t[ 121] = kbits(0x00003d8e);
  g_tracker.w_t[ 122] = kbits(0x00003cd0);
  g_tracker.w_t[ 123] = kbits(0x00003c12);
  g_tracker.w_t[ 124] = kbits(0x00003b56);
  g_tracker.w_t[ 125] = kbits(0x00003a9a);
  g_tracker.w_t[ 126] = kbits(0x000039df);
  g_tracker.w_t[ 127] = kbits(0x00003924);
  g_tracker.w_t[ 128] = kbits(0x0000386b);
  g_tracker.w_t[ 129] = kbits(0x000037b3);
  g_tracker.w_t[ 130] = kbits(0x000036fb);
  g_tracker.w_t[ 131] = kbits(0x00003645);
  g_tracker.w_t[ 132] = kbits(0x0000358f);
  g_tracker.w_t[ 133] = kbits(0x000034db);
  g_tracker.w_t[ 134] = kbits(0x00003427);
  g_tracker.w_t[ 135] = kbits(0x00003375);
  g_tracker.w_t[ 136] = kbits(0x000032c4);
  g_tracker.w_t[ 137] = kbits(0x00003213);
  g_tracker.w_t[ 138] = kbits(0x00003164);
  g_tracker.w_t[ 139] = kbits(0x000030b6);
  g_tracker.w_t[ 140] = kbits(0x0000300a);
  g_tracker.w_t[ 141] = kbits(0x00002f5e);
  g_tracker.w_t[ 142] = kbits(0x00002eb4);
  g_tracker.w_t[ 143] = kbits(0x00002e0b);
  g_tracker.w_t[ 144] = kbits(0x00002d63);
  g_tracker.w_t[ 145] = kbits(0x00002cbc);
  g_tracker.w_t[ 146] = kbits(0x00002c17);
  g_tracker.w_t[ 147] = kbits(0x00002b72);
  g_tracker.w_t[ 148] = kbits(0x00002ad0);
  g_tracker.w_t[ 149] = kbits(0x00002a2e);
  g_tracker.w_t[ 150] = kbits(0x0000298e);
  g_tracker.w_t[ 151] = kbits(0x000028ef);
  g_tracker.w_t[ 152] = kbits(0x00002851);
  g_tracker.w_t[ 153] = kbits(0x000027b5);
  g_tracker.w_t[ 154] = kbits(0x0000271a);
  g_tracker.w_t[ 155] = kbits(0x00002681);
  g_tracker.w_t[ 156] = kbits(0x000025e9);
  g_tracker.w_t[ 157] = kbits(0x00002552);
  g_tracker.w_t[ 158] = kbits(0x000024bd);
  g_tracker.w_t[ 159] = kbits(0x00002429);
  g_tracker.w_t[ 160] = kbits(0x00002396);
  g_tracker.w_t[ 161] = kbits(0x00002305);
  g_tracker.w_t[ 162] = kbits(0x00002276);
  g_tracker.w_t[ 163] = kbits(0x000021e7);
  g_tracker.w_t[ 164] = kbits(0x0000215b);
  g_tracker.w_t[ 165] = kbits(0x000020cf);
  g_tracker.w_t[ 166] = kbits(0x00002045);
  g_tracker.w_t[ 167] = kbits(0x00001fbd);
  g_tracker.w_t[ 168] = kbits(0x00001f36);
  g_tracker.w_t[ 169] = kbits(0x00001eb0);
  g_tracker.w_t[ 170] = kbits(0x00001e2c);
  g_tracker.w_t[ 171] = kbits(0x00001daa);
  g_tracker.w_t[ 172] = kbits(0x00001d29);
  g_tracker.w_t[ 173] = kbits(0x00001ca9);
  g_tracker.w_t[ 174] = kbits(0x00001c2b);
  g_tracker.w_t[ 175] = kbits(0x00001bae);
  g_tracker.w_t[ 176] = kbits(0x00001b33);
  g_tracker.w_t[ 177] = kbits(0x00001ab9);
  g_tracker.w_t[ 178] = kbits(0x00001a41);
  g_tracker.w_t[ 179] = kbits(0x000019ca);
  g_tracker.w_t[ 180] = kbits(0x00001954);
  g_tracker.w_t[ 181] = kbits(0x000018e0);
  g_tracker.w_t[ 182] = kbits(0x0000186e);
  g_tracker.w_t[ 183] = kbits(0x000017fd);
  g_tracker.w_t[ 184] = kbits(0x0000178d);
  g_tracker.w_t[ 185] = kbits(0x0000171f);
  g_tracker.w_t[ 186] = kbits(0x000016b2);
  g_tracker.w_t[ 187] = kbits(0x00001647);
  g_tracker.w_t[ 188] = kbits(0x000015dd);
  g_tracker.w_t[ 189] = kbits(0x00001574);
  g_tracker.w_t[ 190] = kbits(0x0000150d);
  g_tracker.w_t[ 191] = kbits(0x000014a7);
  g_tracker.w_t[ 192] = kbits(0x00001443);
  g_tracker.w_t[ 193] = kbits(0x000013e0);
  g_tracker.w_t[ 194] = kbits(0x0000137f);
  g_tracker.w_t[ 195] = kbits(0x0000131e);
  g_tracker.w_t[ 196] = kbits(0x000012c0);
  g_tracker.w_t[ 197] = kbits(0x00001262);
  g_tracker.w_t[ 198] = kbits(0x00001206);
  g_tracker.w_t[ 199] = kbits(0x000011ac);
  g_tracker.w_t[ 200] = kbits(0x00001152);
  g_tracker.w_t[ 201] = kbits(0x000010fa);
  g_tracker.w_t[ 202] = kbits(0x000010a3);
  g_tracker.w_t[ 203] = kbits(0x0000104e);
  g_tracker.w_t[ 204] = kbits(0x00000ffa);
  g_tracker.w_t[ 205] = kbits(0x00000fa7);
  g_tracker.w_t[ 206] = kbits(0x00000f56);
  g_tracker.w_t[ 207] = kbits(0x00000f05);
  g_tracker.w_t[ 208] = kbits(0x00000eb6);
  g_tracker.w_t[ 209] = kbits(0x00000e69);
  g_tracker.w_t[ 210] = kbits(0x00000e1c);
  g_tracker.w_t[ 211] = kbits(0x00000dd1);
  g_tracker.w_t[ 212] = kbits(0x00000d87);
  g_tracker.w_t[ 213] = kbits(0x00000d3e);
  g_tracker.w_t[ 214] = kbits(0x00000cf6);
  g_tracker.w_t[ 215] = kbits(0x00000cb0);
  g_tracker.w_t[ 216] = kbits(0x00000c6b);
  g_tracker.w_t[ 217] = kbits(0x00000c27);
  g_tracker.w_t[ 218] = kbits(0x00000be4);
  g_tracker.w_t[ 219] = kbits(0x00000ba2);
  g_tracker.w_t[ 220] = kbits(0x00000b61);
  g_tracker.w_t[ 221] = kbits(0x00000b22);
  g_tracker.w_t[ 222] = kbits(0x00000ae3);
  g_tracker.w_t[ 223] = kbits(0x00000aa6);
  g_tracker.w_t[ 224] = kbits(0x00000a6a);
  g_tracker.w_t[ 225] = kbits(0x00000a2f);
  g_tracker.w_t[ 226] = kbits(0x000009f4);
  g_tracker.w_t[ 227] = kbits(0x000009bb);
  g_tracker.w_t[ 228] = kbits(0x00000983);
  g_tracker.w_t[ 229] = kbits(0x0000094c);
  g_tracker.w_t[ 230] = kbits(0x00000916);
  g_tracker.w_t[ 231] = kbits(0x000008e1);
  g_tracker.w_t[ 232] = kbits(0x000008ad);
  g_tracker.w_t[ 233] = kbits(0x0000087a);
  g_tracker.w_t[ 234] = kbits(0x00000848);
  g_tracker.w_t[ 235] = kbits(0x00000817);
  g_tracker.w_t[ 236] = kbits(0x000007e7);
  g_tracker.w_t[ 237] = kbits(0x000007b7);
  g_tracker.w_t[ 238] = kbits(0x00000789);
  g_tracker.w_t[ 239] = kbits(0x0000075c);
  g_tracker.w_t[ 240] = kbits(0x0000072f);
  g_tracker.w_t[ 241] = kbits(0x00000703);
  g_tracker.w_t[ 242] = kbits(0x000006d8);
  g_tracker.w_t[ 243] = kbits(0x000006ae);
  g_tracker.w_t[ 244] = kbits(0x00000685);
  g_tracker.w_t[ 245] = kbits(0x0000065d);
  g_tracker.w_t[ 246] = kbits(0x00000635);
  g_tracker.w_t[ 247] = kbits(0x0000060f);
  g_tracker.w_t[ 248] = kbits(0x000005e9);
  g_tracker.w_t[ 249] = kbits(0x000005c4);
  g_tracker.w_t[ 250] = kbits(0x0000059f);
  g_tracker.w_t[ 251] = kbits(0x0000057c);
  g_tracker.w_t[ 252] = kbits(0x00000559);
  g_tracker.w_t[ 253] = kbits(0x00000537);
  g_tracker.w_t[ 254] = kbits(0x00000515);
  g_tracker.w_t[ 255] = kbits(0x000004f4);
  g_tracker.w_t[ 256] = kbits(0x000004d4);
  g_tracker.w_t[ 257] = kbits(0x000004b5);
  g_tracker.w_t[ 258] = kbits(0x00000496);
  g_tracker.w_t[ 259] = kbits(0x00000478);
  g_tracker.w_t[ 260] = kbits(0x0000045b);
  g_tracker.w_t[ 261] = kbits(0x0000043e);
  g_tracker.w_t[ 262] = kbits(0x00000422);
  g_tracker.w_t[ 263] = kbits(0x00000407);
  g_tracker.w_t[ 264] = kbits(0x000003ec);
  g_tracker.w_t[ 265] = kbits(0x000003d2);
  g_tracker.w_t[ 266] = kbits(0x000003b8);
  g_tracker.w_t[ 267] = kbits(0x0000039f);
  g_tracker.w_t[ 268] = kbits(0x00000387);
  g_tracker.w_t[ 269] = kbits(0x0000036f);
  g_tracker.w_t[ 270] = kbits(0x00000357);
  g_tracker.w_t[ 271] = kbits(0x00000341);
  g_tracker.w_t[ 272] = kbits(0x0000032a);
  g_tracker.w_t[ 273] = kbits(0x00000314);
  g_tracker.w_t[ 274] = kbits(0x000002ff);
  g_tracker.w_t[ 275] = kbits(0x000002ea);
  g_tracker.w_t[ 276] = kbits(0x000002d6);
  g_tracker.w_t[ 277] = kbits(0x000002c2);
  g_tracker.w_t[ 278] = kbits(0x000002af);
  g_tracker.w_t[ 279] = kbits(0x0000029c);
  g_tracker.w_t[ 280] = kbits(0x0000028a);
  g_tracker.w_t[ 281] = kbits(0x00000278);
  g_tracker.w_t[ 282] = kbits(0x00000266);
  g_tracker.w_t[ 283] = kbits(0x00000255);
  g_tracker.w_t[ 284] = kbits(0x00000244);
  g_tracker.w_t[ 285] = kbits(0x00000234);
  g_tracker.w_t[ 286] = kbits(0x00000224);
  g_tracker.w_t[ 287] = kbits(0x00000215);
  g_tracker.w_t[ 288] = kbits(0x00000206);
  g_tracker.w_t[ 289] = kbits(0x000001f7);
  g_tracker.w_t[ 290] = kbits(0x000001e8);
  g_tracker.w_t[ 291] = kbits(0x000001da);
  g_tracker.w_t[ 292] = kbits(0x000001cd);
  g_tracker.w_t[ 293] = kbits(0x000001bf);
  g_tracker.w_t[ 294] = kbits(0x000001b3);
  g_tracker.w_t[ 295] = kbits(0x000001a6);
  g_tracker.w_t[ 296] = kbits(0x0000019a);
  g_tracker.w_t[ 297] = kbits(0x0000018e);
  g_tracker.w_t[ 298] = kbits(0x00000182);
  g_tracker.w_t[ 299] = kbits(0x00000177);
  g_tracker.w_t[ 300] = kbits(0x0000016c);
  g_tracker.w_t[ 301] = kbits(0x00000161);
  g_tracker.w_t[ 302] = kbits(0x00000156);
  g_tracker.w_t[ 303] = kbits(0x0000014c);
  g_tracker.w_t[ 304] = kbits(0x00000142);
  g_tracker.w_t[ 305] = kbits(0x00000138);
  g_tracker.w_t[ 306] = kbits(0x0000012f);
  g_tracker.w_t[ 307] = kbits(0x00000126);
  g_tracker.w_t[ 308] = kbits(0x0000011d);
  g_tracker.w_t[ 309] = kbits(0x00000114);
  g_tracker.w_t[ 310] = kbits(0x0000010c);
  g_tracker.w_t[ 311] = kbits(0x00000104);
  g_tracker.w_t[ 312] = kbits(0x000000fc);
  g_tracker.w_t[ 313] = kbits(0x000000f4);
  g_tracker.w_t[ 314] = kbits(0x000000ec);
  g_tracker.w_t[ 315] = kbits(0x000000e5);
  g_tracker.w_t[ 316] = kbits(0x000000de);
  g_tracker.w_t[ 317] = kbits(0x000000d7);
  g_tracker.w_t[ 318] = kbits(0x000000d0);
  g_tracker.w_t[ 319] = kbits(0x000000ca);
  g_tracker.w_t[ 320] = kbits(0x000000c3);
  g_tracker.w_t[ 321] = kbits(0x000000bd);
  g_tracker.w_t[ 322] = kbits(0x000000b7);
  g_tracker.w_t[ 323] = kbits(0x000000b1);
  g_tracker.w_t[ 324] = kbits(0x000000ac);
  g_tracker.w_t[ 325] = kbits(0x000000a6);
  g_tracker.w_t[ 326] = kbits(0x000000a1);
  g_tracker.w_t[ 327] = kbits(0x0000009c);
  g_tracker.w_t[ 328] = kbits(0x00000097);
  g_tracker.w_t[ 329] = kbits(0x00000092);
  g_tracker.w_t[ 330] = kbits(0x0000008d);
  g_tracker.w_t[ 331] = kbits(0x00000088);
  g_tracker.w_t[ 332] = kbits(0x00000084);
  g_tracker.w_t[ 333] = kbits(0x00000080);
  g_tracker.w_t[ 334] = kbits(0x0000007b);
  g_tracker.w_t[ 335] = kbits(0x00000077);
  g_tracker.w_t[ 336] = kbits(0x00000073);
  g_tracker.w_t[ 337] = kbits(0x00000070);
  g_tracker.w_t[ 338] = kbits(0x0000006c);
  g_tracker.w_t[ 339] = kbits(0x00000068);
  g_tracker.w_t[ 340] = kbits(0x00000065);
  g_tracker.w_t[ 341] = kbits(0x00000061);
  g_tracker.w_t[ 342] = kbits(0x0000005e);
  g_tracker.w_t[ 343] = kbits(0x0000005b);
  g_tracker.w_t[ 344] = kbits(0x00000058);
  g_tracker.w_t[ 345] = kbits(0x00000055);
  g_tracker.w_t[ 346] = kbits(0x00000052);
  g_tracker.w_t[ 347] = kbits(0x0000004f);
  g_tracker.w_t[ 348] = kbits(0x0000004c);
  g_tracker.w_t[ 349] = kbits(0x0000004a);
  g_tracker.w_t[ 350] = kbits(0x00000047);
  g_tracker.w_t[ 351] = kbits(0x00000045);
  g_tracker.w_t[ 352] = kbits(0x00000042);
  g_tracker.w_t[ 353] = kbits(0x00000040);
  g_tracker.w_t[ 354] = kbits(0x0000003e);
  g_tracker.w_t[ 355] = kbits(0x0000003c);
  g_tracker.w_t[ 356] = kbits(0x00000039);
  g_tracker.w_t[ 357] = kbits(0x00000037);
  g_tracker.w_t[ 358] = kbits(0x00000036);
  g_tracker.w_t[ 359] = kbits(0x00000034);
  g_tracker.w_t[ 360] = kbits(0x00000032);
  g_tracker.w_t[ 361] = kbits(0x00000030);
  g_tracker.w_t[ 362] = kbits(0x0000002e);
  g_tracker.w_t[ 363] = kbits(0x0000002d);
  g_tracker.w_t[ 364] = kbits(0x0000002b);
  g_tracker.w_t[ 365] = kbits(0x00000029);
  g_tracker.w_t[ 366] = kbits(0x00000028);
  g_tracker.w_t[ 367] = kbits(0x00000026);
  g_tracker.w_t[ 368] = kbits(0x00000025);
  g_tracker.w_t[ 369] = kbits(0x00000024);
  g_tracker.w_t[ 370] = kbits(0x00000022);
  g_tracker.w_t[ 371] = kbits(0x00000021);
  g_tracker.w_t[ 372] = kbits(0x00000020);
  g_tracker.w_t[ 373] = kbits(0x0000001f);
  g_tracker.w_t[ 374] = kbits(0x0000001e);
  g_tracker.w_t[ 375] = kbits(0x0000001c);
  g_tracker.w_t[ 376] = kbits(0x0000001b);
  g_tracker.w_t[ 377] = kbits(0x0000001a);
  g_tracker.w_t[ 378] = kbits(0x00000019);
  g_tracker.w_t[ 379] = kbits(0x00000018);
  g_tracker.w_t[ 380] = kbits(0x00000017);
  g_tracker.w_t[ 381] = kbits(0x00000017);
  g_tracker.w_t[ 382] = kbits(0x00000016);
  g_tracker.w_t[ 383] = kbits(0x00000015);
  g_tracker.w_t[ 384] = kbits(0x00000014);
  g_tracker.w_t[ 385] = kbits(0x00000013);
  g_tracker.w_t[ 386] = kbits(0x00000013);
  g_tracker.w_t[ 387] = kbits(0x00000012);
  g_tracker.w_t[ 388] = kbits(0x00000011);
  g_tracker.w_t[ 389] = kbits(0x00000010);
  g_tracker.w_t[ 390] = kbits(0x00000010);
  g_tracker.w_t[ 391] = kbits(0x0000000f);
  g_tracker.w_t[ 392] = kbits(0x0000000f);
  g_tracker.w_t[ 393] = kbits(0x0000000e);
  g_tracker.w_t[ 394] = kbits(0x0000000d);
  g_tracker.w_t[ 395] = kbits(0x0000000d);
  g_tracker.w_t[ 396] = kbits(0x0000000c);
  g_tracker.w_t[ 397] = kbits(0x0000000c);
  g_tracker.w_t[ 398] = kbits(0x0000000b);
  g_tracker.w_t[ 399] = kbits(0x0000000b);
  g_tracker.w_t[ 400] = kbits(0x0000000a);
  g_tracker.w_t[ 401] = kbits(0x0000000a);
  g_tracker.w_t[ 402] = kbits(0x0000000a);
  g_tracker.w_t[ 403] = kbits(0x00000009);
  g_tracker.w_t[ 404] = kbits(0x00000009);
  g_tracker.w_t[ 405] = kbits(0x00000008);
  g_tracker.w_t[ 406] = kbits(0x00000008);
  g_tracker.w_t[ 407] = kbits(0x00000008);
  g_tracker.w_t[ 408] = kbits(0x00000007);
  g_tracker.w_t[ 409] = kbits(0x00000007);
  g_tracker.w_t[ 410] = kbits(0x00000007);
  g_tracker.w_t[ 411] = kbits(0x00000007);
  g_tracker.w_t[ 412] = kbits(0x00000006);
  g_tracker.w_t[ 413] = kbits(0x00000006);
  g_tracker.w_t[ 414] = kbits(0x00000006);
  g_tracker.w_t[ 415] = kbits(0x00000005);
  g_tracker.w_t[ 416] = kbits(0x00000005);
  g_tracker.w_t[ 417] = kbits(0x00000005);
  g_tracker.w_t[ 418] = kbits(0x00000005);
  g_tracker.w_t[ 419] = kbits(0x00000005);
  g_tracker.w_t[ 420] = kbits(0x00000004);
  g_tracker.w_t[ 421] = kbits(0x00000004);
  g_tracker.w_t[ 422] = kbits(0x00000004);
  g_tracker.w_t[ 423] = kbits(0x00000004);
  g_tracker.w_t[ 424] = kbits(0x00000004);
  g_tracker.w_t[ 425] = kbits(0x00000003);
  g_tracker.w_t[ 426] = kbits(0x00000003);
  g_tracker.w_t[ 427] = kbits(0x00000003);
  g_tracker.w_t[ 428] = kbits(0x00000003);
  g_tracker.w_t[ 429] = kbits(0x00000003);
  g_tracker.w_t[ 430] = kbits(0x00000003);
  g_tracker.w_t[ 431] = kbits(0x00000003);
  g_tracker.w_t[ 432] = kbits(0x00000002);
  g_tracker.w_t[ 433] = kbits(0x00000002);
  g_tracker.w_t[ 434] = kbits(0x00000002);
  g_tracker.w_t[ 435] = kbits(0x00000002);
  g_tracker.w_t[ 436] = kbits(0x00000002);
  g_tracker.w_t[ 437] = kbits(0x00000002);
  g_tracker.w_t[ 438] = kbits(0x00000002);
  g_tracker.w_t[ 439] = kbits(0x00000002);
  g_tracker.w_t[ 440] = kbits(0x00000002);
  g_tracker.w_t[ 441] = kbits(0x00000001);
  g_tracker.w_t[ 442] = kbits(0x00000001);
  g_tracker.w_t[ 443] = kbits(0x00000001);
  g_tracker.w_t[ 444] = kbits(0x00000001);
  g_tracker.w_t[ 445] = kbits(0x00000001);
  g_tracker.w_t[ 446] = kbits(0x00000001);
  g_tracker.w_t[ 447] = kbits(0x00000001);
  g_tracker.w_t[ 448] = kbits(0x00000001);
  g_tracker.w_t[ 449] = kbits(0x00000001);
  g_tracker.w_t[ 450] = kbits(0x00000001);
  g_tracker.w_t[ 451] = kbits(0x00000001);
  g_tracker.w_t[ 452] = kbits(0x00000001);
  g_tracker.w_t[ 453] = kbits(0x00000001);
  g_tracker.w_t[ 454] = kbits(0x00000001);
  g_tracker.w_t[ 455] = kbits(0x00000001);
  g_tracker.w_t[ 456] = kbits(0x00000001);

  return true;
}
