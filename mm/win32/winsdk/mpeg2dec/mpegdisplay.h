
/*************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#ifndef INC_MPEGDISPLAY
#define INC_MPEGDISPLAY

#ifndef INC_MTSYNC
#include "../common/mtsync.h"
#endif

#ifndef INC_SURFACE
#include "../common/surface.h"
#endif

struct display_info
	{
	int horizontal_size, vertical_size;
	int chroma_format;
	int coded_picture_width, coded_picture_height;
	bool mpeg2_flag;
	bool progressive_frame;
	int matrix_coefficients;
	double frame_rate;
	};

class MpegDisplay
	{
	public:
	typedef unsigned char uchar_t;

	MpegDisplay(const display_info& di);	
	~MpegDisplay();

	void set_surface(surface<color_repr_t> *surf) { m_surf = surf;}
	void update_surface(uchar_t *src[], int frame, int offset,int incr, int vsteps);
	void set_direct_update_box(int x, int y, int w, int h) { m_dx=x; m_dy=y; m_dw=w; m_dh=h;}

	void lock() { m_cs.enter();}
	void unlock() { m_cs.leave();}

	private:
	void init_display(int chroma, int width, int height);
	void conv422to444(uchar_t *src, uchar_t *dst);
	void conv420to422(uchar_t *src, uchar_t *dst);
	
	const display_info& m_di;
	uchar_t *u422, *v422, *u444, *v444;
	surface<color_repr_t> *m_surf;
	critical_section m_cs;
	int m_dx, m_dy, m_dw, m_dh;
	};

#endif // INC_MPEGDISPLAY