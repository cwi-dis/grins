#ifndef INC_VIDEO
#define INC_VIDEO

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

class VideoPlayer
	{
	public:
	virtual ~VideoPlayer() {}
	virtual bool set_input_stream(mpeg_input_stream *in_stream) = 0;
	virtual void close() = 0;
	virtual int get_width() const = 0;
	virtual int get_height() const = 0;
	virtual double get_duration() = 0;
	virtual void prepare_playback(surface<color_repr_t> *psurf) = 0;
	virtual void suspend_playback() = 0;
	virtual void resume_playback() = 0;
	virtual bool finished_playback() = 0;
	virtual void lock_surface() = 0;
	virtual void unlock_surface() = 0;
	virtual void set_direct_update_box(int x, int y, int w, int h) = 0;
	virtual double get_frame_rate() const = 0;
	virtual double get_bit_rate() const = 0;
	};

#endif // INC_VIDEO