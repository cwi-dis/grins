/* This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * The GPL can be found at: http://www.gnu.org/copyleft/gpl.html                      *
 *                                                                                    *
 * This project is based upon the MAD MP3 decoder also released under GPL,but																				  *
 * Optimized for use on POcketPC OS.                                                                                   *
 *
 * Authors:																			  *
 *          Rob Leslie                                                            *
 **************************************************************************************/

// Exclude rarely-used stuff from Windows headers
#define WIN32_LEAN_AND_MEAN		
#include <windows.h>

#include "mp3lib.h"

# include "global.h"

# include <windows.h>
# include <commctrl.h>
# include <prsht.h>
# include <wininet.h>
# include <stdio.h>
# include <stdarg.h>
# include <string.h>
# include <math.h>
# define PCM_CHUNK		576


#include "frame.h"
#include "synth.h"
#include "resample.h"

struct Mp3libState {
Mp3libState()
:	remainder(0),
	currentpos(0),
	framepos(0),
	begin(1),
	seeking(0),
	resample_rate(0),
	resample(0),
	equalizer(0),
	clipped(0),
	attenuation(MAD_F_ONE)
	{}
struct mad_stream stream;
struct mad_frame frame;
struct mad_synth synth;
int remainder;
int currentpos;
int framepos;
int begin;
int seeking;
int resample_rate;
int resample;
int equalizer;
unsigned long  clipped;
mad_fixed_t attenuation;
};

static DWORD conf_attsensitivity = MAD_F(0x02000000) * 4;

#ifndef MS_NO_COREDLL
BOOL APIENTRY DllMain( HANDLE hModule, 
                       DWORD  ul_reason_for_call, 
                       LPVOID lpReserved
					 )
{
    switch (ul_reason_for_call)
	{
		case DLL_PROCESS_ATTACH:
		case DLL_THREAD_ATTACH:
		case DLL_THREAD_DETACH:
		case DLL_PROCESS_DETACH:
			break;
    }
    return TRUE;
}
#endif

