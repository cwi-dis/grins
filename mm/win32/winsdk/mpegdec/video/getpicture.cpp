#include "getpicture.h"

#include <stdlib.h>
#include <string.h>

#include "mpeg2video.h"
#include "streams/bitstream.h"

#include "vlc.h"

#define bzero(b,len) memset(b,0,(size_t)len)

int mpeg2video_get_cbp(mpeg2_slice_t *slice)
{
  	int code;
	mpeg2_slice_buffer_t *slice_buffer = slice->slice_buffer;

  	if((code = mpeg2slice_showbits9(slice_buffer)) >= 128)
	{
    	code >>= 4;
    	mpeg2slice_flushbits(slice_buffer, mpeg2_CBPtab0[code].len);
    	return mpeg2_CBPtab0[code].val;
  	}

  	if(code >= 8)
	{
    	code >>= 1;
    	mpeg2slice_flushbits(slice_buffer, mpeg2_CBPtab1[code].len);
    	return mpeg2_CBPtab1[code].val;
  	}

  	if(code < 1)
	{
/*    	fprintf(stderr,"mpeg2video_get_cbp: invalid coded_block_pattern code\n"); */
    	slice->fault = 1;
    	return 0;
  	}

  	mpeg2slice_flushbits(slice_buffer, mpeg2_CBPtab2[code].len);
  	return mpeg2_CBPtab2[code].val;
}


/* set block to zero */
int mpeg2video_clearblock(mpeg2_slice_t *slice, int comp, int size)
{
	slice->sparse[comp] = 1;

/* Compiler error */
/*
 * 	for(i = 0; i < size; i++)
 * 	{
 * 		bzero(slice->block[comp] + sizeof(short) * 64 * i, sizeof(short) * 64);
 * 	}
 */

	if(size == 6)
	{
		bzero(slice->block[comp], sizeof(short) * 64 * 6);
	}
	else
	{
	_tprintf(TEXT("mpeg2video_clearblock size = %d\n"), size);
		memset(slice->block[comp], 0, sizeof(short) * 64 * size);
	}
	return 0;
}

static inline int mpeg2video_getdclum(mpeg2_slice_buffer_t *slice_buffer)
{
	int code, size, val;
/* decode length */
	code = mpeg2slice_showbits5(slice_buffer);

	if(code < 31)
	{
    	size = mpeg2_DClumtab0[code].val;
    	mpeg2slice_flushbits(slice_buffer, mpeg2_DClumtab0[code].len);
	}
	else 
	{
    	code = mpeg2slice_showbits9(slice_buffer) - 0x1f0;
    	size = mpeg2_DClumtab1[code].val;
    	mpeg2slice_flushbits(slice_buffer, mpeg2_DClumtab1[code].len);
	}

	if(size == 0) val = 0;
	else 
	{
    	val = mpeg2slice_getbits(slice_buffer, size);
    	if((val & (1 << (size - 1))) == 0)  val -= (1 << size) - 1;
	}

	return val;
}


int mpeg2video_getdcchrom(mpeg2_slice_buffer_t *slice_buffer)
{
	int code, size, val;

/* decode length */
	code = mpeg2slice_showbits5(slice_buffer);

	if(code < 31)
	{
    	size = mpeg2_DCchromtab0[code].val;
    	mpeg2slice_flushbits(slice_buffer, mpeg2_DCchromtab0[code].len);
	}
	else 
	{
    	code = mpeg2slice_showbits(slice_buffer, 10) - 0x3e0;
    	size = mpeg2_DCchromtab1[code].val;
    	mpeg2slice_flushbits(slice_buffer, mpeg2_DCchromtab1[code].len);
	}

	if(size == 0) val = 0;
	else 
	{
      val = mpeg2slice_getbits(slice_buffer, size);
      if((val & (1 << (size - 1))) == 0) val -= (1 << size) - 1;
	}

	return val;
}


/* decode one intra coded MPEG-1 block */

