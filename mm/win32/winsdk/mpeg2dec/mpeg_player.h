
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_MPEGPLAYER
#define INC_MPEGPLAYER

#ifndef INC_VIDEO
#include "../common/video.h"
#endif

#ifndef INC_SURFACE
#include "../common/surface.h"
#endif

class MpegDecoder;
class MpegDisplay;
struct display_info;
class VideoThread;

class MpegPlayer : public VideoPlayer
	{
	public:
	MpegPlayer();
	virtual ~MpegPlayer();
	virtual bool can_decode(int handle);
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
	MpegDecoder *decoder;
	MpegDisplay *display;
	display_info *di;
	VideoThread *pVideoThread;
	};

#endif // INC_MPEGPLAYER