static
mad_fixed_t const resample_table[9][9] = {
  /* 48000 */ { MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x116a3b36) /* 1.088435374 */,
		MAD_F(0x18000000) /* 1.500000000 */,
		MAD_F(0x20000000) /* 2.000000000 */,
		MAD_F(0x22d4766c) /* 2.176870748 */,
		MAD_F(0x30000000) /* 3.000000000 */,
		MAD_F(0x40000000) /* 4.000000000 */,
		MAD_F(0x45a8ecd8) /* 4.353741497 */,
		MAD_F(0x60000000) /* 6.000000000 */ },

  /* 44100 */ { MAD_F(0x0eb33333) /* 0.918750000 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x160ccccd) /* 1.378125000 */,
		MAD_F(0x1d666666) /* 1.837500000 */,
		MAD_F(0x20000000) /* 2.000000000 */,
		MAD_F(0x2c19999a) /* 2.756250000 */,
		MAD_F(0x3acccccd) /* 3.675000000 */,
		MAD_F(0x40000000) /* 4.000000000 */,
		MAD_F(0x58333333) /* 5.512500000 */ },

  /* 32000 */ { MAD_F(0x0aaaaaab) /* 0.666666667 */,
		MAD_F(0x0b9c2779) /* 0.725623583 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x15555555) /* 1.333333333 */,
		MAD_F(0x17384ef3) /* 1.451247166 */,
		MAD_F(0x20000000) /* 2.000000000 */,
		MAD_F(0x2aaaaaab) /* 2.666666667 */,
		MAD_F(0x2e709de5) /* 2.902494331 */,
		MAD_F(0x40000000) /* 4.000000000 */ },

  /* 24000 */ { MAD_F(0x08000000) /* 0.500000000 */,
		MAD_F(0x08b51d9b) /* 0.544217687 */,
		MAD_F(0x0c000000) /* 0.750000000 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x116a3b36) /* 1.088435374 */,
		MAD_F(0x18000000) /* 1.500000000 */,
		MAD_F(0x20000000) /* 2.000000000 */,
		MAD_F(0x22d4766c) /* 2.176870748 */,
		MAD_F(0x30000000) /* 3.000000000 */ },

  /* 22050 */ { MAD_F(0x0759999a) /* 0.459375000 */,
		MAD_F(0x08000000) /* 0.500000000 */,
		MAD_F(0x0b066666) /* 0.689062500 */,
		MAD_F(0x0eb33333) /* 0.918750000 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x160ccccd) /* 1.378125000 */,
		MAD_F(0x1d666666) /* 1.837500000 */,
		MAD_F(0x20000000) /* 2.000000000 */,
		MAD_F(0x2c19999a) /* 2.756250000 */ },

  /* 16000 */ { MAD_F(0x05555555) /* 0.333333333 */,
		MAD_F(0x05ce13bd) /* 0.362811791 */,
		MAD_F(0x08000000) /* 0.500000000 */,
		MAD_F(0x0aaaaaab) /* 0.666666667 */,
		MAD_F(0x0b9c2779) /* 0.725623583 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x15555555) /* 1.333333333 */,
		MAD_F(0x17384ef3) /* 1.451247166 */,
		MAD_F(0x20000000) /* 2.000000000 */ },

  /* 12000 */ { MAD_F(0x04000000) /* 0.250000000 */,
		MAD_F(0x045a8ecd) /* 0.272108844 */,
		MAD_F(0x06000000) /* 0.375000000 */,
		MAD_F(0x08000000) /* 0.500000000 */,
		MAD_F(0x08b51d9b) /* 0.544217687 */,
		MAD_F(0x0c000000) /* 0.750000000 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x116a3b36) /* 1.088435374 */,
		MAD_F(0x18000000) /* 1.500000000 */ },

  /* 11025 */ { MAD_F(0x03accccd) /* 0.229687500 */,
		MAD_F(0x04000000) /* 0.250000000 */,
		MAD_F(0x05833333) /* 0.344531250 */,
		MAD_F(0x0759999a) /* 0.459375000 */,
		MAD_F(0x08000000) /* 0.500000000 */,
		MAD_F(0x0b066666) /* 0.689062500 */,
		MAD_F(0x0eb33333) /* 0.918750000 */,
		MAD_F(0x10000000) /* 1.000000000 */,
		MAD_F(0x160ccccd) /* 1.378125000 */ },

  /*  8000 */ { MAD_F(0x02aaaaab) /* 0.166666667 */, 
		MAD_F(0x02e709de) /* 0.181405896 */, 
		MAD_F(0x04000000) /* 0.250000000 */, 
		MAD_F(0x05555555) /* 0.333333333 */, 
		MAD_F(0x05ce13bd) /* 0.362811791 */, 
		MAD_F(0x08000000) /* 0.500000000 */, 
		MAD_F(0x0aaaaaab) /* 0.666666667 */, 
		MAD_F(0x0b9c2779) /* 0.725623583 */, 
		MAD_F(0x10000000) /* 1.000000000 */ }
};

static
int rate_index(unsigned int rate)
{
  switch (rate) {
  case 48000: return 0;
  case 44100: return 1;
  case 32000: return 2;
  case 24000: return 3;
  case 22050: return 4;
  case 16000: return 5;
  case 12000: return 6;
  case 11025: return 7;
  case  8000: return 8;
  }

  return -1;
}

/*
 * NAME:	resample_init()
 * DESCRIPTION:	initialize resampling state
 */
int resample_init(struct resample_state *state,
		  unsigned int oldrate, unsigned int newrate)
{
  int oldi, newi;

  oldi = rate_index(oldrate);
  newi = rate_index(newrate);

  if (oldi == -1 || newi == -1)
    return -1;

  state->ratio = resample_table[oldi][newi];

  state->step = 0;
  state->last = 0;

  return 0;
}

/*
 * NAME:	resample_block()
 * DESCRIPTION:	algorithmically change the sampling rate of a PCM sample block
 */