int mpeg2video_getintrablock(mpeg2_slice_t *slice, 
		mpeg2video_t *video,
		int comp, 
		int dc_dct_pred[])
{
	int val, i, j, sign;
	unsigned int code;
	mpeg2_DCTtab_t *tab = 0;
	short *bp = slice->block[comp];
	mpeg2_slice_buffer_t *slice_buffer = slice->slice_buffer;

/* decode DC coefficients */
  	if(comp < 4)         
  		bp[0] = (dc_dct_pred[0] += mpeg2video_getdclum(slice_buffer)) << 3;
  	else 
  	if(comp == 4)   
  		bp[0] = (dc_dct_pred[1] += mpeg2video_getdcchrom(slice_buffer)) << 3;
	else                
  		bp[0] = (dc_dct_pred[2] += mpeg2video_getdcchrom(slice_buffer)) << 3;

  	if(slice->fault) return 1;

/* decode AC coefficients */
  	for(i = 1; ; i++)
	{
    	code = mpeg2slice_showbits16(slice_buffer);
    	if(code >= 16384)
			tab = &mpeg2_DCTtabnext[(code >> 12) - 4];
    	else 
		if(code >= 1024) tab = &mpeg2_DCTtab0[(code >> 8) - 4];
    	else 
		if(code >= 512) tab = &mpeg2_DCTtab1[(code >> 6) - 8];
    	else 
		if(code >= 256) tab = &mpeg2_DCTtab2[(code >> 4) - 16];
    	else 
		if(code >= 128) tab = &mpeg2_DCTtab3[(code >> 3) - 16];
    	else 
		if(code >= 64) tab = &mpeg2_DCTtab4[(code >> 2) - 16];
    	else 
		if(code >= 32) tab = &mpeg2_DCTtab5[(code >> 1) - 16];
    	else 
		if(code >= 16) tab = &mpeg2_DCTtab6[code - 16];
    	else 
		{
/*    	  	fprintf(stderr, "mpeg2video_getintrablock: invalid Huffman code\n"); */
    	  	slice->fault = 1;
    	  	return  0;
    	}

    	mpeg2slice_flushbits(slice_buffer, tab->len);

    	if(tab->run == 64) break;  /* end_of_block */

    	if(tab->run == 65)
		{
/* escape */
    		i += mpeg2slice_getbits(slice_buffer, 6);

    		if((val = mpeg2slice_getbits(slice_buffer, 8)) == 0) 
				val = mpeg2slice_getbits(slice_buffer, 8);
    		else 
			if(val == 128)         
				val = mpeg2slice_getbits(slice_buffer, 8) - 256;
    		else 
			if(val > 128)          
				val -= 256;

    		if((sign = (val < 0)) != 0) val= -val;
    	}
    	else 
		{
    		i += tab->run;
    		val = tab->level;
    		sign = mpeg2slice_getbit(slice_buffer);
    	}

		if(i < 64)
	    	j = video->mpeg2_zigzag_scan_table[i];
		else
		{
    	  	slice->fault = 1;
    	  	return 0;
		}
			

		{
    		val = (val * slice->quant_scale * video->intra_quantizer_matrix[j]) >> 3;
    		val = (val - 1) | 1;
		}

    	bp[j] = sign ? -val : val;
	}

	if(j != 0) 
	{
/* not a sparse matrix ! */
       slice->sparse[comp] = 0;
	}
	return 0;
}


/* decode one non-intra coded MPEG-1 block */

