/* 
 *
 *	mantissa.c Copyright (C) Aaron Holtzman - May 1999
 *
 *
 *  This file is part of libmpeg2
 *	
 *  libmpeg2 is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2, or (at your option)
 *  any later version.
 *   
 *  libmpeg2 is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *   
 *  You should have received a copy of the GNU General Public License
 *  along with GNU Make; see the file COPYING.  If not, write to
 *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA. 
 *
 */

#include "mpeg2audio.h"
#include "streams/bitstream.h"

/* Lookup tables of 0.16 two's complement quantization values */
static short mpeg2_q_1[3] = 
{
	(-2 << 15) / 3, 
	0, 
	(2 << 15) / 3
};

static short mpeg2_q_2[5] = 
{
	(-4 << 15) / 5, 
	((-2 << 15) / 5) << 1, 
	0,
	(2 << 15) / 5, 
	short(((4 << 15) / 5) << 1)
};

static short mpeg2_q_3[7] = 
{
	(-6 << 15) / 7, 
	(-4 << 15) / 7, 
	(-2 << 15) / 7,
	0, 
	(2 << 15) / 7, 
	(4 << 15) / 7,
	(6 << 15) / 7
};

static short mpeg2_q_4[11] = 
{
	(-10 << 15) / 11, 
	(-8 << 15) / 11, 
	(-6 << 15) / 11,
	(-4 << 15) / 11, 
	(-2 << 15) / 11, 
	0,
	( 2 << 15) / 11, 
	( 4 << 15) / 11, 
	( 6 << 15) / 11,
	( 8 << 15) / 11, 
	(10 << 15) / 11
};

static short mpeg2_q_5[15] = 
{
	(-14 << 15) / 15, 
	(-12 << 15) / 15, 
	(-10 << 15) / 15,
    (-8 << 15) / 15, 
	(-6 << 15) / 15, 
	(-4 << 15) / 15,
	(-2 << 15) / 15, 			
	0, 
	( 2 << 15) / 15,
	( 4 << 15) / 15, 
	( 6 << 15) / 15, 
	( 8 << 15) / 15,
	(10 << 15) / 15, 
	(12 << 15) / 15, 
	(14 << 15) / 15
};

static short mpeg2_qnttztab[16] = {0, 0, 0, 3, 0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16};


/* */
/* Scale factors for tofloat */
/* */

static const unsigned MPEG2_INT32 mpeg2_scale_factors[25] = 
{
	0x38000000, /*2 ^ -(0 + 15) */
	0x37800000, /*2 ^ -(1 + 15) */
	0x37000000, /*2 ^ -(2 + 15) */
	0x36800000, /*2 ^ -(3 + 15) */
	0x36000000, /*2 ^ -(4 + 15) */
	0x35800000, /*2 ^ -(5 + 15) */
	0x35000000, /*2 ^ -(6 + 15) */
	0x34800000, /*2 ^ -(7 + 15) */
	0x34000000, /*2 ^ -(8 + 15) */
	0x33800000, /*2 ^ -(9 + 15) */
	0x33000000, /*2 ^ -(10 + 15) */
	0x32800000, /*2 ^ -(11 + 15) */
	0x32000000, /*2 ^ -(12 + 15) */
	0x31800000, /*2 ^ -(13 + 15) */
	0x31000000, /*2 ^ -(14 + 15) */
	0x30800000, /*2 ^ -(15 + 15) */
	0x30000000, /*2 ^ -(16 + 15) */
	0x2f800000, /*2 ^ -(17 + 15) */
	0x2f000000, /*2 ^ -(18 + 15) */
	0x2e800000, /*2 ^ -(19 + 15) */
	0x2e000000, /*2 ^ -(20 + 15) */
	0x2d800000, /*2 ^ -(21 + 15) */
	0x2d000000, /*2 ^ -(22 + 15) */
	0x2c800000, /*2 ^ -(23 + 15) */
	0x2c000000  /*2 ^ -(24 + 15) */
};

static MPEG2_FLOAT32 *mpeg2_scale_factor = (MPEG2_FLOAT32*)mpeg2_scale_factors;

static inline float mpeg2audio_ac3_tofloat(unsigned short exponent, int mantissa)
{
	float x;
	x = mantissa * mpeg2_scale_factor[exponent];
	return x;
}

static inline void mpeg2audio_ac3_mantissa_reset(mpeg2_ac3_mantissa_t *mantissa)
{
	mantissa->m_1[2] = mantissa->m_1[1] = mantissa->m_1[0] = 0;
	mantissa->m_2[2] = mantissa->m_2[1] = mantissa->m_2[0] = 0;
	mantissa->m_4[1] = mantissa->m_4[0] = 0;
/* Force new groups to be loaded */
	mantissa->m_1_pointer = mantissa->m_2_pointer = mantissa->m_4_pointer = 3;
}

