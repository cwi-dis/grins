
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
	};

class MpegDisplay
	{
	public:
	typedef unsigned char uchar_t;

	MpegDisplay(const display_info& di);	
	~MpegDisplay();

	void update_surface(uchar_t *src[], int frame, int offset,int incr, int vsteps);

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
	};



#endif // INC_MPEGDISPLAY