int mpeg2video_getinterblock(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int comp)
{
	int val, i, j, sign;
	unsigned int code;
	mpeg2_DCTtab_t *tab; 
	short *bp = slice->block[comp];
	mpeg2_slice_buffer_t *slice_buffer = slice->slice_buffer;

/* decode AC coefficients */
	for(i = 0; ; i++)
	{
    	code = mpeg2slice_showbits16(slice_buffer);
    	if(code >= 16384)
		{
    	    if(i == 0) 
				tab = &mpeg2_DCTtabfirst[(code >> 12) - 4];
    	    else      
				tab = &mpeg2_DCTtabnext[(code >> 12) - 4];
    	}
    	else 
		if(code >= 1024) tab = &mpeg2_DCTtab0[(code >> 8) - 4];
    	else 
		if(code >= 512)  tab = &mpeg2_DCTtab1[(code >> 6) - 8];
    	else 
		if(code >= 256)  tab = &mpeg2_DCTtab2[(code >> 4) - 16];
    	else 
		if(code >= 128)  tab = &mpeg2_DCTtab3[(code >> 3) - 16];
    	else 
		if(code >= 64)   tab = &mpeg2_DCTtab4[(code >> 2) - 16];
    	else 
		if(code >= 32)   tab = &mpeg2_DCTtab5[(code >> 1) - 16];
    	else 
		if(code >= 16)   tab = &mpeg2_DCTtab6[code - 16];
    	else 
		{
// invalid Huffman code
    		slice->fault = 1;
    		return 1;
    	}

    	mpeg2slice_flushbits(slice_buffer, tab->len);

/* end of block */
    	if(tab->run == 64)
    	   break;   

    	if(tab->run == 65)
		{          
/* escape  */
    		i += mpeg2slice_getbits(slice_buffer, 6);
    		if((val = mpeg2slice_getbits(slice_buffer, 8)) == 0) 
				val = mpeg2slice_getbits(slice_buffer, 8);
    		else 
			if(val == 128)  
				val = mpeg2slice_getbits(slice_buffer, 8) - 256;
    		else 
			if(val > 128) 
				val -= 256;

    		if((sign = (val < 0)) != 0) val = -val;
    	}
    	else 
		{
    		i += tab->run;
    		val = tab->level;
    		sign = mpeg2slice_getbit(slice_buffer);
    	}

    	j = video->mpeg2_zigzag_scan_table[i];

		{
    		val = (((val << 1)+1) * slice->quant_scale * video->non_intra_quantizer_matrix[j]) >> 4;
    		val = (val - 1) | 1;
		}

    	bp[j] = sign ? -val : val;
	}

	if(j != 0) 
	{
/* not a sparse matrix ! */
       slice->sparse[comp] = 0;
	}
	return 0;
}


