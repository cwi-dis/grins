#include "mpeg2demux.h"

#include <math.h>
#include <string.h>

#include "mpeg2title.h"
#include "mpeg2io.h"
#include "mpeg2css.h"

///////////////////////////

#define ABS(x) ((x) >= 0 ? (x) : -(x))

#ifdef UNICODE
#define strncasecmp _wcsnicmp 
#define strcasecmp _wcsicmp 
#else
#define strncasecmp _strnicmp 
#define strcasecmp _stricmp 
#endif

// Don't advance pointer
inline unsigned char mpeg2packet_next_char(mpeg2_demuxer_t *demuxer)
	{
	return demuxer->raw_data[demuxer->raw_offset];
	}

unsigned char mpeg2packet_read_char(mpeg2_demuxer_t *demuxer)
	{
	return demuxer->raw_data[demuxer->raw_offset++];
	}

inline unsigned int mpeg2packet_read_int16(mpeg2_demuxer_t *demuxer)
	{
	unsigned int a, b, result;
	a = demuxer->raw_data[demuxer->raw_offset++];
	b = demuxer->raw_data[demuxer->raw_offset++];
	result = (a << 8) | b;
	return result;
	}

inline unsigned int mpeg2packet_next_int24(mpeg2_demuxer_t *demuxer)
	{
	unsigned int a, b, c, result;
	a = demuxer->raw_data[demuxer->raw_offset];
	b = demuxer->raw_data[demuxer->raw_offset + 1];
	c = demuxer->raw_data[demuxer->raw_offset + 2];
	result = (a << 16) | (b << 8) | c;

	return result;
	}

inline unsigned int mpeg2packet_read_int24(mpeg2_demuxer_t *demuxer)
	{
	unsigned int a, b, c, result;
	a = demuxer->raw_data[demuxer->raw_offset++];
	b = demuxer->raw_data[demuxer->raw_offset++];
	c = demuxer->raw_data[demuxer->raw_offset++];
	result = (a << 16) | (b << 8) | c;

	return result;
	}

inline unsigned int mpeg2packet_read_int32(mpeg2_demuxer_t *demuxer)
	{
	unsigned int a, b, c, d, result;
	a = demuxer->raw_data[demuxer->raw_offset++];
	b = demuxer->raw_data[demuxer->raw_offset++];
	c = demuxer->raw_data[demuxer->raw_offset++];
	d = demuxer->raw_data[demuxer->raw_offset++];
	result = (a << 24) | (b << 16) | (c << 8) | d;

	return result;
	}

inline unsigned int mpeg2packet_skip(mpeg2_demuxer_t *demuxer, long length)
	{
	demuxer->raw_offset += length;
	return 0;
	}

int mpeg2_get_adaptation_field(mpeg2_demuxer_t *demuxer)
	{
	long length;
	int pcr_flag;

	demuxer->adaptation_fields++;
	// get adaptation field length 
	length = mpeg2packet_read_char(demuxer);
	
	// get first byte
  	pcr_flag = (mpeg2packet_read_char(demuxer) >> 4) & 1;           

	if(pcr_flag)
		{
    	unsigned long clk_ref_base = mpeg2packet_read_int32(demuxer);
    	unsigned int clk_ref_ext = mpeg2packet_read_int16(demuxer);

		if (clk_ref_base > 0x7fffffff)
			{   
			// correct for invalid numbers
			clk_ref_base = 0;               // ie. longer than 32 bits when multiplied by 2 
			clk_ref_ext = 0;                // multiplied by 2 corresponds to shift left 1 (<<=1) 
			}
		else 
			{
			clk_ref_base <<= 1; // Create space for bit 
			clk_ref_base |= (clk_ref_ext >> 15);          // Take bit 
			clk_ref_ext &= 0x01ff;                        // Only lower 9 bits 
			}
		demuxer->time = clk_ref_base + clk_ref_ext / 300;
	    if(length) mpeg2packet_skip(demuxer, length - 7);
		}
	else
		mpeg2packet_skip(demuxer, length - 1);

	return 0;
	}

int mpeg2_get_program_association_table(mpeg2_demuxer_t *demuxer)
	{
	demuxer->program_association_tables++;
	demuxer->table_id = mpeg2packet_read_char(demuxer);
	demuxer->section_length = mpeg2packet_read_int16(demuxer) & 0xfff;
	demuxer->transport_stream_id = mpeg2packet_read_int16(demuxer);
	mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
	return 0;
	}

int mpeg2packet_get_data_buffer(mpeg2_demuxer_t *demuxer)
	{
	while(demuxer->raw_offset < demuxer->raw_size && demuxer->data_size < demuxer->data_allocated)
		{
		demuxer->data_buffer[demuxer->data_size++] = demuxer->raw_data[demuxer->raw_offset++];
		}
	return 0;
	}

int mpeg2_get_pes_packet_header(mpeg2_demuxer_t *demuxer, unsigned long *pts, unsigned long *dts)
	{
	unsigned int pes_header_bytes = 0;
	unsigned int pts_dts_flags;
	int pes_header_data_length;

	// drop first 8 bits 
	mpeg2packet_read_char(demuxer);  
	pts_dts_flags = (mpeg2packet_read_char(demuxer) >> 6) & 0x3;
	pes_header_data_length = mpeg2packet_read_char(demuxer);

	// Get Presentation Time stamps and Decoding Time Stamps
	if(pts_dts_flags == 2)
		{
		*pts = (mpeg2packet_read_char(demuxer) >> 1) & 7;  // Only low 4 bits (7==1111) 
		*pts <<= 15;
		*pts |= (mpeg2packet_read_int16(demuxer) >> 1);
		*pts <<= 15;
		*pts |= (mpeg2packet_read_int16(demuxer) >> 1);
		pes_header_bytes += 5;
		}
	else if(pts_dts_flags == 3)
		{      
		*pts = (mpeg2packet_read_char(demuxer) >> 1) & 7;  // Only low 4 bits (7==1111) 
		*pts <<= 15;
		*pts |= (mpeg2packet_read_int16(demuxer) >> 1);
		*pts <<= 15;
		*pts |= (mpeg2packet_read_int16(demuxer) >> 1);
		*dts = (mpeg2packet_read_char(demuxer) >> 1) & 7;  // Only low 4 bits (7==1111)
		*dts <<= 15;
		*dts |= (mpeg2packet_read_int16(demuxer) >> 1);
		*dts <<= 15;
		*dts |= (mpeg2packet_read_int16(demuxer) >> 1);
		pes_header_bytes += 10;
		}
	// extract other stuff here! 
  
	mpeg2packet_skip(demuxer, pes_header_data_length - pes_header_bytes);
	return 0;
	}

int get_unknown_data(mpeg2_demuxer_t *demuxer)
	{
	mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
	return 0;
	}