unsigned int resample_block(struct resample_state *state,
			    unsigned int nsamples, mad_fixed_t const *old,
			    mad_fixed_t *newone)
{
  mad_fixed_t const *end, *begin;

  /*
   * This resampling algorithm is based on a linear interpolation, which is
   * not at all the best sounding but is relatively fast and efficient.
   *
   * A better algorithm would be one that implements a bandlimited
   * interpolation.
   */

  if (state->ratio == MAD_F_ONE) {
    memcpy(newone, old, nsamples * sizeof(mad_fixed_t));
    return nsamples;
  }

  end   = old + nsamples;
  begin = newone;

  if (state->step < 0) {
    state->step = mad_f_fracpart(-state->step);

    while (state->step < MAD_F_ONE) {
      *newone++ = state->step ?
	state->last + mad_f_mul(*old - state->last, state->step) : state->last;

      state->step += state->ratio;
      if (((state->step + 0x00000080L) & 0x0fffff00L) == 0)
	state->step = (state->step + 0x00000080L) & ~0x0fffffffL;
    }

    state->step -= MAD_F_ONE;
  }

  while (end - old > 1 + mad_f_intpart(state->step)) {
    old        += mad_f_intpart(state->step);
    state->step = mad_f_fracpart(state->step);

    *newone++ = state->step ?
      *old + mad_f_mul(old[1] - old[0], state->step) : *old;

    state->step += state->ratio;
    if (((state->step + 0x00000080L) & 0x0fffff00L) == 0)
      state->step = (state->step + 0x00000080L) & ~0x0fffffffL;
  }

  if (end - old == 1 + mad_f_intpart(state->step)) {
    state->last = end[-1];
    state->step = -state->step;
  }
  else
    state->step -= mad_f_fromint(end - old);

  return newone - begin;
}



//static
//double eq_decibels(int value)
//{
  /* 0-63, 0 == +20 dB, 31 == 0 dB, 63 == -20 dB */

//  return (value == 31) ? 0.0 : 20.0 - (20.0 / 31.5) * value;
//}

mad_fixed_t eqfactor[32];	/* equalizer settings */
//char eq[10]={31,31,31,31,31,31,31,31,31,31};
static
mad_fixed_t eq_factor(double db)
{
  if (db > 18)
    db = 18;

  return mad_f_tofixed(pow(10, db / 20));
}

static
void set_eq(int on, char data[10], int preamp)
{
  double base;
  static unsigned char const map[32] = {
    0, 1, 2, 3, 4, 5, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8,
    8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9
  };
  int i;

  /* 60, 170, 310, 600, 1k, 3k, 6k, 12k, 14k, 16k */

  base = preamp;

  for (i = 0; i < 32; ++i)
    eqfactor[i] = eq_factor(base + (double)data[map[i]]);

}

static
void attenuate_filter(struct mad_frame *frame, mad_fixed_t scalefactor)
{
  unsigned int nch, ch, ns, s, sb;

  nch = MAD_NCHANNELS(&frame->header);
  ns  = MAD_NSBSAMPLES(&frame->header);

  for (ch = 0; ch < nch; ++ch) {
    for (s = 0; s < ns; ++s) {
      for (sb = 0; sb < 32; ++sb) {
	frame->sbsample[ch][s][sb] =
	  mad_f_mul(frame->sbsample[ch][s][sb], scalefactor);
      }
    }
  }
}

static
void equalizer_filter(struct mad_frame *frame, mad_fixed_t eqfactor[32])
{
  unsigned int nch, ch, ns, s, sb;

  nch = MAD_NCHANNELS(&frame->header);
  ns  = MAD_NSBSAMPLES(&frame->header);

  for (ch = 0; ch < nch; ++ch) {
    for (s = 0; s < ns; ++s) {
      for (sb = 0; sb < 32; ++sb) {
	frame->sbsample[ch][s][sb] =
	  mad_f_mul(frame->sbsample[ch][s][sb], eqfactor[sb]);
      }
    }
  }
}

/*
static __inline
signed long linear_dither(unsigned int bits, mad_fixed_t sample,
			  mad_fixed_t *error)
{
  mad_fixed_t quantized, check;

  sample += *error;

  quantized = sample;
  check = (sample >> MAD_F_FRACBITS) + 1;
  if (check & ~1) {
    if (sample >= MAD_F_ONE) {
      quantized = MAD_F_ONE - 1;
    }
    else if (sample < -MAD_F_ONE) {
      quantized = -MAD_F_ONE;
    }
  }

  quantized &= ~((1L << (MAD_F_FRACBITS + 1 - bits)) - 1);

  *error = sample - quantized;

  return quantized >> (MAD_F_FRACBITS + 1 - bits);
}
*/
static inline
signed long linear_dither(unsigned int bits, mad_fixed_t sample,
			  mad_fixed_t *error, unsigned long *clipped,
			  mad_fixed_t *clipping)
{
  mad_fixed_t quantized, check;

  /* dither */
  sample += *error;

  /* clip */
  quantized = sample;
  check = (sample >> MAD_F_FRACBITS) + 1;
  if (check & ~1) {
    if (sample >= MAD_F_ONE) {
      quantized = MAD_F_ONE - 1;
      ++*clipped;
      if (sample - quantized > *clipping &&
	  mad_f_abs(*error) < (MAD_F_ONE >> (MAD_F_FRACBITS + 1 - bits)))
	*clipping = sample - quantized;
    }
    else if (sample < -MAD_F_ONE) {
      quantized = -MAD_F_ONE;
      ++*clipped;
      if (quantized - sample > *clipping &&
	  mad_f_abs(*error) < (MAD_F_ONE >> (MAD_F_FRACBITS + 1 - bits)))
	*clipping = quantized - sample;
    }
  }

  /* quantize */
  quantized &= ~((1L << (MAD_F_FRACBITS + 1 - bits)) - 1);

  /* error */
  *error = sample - quantized;

  /* scale */
  return quantized >> (MAD_F_FRACBITS + 1 - bits);
}