/* decode one intra coded MPEG-2 block */
int mpeg2video_getmpg2intrablock(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int comp, 
		int dc_dct_pred[])
{
	int val, i, j, sign, nc;
	unsigned int code;
	mpeg2_DCTtab_t *tab;
	short *bp;
	int *qmat;
	mpeg2_slice_buffer_t *slice_buffer = slice->slice_buffer;

/* with data partitioning, data always goes to base layer */
  	bp = slice->block[comp];

  	qmat = (comp < 4 || video->chroma_format == CHROMA420)
         ? video->intra_quantizer_matrix
         : video->chroma_intra_quantizer_matrix;

/* decode DC coefficients */
	if(comp < 4)           
		val = (dc_dct_pred[0] += mpeg2video_getdclum(slice_buffer));
	else 
	if((comp & 1) == 0) 
		val = (dc_dct_pred[1] += mpeg2video_getdcchrom(slice_buffer));
	else                  
		val = (dc_dct_pred[2] += mpeg2video_getdcchrom(slice_buffer));

  	if(slice->fault) return 0;
  		bp[0] = val << (3 - video->dc_prec);

  	nc = 0;

/* decode AC coefficients */
  	for(i = 1; ; i++)
	{
    	code = mpeg2slice_showbits16(slice_buffer);

    	if(code >= 16384 && !video->intravlc)
			tab = &mpeg2_DCTtabnext[(code >> 12) - 4];
    	else 
		if(code >= 1024)
		{
    		if(video->intravlc) 
				tab = &mpeg2_DCTtab0a[(code >> 8) - 4];
    		else 
				tab = &mpeg2_DCTtab0[(code >> 8) - 4];
    	}
    	else 
		if(code >= 512)
		{
    		if(video->intravlc)     
		  	  	tab = &mpeg2_DCTtab1a[(code >> 6) - 8];
    		else              
				tab = &mpeg2_DCTtab1[(code >> 6) - 8];
    	}
    	else 
		if(code >= 256) tab = &mpeg2_DCTtab2[(code >> 4) - 16];
    	else 
		if(code >= 128) tab = &mpeg2_DCTtab3[(code >> 3) - 16];
    	else 
		if(code >= 64)  tab = &mpeg2_DCTtab4[(code >> 2) - 16];
    	else 
		if(code >= 32)  tab = &mpeg2_DCTtab5[(code >> 1) - 16];
    	else 
		if(code >= 16)  tab = &mpeg2_DCTtab6[code - 16];
    	else 
		{
/*    		fprintf(stderr,"mpeg2video_getmpg2intrablock: invalid Huffman code\n"); */
    		slice->fault = 1;
    		return 1;
    	}

    	mpeg2slice_flushbits(slice_buffer, tab->len);

/* end_of_block */
    	if(tab->run == 64)
    	   	break; 

    	if(tab->run == 65)
		{
/* escape */
    	  	i += mpeg2slice_getbits(slice_buffer, 6);

    	  	val = mpeg2slice_getbits(slice_buffer, 12);
    	  	if((val & 2047) == 0)
			{
// invalid signed_level (escape)
        		slice->fault = 1;
        		return 0;
    	  	}
    	  	if((sign = (val >= 2048)) != 0) val = 4096 - val;
    	}
    	else 
		{
    		i += tab->run;
    		val = tab->level;
    		sign = mpeg2slice_getbit(slice_buffer);
    	}

    	j = (video->altscan ? video->mpeg2_alternate_scan_table : video->mpeg2_zigzag_scan_table)[i];

    		val = (val * slice->quant_scale * qmat[j]) >> 4;

    	bp[j] = sign ? -val : val;
    	nc++;
	}

	if(j != 0)
	{
/* not a sparse matrix ! */
    	 slice->sparse[comp] = 0;
	}
	return 1;
}


/* decode one non-intra coded MPEG-2 block */

int mpeg2video_getmpg2interblock(mpeg2_slice_t *slice, 
		mpeg2video_t *video, 
		int comp)
{
	int val, i, j, sign, nc;
	unsigned int code;
	mpeg2_DCTtab_t *tab;
	short *bp;
	int *qmat;
	mpeg2_slice_buffer_t *slice_buffer = slice->slice_buffer;

/* with data partitioning, data always goes to base layer */
  	bp = slice->block[comp];

  	qmat = (comp < 4 || video->chroma_format == CHROMA420)
         ? video->non_intra_quantizer_matrix
         : video->chroma_non_intra_quantizer_matrix;

  	nc = 0;

/* decode AC coefficients */
  	for(i = 0; ; i++)
	{
    	code = mpeg2slice_showbits16(slice_buffer);
    	if(code >= 16384)
		{
    	  if(i == 0) tab = &mpeg2_DCTtabfirst[(code >> 12) - 4];
    	  else      tab = &mpeg2_DCTtabnext[(code >> 12) - 4];
    	}
    	else 
		if(code >= 1024) tab = &mpeg2_DCTtab0[(code >> 8) - 4];
    	else 
		if(code >= 512)  tab = &mpeg2_DCTtab1[(code >> 6) - 8];
    	else 
		if(code >= 256)  tab = &mpeg2_DCTtab2[(code >> 4) - 16];
    	else 
		if(code >= 128)  tab = &mpeg2_DCTtab3[(code >> 3) - 16];
    	else 
		if(code >= 64)   tab = &mpeg2_DCTtab4[(code >> 2) - 16];
    	else 
		if(code >= 32)   tab = &mpeg2_DCTtab5[(code >> 1) - 16];
    	else 
		if(code >= 16)   tab = &mpeg2_DCTtab6[code - 16];
    	else 
		{
// invalid Huffman code
    		slice->fault = 1;
    		return 0;
    	}

    	mpeg2slice_flushbits(slice_buffer, tab->len);

/* end_of_block */
    	if(tab->run == 64)
       		break;          

    	if(tab->run == 65)
		{                 
/* escape */
    		i += mpeg2slice_getbits(slice_buffer, 6);
    		val = mpeg2slice_getbits(slice_buffer, 12);
    		if((val & 2047) == 0)
			{
/*        		fprintf(stderr, "mpeg2video_getmpg2interblock: invalid signed_level (escape)\n"); */
        		slice->fault = 1;
        		return 1;
    		}
    		if((sign = (val >= 2048)) != 0) val = 4096 - val;
    	}
    	else 
		{
    		i += tab->run;
    		val = tab->level;
    		sign = mpeg2slice_getbit(slice_buffer);
    	}

    	j = (video->altscan ? video->mpeg2_alternate_scan_table : video->mpeg2_zigzag_scan_table)[i];

     		val = (((val << 1)+1) * slice->quant_scale * qmat[j]) >> 5;

    	bp[j] = sign ? (-val) : val ;
    	nc++;
	}

	if(j != 0) 
	{
      	slice->sparse[comp] = 0;
	}
	return 0;
}


