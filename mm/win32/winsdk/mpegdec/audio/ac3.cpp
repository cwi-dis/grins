/* 
 *
 *	ac3.c Copyright (C) Aaron Holtzman - May 1999
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
#include <math.h>
#include <stdlib.h>
#include <string.h>


#include "mpeg2audio.h"
#include "streams/mpeg2demux.h"
#include "streams/bitstream.h"

#include "ac3.h"

#define MPEG2AC3_MAGIC_NUMBER 0xdeadbeef


int mpeg2_ac3_samplerates[] = { 48000, 44100, 32000 };

struct mpeg2_framesize_s
{
	unsigned short bit_rate;
	unsigned short frm_size[3];
};

struct mpeg2_framesize_s framesize_codes[] = 
{
      { 32  ,{64   ,69   ,96   } },
      { 32  ,{64   ,70   ,96   } },
      { 40  ,{80   ,87   ,120  } },
      { 40  ,{80   ,88   ,120  } },
      { 48  ,{96   ,104  ,144  } },
      { 48  ,{96   ,105  ,144  } },
      { 56  ,{112  ,121  ,168  } },
      { 56  ,{112  ,122  ,168  } },
      { 64  ,{128  ,139  ,192  } },
      { 64  ,{128  ,140  ,192  } },
      { 80  ,{160  ,174  ,240  } },
      { 80  ,{160  ,175  ,240  } },
      { 96  ,{192  ,208  ,288  } },
      { 96  ,{192  ,209  ,288  } },
      { 112 ,{224  ,243  ,336  } },
      { 112 ,{224  ,244  ,336  } },
      { 128 ,{256  ,278  ,384  } },
      { 128 ,{256  ,279  ,384  } },
      { 160 ,{320  ,348  ,480  } },
      { 160 ,{320  ,349  ,480  } },
      { 192 ,{384  ,417  ,576  } },
      { 192 ,{384  ,418  ,576  } },
      { 224 ,{448  ,487  ,672  } },
      { 224 ,{448  ,488  ,672  } },
      { 256 ,{512  ,557  ,768  } },
      { 256 ,{512  ,558  ,768  } },
      { 320 ,{640  ,696  ,960  } },
      { 320 ,{640  ,697  ,960  } },
      { 384 ,{768  ,835  ,1152 } },
      { 384 ,{768  ,836  ,1152 } },
      { 448 ,{896  ,975  ,1344 } },
      { 448 ,{896  ,976  ,1344 } },
      { 512 ,{1024 ,1114 ,1536 } },
      { 512 ,{1024 ,1115 ,1536 } },
      { 576 ,{1152 ,1253 ,1728 } },
      { 576 ,{1152 ,1254 ,1728 } },
      { 640 ,{1280 ,1393 ,1920 } },
      { 640 ,{1280 ,1394 ,1920 } }
};

/* Audio channel modes */
short mpeg2_ac3_acmodes[] = {2, 1, 2, 3, 3, 4, 4, 5};

/* Rematrix tables */
struct rematrix_band_s
{
	int start;
	int end;
};

struct rematrix_band_s mpeg2_rematrix_band[] = 
{ 
	{13, 24}, 
	{25, 36}, 
	{37, 60}, 
	{61, 252}
};

inline int mpeg2_min(int x, int y)
{
	return (x < y) ? x : y;
}

inline int mpeg2_max(int x, int y)
{
	return (x > y) ? x : y;
}