/* 
 * Generate eight bits of pseudo-entropy using a 16 bit linear
 * feedback shift register (LFSR). The primitive polynomial used
 * is 1 + x^4 + x^14 + x^16.
 *
 * The distribution is uniform, over the range [-0.707,0.707]
 *
 */
inline unsigned int mpeg2audio_ac3_dither_gen(mpeg2audio_t *audio)
{
	int i;
	unsigned int state;

/* explicitly bring the state into a local var as gcc > 3.0? */
/* doesn't know how to optimize out the stores */
	state = audio->ac3_lfsr_state;

/* Generate eight pseudo random bits */
	for(i = 0; i < 8; i++)
	{
		state <<= 1;	

		if(state & 0x10000)
			state ^= 0xa011;
	}

	audio->ac3_lfsr_state = state;
	return (((((int)state << 8) >> 8) * (int)(0.707106f * 256.0f)) >> 16);
}


/* Fetch an unpacked, left justified, and properly biased/dithered mantissa value */
static inline unsigned short mpeg2audio_ac3_mantissa_get(mpeg2audio_t *audio, 
	unsigned short bap, 
	unsigned short dithflag)
{
	unsigned short mantissa;
	unsigned int group_code = 0;
	mpeg2_ac3_mantissa_t *mantissa_struct = &(audio->ac3_mantissa);

/* If the bap is 0-5 then we have special cases to take care of */
	switch(bap)
	{
		case 0:
			if(dithflag)
				mantissa = mpeg2audio_ac3_dither_gen(audio);
			else
				mantissa = 0;
			break;

		case 1:
			if(mantissa_struct->m_1_pointer > 2)
			{
				group_code = mpeg2bits_getbits(audio->astream, 5);

				if(group_code > 26)
				{
/* FIXME do proper block error handling */
					_tprintf(TEXT("mpeg2audio_ac3_mantissa_get: Invalid mantissa 1 %d\n"), group_code);
					return 0;
				}

				mantissa_struct->m_1[0] = group_code / 9; 
				mantissa_struct->m_1[1] = (group_code % 9) / 3; 
				mantissa_struct->m_1[2] = (group_code % 9) % 3; 
				mantissa_struct->m_1_pointer = 0;
			}
			mantissa = mantissa_struct->m_1[mantissa_struct->m_1_pointer++];
			mantissa = mpeg2_q_1[mantissa];
			break;

		case 2:
			if(mantissa_struct->m_2_pointer > 2)
			{
				group_code = mpeg2bits_getbits(audio->astream, 7);

				if(group_code > 124)
				{
					_tprintf(TEXT("mpeg2audio_ac3_mantissa_get: Invalid mantissa 2 %d\n"), group_code);
					return 0;
				}

				mantissa_struct->m_2[0] = group_code / 25;
				mantissa_struct->m_2[1] = (group_code % 25) / 5;
				mantissa_struct->m_2[2] = (group_code % 25) % 5; 
				mantissa_struct->m_2_pointer = 0;
			}
			mantissa = mantissa_struct->m_2[mantissa_struct->m_2_pointer++];
			mantissa = mpeg2_q_2[mantissa];
			break;

		case 3:
			mantissa = mpeg2bits_getbits(audio->astream, 3);

			if(mantissa > 6)
			{
				_tprintf(TEXT("2audio_ac3_mantissa_get: Invalid mantissa 3 %d\n"), group_code);
				return 0;
			}

			mantissa = mpeg2_q_3[mantissa];
			break;

		case 4:
			if(mantissa_struct->m_4_pointer > 1)
			{
				group_code = mpeg2bits_getbits(audio->astream, 7);

				if(group_code > 120)
				{
					_tprintf(TEXT("mpeg2audio_ac3_mantissa_get: Invalid mantissa 4 %d\n"), group_code);
					return 0;
				}

				mantissa_struct->m_4[0] = group_code / 11;
				mantissa_struct->m_4[1] = group_code % 11;
				mantissa_struct->m_4_pointer = 0;
			}
			mantissa = mantissa_struct->m_4[mantissa_struct->m_4_pointer++];
			mantissa = mpeg2_q_4[mantissa];
			break;

		case 5:
			mantissa = mpeg2bits_getbits(audio->astream, 4);

			if(mantissa > 14)
			{
			/* FIXME do proper block error handling */
				_tprintf(TEXT("mpeg2audio_ac3_mantissa_get: Invalid mantissa 5 %d\n"), group_code);
				return 0;
			}

			mantissa = mpeg2_q_5[mantissa];
			break;

		default:
			mantissa = mpeg2bits_getbits(audio->astream, mpeg2_qnttztab[bap]);
			mantissa <<= 16 - mpeg2_qnttztab[bap];
	}
	return mantissa;
}

