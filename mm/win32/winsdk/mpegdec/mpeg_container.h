#ifndef INC_MPEG_CONTAINER
#define INC_MPEG_CONTAINER

#ifndef INC_MPEG2DEF
#include "mpeg2def.h"
#endif

#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <string>

class mpeg_input_stream;

class mpeg_container
	{
	public:

	mpeg_container();
	~mpeg_container();

	bool open(const TCHAR *path);
	void close();

	bool has_audio() const { return m_pmpeg2->has_audio != 0;}
	bool has_video() const { return m_pmpeg2->has_video != 0;}
	
	bool has_audio_stream(int stream) const 
		{ return m_pmpeg2->has_audio != 0 && stream < m_pmpeg2->total_astreams;}
	bool has_video_stream(int stream) const 
		{ return m_pmpeg2->has_video != 0 && stream < m_pmpeg2->total_vstreams;}

	int get_audio_streams_size() const { return m_pmpeg2->total_astreams;}
	int get_audio_channels(int stream = 0) const 
		{ return has_audio_stream(stream)?m_pmpeg2->atrack[stream]->channels:0;}
	int get_audio_samples(int stream = 0) const 
		{ return has_audio_stream(stream)?m_pmpeg2->atrack[stream]->total_samples:0;}
	int get_sample_rate(int stream = 0) const 
		{ return has_audio_stream(stream)?m_pmpeg2->atrack[stream]->sample_rate:0;}
	int get_audio_current_position(int stream = 0) const 
		{ return has_audio_stream(stream)?m_pmpeg2->atrack[stream]->current_position:0;}

	int get_video_streams_size() const { return m_pmpeg2->total_vstreams;}
	int get_video_frames(int stream = 0) const 
		{ return has_video_stream(stream)?m_pmpeg2->vtrack[stream]->total_frames:0;}
	int get_video_width(int stream = 0) const 
		{ return has_video_stream(stream)?m_pmpeg2->vtrack[stream]->width:0;}
	int get_video_height(int stream = 0) const 
		{ return has_video_stream(stream)?m_pmpeg2->vtrack[stream]->height:0;}
	double get_frame_rate(int stream = 0) const 
		{ return has_video_stream(stream)?m_pmpeg2->vtrack[stream]->frame_rate:0;}
	
	long read_audio(short *output, long samples, int stream = 0, int channel = 0);
	void read_audio(std::basic_string<char>& audio_data, int stream = 0, int channel = 0);

	protected:
	bool read_toc();

	private:
	mpeg2_t *m_pmpeg2;
	};

#endif  // INC_MPEG_CONTAINER

