
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_MPEGPLAYER
#define INC_MPEGPLAYER

#ifndef INC_VIDEO
#include "../common/video.h"
#endif

#ifdef _WIN32_WCE

// _WIN32_WCE defined
#ifndef INC_SURFACE
#include "../common/surface.h"
#endif

#else 

// _WIN32
#ifndef INC_XG
#include "../common/xg.h"
#endif

#endif // _WIN32_WCE


class mpeg_input_stream;
class mpeg_video_bitstream;
class mpeg_video;
class mpeg_video_display;
struct display_info;
class video_thread;
class wave_out_device;

class mpeg_player : public VideoPlayer
	{
	public:
	mpeg_player();
	virtual ~mpeg_player();
	virtual bool set_input_stream(mpeg_input_stream *in_stream);
	virtual bool set_audio_input_stream(mpeg_input_stream *in_stream);
	virtual void close();
	virtual int get_width() const;
	virtual int get_height() const;
	virtual double get_duration();
	virtual void prepare_playback(surface<color_repr_t> *psurf);
	virtual void suspend_playback();
	virtual void resume_playback();
	virtual bool finished_playback();
	virtual void lock_surface();
	virtual void unlock_surface();
	virtual void set_direct_update_box(int x, int y, int w, int h);
	virtual double get_frame_rate() const;
	virtual double get_bit_rate() const;

	private:
	mpeg_input_stream *pinstream;
	mpeg_video_bitstream *pvbitstream;
	mpeg_video *decoder;
	mpeg_video_display *display;
	display_info *di;
	video_thread *pVideoThread;
	wave_out_device *pwavout;
	};

#endif // INC_MPEGPLAYER