static
unsigned int pack_pcm(unsigned char *data, unsigned int nsamples,
		      mad_fixed_t const *left, mad_fixed_t const *right,
		      int resolution, unsigned long *clipped,
			  mad_fixed_t *clipping)
{
  static mad_fixed_t left_err, right_err;
  unsigned char const *start;
  register signed long sample0, sample1;
  //int effective;
  //int bytes;

  start     = data;
//  effective = resolution;//(resolution > 24) ? 24 : resolution;
//  bytes     = resolution >>3;

  if (right) {  /* stereo */
    while (nsamples--) {
      sample0 = linear_dither(16, *left++, &left_err, clipped,clipping);
      sample1 = linear_dither(16, *right++, &right_err, clipped,clipping);

	data[0] = sample0 >>  0;
	data[1] = sample0 >>  8;
	data[2] = sample1 >>  0;
	data[3] = sample1 >>  8;

      data += 4; //bytes << 1;
    }
  }
  else {  /* mono */
    while (nsamples--)
	{
      sample0 = linear_dither(16, *left++, &left_err, clipped,clipping);

		data[1] = sample0 >>  8;
		data[0] = sample0 >>  0;
		data += 2;
    }
  }

  return data - start;
}

MP3LIB_API void mp3_lib_create_instance(void **pp)
	{
	if(pp != NULL && *pp == NULL)
		*pp = new Mp3libState();
	}

MP3LIB_API void mp3_lib_release_instance(void *vps)
	{
	Mp3libState *ps = (Mp3libState*) vps;
	delete ps;
	}

// This is an example of an exported function.
MP3LIB_API void mp3_lib_init(void *vps, int Equalizer,char* eq)
{
	//MessageBox(GetActiveWindow(),_T("In"),_T(""),MB_OK);
	Mp3libState *ps = (Mp3libState*) vps;
	if (ps->begin)
	{
	  mad_stream_init(&ps->stream);
	  mad_frame_init(&ps->frame);
	  mad_synth_init(&ps->synth);
	  ps->currentpos=0;
	  ps->framepos=0;
	  ps->begin=1;
	  ps->seeking=1;
	}
	ps->equalizer=Equalizer;
	ps->clipped=0;
	ps->attenuation=MAD_F_ONE;
	if (eq)
	{
		set_eq(1,eq,eq[10]);
	}

}
// This is an example of an exported function.
MP3LIB_API void mp3_lib_finalize(void *vps)
{
  Mp3libState *ps = (Mp3libState*) vps;
  mad_frame_finish(&ps->frame);
  mad_stream_finish(&ps->stream);
  mad_synth_finish(&ps->synth);
  ps->begin = 1;
}

//static char buffer[40000];
MP3LIB_API int mp3_lib_decode_header(void *vps, unsigned char * inbuff, int insize, int* Freq, int* ch, int* BitRate)
{
	  Mp3libState *ps = (Mp3libState*) vps;
	  ps->resample=0;
   	  mad_stream_buffer(&ps->stream, (const unsigned char *)inbuff, insize);
	  while (mad_frame_decode(&ps->frame, &ps->stream) == -1);
	  if (!*Freq)
	  {
		*Freq=ps->frame.header.samplerate;
	  }
	  else
	  {
		  ps->resample=1;
		  ps->resample_rate=*Freq;
	  }
	  *BitRate=ps->frame.header.bitrate;
	  *ch=(ps->frame.header.mode > 0) ? 2 : 1;
	  mp3_lib_finalize(vps);
	  mp3_lib_init(vps, ps->equalizer,0);
	  return 1;
}