int mpeg2_get_pes_packet_data(mpeg2_demuxer_t *demuxer, unsigned int stream_id)
	{
	unsigned long pts = 0, dts = 0;

	if((stream_id >> 4) == 12 || (stream_id >> 4) == 13)
		{
		// Just pick the first available stream if no ID is set
		if(demuxer->astream == -1)
		    demuxer->astream = (stream_id & 0x0f);

    	if((stream_id & 0x0f) == (unsigned int)demuxer->astream && demuxer->do_audio)
			{
			mpeg2_get_pes_packet_header(demuxer, &pts, &dts);
			demuxer->pes_audio_time = pts;
			demuxer->audio_pid = demuxer->pid;
			return mpeg2packet_get_data_buffer(demuxer);
    		}
		}
	else if((stream_id >> 4)==14)
		{
		// Just pick the first available stream if no ID is set
		if(demuxer->vstream == -1)
			demuxer->vstream = (stream_id & 0x0f);

		if((stream_id & 0x0f) == (unsigned int)demuxer->vstream && demuxer->do_video)
			{
			mpeg2_get_pes_packet_header(demuxer, &pts, &dts);
			demuxer->pes_video_time = pts;
			demuxer->video_pid = demuxer->pid;
			return mpeg2packet_get_data_buffer(demuxer);
			}
		}
	else 
		{
		return get_unknown_data(demuxer);
		}

	mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
	return 0;
	}

int mpeg2_get_pes_packet(mpeg2_demuxer_t *demuxer)
	{
	unsigned int stream_id;

	demuxer->pes_packets++;
	stream_id = mpeg2packet_read_char(demuxer);
	
	// Skip startcode
	mpeg2packet_read_int24(demuxer);

	// Skip pes packet length 
	mpeg2packet_read_int16(demuxer);

	if(stream_id != MPEG2_PRIVATE_STREAM_2 && stream_id != MPEG2_PADDING_STREAM)
		{
		return mpeg2_get_pes_packet_data(demuxer, stream_id);
		}
	else if(stream_id == MPEG2_PRIVATE_STREAM_2)
		{
		// Dump private data! */
		_tprintf(TEXT("stream_id == MPEG2_PRIVATE_STREAM_2\n"));
		mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
		return 0;
		}
	else if(stream_id == MPEG2_PADDING_STREAM)
		{
		mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
		return 0;
		}
   	_tprintf(TEXT("unknown stream_id in pes packet"));
	return 1;
	}

int mpeg2_get_payload(mpeg2_demuxer_t *demuxer)
	{
	if(demuxer->payload_unit_start_indicator)
		{
    	if(demuxer->pid==0) 
				mpeg2_get_program_association_table(demuxer);
    	else if(mpeg2packet_next_int24(demuxer) == MPEG2_PACKET_START_CODE_PREFIX) 
				mpeg2_get_pes_packet(demuxer);
    	else 
			mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
		}
	else
		{
    	if(demuxer->pid == demuxer->audio_pid && demuxer->do_audio)
			{
			mpeg2packet_get_data_buffer(demuxer);
			}
    	else if(demuxer->pid == demuxer->video_pid && demuxer->do_video)
			{
			mpeg2packet_get_data_buffer(demuxer);
			}
    	else 
			mpeg2packet_skip(demuxer, demuxer->raw_size - demuxer->raw_offset);
		}
	return 0;
	}

// Read a transport packet
int mpeg2_read_transport(mpeg2_demuxer_t *demuxer)
	{
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];
	int result = mpeg2io_read_data(demuxer->raw_data, demuxer->packet_size, title->fs);
	unsigned int bits;
	int table_entry;

	demuxer->raw_size = demuxer->packet_size;
	demuxer->raw_offset = 0;
	if(result)
		{
		//perror("mpeg2_read_transport");
		return 1;
		}

	// Sync byte 
	if(mpeg2packet_read_char(demuxer) != MPEG2_SYNC_BYTE)
		{
		_tprintf(TEXT("mpeg2packet_read_char(demuxer) != MPEG2_SYNC_BYTE\n"));
		return 1;
		}

	// 	bits = 	mpeg2packet_read_int24(demuxer) & 0x0000ffff; 
	// 	demuxer->transport_error_indicator = bits >> 15; 
	// 	demuxer->payload_unit_start_indicator = (bits >> 14) & 1; 
	// 	demuxer->pid = bits & 0x00001fff; 
	// 	demuxer->transport_scrambling_control = (mpeg2packet_next_char(demuxer) >> 6) & 0x3; 
	// 	demuxer->adaptation_field_control = (mpeg2packet_next_char(demuxer) >> 4) & 0x3; 
	// 	demuxer->continuity_counter = (mpeg2packet_read_char(demuxer) & 0xf); 

    bits =  mpeg2packet_read_int24(demuxer) & 0x00ffffff;
    demuxer->transport_error_indicator = (bits >> 23) & 0x1;
    demuxer->payload_unit_start_indicator = (bits >> 22) & 0x1;
    demuxer->pid = (bits >> 8) & 0x00001fff;
    demuxer->transport_scrambling_control = (bits >> 6) & 0x3;
    demuxer->adaptation_field_control = (bits >> 4) & 0x3;
    demuxer->continuity_counter = bits & 0xf;

	if(demuxer->transport_error_indicator)
		{
		_tprintf(TEXT("demuxer->transport_error_indicator\n"));
		return 1;
		}
 
    if (demuxer->pid == 0x1fff)
		{
		demuxer->is_padding = 1;  /* padding; just go to next */
		return 0;
		}
	else
		{
		demuxer->is_padding = 0;
		}

	// Get pid
	for(table_entry = 0, result = 0; table_entry < demuxer->total_pids; table_entry++)
		{
		if(demuxer->pid == demuxer->pid_table[table_entry])
			{
			result = 1;
			break;
			}
		}

	// Not in pid table 
	if(!result)
		{
		demuxer->pid_table[table_entry] = demuxer->pid;
		demuxer->continuity_counters[table_entry] = demuxer->continuity_counter;  /* init */
		demuxer->total_pids++;
		}
	result = 0;

	// Check counters
    if(demuxer->pid != MPEG2_PROGRAM_ASSOCIATION_TABLE && 
		demuxer->pid != MPEG2_CONDITIONAL_ACCESS_TABLE &&
        (demuxer->adaptation_field_control == 1 || demuxer->adaptation_field_control == 3))
		{
		if(demuxer->continuity_counters[table_entry] != demuxer->continuity_counter)
			{
			_tprintf(TEXT("demuxer->continuity_counters[table_entry] != demuxer->continuity_counter\n"));
			// Reset it
			demuxer->continuity_counters[table_entry] = demuxer->continuity_counter;
			}
		if(++(demuxer->continuity_counters[table_entry]) > 15) 
			demuxer->continuity_counters[table_entry] = 0;
		}

    if(demuxer->adaptation_field_control == 2 || demuxer->adaptation_field_control == 3)
    	result = mpeg2_get_adaptation_field(demuxer);

    if(demuxer->adaptation_field_control == 1 || demuxer->adaptation_field_control == 3)
    	result = mpeg2_get_payload(demuxer);

	return result;
	}

int mpeg2_get_system_header(mpeg2_demuxer_t *demuxer)
	{
	int length = mpeg2packet_read_int16(demuxer);
	mpeg2packet_skip(demuxer, length);
	return 0;
	}

unsigned long mpeg2_get_timestamp(mpeg2_demuxer_t *demuxer)
	{
	unsigned long timestamp;
	// Only low 4 bits (7==1111)
	timestamp = (mpeg2packet_read_char(demuxer) >> 1) & 7;  
	timestamp <<= 15;
	timestamp |= (mpeg2packet_read_int16(demuxer) >> 1);
	timestamp <<= 15;
	timestamp |= (mpeg2packet_read_int16(demuxer) >> 1);
	return timestamp;
	}

