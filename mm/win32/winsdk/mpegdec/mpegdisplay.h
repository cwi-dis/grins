
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_MPEGDISPLAY
#define INC_MPEGDISPLAY

#ifndef INC_MPEG_VIDEO_DISPLAY
#include "mpeg_video_display.h"
#endif

#ifndef INC_MTSYNC
#include "../common/mtsync.h"
#endif

#ifdef _WIN32_WCE

// _WIN32_WCE
#ifndef INC_SURFACE
#include "../common/surface.h"
#endif

#else 

// _WIN32
#ifndef INC_XG
#include "../common/xg.h"
#endif

#endif // _WIN32_WCE

class MpegDisplay : public mpeg_video_display
	{
	public:
	typedef unsigned char uchar_t;

	MpegDisplay(const display_info& di);	
	~MpegDisplay();

	virtual void set_direct_update_box(int x, int y, int w, int h) { m_dx=x; m_dy=y; m_dw=w; m_dh=h;}
	virtual void update_surface(uchar_t *src[], int frame, int offset,int incr, int vsteps);
	virtual void lock() { m_cs.enter();}
	virtual void unlock() { m_cs.leave();}
	
	void set_surface(surface<color_repr_t> *surf) { m_surf = surf;}

	private:
	void init_display(int chroma, int width, int height);
	void conv422to444(uchar_t *src, uchar_t *dst);
	void conv420to422(uchar_t *src, uchar_t *dst);
	void copy_surf();

	const display_info& m_di;
	uchar_t *u422, *v422, *u444, *v444;
	surface<color_repr_t> *m_surf;
	critical_section m_cs;
	int m_dx, m_dy, m_dw, m_dh;
	};

#endif // INC_MPEGDISPLAY