/* decode all macroblocks of the current picture */
int mpeg2video_get_macroblocks(mpeg2video_t *video, int framenum)
{
	//unsigned int code;
	mpeg2_slice_buffer_t *slice_buffer; /* Buffer being loaded */
	int i;
	int current_buffer;
	mpeg2_bits_t *vstream = video->vstream;

/* Load every slice into a buffer array */
	video->total_slice_buffers = 0;
	current_buffer = 0;
	while(!mpeg2bits_eof(vstream) && 
		mpeg2bits_showbits32_noptr(vstream) >= MPEG2_SLICE_START_CODE_MIN && 
		mpeg2bits_showbits32_noptr(vstream) <= MPEG2_SLICE_START_CODE_MAX)
	{
/* Initialize the buffer */
		if(current_buffer >= video->slice_buffers_initialized)
			mpeg2_new_slice_buffer(&(video->slice_buffers[video->slice_buffers_initialized++]));
		slice_buffer = &(video->slice_buffers[current_buffer]);
		slice_buffer->buffer_size = 0;
		slice_buffer->current_position = 0;
		slice_buffer->bits_size = 0;
		slice_buffer->done = 0;

/* Read the slice into the buffer including the slice start code */
		do
		{
/* Expand buffer */
			if(slice_buffer->buffer_allocation <= slice_buffer->buffer_size)
				mpeg2_expand_slice_buffer(slice_buffer);

/* Load 1 char into buffer */
			slice_buffer->data[slice_buffer->buffer_size++] = mpeg2bits_getbyte_noptr(vstream);
		}while(!mpeg2bits_eof(vstream) &&
			mpeg2bits_showbits24_noptr(vstream) != MPEG2_PACKET_START_CODE_PREFIX);

/* Pad the buffer to get the last macroblock */
		if(slice_buffer->buffer_allocation <= slice_buffer->buffer_size + 4)
			mpeg2_expand_slice_buffer(slice_buffer);

		slice_buffer->data[slice_buffer->buffer_size++] = 0;
		slice_buffer->data[slice_buffer->buffer_size++] = 0;
		slice_buffer->data[slice_buffer->buffer_size++] = 1;
		slice_buffer->data[slice_buffer->buffer_size++] = 0;
		slice_buffer->bits_size = 0;

		//pthread_mutex_lock(&(slice_buffer->completion_lock)); fflush(stdout);
		current_buffer++;
		video->total_slice_buffers++;
	}

/* Run the slice decoders */
	if(video->total_slice_buffers > 0)
	{
		for(i = 0; i < video->total_slice_decoders; i++)
		{
			if(i == 0 && video->total_slice_decoders > 1)
			{
				video->slice_decoders[i].current_buffer = 0;
				video->slice_decoders[i].buffer_step = 1;
				video->slice_decoders[i].last_buffer = (video->total_slice_buffers - 1);
			}
			else
			if(i == 1)
			{
				video->slice_decoders[i].current_buffer = video->total_slice_buffers - 1;
				video->slice_decoders[i].buffer_step = -1;
				video->slice_decoders[i].last_buffer = 0;
			}
			else
			{
				video->slice_decoders[i].current_buffer = i;
				video->slice_decoders[i].buffer_step = 1;
				video->slice_decoders[i].last_buffer = video->total_slice_buffers - 1;
			}
			//pthread_mutex_unlock(&(video->slice_decoders[i].input_lock));
		}
	}

/* Wait for the slice decoders to finish */
	if(video->total_slice_buffers > 0)
	{
		for(i = 0; i < video->total_slice_buffers; i++)
		{
			//pthread_mutex_lock(&(video->slice_buffers[i].completion_lock));
			//pthread_mutex_unlock(&(video->slice_buffers[i].completion_lock));
		}
	}
	return 0;
}