int mpeg2_get_pack_header(mpeg2_demuxer_t *demuxer, unsigned int *header)
	{
	unsigned long i, j;
	unsigned long clock_ref, clock_ref_ext;

	// Get the time code
	if((mpeg2packet_next_char(demuxer) >> 4) == 2)
		{
		// MPEG-1
		demuxer->time = (double)mpeg2_get_timestamp(demuxer) / 90000;
		// Skip 3 bytes
		mpeg2packet_read_int24(demuxer);
		}
	else if(mpeg2packet_next_char(demuxer) & 0x40)
		{
		i = mpeg2packet_read_int32(demuxer);
		j = mpeg2packet_read_int16(demuxer);
		if(i & 0x40000000 || (i >> 28) == 2)
			{
    		clock_ref = ((i & 0x31000000) << 3);
    		clock_ref |= ((i & 0x03fff800) << 4);
    		clock_ref |= ((i & 0x000003ff) << 5);
    		clock_ref |= ((j & 0xf800) >> 11);
    		clock_ref_ext = (j >> 1) & 0x1ff;

   			demuxer->time = (double)(clock_ref + clock_ref_ext / 300) / 90000;
			// Skip 3 bytes
			mpeg2packet_read_int24(demuxer);
			i = mpeg2packet_read_char(demuxer) & 0x7;

			// stuffing
			mpeg2packet_skip(demuxer, i);  
			}
		}
	else
		{
		mpeg2packet_skip(demuxer, 2);
		}

	*header = mpeg2packet_read_int32(demuxer);
	if(*header == MPEG2_SYSTEM_START_CODE)
		{
    	mpeg2_get_system_header(demuxer);
    	*header = mpeg2packet_read_int32(demuxer);
		}
	return 0;
	}

// Program packet reading core
int mpeg2_get_ps_pes_packet(mpeg2_demuxer_t *demuxer, unsigned int *header)
	{
	unsigned long pts = 0, dts = 0;
	int stream_id;
	int pes_packet_length;
	int pes_packet_start;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;

	stream_id = *header & 0xff;
	pes_packet_length = mpeg2packet_read_int16(demuxer);
	pes_packet_start = demuxer->raw_offset;

	if(stream_id != MPEG2_PRIVATE_STREAM_2 && 
		stream_id != MPEG2_PADDING_STREAM)
		{
		if((mpeg2packet_next_char(demuxer) >> 6) == 0x02)
			{
			// Get MPEG-2 packet
			int pes_header_bytes = 0;
			int scrambling = (mpeg2packet_read_char(demuxer) >> 4) & 0x3;
    		int pts_dts_flags = (mpeg2packet_read_char(demuxer) >> 6) & 0x3;
			int pes_header_data_length = mpeg2packet_read_char(demuxer);

			if(scrambling && (demuxer->do_audio || demuxer->do_video))
				{
				// Decrypt it
				if(mpeg2_decrypt_packet(demuxer->titles[demuxer->current_title]->fs->css, 
					demuxer->raw_data))
					{
					_tprintf(TEXT("mpeg2_get_ps_pes_packet: Decryption not available\n"));
					return 1;
					}
				}

			// Get Presentation and Decoding Time Stamps
			if(pts_dts_flags == 2)
				{
				pts = (mpeg2packet_read_char(demuxer) >> 1) & 7;  /* Only low 4 bits (7==1111) */
				pts <<= 15;
				pts |= (mpeg2packet_read_int16(demuxer) >> 1);
				pts <<= 15;
				pts |= (mpeg2packet_read_int16(demuxer) >> 1);
				pes_header_bytes += 5;
				}
    		else if(pts_dts_flags == 3)
				{
        		pts = (mpeg2packet_read_char(demuxer) >> 1) & 7;  /* Only low 4 bits (7==1111) */
        		pts <<= 15;
        		pts |= (mpeg2packet_read_int16(demuxer) >> 1);
        		pts <<= 15;
        		pts |= (mpeg2packet_read_int16(demuxer) >> 1);
        		dts = (mpeg2packet_read_char(demuxer) >> 1) & 7;  /* Only low 4 bits (7==1111) */
        		dts <<= 15;
        		dts |= (mpeg2packet_read_int16(demuxer) >> 1);
        		dts <<= 15;
        		dts |= (mpeg2packet_read_int16(demuxer) >> 1);
        		pes_header_bytes += 10;
    			}

			// Skip unknown */
			mpeg2packet_skip(demuxer, pes_header_data_length - pes_header_bytes);
			}
		else
			{
			int pts_dts_flags;
			// Get MPEG-1 packet
			while(mpeg2packet_next_char(demuxer) == 0xff)
				{
				mpeg2packet_read_char(demuxer);
				}

			// Skip STD buffer scale
			if((mpeg2packet_next_char(demuxer) & 0x40) == 0x40)
				{
				mpeg2packet_skip(demuxer, 2);
				}

			// Decide which timestamps are available
			pts_dts_flags = mpeg2packet_next_char(demuxer);

			if(pts_dts_flags >= 0x30)
				{
				// Get the presentation and decoding time stamp
				pts = mpeg2_get_timestamp(demuxer);
				dts = mpeg2_get_timestamp(demuxer);
				}
			else if(pts_dts_flags >= 0x20)
				{
				// Get just the presentation time stamp
				pts = mpeg2_get_timestamp(demuxer);
				}
			else if(pts_dts_flags == 0x0f)
				{
				// End of timestamps
				mpeg2packet_read_char(demuxer);
				}
			else
				{
				return 1;     // Error
				}
			}

		// Now extract the payload.
		if((stream_id >> 4) == 0xc || (stream_id >> 4) == 0xd)
			{
			// Audio data
			// Take first stream ID if -1
			pes_packet_length -= demuxer->raw_offset - pes_packet_start;
			if(!demuxer->do_audio && !demuxer->do_video)
				demuxer->astream_table[stream_id & 0x0f] = AUDIO_MPEG;
			else if(demuxer->astream == -1) 
				demuxer->astream = stream_id & 0x0f;

			if((stream_id & 0x0f) == demuxer->astream && demuxer->do_audio)
				{
				if(pts) demuxer->pes_audio_time = pts;

				memcpy(&demuxer->data_buffer[demuxer->data_size],
					&demuxer->raw_data[demuxer->raw_offset],
					pes_packet_length);
				demuxer->data_size += pes_packet_length;
				demuxer->raw_offset += pes_packet_length;
		  		}
			else 
				{
    			mpeg2packet_skip(demuxer, pes_packet_length);
				}
			}
    	else if((stream_id >> 4) == 0xe)
			{
			// Video data
			// Take first stream ID if -1
			if(!demuxer->do_audio && !demuxer->do_video) 
				demuxer->vstream_table[stream_id & 0x0f] = 1;
			else if(demuxer->vstream == -1) 
				demuxer->vstream = stream_id & 0x0f;

			pes_packet_length -= demuxer->raw_offset - pes_packet_start;
    	    if((stream_id & 0x0f) == demuxer->vstream && demuxer->do_video)
				{
        		if(pts) demuxer->pes_video_time = pts;

				memcpy(&demuxer->data_buffer[demuxer->data_size], 
					&demuxer->raw_data[demuxer->raw_offset],
					pes_packet_length);
				demuxer->data_size += pes_packet_length;
				demuxer->raw_offset += pes_packet_length;
    	  		}
    		else 
				{
        	    mpeg2packet_skip(demuxer, pes_packet_length);
    			}
    		}
    	else if(stream_id == 0xbd && demuxer->raw_data[demuxer->raw_offset] != 0xff)
			{
			// DVD audio data
			// Get the audio format
			int format;
			if((demuxer->raw_data[demuxer->raw_offset] & 0xf0) == 0xa0)
				format = AUDIO_PCM;
			else
				format = AUDIO_AC3;

			stream_id = demuxer->raw_data[demuxer->raw_offset] - 0x80;

			// Take first stream ID if not building TOC. 
			if(!demuxer->do_audio && !demuxer->do_video)
				demuxer->astream_table[stream_id] = format;
			else if(demuxer->astream == -1)
				demuxer->astream = stream_id;

      		if(stream_id == demuxer->astream && demuxer->do_audio)
				{
				demuxer->aformat = format;
        		if(pts) demuxer->pes_audio_time = pts;
				mpeg2packet_read_int32(demuxer);
				pes_packet_length -= demuxer->raw_offset - pes_packet_start;

				memcpy(&demuxer->data_buffer[demuxer->data_size],
					&demuxer->raw_data[demuxer->raw_offset],
					pes_packet_length);
				demuxer->data_size += pes_packet_length;
				demuxer->raw_offset += pes_packet_length;
      			}
      		else
				{
				pes_packet_length -= demuxer->raw_offset - pes_packet_start;
        	    mpeg2packet_skip(demuxer, pes_packet_length);
      			}
    		}
    	else if(stream_id == 0xbc || 1)
			{
			pes_packet_length -= demuxer->raw_offset - pes_packet_start;
        	mpeg2packet_skip(demuxer, pes_packet_length);
    		}
		}
  	else if(stream_id == MPEG2_PRIVATE_STREAM_2 || stream_id == MPEG2_PADDING_STREAM)
		{
		pes_packet_length -= demuxer->raw_offset - pes_packet_start;
        mpeg2packet_skip(demuxer, pes_packet_length);
  		}

	while(demuxer->raw_offset + 4 < demuxer->raw_size)
		{
		*header = mpeg2packet_read_int32(demuxer);
		if((*header >> 8) != MPEG2_PACKET_START_CODE_PREFIX)
			demuxer->raw_offset -= 3;
		else
			break;
		}

	return 0;
	}

