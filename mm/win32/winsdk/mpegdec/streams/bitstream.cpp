#include "bitstream.h"

#include <stdlib.h>
#include <string.h>

/////////////////////////
mpeg2_bits_t * mpeg2bits_new_stream(mpeg2_t *file, mpeg2_demuxer_t *demuxer)
	{
	mpeg2_bits_t *stream = new mpeg2_bits_t;
	memset(stream, 0, sizeof(mpeg2_bits_t));
	stream->file = file;
	stream->demuxer = demuxer;
	return stream;
	}

int mpeg2bits_delete_stream(mpeg2_bits_t* stream)
	{
	delete stream;
	return 0;
	}

// Fill a buffer.  Only works if bit_number is on an 8 bit boundary
int mpeg2bits_read_buffer(mpeg2_bits_t* stream, unsigned char *buffer, int bytes)
	{
	while(stream->bit_number > 0)
		{
		stream->bit_number -= 8;
		mpeg2demux_read_prev_char(stream->demuxer);
		}

	stream->bit_number = 0;
	stream->bfr_size = 0;
	stream->bfr = 0;
	int result = mpeg2demux_read_data(stream->demuxer, buffer, bytes);
	return result;
	}

// For mp3 decompression use a pointer in a buffer for getbits
int mpeg2bits_use_ptr(mpeg2_bits_t* stream, unsigned char *buffer)
	{
	stream->bfr_size = stream->bit_number = 0;
	stream->bfr = 0;
	stream->input_ptr = buffer;
	return 0;
	}

// Go back to using the demuxer for getbits in mp3
int mpeg2bits_use_demuxer(mpeg2_bits_t* stream)
	{
	if(stream->input_ptr)
		{
		stream->bfr_size = stream->bit_number = 0;
		stream->input_ptr = 0;
		stream->bfr = 0;
		}
	return 0;
	}

// Reconfigure for reverse operation 
// Default is forward operation
void mpeg2bits_start_reverse(mpeg2_bits_t* stream)
	{
	for(int i = 0; i < stream->bfr_size; i += 8)
		{
		if(stream->input_ptr)
			stream->input_ptr--;
		else
			mpeg2demux_read_prev_char(stream->demuxer);
		}
	}

// Reconfigure for forward operation
void mpeg2bits_start_forward(mpeg2_bits_t* stream)
	{
	for(int i = 0; i < stream->bfr_size; i += 8)
		{
		if(stream->input_ptr)
			stream->input_ptr++;
		else
			mpeg2demux_read_char(stream->demuxer);
		}
	}

// Erase the buffer with the next 4 bytes in the file
int mpeg2bits_refill(mpeg2_bits_t* stream)
	{
	stream->bit_number = 32;
	stream->bfr_size = 32;

	if(stream->input_ptr)
		{
		stream->bfr = (unsigned int)(*stream->input_ptr++) << 24;
		stream->bfr |= (unsigned int)(*stream->input_ptr++) << 16;
		stream->bfr |= (unsigned int)(*stream->input_ptr++) << 8;
		stream->bfr |= *stream->input_ptr++;
		}
	else
		{
		stream->bfr = mpeg2demux_read_char(stream->demuxer) << 24;
		stream->bfr |= mpeg2demux_read_char(stream->demuxer) << 16;
		stream->bfr |= mpeg2demux_read_char(stream->demuxer) << 8;
		stream->bfr |= mpeg2demux_read_char(stream->demuxer);
		}
	return mpeg2demux_eof(stream->demuxer);
	}

// Erase the buffer with the previous 4 bytes in the file
int mpeg2bits_refill_backwards(mpeg2_bits_t* stream)
	{
	stream->bit_number = 0;
	stream->bfr_size = 32;
	stream->bfr = mpeg2demux_read_prev_char(stream->demuxer);
	stream->bfr |= (unsigned int)mpeg2demux_read_prev_char(stream->demuxer) << 8;
	stream->bfr |= (unsigned int)mpeg2demux_read_prev_char(stream->demuxer) << 16;
	stream->bfr |= (unsigned int)mpeg2demux_read_prev_char(stream->demuxer) << 24;
	return mpeg2demux_eof(stream->demuxer);
	}

int mpeg2bits_byte_align(mpeg2_bits_t *stream)
	{
	stream->bit_number = (stream->bit_number + 7) & 0xf8;
	return 0;
	}

int mpeg2bits_seek_end(mpeg2_bits_t* stream)
	{
	stream->bfr_size = stream->bit_number = 0;
	return mpeg2demux_seek_byte(stream->demuxer, mpeg2demuxer_total_bytes(stream->demuxer));
	}

int mpeg2bits_seek_start(mpeg2_bits_t* stream)
	{
	stream->bfr_size = stream->bit_number = 0;
	return mpeg2demux_seek_byte(stream->demuxer, 0);
	}

int mpeg2bits_seek_time(mpeg2_bits_t* stream, double time_position)
	{
	stream->bfr_size = stream->bit_number = 0;
	return mpeg2demux_seek_time(stream->demuxer, time_position);
	}

int mpeg2bits_seek_byte(mpeg2_bits_t* stream, long position)
	{
	stream->bfr_size = stream->bit_number = 0;
	return mpeg2demux_seek_byte(stream->demuxer, position);
	}

int mpeg2bits_seek_percentage(mpeg2_bits_t* stream, double percentage)
	{
	stream->bfr_size = stream->bit_number = 0;
	return mpeg2demux_seek_percentage(stream->demuxer, percentage);
	}

int mpeg2bits_tell(mpeg2_bits_t* stream)
	{
	return mpeg2demux_tell(stream->demuxer);
	}

int mpeg2bits_getbitoffset(mpeg2_bits_t *stream)
	{
	return stream->bit_number & 7;
	}

