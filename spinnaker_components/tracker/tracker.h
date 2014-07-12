typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;

extern ushort deltas[128][128];     //!< Pixel deltas
extern ushort * gaussian_time;      //!< Gaussian for time filtering - 16b
                                    //   fract
extern ushort gaussian_space[256];  //!< Gaussian for position filtering - 16b
                                    //   fract
extern uchar gaussian_time_length;  //!< Index of the position at which the
                                    //   Gaussian for time effectively becomes
                                    //   zero

extern uchar pos_x;   //!< Current estimated x position (pixel space)
extern uchar pos_y;   //!< Current estimated y position (pixel space)
extern ushort r_adaptation; //!< Adaptation rate

extern ushort t_exp;  //!< Expected time delta


void spike_rx(uint key, uint payload);