int mpeg2_read_program(mpeg2_demuxer_t *demuxer)
	{
	int result = 0, count = 0;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];
	unsigned int header;
	demuxer->raw_size = demuxer->packet_size;
	demuxer->raw_offset = 0;
	demuxer->data_size = 0;

	// Search backward for it
	header = mpeg2io_read_int32(title->fs);
	result = mpeg2io_eof(title->fs);

	if(!result) result = mpeg2io_seek_relative(title->fs, -4);

	// Search backwards for header
	while(header != MPEG2_PACK_START_CODE && !result && count < demuxer->packet_size)
		{
		result = mpeg2io_seek_relative(title->fs, -1);
		if(!result)
			{
			header >>= 8;
			header |= mpeg2io_read_char(title->fs) << 24;
			result = mpeg2io_seek_relative(title->fs, -1);
			}
		count++;
		}

	if(result)
		{
		// couldn't find MPEG2_PACK_START_CODE
		return 1;
		}

	result = mpeg2io_read_data(demuxer->raw_data, demuxer->packet_size, title->fs);

	if(result)
		{
		//perror("mpeg2_read_program");
		return 1;
		}

	header = mpeg2packet_read_int32(demuxer);
	while(demuxer->raw_offset + 4 < demuxer->raw_size && !result)
		{
		if(header == MPEG2_PACK_START_CODE)
			{
			result = mpeg2_get_pack_header(demuxer, &header);
			}
		else if((header >> 8) == MPEG2_PACKET_START_CODE_PREFIX)
			{
			result = mpeg2_get_ps_pes_packet(demuxer, &header);
			}
		}
	return result;
	}

double mpeg2_lookup_time_offset(mpeg2_demuxer_t *demuxer, long byte)
	{
	int i;
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];

	if(!title->timecode_table_size) return 0;

	for(i = title->timecode_table_size - 1; 
		i >= 0 && title->timecode_table[i].start_byte > byte;
		i--)
		;
	if(i < 0) i = 0;
	return title->timecode_table[i].absolute_start_time - title->timecode_table[i].start_time;
	}

int mpeg2_advance_timecode(mpeg2_demuxer_t *demuxer, int reverse)
	{
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];
	int result = 0;
	int do_seek = 0;

	// Skip timecode advancing when constructing timecode table
	if(!title->timecode_table || 
		!title->timecode_table_size || 
		demuxer->generating_timecode) return 0;

	if(!reverse)
		{
		// Get inside the current timecode
		if(mpeg2io_tell(title->fs) < title->timecode_table[demuxer->current_timecode].start_byte)
			{
			mpeg2io_seek(title->fs, title->timecode_table[demuxer->current_timecode].start_byte);
			}
		
		// Get the next timecode
		while(!result && (mpeg2io_tell(title->fs) >= title->timecode_table[demuxer->current_timecode].end_byte ||
				demuxer->current_program != title->timecode_table[demuxer->current_timecode].program))
			{

			// printf("mpeg2_advance_timecode %d %d %d %d\n", mpeg2io_tell(title->fs), title->timecode_table[demuxer->current_timecode].end_byte,
			//  demuxer->current_program, title->timecode_table[demuxer->current_timecode].program);

			demuxer->current_timecode++;
			if(demuxer->current_timecode >= title->timecode_table_size)
				{
				demuxer->current_timecode = 0;
				if(demuxer->current_title + 1 < demuxer->total_titles)
					{
					mpeg2demux_open_title(demuxer, demuxer->current_title + 1);
					do_seek = 1;
					}
				else
					{
					mpeg2io_seek(title->fs, mpeg2io_total_bytes(title->fs));
			 		result = 1;
					}
				}
			title = demuxer->titles[demuxer->current_title];
			}

		if(!result && do_seek)
			{
			mpeg2io_seek(title->fs, title->timecode_table[demuxer->current_timecode].start_byte);
			}
		}
	else
		{
		// Get the previous timecode */
		while(!result && (mpeg2io_tell(title->fs) < title->timecode_table[demuxer->current_timecode].start_byte ||
				demuxer->current_program != title->timecode_table[demuxer->current_timecode].program))
			{
			// if(demuxer->do_audio) printf("mpeg2_reverse_timecode %d %d %d %d\n", mpeg2io_tell(title->fs), title->timecode_table[demuxer->current_timecode].end_byte,
			// 	demuxer->current_program, title->timecode_table[demuxer->current_timecode].program);

			demuxer->current_timecode--;
			if(demuxer->current_timecode < 0)
				{
				if(demuxer->current_title > 0)
					{
					mpeg2demux_open_title(demuxer, demuxer->current_title - 1);
					title = demuxer->titles[demuxer->current_title];
					demuxer->current_timecode = title->timecode_table_size - 1;
					do_seek = 1;
					}
				else
					{
					mpeg2io_seek(title->fs, 0);
					demuxer->current_timecode = 0;
					result = 1;
					}
				}
			}

		if(!result && do_seek) 
			mpeg2io_seek(title->fs, title->timecode_table[demuxer->current_timecode].start_byte);
		}
	return result;
	}