int mpeg2audio_read_ac3_header(mpeg2audio_t *audio)
{
	unsigned int code, crc;
	mpeg2_ac3bsi_t *bsi = &(audio->ac3_bsi);

/* Get the sync code */
	code = mpeg2bits_getbits(audio->astream, 16);
	while(!mpeg2bits_eof(audio->astream) && code != MPEG2_AC3_START_CODE)
	{
		code <<= 8;
		code &= 0xffff;
		code |= mpeg2bits_getbits(audio->astream, 8);
	}

	if(mpeg2bits_eof(audio->astream)) return 1;

/* Get crc1 - we don't actually use this data though */
/* The crc can be the same as the sync code or come after a sync code repeated twice */
	crc = mpeg2bits_getbits(audio->astream, 16);

/* Got the sync code.  Read the entire frame into a buffer if possible. */
	if(audio->avg_framesize > 0)
	{
		if(mpeg2bits_read_buffer(audio->astream, audio->ac3_buffer, audio->framesize - 4))
			return 1;
		mpeg2bits_use_ptr(audio->astream, audio->ac3_buffer);	
	}

/* Get the sampling rate code */
	audio->sampling_frequency_code  = mpeg2bits_getbits(audio->astream, 2);

/* Get the frame size code */
	audio->ac3_framesize_code = mpeg2bits_getbits(audio->astream, 6);

	audio->bitrate = framesize_codes[audio->ac3_framesize_code].bit_rate;
	audio->framesize = 2 * framesize_codes[audio->ac3_framesize_code].frm_size[audio->sampling_frequency_code];
	audio->avg_framesize = (float)audio->framesize;

/* Check the AC-3 version number */
	bsi->bsid = mpeg2bits_getbits(audio->astream, 5);

/* Get the audio service provided by the steram */
	bsi->bsmod = mpeg2bits_getbits(audio->astream, 3);

/* Get the audio coding mode (ie how many channels)*/
	bsi->acmod = mpeg2bits_getbits(audio->astream, 3);
	
/* Predecode the number of full bandwidth channels as we use this
 * number a lot */
	bsi->nfchans = mpeg2_ac3_acmodes[bsi->acmod];
	audio->channels = bsi->nfchans;

/* If it is in use, get the centre channel mix level */
	if((bsi->acmod & 0x1) && (bsi->acmod != 0x1))
		bsi->cmixlev = mpeg2bits_getbits(audio->astream, 2);

/* If it is in use, get the surround channel mix level */
	if(bsi->acmod & 0x4)
		bsi->surmixlev = mpeg2bits_getbits(audio->astream, 2);

/* Get the dolby surround mode if in 2/0 mode */
	if(bsi->acmod == 0x2)
		bsi->dsurmod= mpeg2bits_getbits(audio->astream, 2);

/* Is the low frequency effects channel on? */
	bsi->lfeon = mpeg2bits_getbits(audio->astream, 1);

/* Get the dialogue normalization level */
	bsi->dialnorm = mpeg2bits_getbits(audio->astream, 5);

/* Does compression gain exist? */
	bsi->compre = mpeg2bits_getbits(audio->astream, 1);
	if (bsi->compre)
	{
/* Get compression gain */
		bsi->compr = mpeg2bits_getbits(audio->astream, 8);
	}

/* Does language code exist? */
	bsi->langcode = mpeg2bits_getbits(audio->astream, 1);
	if (bsi->langcode)
	{
/* Get langauge code */
		bsi->langcod = mpeg2bits_getbits(audio->astream, 8);
	}

/* Does audio production info exist? */
	bsi->audprodie = mpeg2bits_getbits(audio->astream, 1);
	if (bsi->audprodie)
	{
/* Get mix level */
		bsi->mixlevel = mpeg2bits_getbits(audio->astream, 5);

/* Get room type */
		bsi->roomtyp = mpeg2bits_getbits(audio->astream, 2);
	}

/* If we're in dual mono mode then get some extra info */
	if (bsi->acmod == 0)
	{
/* Get the dialogue normalization level two */
		bsi->dialnorm2 = mpeg2bits_getbits(audio->astream, 5);

/* Does compression gain two exist? */
		bsi->compr2e = mpeg2bits_getbits(audio->astream, 1);
		if (bsi->compr2e)
		{
/* Get compression gain two */
			bsi->compr2 = mpeg2bits_getbits(audio->astream, 8);
		}

/* Does language code two exist? */
		bsi->langcod2e = mpeg2bits_getbits(audio->astream, 1);
		if (bsi->langcod2e)
		{
/* Get langauge code two */
			bsi->langcod2 = mpeg2bits_getbits(audio->astream, 8);
		}

/* Does audio production info two exist? */
		bsi->audprodi2e = mpeg2bits_getbits(audio->astream, 1);
		if (bsi->audprodi2e)
		{
/* Get mix level two */
			bsi->mixlevel2 = mpeg2bits_getbits(audio->astream, 5);

/* Get room type two */
			bsi->roomtyp2 = mpeg2bits_getbits(audio->astream, 2);
		}
	}

/* Get the copyright bit */
	bsi->copyrightb = mpeg2bits_getbits(audio->astream, 1);

/* Get the original bit */
	bsi->origbs = mpeg2bits_getbits(audio->astream, 1);
	
/* Does timecode one exist? */
	bsi->timecod1e = mpeg2bits_getbits(audio->astream, 1);

	if(bsi->timecod1e)
		bsi->timecod1 = mpeg2bits_getbits(audio->astream, 14);

/* Does timecode two exist? */
	bsi->timecod2e = mpeg2bits_getbits(audio->astream, 1);

	if(bsi->timecod2e)
		bsi->timecod2 = mpeg2bits_getbits(audio->astream, 14);

/* Does addition info exist? */
	bsi->addbsie = mpeg2bits_getbits(audio->astream, 1);

	if(bsi->addbsie)
	{
/* Get how much info is there */
		bsi->addbsil = mpeg2bits_getbits(audio->astream, 6);

/* Get the additional info */
		for(int i = 0; i < (bsi->addbsil + 1); i++)
			bsi->addbsi[i] = mpeg2bits_getbits(audio->astream, 8);
	}

	if(mpeg2bits_eof(audio->astream))
	{
		mpeg2bits_use_demuxer(audio->astream);
		return 1;
	}
//	return mpeg2bits_error(audio->astream);
	return 0;
}