MP3LIB_API int mp3_lib_decode_buffer(void *vps,unsigned char * inbuff, int insize, char *outmemory, int outmemsize, int *done, int* inputpos)
{
	Mp3libState *ps = (Mp3libState*) vps;
	int retval=0;
	resample_state rs;
    mad_fixed_t const *ch1, *ch2;
    mad_fixed_t *rch1, *rch2;
	int resolution=16;
//	unsigned long *clipped;
//	mad_fixed_t *clipping;

	if (inbuff)
	{
//	    int remainder = stream.bufend - stream.this_frame;
//		memcpy(buffer, stream.this_frame, remainder);
//		memcpy(buffer+remainder,inbuff,insize+remainder);
		mad_stream_buffer(&ps->stream, (const unsigned char *)inbuff, insize);
		ps->currentpos+=ps->framepos;
		ps->begin=0;
	}
	else if (ps->begin)
	{
		*done=0;
		return 1;
	}
	int nch;
	int output_length=0;
	mad_fixed_t clipping=0;
	int err=mad_frame_decode(&ps->frame, &ps->stream);
	if (err==-1)
	{
		if (ps->stream.error == MAD_ERROR_BUFLEN)
		{

			ps->framepos=(int)(ps->stream.this_frame-ps->stream.buffer);
			*inputpos=ps->currentpos+ps->framepos;
			*done=0;
			return ps->stream.bufend - ps->stream.this_frame+1;
//				retval=stream.bufend - stream.this_frame+1;			
		}
		else //if((stream.error ==MAD_ERROR_LOSTSYNC||(stream.error==MAD_ERROR_BADDATAPTR)))
		{
			ps->stream.sync=0;
			ps->framepos=(int)(ps->stream.this_frame-ps->stream.buffer);
			*inputpos=ps->currentpos+ps->framepos;
			*done=0;
			return 0;
		}
//		else
//		{
//			return -1;
//		}
	}
	ps->seeking=0;
	ps->framepos=(int)(ps->stream.this_frame-ps->stream.buffer);
	*inputpos=ps->currentpos+ps->framepos;
	if (ps->equalizer)
	{
		attenuate_filter(&ps->frame,ps->attenuation);
		equalizer_filter(&ps->frame,eqfactor);
	}
	mad_synth_frame(&ps->synth,&ps->frame);
	nch= ps->synth.pcm.channels;
	ch1 = ps->synth.pcm.samples[0];
	ch2 = ps->synth.pcm.samples[1];
	if (ps->resample)
	{
		int t;
		rch1=(long*)malloc(sizeof(ch1[0])*(ps->synth.pcm.length));
		resample_init(&rs,ps->synth.pcm.samplerate,ps->resample_rate);
		t=resample_block(&rs,ps->synth.pcm.length,ch1,rch1);
		if (nch == 1)
		{
			rch2 = 0;
		}
		else
		{
			rch2=(long*)malloc(sizeof(ch1[1])*(ps->synth.pcm.length));
			resample_init(&rs,48000,44100);
			t=resample_block(&rs,ps->synth.pcm.length,ch2,rch2);
		}
		ps->synth.pcm.length=t;
		*done=pack_pcm(((unsigned char *)outmemory),
			 ps->synth.pcm.length, rch1, rch2, resolution, &ps->clipped,&clipping);
		free(rch1);
		if (rch2)
			free(rch2);
		if (ps->equalizer)
		{
			ps->attenuation =
			  mad_f_tofixed(mad_f_todouble(ps->attenuation) /
					mad_f_todouble(MAD_F_ONE +
							   mad_f_mul(clipping,
								 conf_attsensitivity)));
		}
		return retval;    
	}
	if (nch == 1)
		ch2 = 0;
	*done=pack_pcm(((unsigned char *)outmemory),
		 ps->synth.pcm.length, ch1, ch2, resolution, &ps->clipped,&clipping);
		if (ps->equalizer)
		{
			ps->attenuation =
			  mad_f_tofixed(mad_f_todouble(ps->attenuation) /
					mad_f_todouble(MAD_F_ONE +
							   mad_f_mul(clipping,
								 conf_attsensitivity)));
		}
	return retval;    
}