// Read packet in the forward direction
int mpeg2_read_next_packet(mpeg2_demuxer_t *demuxer)
	{
	int result = 0;
	//long current_position;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];
	demuxer->data_size = 0;
	demuxer->data_position = 0;

	// Flip the file descriptor back to the end of the packet for forward reading
	if(demuxer->reverse)
		{
		result = mpeg2io_seek_relative(title->fs, demuxer->packet_size);
		demuxer->reverse = 0;
		}

	// Read packets until the output buffer is full
	if(!result)
		{
		do	{
			result = mpeg2_advance_timecode(demuxer, 0);

			if(!result)
				{
				demuxer->time_offset = mpeg2_lookup_time_offset(demuxer, mpeg2io_tell(title->fs));

				if(file->is_transport_stream)
					{
					result = mpeg2_read_transport(demuxer);
					}
				else if(file->is_program_stream)
					{
					result = mpeg2_read_program(demuxer);
					}
				else
					{
					// Read elementary stream. 
					result = mpeg2io_read_data(demuxer->data_buffer, demuxer->packet_size, title->fs);
					if(!result) demuxer->data_size = demuxer->packet_size;
					}
				}
			} while(!result && demuxer->data_size == 0 && (demuxer->do_audio || demuxer->do_video));
		}

	return result;
	}

// Read the packet right before the packet we're currently on
int mpeg2_read_prev_packet(mpeg2_demuxer_t *demuxer)
	{
	int result = 0;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;
	//long current_position;
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];

	demuxer->data_size = 0;
	demuxer->data_position = 0;

	do	{
		// Rewind to the start of the packet to be read
		result = mpeg2io_seek_relative(title->fs, -demuxer->packet_size);

		if(!result) result = mpeg2_advance_timecode(demuxer, 1);
		if(!result) demuxer->time_offset = mpeg2_lookup_time_offset(demuxer, mpeg2io_tell(title->fs));

		if(file->is_transport_stream && !result)
			{
			result = mpeg2_read_transport(demuxer);
			if(!mpeg2io_bof(title->fs))
				result = mpeg2io_seek_relative(title->fs, -demuxer->packet_size);
			}
		else if(file->is_program_stream && !result)
			{

			result = mpeg2_read_program(demuxer);
			if(!mpeg2io_bof(title->fs))
			result = mpeg2io_seek_relative(title->fs, -demuxer->packet_size);
			}
		else if(!result)
			{
			// Elementary stream 
			// Read the packet forwards and seek back to the start
			result = mpeg2io_read_data(demuxer->data_buffer, demuxer->packet_size, title->fs);
			if(!result) 
				{
				demuxer->data_size = demuxer->packet_size;
				result = mpeg2io_seek_relative(title->fs, -demuxer->packet_size);
				}
			}
		} while(!result && demuxer->data_size == 0 && (demuxer->do_audio || demuxer->do_video));

	// Remember that the file descriptor is at the beginning of the packet just read
	demuxer->reverse = 1;
	demuxer->error_flag = result;
	return result;
	}


// Used for audio
int mpeg2demux_read_data(mpeg2_demuxer_t *demuxer, unsigned char *output, long size)
	{
	long i;
	int result = 0;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;
	demuxer->error_flag = 0;
	
	if(demuxer->data_position >= 0)
		{
		// Read forwards
		for(i = 0; i < size && !result; )
			{
			int fragment_size = size - i;
			if(fragment_size > demuxer->data_size - demuxer->data_position)
				fragment_size = demuxer->data_size - demuxer->data_position;
			memcpy(output + i, demuxer->data_buffer + demuxer->data_position, fragment_size);
			demuxer->data_position += fragment_size;
			i += fragment_size;

			if(i < size)
				{
				result = mpeg2_read_next_packet(demuxer);
				}
			}
		}
	else
		{
		// Read backwards a full packet. 
		// Only good for reading less than the size of a full packet, but 
		// this routine should only be used for searching for previous markers. 
		long current_position = demuxer->data_position;
		result = mpeg2_read_prev_packet(demuxer);
		if(!result) demuxer->data_position = demuxer->data_size + current_position;
		memcpy(output, demuxer->data_buffer + demuxer->data_position, size);
		demuxer->data_position += size;
		}

	demuxer->error_flag = result;
	return result;
	}

unsigned int mpeg2demux_read_char_packet(mpeg2_demuxer_t *demuxer)
	{
	demuxer->error_flag = 0;
	if(demuxer->data_position >= demuxer->data_size)
		demuxer->error_flag = mpeg2_read_next_packet(demuxer);
	demuxer->next_char = demuxer->data_buffer[demuxer->data_position++];
	return demuxer->next_char;
	}

unsigned int mpeg2demux_read_prev_char_packet(mpeg2_demuxer_t *demuxer)
	{
	demuxer->error_flag = 0;
	demuxer->data_position--;
	if(demuxer->data_position < 0)
		{
		demuxer->error_flag = mpeg2_read_prev_packet(demuxer);
		if(!demuxer->error_flag) demuxer->data_position = demuxer->data_size - 1;
		}
	demuxer->next_char = demuxer->data_buffer[demuxer->data_position];
	return demuxer->next_char;
	}

mpeg2demux_timecode_t* mpeg2_append_timecode(mpeg2_demuxer_t *demuxer, 
		mpeg2_title_t *title, 
		long prev_byte, 
		double prev_time, 
		long next_byte, 
		double next_time,
		int dont_store)
	{
	mpeg2demux_timecode_t *new_table;
	mpeg2demux_timecode_t *new_timecode, *old_timecode;
	long i;

	if(!title->timecode_table || 
		title->timecode_table_allocation <= title->timecode_table_size)
		{
		if(title->timecode_table_allocation == 0) 
			title->timecode_table_allocation = 1;
		else
			title->timecode_table_allocation *= 2;

		new_table = (mpeg2demux_timecode_t *)calloc(1, sizeof(mpeg2demux_timecode_t) * title->timecode_table_allocation);
		if(title->timecode_table)
			{
			for(i = 0; i < title->timecode_table_size; i++)
				{
				new_table[i] = title->timecode_table[i];
				}
			free(title->timecode_table);
			}
		title->timecode_table = new_table;
		}

	if(!dont_store)
		{
		new_timecode = &title->timecode_table[title->timecode_table_size];
		new_timecode->start_byte = next_byte;
		new_timecode->start_time = next_time;
		new_timecode->absolute_start_time = 0;

		if(title->timecode_table_size > 0)
			{
			old_timecode = &title->timecode_table[title->timecode_table_size - 1];
			old_timecode->end_byte = prev_byte;
			old_timecode->end_time = prev_time;
			new_timecode->absolute_start_time = 
				prev_time - 
				old_timecode->start_time + 
				old_timecode->absolute_start_time;
			new_timecode->absolute_end_time = next_time;
			}
		}
	title->timecode_table_size++;
	return new_timecode;
	}

