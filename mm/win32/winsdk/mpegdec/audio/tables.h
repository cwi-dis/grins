#ifndef TABLES_H
#define TABLES_H

extern int mpeg2_tabsel_123[2][3][16];

extern long mpeg2_freqs[9];

struct mpeg2_bandInfoStruct 
{
	int longIdx[23];
	int longDiff[22];
	int shortIdx[14];
	int shortDiff[13];
};


extern float mpeg2_decwin[512 + 32];
extern float mpeg2_cos64[16], mpeg2_cos32[8], mpeg2_cos16[4], mpeg2_cos8[2], mpeg2_cos4[1];

extern float *mpeg2_pnts[5];

extern int mpeg2_grp_3tab[32 * 3];   /* used: 27 */
extern int mpeg2_grp_5tab[128 * 3];  /* used: 125 */
extern int mpeg2_grp_9tab[1024 * 3]; /* used: 729 */
extern float mpeg2_muls[27][64];	/* also used by layer 1 */
extern float mpeg2_gainpow2[256 + 118 + 4];
extern long mpeg2_intwinbase[257];
extern float mpeg2_ispow[8207];
extern float mpeg2_aa_ca[8], mpeg2_aa_cs[8];
extern float mpeg2_win[4][36];
extern float mpeg2_win1[4][36];
extern float mpeg2_COS1[12][6];
extern float mpeg2_COS9[9];
extern float mpeg2_COS6_1, mpeg2_COS6_2;
extern float mpeg2_tfcos36[9];
extern float mpeg2_tfcos12[3];
extern float mpeg2_cos9[3], mpeg2_cos18[3];
extern float mpeg2_tan1_1[16], mpeg2_tan2_1[16], mpeg2_tan1_2[16], mpeg2_tan2_2[16];
extern float mpeg2_pow1_1[2][16], mpeg2_pow2_1[2][16], mpeg2_pow1_2[2][16], mpeg2_pow2_2[2][16];

extern int mpeg2_longLimit[9][23];
extern int mpeg2_shortLimit[9][14];

extern struct mpeg2_bandInfoStruct mpeg2_bandInfo[9];

extern int mpeg2_mapbuf0[9][152];
extern int mpeg2_mapbuf1[9][156];
extern int mpeg2_mapbuf2[9][44];
extern int *mpeg2_map[9][3];
extern int *mpeg2_mapend[9][3];

extern unsigned int mpeg2_n_slen2[512]; /* MPEG 2.0 slen for 'normal' mode */
extern unsigned int mpeg2_i_slen2[256]; /* MPEG 2.0 slen for intensity stereo */


#ifndef MPEG2AUDIO_H
#include "mpeg2audio.h"
#endif

int mpeg2audio_new_decode_tables(mpeg2audio_t *audio);

#endif
