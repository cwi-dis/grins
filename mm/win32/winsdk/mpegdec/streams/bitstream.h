#ifndef BITSTREAM_H
#define BITSTREAM_H

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

#ifndef INC_MPEG2_DEMUX
#include "mpeg2demux.h"
#endif

int mpeg2bits_delete_stream(mpeg2_bits_t* stream);
int mpeg2bits_seek_start(mpeg2_bits_t* stream);
int mpeg2bits_seek_end(mpeg2_bits_t* stream);
int mpeg2bits_seek_percentage(mpeg2_bits_t* stream, double percentage);
void mpeg2bits_start_reverse(mpeg2_bits_t* stream);
void mpeg2bits_start_forward(mpeg2_bits_t* stream);
int mpeg2bits_seek_byte(mpeg2_bits_t* stream, long position);
int mpeg2bits_byte_align(mpeg2_bits_t *stream);
int mpeg2bits_seek_time(mpeg2_bits_t* stream, double time_position);
int mpeg2bits_refill(mpeg2_bits_t* stream);
int mpeg2bits_read_buffer(mpeg2_bits_t* stream, unsigned char *buffer, int bytes);
int mpeg2bits_use_ptr(mpeg2_bits_t* stream, unsigned char *buffer);
int mpeg2bits_getbitoffset(mpeg2_bits_t *stream);
int mpeg2bits_use_demuxer(mpeg2_bits_t* stream);
mpeg2_bits_t* mpeg2bits_new_stream(mpeg2_t *file, mpeg2_demuxer_t *demuxer);
unsigned int mpeg2bits_getbits(mpeg2_bits_t* stream, int n);

//                                    next bit in forward direction
//                                  next bit in reverse direction |
//                                                              v v
// | | | | | | | | | | | | | | | | | | | | | | | | | | |1|1|1|1|1|1| */
//                                                     ^         ^
//                                                     |         bit_number = 1
//                                                     bfr_size = 6


/* ======================================================================== */
/*                                 Entry Points */
/* ======================================================================== */

#define mpeg2bits_tell_percentage(stream) mpeg2demux_tell_percentage((stream)->demuxer)

#define mpeg2bits_packet_time(stream) mpeg2demux_current_time((stream)->demuxer)

#define mpeg2bits_time_offset(stream) mepg2demux_time_offset((stream)->demuxer)

#define mpeg2bits_error(stream) mpeg2demux_error((stream)->demuxer)

#define mpeg2bits_eof(stream) mpeg2demux_eof((stream)->demuxer)

#define mpeg2bits_bof(stream) mpeg2demux_bof((stream)->demuxer)

/* Read bytes backward from the file until the reverse_bits is full. */
static inline void mpeg2bits_fill_reverse_bits(mpeg2_bits_t* stream, int bits)
{
// Right justify
	while(stream->bit_number > 7)
	{
		stream->bfr >>= 8;
		stream->bfr_size -= 8;
		stream->bit_number -= 8;
	}

// Insert bytes before bfr_size
	while(stream->bfr_size - stream->bit_number < bits)
	{
		if(stream->input_ptr)
			stream->bfr |= (unsigned int)(*--stream->input_ptr) << stream->bfr_size;
		else
			stream->bfr |= (unsigned int)mpeg2demux_read_prev_char(stream->demuxer) << stream->bfr_size;
		stream->bfr_size += 8;
	}
}

/* Read bytes forward from the file until the forward_bits is full. */
extern inline void mpeg2bits_fill_bits(mpeg2_bits_t* stream, int bits)
{
	while(stream->bit_number < bits)
	{
		stream->bfr <<= 8;
		if(stream->input_ptr)
		{
			stream->bfr |= *stream->input_ptr++;
		}
		else
		{
			stream->bfr |= mpeg2demux_read_char(stream->demuxer);
		}
		stream->bit_number += 8;
		stream->bfr_size += 8;
		if(stream->bfr_size > 32) stream->bfr_size = 32;
	}
}