mpeg2demux_timecode_t* mpeg2demux_next_timecode(mpeg2_demuxer_t *demuxer, 
		int *current_title, 
		int *current_timecode,
		int current_program)
	{
	int done = 0;
	while(!done)
		{
		// Increase timecode number
		if(*current_timecode < demuxer->titles[*current_title]->timecode_table_size - 1) 
			{
			(*current_timecode)++;
			if(demuxer->titles[*current_title]->timecode_table[*current_timecode].program == current_program)
				return &(demuxer->titles[*current_title]->timecode_table[*current_timecode]);
			}
		else if(*current_title < demuxer->total_titles - 1)
			{
			// Increase title number 
			(*current_title)++;
			(*current_timecode) = 0;
			if(demuxer->titles[*current_title]->timecode_table[*current_timecode].program == current_program)
				return &(demuxer->titles[*current_title]->timecode_table[*current_timecode]);
			}
		else
			// End of disk
			done = 1;
		}
	return 0;
	}

mpeg2demux_timecode_t* mpeg2demux_prev_timecode(mpeg2_demuxer_t *demuxer, 
		int *current_title, 
		int *current_timecode,
		int current_program)
	{
	int done = 0;
	while(!done)
		{
		// Increase timecode number
		if(*current_timecode > 0)
			{
			(*current_timecode)--;
			if(demuxer->titles[*current_title]->timecode_table[*current_timecode].program == current_program)
				return &(demuxer->titles[*current_title]->timecode_table[*current_timecode]);
			}
		else if(*current_title > 0)
			{
			// Increase title number
			(*current_title)--;
			(*current_timecode) = demuxer->titles[*current_title]->timecode_table_size - 1;
			if(demuxer->titles[*current_title]->timecode_table[*current_timecode].program == current_program)
				return &(demuxer->titles[*current_title]->timecode_table[*current_timecode]);
			}
		else
			// End of disk
			done = 1;
		
		}
	return 0;
	}

int mpeg2demux_open_title(mpeg2_demuxer_t *demuxer, int title_number)
	{
	mpeg2_title_t *title;

	if(title_number < demuxer->total_titles)
		{
		if(demuxer->current_title >= 0)
			{
			mpeg2io_close_file(demuxer->titles[demuxer->current_title]->fs);
			demuxer->current_title = -1;
			}

		title = demuxer->titles[title_number];
		if(mpeg2io_open_file(title->fs))
			{
			demuxer->error_flag = 1;
			//perror("mpeg2demux_open_title");
			}
		else
			{
			demuxer->current_title = title_number;
			}
		}

	demuxer->current_timecode = 0;

	return demuxer->error_flag;
	}

// Assign program numbers to interleaved programs
int mpeg2demux_assign_programs(mpeg2_demuxer_t *demuxer)
	{
	int current_program = 0;
	int current_title = 0;// previous_title;
	int current_timecode = 0;//previous_timecode;
	double current_time;// current_length;
	int done = 0;
	int interleaved = 0;
	mpeg2demux_timecode_t *timecode1;// *timecode2;
	//double program_times[MPEG2_MAX_STREAMS];
	int total_programs = 1;
	int i;
	//int program_exists;
	int last_program_assigned = 0;
	int total_timecodes;
	mpeg2_title_t **titles = demuxer->titles;

	for(i = 0, total_timecodes = 0; i < demuxer->total_titles; i++)
		total_timecodes += demuxer->titles[i]->timecode_table_size;
	
	// Assign absolute timecodes in each program
	for(current_program = 0; 
		current_program < total_programs; 
		current_program++)
		{
		current_time = 0;
		current_title = 0;
		current_timecode = -1;
		while(timecode1 = mpeg2demux_next_timecode(demuxer, 
		    &current_title, 
			&current_timecode, 
			current_program))
			{
			timecode1->absolute_start_time = current_time;
			current_time += timecode1->end_time - timecode1->start_time;
			timecode1->absolute_end_time = current_time;
			}
		}
	//for(i = 0; i < demuxer->total_titles; i++) mpeg2_dump_title(demuxer->titles[i]);
	demuxer->current_program = 0;
	return 0;
	}


///////////////////////////////////////////////////////////////////////
// Entry points

mpeg2_demuxer_t* mpeg2_new_demuxer(mpeg2_t *file, int do_audio, int do_video, int stream_id)
	{
	mpeg2_demuxer_t *demuxer = (mpeg2_demuxer_t *)calloc(1, sizeof(mpeg2_demuxer_t));

	// The demuxer will change the default packet size for its own use
	demuxer->file = file;
	demuxer->packet_size = file->packet_size;
	demuxer->do_audio = do_audio;
	demuxer->do_video = do_video;

	// Allocate buffer + padding
	demuxer->raw_data = (unsigned char*)calloc(1, MPEG2_MAX_PACKSIZE);
	demuxer->data_buffer = (unsigned char*)calloc(1, MPEG2_MAX_PACKSIZE);
	demuxer->data_allocated = MPEG2_MAX_PACKSIZE;
	// System specific variables
	demuxer->audio_pid = stream_id;
	demuxer->video_pid = stream_id;
	demuxer->astream = stream_id;
	demuxer->vstream = stream_id;
	demuxer->current_title = -1;
	return demuxer;
	}

int mpeg2_delete_demuxer(mpeg2_demuxer_t *demuxer)
	{
	int i;

	if(demuxer->current_title >= 0)
		{
		mpeg2io_close_file(demuxer->titles[demuxer->current_title]->fs);
		}

	for(i = 0; i < demuxer->total_titles; i++)
		{
		mpeg2_delete_title(demuxer->titles[i]);
		}

	if(demuxer->data_buffer) free(demuxer->data_buffer);
	free(demuxer->raw_data);
	free(demuxer);
	return 1;
	}

