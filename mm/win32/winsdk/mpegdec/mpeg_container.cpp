#include "mpeg_container.h"

#include "streams/mpeg2demux.h"
#include "streams/mpeg2io.h"
#include "audio/mpeg2audio.h"
//#include "video/mpeg2video.h"


#include <stdlib.h>
#include <memory.h>

///////////////
// open platform input stream
#include "wnds_mpeg_input_stream.h"

mpeg_input_stream *open_mpeg_input_stream(TCHAR *path)
	{
	//_tprintf(TEXT("open_mpeg_input_stream\n"));
	wnds_mpeg_input_stream *p = new wnds_mpeg_input_stream(path);
	if(p != NULL && !p->is_valid())
		{
		delete p;
		p = NULL;
		}
	return p;
	}


///////////////
mpeg_container::mpeg_container() 
:	m_pmpeg2(0)
	{
	}

mpeg_container::~mpeg_container()
	{
	close();
	}

bool mpeg_container::open(const TCHAR *path)
	{
	// Initialize the file structure
	m_pmpeg2 = new mpeg2_t;
	memset(m_pmpeg2, 0, sizeof(mpeg2_t));
	m_pmpeg2->fs = mpeg2_new_fs((TCHAR *)path);
	m_pmpeg2->demuxer = mpeg2_new_demuxer(m_pmpeg2, 0, 0, -1);
	m_pmpeg2->cpus = 1;

	// Need to perform authentication before reading a single byte
	if(mpeg2io_open_file(m_pmpeg2->fs))
		{
		close();
		return false;
		}

	// ============= Create the title objects ================== 

	unsigned int bits = mpeg2io_read_int32(m_pmpeg2->fs);

	if(bits == MPEG2_TOC_PREFIX || bits == MPEG2_TOC_PREFIXLOWER) 
		{
		if(bits == MPEG2_TOC_PREFIX) printf("MPEG2_TOC_PREFIX\n");
		else if(bits == MPEG2_TOC_PREFIXLOWER) printf("MPEG2_TOC_PREFIXLOWER\n");
		// Table of contents for another file
		if(!read_toc())
			{
			close();
			return false;
			}
		mpeg2io_close_file(m_pmpeg2->fs);
		}
	else if(((bits >> 24) & 0xff) == MPEG2_SYNC_BYTE)
		{
		// Transport stream
		//printf("Transport stream\n");
		m_pmpeg2->packet_size = MPEG2_TS_PACKET_SIZE;
		m_pmpeg2->is_transport_stream = 1;
		}
	else if(bits == MPEG2_PACK_START_CODE)
		{
		// *** Program stream
		//printf("Program stream\n");
		m_pmpeg2->packet_size = MPEG2_DVD_PACKET_SIZE;
		m_pmpeg2->is_program_stream = 1;
		}
	else if((bits & 0xfff00000) == 0xfff00000 ||
		((bits >> 8) == MPEG2_ID3_PREFIX) ||
		(bits == MPEG2_RIFF_CODE))
		{
		// MPEG Audio only
		//printf("MPEG Audio only\n");
		m_pmpeg2->packet_size = MPEG2_DVD_PACKET_SIZE;
		m_pmpeg2->has_audio = 1;
		m_pmpeg2->is_audio_stream = 1;
		}
	else if(bits == MPEG2_SEQUENCE_START_CODE ||
		bits == MPEG2_PICTURE_START_CODE)
		{
		// Video only
		//printf("Video only\n");
		m_pmpeg2->packet_size = MPEG2_DVD_PACKET_SIZE;
		m_pmpeg2->is_video_stream = 1;
		}
	else if(((bits & 0xffff0000) >> 16) == MPEG2_AC3_START_CODE)
		{
		// AC3 Audio only
		//printf("AC3 Audio only\n");
		m_pmpeg2->packet_size = MPEG2_DVD_PACKET_SIZE;
		m_pmpeg2->has_audio = 1;
		m_pmpeg2->is_audio_stream = 1;
		}
	else
		{
		close();
		fprintf(stderr, "mpeg2_open: not an MPEG 2 stream\n");
		return false;
		}

	// Create title 
	if(!m_pmpeg2->demuxer->total_titles)
		{
		mpeg2demux_create_title(m_pmpeg2->demuxer, 0, 0);
		}

	//  ====== Get title information =====================
	
	if(m_pmpeg2->is_transport_stream || m_pmpeg2->is_program_stream)
		{
		//printf("Create audio and video tracks\n");
		/*
		// Create video tracks
		// Video must be created before audio because audio uses the video timecode to get its length
		for(int i = 0; i < MPEG2_MAX_STREAMS; i++)
			{
			if(m_pmpeg2->demuxer->vstream_table[i])
				{
				printf("Create video track %d\n", i);
				m_pmpeg2->vtrack[m_pmpeg2->total_vstreams] = mpeg2_new_vtrack(m_pmpeg2, i, m_pmpeg2->demuxer);
				if(m_pmpeg2->vtrack[m_pmpeg2->total_vstreams]) m_pmpeg2->total_vstreams++;
				}
			}
		*/
		// Create audio tracks
		for(int i = 0; i < MPEG2_MAX_STREAMS; i++)
			{
			if(m_pmpeg2->demuxer->astream_table[i])
				{
				//printf("Create audio track %d\n", i);
				m_pmpeg2->atrack[m_pmpeg2->total_astreams] = 
					mpeg2_new_atrack(m_pmpeg2, i, m_pmpeg2->demuxer->astream_table[i], m_pmpeg2->demuxer);
				if(m_pmpeg2->atrack[m_pmpeg2->total_astreams]) m_pmpeg2->total_astreams++;
				}
			}
		}
	else if(m_pmpeg2->is_video_stream)
		{
		//printf("Create video track\n");
		// Create video tracks
		//m_pmpeg2->vtrack[0] = mpeg2_new_vtrack(m_pmpeg2, -1, m_pmpeg2->demuxer);
		//if(m_pmpeg2->vtrack[0]) m_pmpeg2->total_vstreams++;
		}
	else if(m_pmpeg2->is_audio_stream)
		{
		//printf("Create audio track\n");
		// Create audio tracks
		m_pmpeg2->atrack[0] = mpeg2_new_atrack(m_pmpeg2, -1, AUDIO_UNKNOWN, m_pmpeg2->demuxer);
		if(m_pmpeg2->atrack[0]) m_pmpeg2->total_astreams++;
		}

	if(m_pmpeg2->total_vstreams) m_pmpeg2->has_video = 1;
	if(m_pmpeg2->total_astreams) m_pmpeg2->has_audio = 1;
	mpeg2io_close_file(m_pmpeg2->fs);
	return true;
	}