/* Return 8 bits, advancing the file position. */
inline unsigned int mpeg2bits_getbyte_noptr(mpeg2_bits_t* stream)
{
	if(stream->bit_number < 8)
	{
		stream->bfr <<= 8;
		if(stream->input_ptr)
			stream->bfr |= *stream->input_ptr++;
		else
			stream->bfr |= mpeg2demux_read_char(stream->demuxer);

		stream->bfr_size += 8;
		if(stream->bfr_size > 32) stream->bfr_size = 32;

		return (stream->bfr >> stream->bit_number) & 0xff;
	}
	return (stream->bfr >> (stream->bit_number -= 8)) & 0xff;
}

inline unsigned int mpeg2bits_getbit_noptr(mpeg2_bits_t* stream)
{
	if(!stream->bit_number)
	{
		stream->bfr <<= 8;
		stream->bfr |= mpeg2demux_read_char(stream->demuxer);

		stream->bfr_size += 8;
		if(stream->bfr_size > 32) stream->bfr_size = 32;

		stream->bit_number = 7;

		return (stream->bfr >> 7) & 0x1;
	}
	return (stream->bfr >> (--stream->bit_number)) & (0x1);
}

/* Return n number of bits, advancing the file position. */
/* Use in place of flushbits */
inline unsigned int mpeg2bits_getbits(mpeg2_bits_t* stream, int bits)
{
	if(bits <= 0) return 0;
	mpeg2bits_fill_bits(stream, bits);
	return (stream->bfr >> (stream->bit_number -= bits)) & (0xffffffff >> (32 - bits));
}

inline unsigned int mpeg2bits_showbits24_noptr(mpeg2_bits_t* stream)
{
	while(stream->bit_number < 24)
	{
		stream->bfr <<= 8;
		stream->bfr |= mpeg2demux_read_char(stream->demuxer);
		stream->bit_number += 8;
		stream->bfr_size += 8;
		if(stream->bfr_size > 32) stream->bfr_size = 32;
	}
	return (stream->bfr >> (stream->bit_number - 24)) & 0xffffff;
}

inline unsigned int mpeg2bits_showbits32_noptr(mpeg2_bits_t* stream)
{
	while(stream->bit_number < 32)
	{
		stream->bfr <<= 8;
		stream->bfr |= mpeg2demux_read_char(stream->demuxer);
		stream->bit_number += 8;
		stream->bfr_size += 8;
		if(stream->bfr_size > 32) stream->bfr_size = 32;
	}
	return stream->bfr;
}

inline unsigned int mpeg2bits_showbits(mpeg2_bits_t* stream, int bits)
{
	mpeg2bits_fill_bits(stream, bits);
	return (stream->bfr >> (stream->bit_number - bits)) & (0xffffffff >> (32 - bits));
}

inline unsigned int mpeg2bits_getbits_reverse(mpeg2_bits_t* stream, int bits)
{
	unsigned int result;
	mpeg2bits_fill_reverse_bits(stream, bits);
	result = (stream->bfr >> stream->bit_number) & (0xffffffff >> (32 - bits));
	stream->bit_number += bits;
	return result;
}

inline unsigned int mpeg2bits_showbits_reverse(mpeg2_bits_t* stream, int bits)
{
	unsigned int result;
	mpeg2bits_fill_reverse_bits(stream, bits);
	result = (stream->bfr >> stream->bit_number) & (0xffffffff >> (32 - bits));
	return result;
}

inline unsigned int mpeg2bits_next_startcode(mpeg2_bits_t* stream)
	{
	// Perform forwards search
	mpeg2bits_byte_align(stream);

	// Perform search
	while((mpeg2bits_showbits32_noptr(stream) >> 8) != MPEG2_PACKET_START_CODE_PREFIX && !mpeg2bits_eof(stream))
		{
		mpeg2bits_getbyte_noptr(stream);
		}
	return mpeg2bits_showbits32_noptr(stream);
	}

#endif