// Create a title
// Build a table of timecodes contained in the program stream
// If toc is 0 just read the first and last timecode
int mpeg2demux_create_title(mpeg2_demuxer_t *demuxer, int timecode_search, FILE *toc)
	{
	int result = 0, done = 0, counter_start, counter;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;
	long next_byte, prev_byte;
	double next_time = 0.0, prev_time = 0.0, absolute_time = 0.0;
	long i;
	mpeg2_title_t *title;
	mpeg2demux_timecode_t *timecode = 0;

	demuxer->error_flag = 0;
	demuxer->generating_timecode = 1;

	// Create a single title
	if(!demuxer->total_titles)
		{
		demuxer->titles[0] = mpeg2_new_title(file, file->fs->path);
		demuxer->total_titles = 1;
		mpeg2demux_open_title(demuxer, 0);
		}
	title = demuxer->titles[0];
	title->total_bytes = mpeg2io_total_bytes(title->fs);


	// Get the packet size from the file
	if(file->is_program_stream)
		{
		//printf("Get the packet size from the file\n");
		mpeg2io_seek(title->fs, 4);
		unsigned long test_header = 0;
		for(i = 0; i < MPEG2_MAX_PACKSIZE && 
			test_header != MPEG2_PACK_START_CODE; i++)
			{
			test_header <<= 8;
			test_header |= mpeg2io_read_char(title->fs);
			}
		if(i < MPEG2_MAX_PACKSIZE) 
			demuxer->packet_size = i;
		mpeg2io_seek(title->fs, 0);
		}
	else
		demuxer->packet_size = file->packet_size;

	// Get timecodes for the title
	if(file->is_transport_stream || file->is_program_stream)
		{
		//printf("Get timecodes for the title\n");
		mpeg2io_seek(title->fs, 0);
		while(!done && !result && !mpeg2io_eof(title->fs))
			{
			next_byte = mpeg2io_tell(title->fs);
			result = mpeg2_read_next_packet(demuxer);
			if(!result)
				{
				next_time = demuxer->time;
				//printf("%f %f\n", prev_time, next_time);
				if(next_time < prev_time || 
					next_time - prev_time > MPEG2_CONTIGUOUS_THRESHOLD ||
					!title->timecode_table_size)
					{
					// Discontinuous
					//printf("Discontinuous\n");
					timecode = mpeg2_append_timecode(demuxer, 
						title, 
						prev_byte, 
						prev_time, 
						next_byte, 
						next_time,
						0);

					//printf("timecode: %ld %ld %f %f\n",
 					//	timecode->start_byte,
 					//	timecode->end_byte,
 					//	timecode->start_time,
 					//	timecode->end_time);

					counter_start = (int)next_time;
					}
				prev_time = next_time;
				prev_byte = next_byte;
				counter = (int)next_time;
				}

			// Just get the first bytes if not building a toc to get the stream ID's
			if(next_byte > 0x100000 && 
				(!timecode_search || !toc)) done = 1;
			}

		// Get the last timecode
		if(!toc || !timecode_search)
			{
			result = mpeg2io_seek(title->fs, title->total_bytes);
			if(!result) result = mpeg2_read_prev_packet(demuxer);
			}

		if(title->timecode_table && timecode)
			{
			timecode->end_byte = title->total_bytes;
			//	timecode->end_byte = mpeg2io_tell(title->fs)//  + demuxer->packet_size ;
			timecode->end_time = demuxer->time;
			timecode->absolute_end_time = timecode->end_time - timecode->start_time;
			}
		}

	mpeg2io_seek(title->fs, 0);
	demuxer->generating_timecode = 0;
	return 0;
	}

int mpeg2demux_print_timecodes(mpeg2_title_t *title, FILE *output)
	{
	mpeg2demux_timecode_t *timecode;
	int i;

	if(title->timecode_table)
		{
		for(i = 0; i < title->timecode_table_size; i++)
			{
			timecode = &title->timecode_table[i];

			_ftprintf(output, TEXT("REGION: %ld %ld %f %f\n"),
				timecode->start_byte,
				timecode->end_byte,
				timecode->start_time,
				timecode->end_time);
			}
		}
	return 0;
	}

// Read the title information from a toc
int mpeg2demux_read_titles(mpeg2_demuxer_t *demuxer)
	{
	TCHAR string1[MPEG2_STRLEN], string2[MPEG2_STRLEN];
	long start_byte, end_byte;
	float start_time, end_time;
	mpeg2_title_t *title = 0;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;

	// Eventually use IFO file to generate titles
	while(!file->fs->fd->is_eof())
		{
		/*
		fscanf(file->fs->fd, "%s %s %ld %f %f %f", 
			string1,
			string2,
			&end_byte, 
			&start_time, 
			&end_time);*/
		_tscanf(TEXT("%s %s %ld %f %f %f"), 
			string1,
			string2,
			&end_byte, 
			&start_time, 
			&end_time);

		if(!strncasecmp(string1, TEXT("PATH:"), 5))
			{
			title = demuxer->titles[demuxer->total_titles++] = mpeg2_new_title(file, string2);

			if(demuxer->current_title < 0)
					mpeg2demux_open_title(demuxer, 0);
			}
		else if(title)
			{
#ifdef UNICODE		
			start_byte = _wtoi(string2);
#else
			start_byte = atol(string2);
#endif
			if(!strcasecmp(string1, TEXT("REGION:")))
				{
				mpeg2_append_timecode(demuxer, 
					title, 
					0, 
					0, 
					0, 
					0,
					1);
				title->timecode_table[title->timecode_table_size - 1].start_byte = start_byte;
				title->timecode_table[title->timecode_table_size - 1].end_byte = end_byte;
				title->timecode_table[title->timecode_table_size - 1].start_time = start_time;
				title->timecode_table[title->timecode_table_size - 1].end_time = end_time;
				}
			else if(!strcasecmp(string1, TEXT("ASTREAM:")))
				demuxer->astream_table[start_byte] = end_byte;
			else if(!strcasecmp(string1, TEXT("VSTREAM:")))
				demuxer->vstream_table[start_byte] = end_byte;
			else if(!strcasecmp(string1, TEXT("SIZE:")))
				title->total_bytes = start_byte;
			else if(!strcasecmp(string1, TEXT("PACKETSIZE:")))
				demuxer->packet_size = start_byte;
			}
		}

	mpeg2demux_assign_programs(demuxer);
	return 0;
	}

int mpeg2demux_copy_titles(mpeg2_demuxer_t *dst, mpeg2_demuxer_t *src)
	{
	long i;
	mpeg2_t *file = (mpeg2_t *)dst->file;
	mpeg2_title_t *dst_title, *src_title;

	dst->packet_size = src->packet_size;
	dst->total_titles = src->total_titles;
	dst->total_programs = src->total_programs;
	for(i = 0; i < MPEG2_MAX_STREAMS; i++)
		{
		dst->astream_table[i] = src->astream_table[i];
		dst->vstream_table[i] = src->vstream_table[i];
		}
	for(i = 0; i < src->total_titles; i++)
		{
		src_title = src->titles[i];
		dst_title = dst->titles[i] = mpeg2_new_title(file, src->titles[i]->fs->path);
		mpeg2_copy_title(dst_title, src_title);
		}

	mpeg2demux_open_title(dst, src->current_title);
	return 0;
	}

int mpeg2demux_print_streams(mpeg2_demuxer_t *demuxer, FILE *toc)
	{
	int i;
	// Print the stream information
	for(i = 0; i < MPEG2_MAX_STREAMS; i++)
		{
		if(demuxer->astream_table[i])
			_ftprintf(toc, TEXT("ASTREAM: %d %d\n"), i, demuxer->astream_table[i]);

		if(demuxer->vstream_table[i])
			_ftprintf(toc, TEXT("VSTREAM: %d %d\n"), i, demuxer->vstream_table[i]);
		}
	return 0;
	}

// Need a timecode table to do this
double mpeg2demux_length(mpeg2_demuxer_t *demuxer)
	{
	mpeg2_title_t *title;
	int i, j;
	//double length;
	for(i = demuxer->total_titles - 1; i >= 0; i--)
		{
		title = demuxer->titles[i];
		for(j = title->timecode_table_size - 1; j >= 0; j--)
			{
			if(title->timecode_table[j].program == demuxer->current_program)
				{
				return title->timecode_table[j].end_time - 
					title->timecode_table[j].start_time + 
					title->timecode_table[j].absolute_start_time;
				}
			}
		}
	return 1;
	}

int mpeg2demux_eof(mpeg2_demuxer_t *demuxer)
	{
	if(demuxer->current_title >= 0)
		{
		if(mpeg2io_eof(demuxer->titles[demuxer->current_title]->fs) &&
			demuxer->current_title >= demuxer->total_titles - 1)
			return 1;
		}
	return 0;
	}