int mpeg2audio_read_ac3_audblk(mpeg2audio_t *audio)
{
	int i, j;
	mpeg2_ac3bsi_t *bsi = &(audio->ac3_bsi);
	mpeg2_ac3audblk_t *audblk = &(audio->ac3_audblk);

	for(i = 0; i < bsi->nfchans; i++)
	{
/* Is this channel an interleaved 256 + 256 block ? */
		audblk->blksw[i] = mpeg2bits_getbits(audio->astream, 1);
	}

	for(i = 0; i < bsi->nfchans; i++)
	{
/* Should we dither this channel? */
		audblk->dithflag[i] = mpeg2bits_getbits(audio->astream, 1);
	}

/* Does dynamic range control exist? */
	audblk->dynrnge = mpeg2bits_getbits(audio->astream, 1);
	if(audblk->dynrnge)
	{
/* Get dynamic range info */
		audblk->dynrng = mpeg2bits_getbits(audio->astream, 8);
	}

/* If we're in dual mono mode then get the second channel DR info */
	if(bsi->acmod == 0)
	{
/* Does dynamic range control two exist? */
		audblk->dynrng2e = mpeg2bits_getbits(audio->astream, 1);
		if (audblk->dynrng2e)
		{
/* Get dynamic range info */
			audblk->dynrng2 = mpeg2bits_getbits(audio->astream, 8);
		}
	}

/* Does coupling strategy exist? */
	audblk->cplstre = mpeg2bits_getbits(audio->astream, 1);
	if(audblk->cplstre)
	{
/* Is coupling turned on? */
		audblk->cplinu = mpeg2bits_getbits(audio->astream, 1);
		if(audblk->cplinu)
		{
			for(i = 0; i < bsi->nfchans; i++)
				audblk->chincpl[i] = mpeg2bits_getbits(audio->astream, 1);

			if(bsi->acmod == 0x2)
				audblk->phsflginu = mpeg2bits_getbits(audio->astream, 1);

 			audblk->cplbegf = mpeg2bits_getbits(audio->astream, 4);
 			audblk->cplendf = mpeg2bits_getbits(audio->astream, 4);
			audblk->ncplsubnd = (audblk->cplendf + 2) - audblk->cplbegf + 1;

/* Calculate the start and end bins of the coupling channel */
			audblk->cplstrtmant = (audblk->cplbegf * 12) + 37 ; 
			audblk->cplendmant =  ((audblk->cplendf + 3) * 12) + 37;

/* The number of combined subbands is ncplsubnd minus each combined band */
			audblk->ncplbnd = audblk->ncplsubnd; 

			for(i = 1; i < audblk->ncplsubnd; i++)
			{
				audblk->cplbndstrc[i] = mpeg2bits_getbits(audio->astream, 1);
				audblk->ncplbnd -= audblk->cplbndstrc[i];
			}
		}
	}

	if(audblk->cplinu)
	{
/* Loop through all the channels and get their coupling co-ords */	
		for(i = 0; i < bsi->nfchans; i++)
		{
			if(!audblk->chincpl[i])
				continue;

/* Is there new coupling co-ordinate info? */
			audblk->cplcoe[i] = mpeg2bits_getbits(audio->astream, 1);

			if(audblk->cplcoe[i])
			{
				audblk->mstrcplco[i] = mpeg2bits_getbits(audio->astream, 2); 
				for(j = 0; j < audblk->ncplbnd; j++)
				{
					audblk->cplcoexp[i][j] = mpeg2bits_getbits(audio->astream, 4); 
					audblk->cplcomant[i][j] = mpeg2bits_getbits(audio->astream, 4); 
				}
			}
		}

/* If we're in dual mono mode, there's going to be some phase info */
		if((bsi->acmod == 0x2) && audblk->phsflginu && 
			(audblk->cplcoe[0] || audblk->cplcoe[1]))
		{
			for(j = 0; j < audblk->ncplbnd; j++)
			{
				audblk->phsflg[j] = mpeg2bits_getbits(audio->astream, 1);
			}
		}
	}

/* If we're in dual mono mode, there may be a rematrix strategy */
	if(bsi->acmod == 0x2)
	{
		audblk->rematstr = mpeg2bits_getbits(audio->astream, 1);
		if(audblk->rematstr)
		{
			if (audblk->cplinu == 0) 
			{ 
				for(i = 0; i < 4; i++) 
					audblk->rematflg[i] = mpeg2bits_getbits(audio->astream, 1);
			}
			if((audblk->cplbegf > 2) && audblk->cplinu) 
			{
				for(i = 0; i < 4; i++) 
					audblk->rematflg[i] = mpeg2bits_getbits(audio->astream, 1);
			}
			if((audblk->cplbegf <= 2) && audblk->cplinu) 
			{ 
				for(i = 0; i < 3; i++) 
					audblk->rematflg[i] = mpeg2bits_getbits(audio->astream, 1);
			} 
			if((audblk->cplbegf == 0) && audblk->cplinu) 
				for(i = 0; i < 2; i++) 
					audblk->rematflg[i] = mpeg2bits_getbits(audio->astream, 1);

		}
	}

	if (audblk->cplinu)
	{
/* Get the coupling channel exponent strategy */
		audblk->cplexpstr = mpeg2bits_getbits(audio->astream, 2);

		if(audblk->cplexpstr == 0) 
			audblk->ncplgrps = 0;
		else
			audblk->ncplgrps = (audblk->cplendmant - audblk->cplstrtmant) / 
				(3 << (audblk->cplexpstr - 1));

	}

	for(i = 0; i < bsi->nfchans; i++)
	{
		audblk->chexpstr[i] = mpeg2bits_getbits(audio->astream, 2);
	}

/* Get the exponent strategy for lfe channel */
	if(bsi->lfeon) 
		audblk->lfeexpstr = mpeg2bits_getbits(audio->astream, 1);

/* Determine the bandwidths of all the fbw channels */
	for(i = 0; i < bsi->nfchans; i++)
	{ 
		unsigned short grp_size;

		if(audblk->chexpstr[i] != MPEG2_EXP_REUSE) 
		{ 
			if (audblk->cplinu && audblk->chincpl[i]) 
			{
				audblk->endmant[i] = audblk->cplstrtmant;
			}
			else
			{
				audblk->chbwcod[i] = mpeg2bits_getbits(audio->astream, 6); 
				audblk->endmant[i] = ((audblk->chbwcod[i] + 12) * 3) + 37;
			}

/* Calculate the number of exponent groups to fetch */
			grp_size =  3 * (1 << (audblk->chexpstr[i] - 1));
			audblk->nchgrps[i] = (audblk->endmant[i] - 1 + (grp_size - 3)) / grp_size;
		}
	}

/* Get the coupling exponents if they exist */
	if(audblk->cplinu && (audblk->cplexpstr != MPEG2_EXP_REUSE))
	{
		audblk->cplabsexp = mpeg2bits_getbits(audio->astream, 4);
		for(i = 0; i< audblk->ncplgrps; i++)
			audblk->cplexps[i] = mpeg2bits_getbits(audio->astream, 7);
	}

/* Get the fwb channel exponents */
	for(i = 0; i < bsi->nfchans; i++)
	{
		if(audblk->chexpstr[i] != MPEG2_EXP_REUSE)
		{
			audblk->exps[i][0] = mpeg2bits_getbits(audio->astream, 4);
			for(j = 1; j <= audblk->nchgrps[i]; j++)
				audblk->exps[i][j] = mpeg2bits_getbits(audio->astream, 7);
			audblk->gainrng[i] = mpeg2bits_getbits(audio->astream, 2);
		}
	}

/* Get the lfe channel exponents */
	if(bsi->lfeon && (audblk->lfeexpstr != MPEG2_EXP_REUSE))
	{
		audblk->lfeexps[0] = mpeg2bits_getbits(audio->astream, 4);
		audblk->lfeexps[1] = mpeg2bits_getbits(audio->astream, 7);
		audblk->lfeexps[2] = mpeg2bits_getbits(audio->astream, 7);
	}

/* Get the parametric bit allocation parameters */
	audblk->baie = mpeg2bits_getbits(audio->astream, 1);

	if(audblk->baie)
	{
		audblk->sdcycod = mpeg2bits_getbits(audio->astream, 2);
		audblk->fdcycod = mpeg2bits_getbits(audio->astream, 2);
		audblk->sgaincod = mpeg2bits_getbits(audio->astream, 2);
		audblk->dbpbcod = mpeg2bits_getbits(audio->astream, 2);
		audblk->floorcod = mpeg2bits_getbits(audio->astream, 3);
	}


/* Get the SNR off set info if it exists */
	audblk->snroffste = mpeg2bits_getbits(audio->astream, 1);

	if(audblk->snroffste)
	{
		audblk->csnroffst = mpeg2bits_getbits(audio->astream, 6);

		if(audblk->cplinu)
		{
			audblk->cplfsnroffst = mpeg2bits_getbits(audio->astream, 4);
			audblk->cplfgaincod = mpeg2bits_getbits(audio->astream, 3);
		}

		for(i = 0; i < bsi->nfchans; i++)
		{
			audblk->fsnroffst[i] = mpeg2bits_getbits(audio->astream, 4);
			audblk->fgaincod[i] = mpeg2bits_getbits(audio->astream, 3);
		}
		if(bsi->lfeon)
		{

			audblk->lfefsnroffst = mpeg2bits_getbits(audio->astream, 4);
			audblk->lfefgaincod = mpeg2bits_getbits(audio->astream, 3);
		}
	}

/* Get coupling leakage info if it exists */
	if(audblk->cplinu)
	{
		audblk->cplleake = mpeg2bits_getbits(audio->astream, 1);	
		
		if(audblk->cplleake)
		{
			audblk->cplfleak = mpeg2bits_getbits(audio->astream, 3);
			audblk->cplsleak = mpeg2bits_getbits(audio->astream, 3);
		}
	}
	
/* Get the delta bit alloaction info */
	audblk->deltbaie = mpeg2bits_getbits(audio->astream, 1);	

	if(audblk->deltbaie)
	{
		if(audblk->cplinu)
			audblk->cpldeltbae = mpeg2bits_getbits(audio->astream, 2);

		for(i = 0; i < bsi->nfchans; i++)
			audblk->deltbae[i] = mpeg2bits_getbits(audio->astream, 2);

		if (audblk->cplinu && (audblk->cpldeltbae == DELTA_BIT_NEW))
		{
			audblk->cpldeltnseg = mpeg2bits_getbits(audio->astream, 3);
			for(i = 0; i < audblk->cpldeltnseg + 1; i++)
			{
				audblk->cpldeltoffst[i] = mpeg2bits_getbits(audio->astream, 5);
				audblk->cpldeltlen[i] = mpeg2bits_getbits(audio->astream, 4);
				audblk->cpldeltba[i] = mpeg2bits_getbits(audio->astream, 3);
			}
		}

		for(i = 0; i < bsi->nfchans; i++)
		{
			if (audblk->deltbae[i] == DELTA_BIT_NEW)
			{
				audblk->deltnseg[i] = mpeg2bits_getbits(audio->astream, 3);
				for(j = 0; j < audblk->deltnseg[i] + 1; j++)
				{
					audblk->deltoffst[i][j] = mpeg2bits_getbits(audio->astream, 5);
					audblk->deltlen[i][j] = mpeg2bits_getbits(audio->astream, 4);
					audblk->deltba[i][j] = mpeg2bits_getbits(audio->astream, 3);
				}
			}
		}
	}

/* Check to see if there's any dummy info to get */
	if((audblk->skiple = mpeg2bits_getbits(audio->astream, 1)))
	{
		unsigned int skip_data;
		audblk->skipl = mpeg2bits_getbits(audio->astream, 9);
		for(i = 0; i < audblk->skipl ; i++)
		{
			skip_data = mpeg2bits_getbits(audio->astream, 8);
		}
	}

	return mpeg2bits_error(audio->astream);
}


