#ifndef SLICE_H
#define SLICE_H

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

//#include <pthread.h>

/* Array of these feeds the slice decoders */
typedef struct
{
	unsigned char *data;   /* Buffer for holding the slice data */
	int buffer_size;         /* Size of buffer */
	int buffer_allocation;   /* Space allocated for buffer  */
	int current_position;    /* Position in buffer */
	unsigned MPEG2_INT32 bits;
	int bits_size;
	//pthread_mutex_t completion_lock; /* Lock slice until completion */
	int done;           /* Signal for slice decoder to skip */
} mpeg2_slice_buffer_t;

/* Each slice decoder */
typedef struct
{
	void *video;     /* mpeg2video_t */
	mpeg2_slice_buffer_t *slice_buffer;

	int thread_number;      /* Number of this thread */
	int current_buffer;     /* Buffer this slice decoder is on */
	int buffer_step;        /* Number of buffers to skip */
	int last_buffer;        /* Last buffer this decoder should process */
	int fault;
	int done;
	int quant_scale;
	int pri_brk;                  /* slice/macroblock */
	short block[12][64];
	int sparse[12];
	//pthread_t tid;   /* ID of thread */
	//pthread_mutex_t input_lock, output_lock;
} mpeg2_slice_t;

#define mpeg2slice_fillbits(buffer, nbits) \
	while(((mpeg2_slice_buffer_t*)(buffer))->bits_size < (nbits)) \
	{ \
		if(((mpeg2_slice_buffer_t*)(buffer))->current_position < ((mpeg2_slice_buffer_t*)(buffer))->buffer_size) \
		{ \
			((mpeg2_slice_buffer_t*)(buffer))->bits <<= 8; \
			((mpeg2_slice_buffer_t*)(buffer))->bits |= ((mpeg2_slice_buffer_t*)(buffer))->data[((mpeg2_slice_buffer_t*)(buffer))->current_position++]; \
		} \
		((mpeg2_slice_buffer_t*)(buffer))->bits_size += 8; \
	}

#define mpeg2slice_flushbits(buffer, nbits) \
	{ \
		mpeg2slice_fillbits((buffer), (nbits)); \
		((mpeg2_slice_buffer_t*)(buffer))->bits_size -= (nbits); \
	}

#define mpeg2slice_flushbit(buffer) \
{ \
	if(((mpeg2_slice_buffer_t*)(buffer))->bits_size) \
		((mpeg2_slice_buffer_t*)(buffer))->bits_size--; \
	else \
	if(((mpeg2_slice_buffer_t*)(buffer))->current_position < ((mpeg2_slice_buffer_t*)(buffer))->buffer_size) \
	{ \
		((mpeg2_slice_buffer_t*)(buffer))->bits = \
			((mpeg2_slice_buffer_t*)(buffer))->data[((mpeg2_slice_buffer_t*)(buffer))->current_position++]; \
		((mpeg2_slice_buffer_t*)(buffer))->bits_size = 7; \
	} \
}

extern inline unsigned int mpeg2slice_getbit(mpeg2_slice_buffer_t *buffer)
{
	if(buffer->bits_size)
		return (buffer->bits >> (--buffer->bits_size)) & 0x1;
	else
	if(buffer->current_position < buffer->buffer_size)
	{
		buffer->bits = buffer->data[buffer->current_position++];
		buffer->bits_size = 7;
		return (buffer->bits >> 7) & 0x1;
	}
	return 0; // na
}

extern inline unsigned int mpeg2slice_getbits2(mpeg2_slice_buffer_t *buffer)
{
	if(buffer->bits_size >= 2)
		return (buffer->bits >> (buffer->bits_size -= 2)) & 0x3;
	else
	if(buffer->current_position < buffer->buffer_size)
	{
		buffer->bits <<= 8;
		buffer->bits |= buffer->data[buffer->current_position++];
		buffer->bits_size += 6;
		return (buffer->bits >> buffer->bits_size)  & 0x3;
	}
	return 0; // na
}

extern inline unsigned int mpeg2slice_getbyte(mpeg2_slice_buffer_t *buffer)
{
	if(buffer->bits_size >= 8)
		return (buffer->bits >> (buffer->bits_size -= 8)) & 0xff;
	else
	if(buffer->current_position < buffer->buffer_size)
	{
		buffer->bits <<= 8;
		buffer->bits |= buffer->data[buffer->current_position++];
		return (buffer->bits >> buffer->bits_size) & 0xff;
	}
	return 0; // na
}


extern inline unsigned int mpeg2slice_getbits(mpeg2_slice_buffer_t *slice_buffer, int bits)
{
	if(bits == 1) return mpeg2slice_getbit(slice_buffer);
	mpeg2slice_fillbits(slice_buffer, bits);
	return (slice_buffer->bits >> (slice_buffer->bits_size -= bits)) & (0xffffffff >> (32 - bits));
}

extern inline unsigned int mpeg2slice_showbits16(mpeg2_slice_buffer_t *buffer)
{
	if(buffer->bits_size >= 16)
		return (buffer->bits >> (buffer->bits_size - 16)) & 0xffff;
	else
	if(buffer->current_position < buffer->buffer_size)
	{
		buffer->bits <<= 16;
		buffer->bits_size += 16;
		buffer->bits |= (unsigned int)buffer->data[buffer->current_position++] << 8;
		buffer->bits |= buffer->data[buffer->current_position++];
		return (buffer->bits >> (buffer->bits_size - 16)) & 0xffff;
	}
	return 0; // na
}

extern inline unsigned int mpeg2slice_showbits9(mpeg2_slice_buffer_t *buffer)
{
	if(buffer->bits_size >= 9)
		return (buffer->bits >> (buffer->bits_size - 9)) & 0x1ff;
	else
	if(buffer->current_position < buffer->buffer_size)
	{
		buffer->bits <<= 16;
		buffer->bits_size += 16;
		buffer->bits |= (unsigned int)buffer->data[buffer->current_position++] << 8;
		buffer->bits |= buffer->data[buffer->current_position++];
		return (buffer->bits >> (buffer->bits_size - 9)) & 0x1ff;
	}
	return 0; // na

}

extern inline unsigned int mpeg2slice_showbits5(mpeg2_slice_buffer_t *buffer)
{
	if(buffer->bits_size >= 5)
		return (buffer->bits >> (buffer->bits_size - 5)) & 0x1f;
	else
	if(buffer->current_position < buffer->buffer_size)
	{
		buffer->bits <<= 8;
		buffer->bits_size += 8;
		buffer->bits |= buffer->data[buffer->current_position++];
		return (buffer->bits >> (buffer->bits_size - 5)) & 0x1f;
	}
	return 0; // na
}

extern inline unsigned int mpeg2slice_showbits(mpeg2_slice_buffer_t *slice_buffer, int bits)
{
	mpeg2slice_fillbits(slice_buffer, bits);
	return (slice_buffer->bits >> (slice_buffer->bits_size - bits)) & (0xffffffff >> (32 - bits));
}

int mpeg2_new_slice_buffer(mpeg2_slice_buffer_t *slice_buffer);
int mpeg2_delete_slice_buffer(mpeg2_slice_buffer_t *slice_buffer);
int mpeg2_expand_slice_buffer(mpeg2_slice_buffer_t *slice_buffer);
int mpeg2_delete_slice_decoder(mpeg2_slice_t *slice);
void mpeg2_slice_loop(mpeg2_slice_t *slice);
int mpeg2_decode_slice(mpeg2_slice_t *slice);
int mpeg2_new_slice_decoder(void *video, mpeg2_slice_t *slice);

#endif
