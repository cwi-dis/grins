#ifndef INC_VIDEO
#define INC_VIDEO

#ifndef INC_SURFACE
#include "surface.h"
#endif

class VideoPlayer
	{
	public:
	virtual ~VideoPlayer() {}
	virtual bool can_decode(int handle) = 0;
	virtual void close() = 0;
	virtual int get_width() const = 0;
	virtual int get_height() const = 0;
	virtual double get_duration() const = 0;
	virtual void prepare_playback(surface<color_repr_t> *psurf) = 0;
	virtual void suspend_playback() = 0;
	virtual void resume_playback() = 0;
	virtual bool finished_playback() = 0;
	virtual void lock_surface() = 0;
	virtual void unlock_surface() = 0;
	};

#endif // INC_VIDEO