/* This routine simply does stereo rematrixing for the 2 channel 
 * stereo mode */
int mpeg2audio_ac3_rematrix(mpeg2_ac3audblk_t *audblk, 
		mpeg2ac3_stream_samples_t samples)
{
	int num_bands;
	int start;
	int end;
	int i, j;
	float left, right;

	if(audblk->cplinu || audblk->cplbegf > 2)
		num_bands = 4;
	else if (audblk->cplbegf > 0)
		num_bands = 3;
	else
		num_bands = 2;

	for(i = 0; i < num_bands; i++)
	{
		if(!audblk->rematflg[i])
			continue;

		start = mpeg2_rematrix_band[i].start;
		end = mpeg2_min(mpeg2_rematrix_band[i].end, 12 * audblk->cplbegf + 36);
	
		for(j = start; j < end; j++)
		{
			left = samples[0][j] + samples[1][j];
			right = samples[0][j] - samples[1][j];
			samples[0][j] = left;
			samples[1][j] = right;
		}
	}
	return 0;
}


int mpeg2audio_ac3_reset_frame(mpeg2audio_t *audio)
{
	memset(&audio->ac3_bit_allocation, 0, sizeof(mpeg2_ac3_bitallocation_t));
	memset(&audio->ac3_mantissa, 0, sizeof(mpeg2_ac3_mantissa_t));
	memset(&audio->ac3_audblk, 0, sizeof(mpeg2_ac3audblk_t));

	return 0;
}