int mpeg2demux_bof(mpeg2_demuxer_t *demuxer)
	{
	if(demuxer->current_title >= 0)
		{
		if(mpeg2io_bof(demuxer->titles[demuxer->current_title]->fs) &&
			demuxer->current_title <= 0)
			return 1;
		}
	return 0;
	}


// For elemental streams seek to a byte
int mpeg2demux_seek_byte(mpeg2_demuxer_t *demuxer, long byte)
	{
	long current_position;
	mpeg2_t *file = (mpeg2_t *)demuxer->file;
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];
	
	demuxer->data_position = 0;
	demuxer->data_size = 0;

	demuxer->error_flag = mpeg2io_seek(title->fs, byte);

	if(!demuxer->error_flag && (file->is_transport_stream || file->is_program_stream))
		{
		// Get on a packet boundary only for system streams
		current_position = mpeg2io_tell(title->fs);
		if(byte % demuxer->packet_size)
			{
			demuxer->error_flag |= mpeg2io_seek(title->fs, current_position - (current_position % demuxer->packet_size));
			}
		}
	return demuxer->error_flag;
	}

// For programs streams and toc seek to a time
int mpeg2demux_seek_time(mpeg2_demuxer_t *demuxer, double new_time)
	{
	int i, j, done = 0, result = 0;
	double byte_offset, new_byte_offset;
	double guess = 0, minimum = 65535;
	mpeg2_title_t *title;
	mpeg2demux_timecode_t *timecode;

	demuxer->error_flag = 0;

	i = 0;
	j = 0;
	title = demuxer->titles[i];
	timecode = &title->timecode_table[j];

	// Get the title and timecode of the new position
	while(!demuxer->error_flag &&
		!(timecode->absolute_start_time <= new_time &&
		timecode->absolute_end_time > new_time &&
		timecode->program == demuxer->current_program))
		{
		// Next timecode
		j++;
		if(j >= title->timecode_table_size)
			{
			i++;
			j = 0;
			if(i >= demuxer->total_titles)
				{
				demuxer->error_flag = 1;
				return 1;
				}
			else
				{
				mpeg2demux_open_title(demuxer, i);
				}
			}
		title = demuxer->titles[i];
		timecode = &title->timecode_table[j];
		}

	// Guess the new byte position
	demuxer->current_timecode = j;

	byte_offset = ((new_time - timecode->absolute_start_time) /
		(timecode->absolute_end_time - timecode->absolute_start_time) *
		(timecode->end_byte - timecode->start_byte) +
		timecode->start_byte);
	//printf("mpeg2demux_seek_time %f %f\n", new_time, byte_offset);

	while(!done && !result && byte_offset >= 0)
		{
		result = mpeg2demux_seek_byte(demuxer, (long)byte_offset);
		//printf("seek_time 0 byte %.0f want %f result %d\n", byte_offset, new_time, result); 

		if(!result)
			{
			result = mpeg2_read_next_packet(demuxer);
			// printf("seek_time 1 guess %f want %f\n", guess, new_time); 
			guess = demuxer->time + demuxer->time_offset;

			if(fabs(new_time - guess) >= fabs(minimum)) done = 1;
			else
				{
				minimum = guess - new_time;
				new_byte_offset = byte_offset + ((new_time - guess) / 
					(timecode->end_time - timecode->start_time) *
					(timecode->end_byte - timecode->start_byte));
				if(labs((long)new_byte_offset - (long)byte_offset) < demuxer->packet_size) done = 1;
				byte_offset = new_byte_offset;
				}
			}
		}

	// Get one packet before the packet just read
	if(!result && byte_offset > demuxer->packet_size && minimum > 0)
		{
		mpeg2_read_prev_packet(demuxer);
		mpeg2_read_prev_packet(demuxer);
		}
	//printf("seek_time %d %d %d\n", demuxer->current_title, demuxer->current_timecode, mpeg2demux_tell(demuxer));
	demuxer->error_flag = result;
	return result;
	}

int mpeg2demux_seek_percentage(mpeg2_demuxer_t *demuxer, double percentage)
	{
	double total_bytes = 0;
	double absolute_position;
	long relative_position;
	int i, new_title;
	mpeg2_title_t *title;

	demuxer->error_flag = 0;

	// Get the absolute byte position
	for(i = 0; i < demuxer->total_titles; i++)
		total_bytes += demuxer->titles[i]->total_bytes;

	absolute_position = percentage * total_bytes;

	// Get the title the byte is inside
	for(new_title = 0, total_bytes = 0; new_title < demuxer->total_titles; new_title++)
		{
		total_bytes += demuxer->titles[new_title]->total_bytes;
		if(absolute_position < total_bytes) break;
		}

	if(new_title >= demuxer->total_titles)
		{
		new_title = demuxer->total_titles - 1;
		}

	// Got a title
	title = demuxer->titles[new_title];
	total_bytes -= title->total_bytes;
	relative_position = (long)(absolute_position - total_bytes);

	// Get the timecode the byte is inside
	for(demuxer->current_timecode = 0; 
		demuxer->current_timecode < title->timecode_table_size; 
		demuxer->current_timecode++)
		{
		if(title->timecode_table[demuxer->current_timecode].start_byte <= relative_position &&
			title->timecode_table[demuxer->current_timecode].end_byte > relative_position)
			{
			break;
			}
		}

	if(demuxer->current_timecode >= title->timecode_table_size)
		demuxer->current_timecode = title->timecode_table_size - 1;

	// Get the nearest timecode in the same program
	while(demuxer->current_timecode < title->timecode_table_size - 1 &&
			title->timecode_table[demuxer->current_timecode].program != demuxer->current_program)
		{
		demuxer->current_timecode++;
		}

	// Open the new title and seek to the correct byte
	if(new_title != demuxer->current_title)
		{
		demuxer->error_flag = mpeg2demux_open_title(demuxer, new_title);
		}

	if(!demuxer->error_flag)
		demuxer->error_flag = mpeg2io_seek(title->fs, relative_position);

	return demuxer->error_flag;
	}

double mpeg2demux_tell_percentage(mpeg2_demuxer_t *demuxer)
	{
	double total_bytes = 0;
	double position = 0;
	int i;

	demuxer->error_flag = 0;
	position = mpeg2io_tell(demuxer->titles[demuxer->current_title]->fs);
	for(i = 0; i < demuxer->total_titles; i++)
		{
		if(i == demuxer->current_title)
			{
			position += total_bytes;
			}
		total_bytes += demuxer->titles[i]->total_bytes;
		}
	return position / total_bytes;
	}

double mpeg2demux_get_time(mpeg2_demuxer_t *demuxer)
	{
	return demuxer->time;
	}

long mpeg2demux_tell(mpeg2_demuxer_t *demuxer)
	{
	return mpeg2io_tell(demuxer->titles[demuxer->current_title]->fs);
	}

long mpeg2demuxer_total_bytes(mpeg2_demuxer_t *demuxer)
	{
	mpeg2_title_t *title = demuxer->titles[demuxer->current_title];
	return title->total_bytes;
	}

mpeg2_demuxer_t* mpeg2_get_demuxer(mpeg2_t *file)
	{
	if(file->is_program_stream || file->is_transport_stream)
		{
		if(file->has_audio) 
			return file->atrack[0]->demuxer;
		else if(file->has_video) 
			return file->vtrack[0]->demuxer;
		}
	return 0;
	}