void mpeg_container::close()
	{
	if(m_pmpeg2 != 0) 
		{
		//for(int i = 0; i < m_pmpeg2->total_vstreams; i++)
		//	mpeg2_delete_vtrack(m_pmpeg2, m_pmpeg2->vtrack[i]);

		for(int i = 0; i < m_pmpeg2->total_astreams; i++)
			mpeg2_delete_atrack(m_pmpeg2, m_pmpeg2->atrack[i]);

		mpeg2_delete_fs(m_pmpeg2->fs);
		mpeg2_delete_demuxer(m_pmpeg2->demuxer);
		delete m_pmpeg2;
		m_pmpeg2 = 0;
		}
	}

bool mpeg_container::read_toc()
	{
	return true;
	}

long mpeg_container::read_audio(short *output, long samples, int stream, int channel)
	{
	if(!m_pmpeg2->has_audio) return 0;
	long writelen = 0;
	bool res = mpeg2audio_decode_audio(m_pmpeg2->atrack[stream]->audio, 
		NULL, output, channel, 
		m_pmpeg2->atrack[stream]->current_position, samples, &writelen);
	if(!res) return 0;
	m_pmpeg2->last_type_read = 1;
	m_pmpeg2->last_stream_read = stream;
	m_pmpeg2->atrack[stream]->current_position += writelen;
	return writelen;
	}

void mpeg_container::read_audio(std::basic_string<char>& audio_data, int stream, int channel)
	{
	if(!m_pmpeg2->has_audio) return;
	audio_data.reserve(m_pmpeg2->atrack[stream]->total_samples+8*1024);
	int samples = 8*1024;
	short *output = new short[samples];
	while(true)
		{
		long n = read_audio(output, samples, stream, channel);
		if(n == 0) break;
		audio_data.append((char*)output, (char*)(output + n));
#ifdef _WIN32_WCE
		if(audio_data.length()>512000) break;
#endif
		}
	delete[] output;
	}