int mpeg2audio_do_ac3(mpeg2audio_t *audio)
{
	int result = 0, i;

/* Reset the coefficients and exponents */
	mpeg2audio_ac3_reset_frame(audio);

	for(i = 0; i < 6 && !result; i++)
	{
		memset(audio->ac3_samples, 0, sizeof(float) * 256 * (audio->ac3_bsi.nfchans + audio->ac3_bsi.lfeon));
/* Extract most of the audblk info from the bitstream
 * (minus the mantissas */
		result |= mpeg2audio_read_ac3_audblk(audio);

/* Take the differential exponent data and turn it into
 * absolute exponents */
		if(!result) result |= mpeg2audio_ac3_exponent_unpack(audio, 
					&(audio->ac3_bsi), 
					&(audio->ac3_audblk));

/* Figure out how many bits per mantissa */
		if(!result) result |= mpeg2audio_ac3_bit_allocate(audio, 
					audio->sampling_frequency_code, 
					&(audio->ac3_bsi), 
					&(audio->ac3_audblk));

/* Extract the mantissas from the data stream */
		if(!result) result |= mpeg2audio_ac3_coeff_unpack(audio,
					&(audio->ac3_bsi), 
					&(audio->ac3_audblk),
					audio->ac3_samples);

		if(audio->ac3_bsi.acmod == 0x2)
			if(!result) result |= mpeg2audio_ac3_rematrix(&(audio->ac3_audblk), 
					audio->ac3_samples);

/* Convert the frequency data into time samples */
		if(!result) result |= mpeg2audio_ac3_imdct(audio, 
			&(audio->ac3_bsi), 
			&(audio->ac3_audblk), 
			audio->ac3_samples);

		if(audio->pcm_point / audio->channels >= audio->pcm_allocated - MPEG2AUDIO_PADDING * audio->channels)
		{
/* Need more room */
			mpeg2audio_replace_buffer(audio, audio->pcm_allocated + MPEG2AUDIO_PADDING * audio->channels);
		}
	}

	mpeg2bits_use_demuxer(audio->astream);

	return result;
}