void mpeg2audio_ac3_uncouple_channel(mpeg2audio_t *audio,
		float samples[],
		mpeg2_ac3bsi_t *bsi, 
		mpeg2_ac3audblk_t *audblk, 
		unsigned int ch)
{
	unsigned int bnd = 0;
	unsigned int sub_bnd = 0;
	unsigned int j;
	MPEG2_FLOAT32 cpl_coord = 1.0;
	unsigned int cpl_exp_tmp;
	unsigned int cpl_mant_tmp;
	short mantissa;

	for(int i = audblk->cplstrtmant; i < audblk->cplendmant; )
	{
		if(!audblk->cplbndstrc[sub_bnd++])
		{
			cpl_exp_tmp = audblk->cplcoexp[ch][bnd] + 3 * audblk->mstrcplco[ch];
			if(audblk->cplcoexp[ch][bnd] == 15)
				cpl_mant_tmp = (audblk->cplcomant[ch][bnd]) << 11;
			else
				cpl_mant_tmp = ((0x10) | audblk->cplcomant[ch][bnd]) << 10;

			cpl_coord = mpeg2audio_ac3_tofloat(cpl_exp_tmp, cpl_mant_tmp) * 8.0f;

/*Invert the phase for the right channel if necessary */
			if(bsi->acmod == 0x2 && audblk->phsflginu && ch == 1 && audblk->phsflg[bnd])
				cpl_coord *= -1;

			bnd++;
		}

		for(j = 0; j < 12; j++)
		{
/* Get new dither values for each channel if necessary, so */
/* the channels are uncorrelated */
			if(audblk->dithflag[ch] && audblk->cpl_bap[i] == 0)
				mantissa = mpeg2audio_ac3_dither_gen(audio);
			else
				mantissa = audblk->cplmant[i];

			samples[i] = cpl_coord * mpeg2audio_ac3_tofloat(audblk->cpl_exp[i], mantissa);;

			i++;
		}
	}
	return;
}

int mpeg2audio_ac3_coeff_unpack(mpeg2audio_t *audio, 
	mpeg2_ac3bsi_t *bsi, 
	mpeg2_ac3audblk_t *audblk,
	mpeg2ac3_stream_samples_t samples)
{
	int i, j;
	int done_cpl = 0;
	short mantissa;

	mpeg2audio_ac3_mantissa_reset(&(audio->ac3_mantissa));

	for(i = 0; i < bsi->nfchans && !mpeg2bits_error(audio->astream); i++)
	{
		for(j = 0; j < audblk->endmant[i] && !mpeg2bits_error(audio->astream); j++)
		{
			mantissa = mpeg2audio_ac3_mantissa_get(audio, audblk->fbw_bap[i][j], audblk->dithflag[i]);
			samples[i][j] = mpeg2audio_ac3_tofloat(audblk->fbw_exp[i][j], mantissa);
		}

		if(audblk->cplinu && audblk->chincpl[i] && !(done_cpl) && !mpeg2bits_error(audio->astream))
		{
/* ncplmant is equal to 12 * ncplsubnd */
/* Don't dither coupling channel until channel separation so that
 * interchannel noise is uncorrelated */
			for(j = audblk->cplstrtmant; 
				j < audblk->cplendmant && !mpeg2bits_error(audio->astream); 
				j++)
			{
				audblk->cplmant[j] = mpeg2audio_ac3_mantissa_get(audio, audblk->cpl_bap[j], 0);
			}
			done_cpl = 1;
		}
	}

/* Uncouple the channel */
	if(audblk->cplinu)
	{
		if(audblk->chincpl[i])
			mpeg2audio_ac3_uncouple_channel(audio, samples[i], bsi, audblk, i);
	}

	if(bsi->lfeon && !mpeg2bits_error(audio->astream))
	{
/* There are always 7 mantissas for lfe, no dither for lfe */
		for(j = 0; j < 7 && !mpeg2bits_error(audio->astream); j++)
			mantissa = mpeg2audio_ac3_mantissa_get(audio, audblk->lfe_bap[j], 0);
			samples[5][j] = mpeg2audio_ac3_tofloat(audblk->lfe_exp[j], mantissa);
	}

	return mpeg2bits_error(audio->astream);
}