int mpeg2video_allocate_decoders(mpeg2video_t *video, int decoder_count)
{
	int i;
	mpeg2_t *file = (mpeg2_t *)video->file;
/* Get the slice decoders */
	if(video->total_slice_decoders != file->cpus)
	{
		for(i = 0; i < video->total_slice_decoders; i++)
		{
			mpeg2_delete_slice_decoder(&video->slice_decoders[i]);
		}

		for(i = 0; i < file->cpus && i < MPEG2_MAX_CPUS; i++)
		{
			mpeg2_new_slice_decoder(video, &(video->slice_decoders[i]));
			video->slice_decoders[i].thread_number = i;
		}

		video->total_slice_decoders = file->cpus;
	}
	return 0;
}

/* decode one frame or field picture */

int mpeg2video_getpicture(mpeg2video_t *video, int framenum)
{
	int i, result = 0;
	mpeg2_t *file = (mpeg2_t *)video->file;

	if(video->pict_struct == FRAME_PICTURE && video->secondfield)
	{
/* recover from illegal number of field pictures */
    	video->secondfield = 0;
	}

	if(!video->mpeg2)
	{
		video->current_repeat = video->repeat_count = 0;
	}

	mpeg2video_allocate_decoders(video, file->cpus);

  	for(i = 0; i < 3; i++)
	{
    	if(video->pict_type == B_TYPE)
		{
			video->newframe[i] = video->auxframe[i];
		}
    	else 
		{
    	  	if(!video->secondfield && !video->current_repeat)
			{
/* Swap refframes for I frames */
        		unsigned char* tmp = video->oldrefframe[i];
        		video->oldrefframe[i] = video->refframe[i];
        		video->refframe[i] = tmp;
    	  	}

    	 	video->newframe[i] = video->refframe[i];
    	}

    	if(video->pict_struct == BOTTOM_FIELD)
		{
/* Only used if fields are in different pictures */
    	    video->newframe[i] += (i == 0) ? video->coded_picture_width : video->chrom_width;
		}
	}

/* The problem is when a B frame lands on the first repeat and is skipped, */
/* the second repeat goes for the same bitmap as the skipped repeat, */
/* so it picks up a frame from 3 frames back. */
/* The first repeat must consititutively read a B frame if its B frame is going to be */
/* used in a later repeat. */
	if(!video->current_repeat)
		if(!(video->skip_bframes && video->pict_type == B_TYPE) || 
			(video->repeat_count >= 100 + 100 * video->skip_bframes))
  			result = mpeg2video_get_macroblocks(video, framenum);

/* Set the frame to display */
	video->output_src = 0;
	if(framenum > -1 && !result)
	{
    	if(video->pict_struct == FRAME_PICTURE || video->secondfield)
		{
     	  	if(video->pict_type == B_TYPE)
			{
				video->output_src = video->auxframe;
			}
     	  	else
			{
				video->output_src = video->oldrefframe;
			}
    	}
    	else 
		{
			;//mpeg2video_display_second_field(video);
		}
	}

	if(video->mpeg2)
	{
		video->current_repeat += 100;
	}

  	if(video->pict_struct != FRAME_PICTURE) video->secondfield = !video->secondfield;
	return result;
}
