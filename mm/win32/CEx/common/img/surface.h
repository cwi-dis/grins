
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_SURFACE
#define INC_SURFACE


#ifndef INC_EXTRA_TYPES
#include "extra_types.h"
#endif

// 5-5-5 bit field (BITMAPINFOHEADER.biCompression = BI_BITFIELDS)
// least significant 5 bits is blue followed by 5 bits of green and 5 bits of red
// The most significant bit is not used.
const uint16_t rgbbf_mask =  0x1F;
const uint16_t blue_mask =  rgbbf_mask;
const uint16_t green_mask = rgbbf_mask << 5; // 0x3E0
const uint16_t red_mask = rgbbf_mask << 10; // 0x7C00
const float rgbbf_scale = 8.25806451f;
struct rgbbf
	{
	uint16_t rgb;

	rgbbf() : rgb(0) {}

	rgbbf(uchar_t _r, uchar_t _g, uchar_t _b) 
	:	rgb(uint16_t(_b/rgbbf_scale) & uint16_t(_g/rgbbf_scale) << 5 & uint16_t(_r/rgbbf_scale)) {}
	rgbbf(int _r, int _g, int _b) 
	:	rgb(uint16_t(uchar_t(_b)/rgbbf_scale) & (uint16_t(uchar_t(_g)/rgbbf_scale) << 5) & (uint16_t(uchar_t(_r)/rgbbf_scale) << 10)) {}

	rgbbf(color_t rgb)
	:	rgb(uint16_t(le::bluec(rgb)/rgbbf_scale) & (uint16_t(le::greenc(rgb)/rgbbf_scale) << 5) & (uint16_t(le::redc(rgb)/rgbbf_scale) << 10)) {}

	BYTE blue() { return BYTE((rgb & blue_mask)*rgbbf_scale);}
	BYTE green() { return BYTE(((rgb & green_mask) >> 5)*rgbbf_scale);}
	BYTE red() { return BYTE(((rgb & red_mask) >> 10)*rgbbf_scale);}
	};

// surface classification (see imgformat python module)
struct surf_format
	{
	uint32_t compression;
	bool bottom2top;
	size_t size;
	size_t align;
	size_t rshift;
	size_t rmask;
	size_t gshift;
	size_t gmask;
	size_t bshift;
	size_t bmask;

	enum {SF_RGB, SF_RGB_PALETTE, SF_BITFIELDS};
	};

const surf_format rgb32 = {surf_format::SF_RGB, true, 32, 32, 16, 8, 8, 8, 0, 8};
const surf_format rgb24 = {surf_format::SF_RGB, true, 24, 32, 16, 8, 8, 8, 0, 8};
const surf_format rgb16 = {surf_format::SF_BITFIELDS, true, 16, 32, 10, 5, 5, 5, 0, 5};
const surf_format rgb8 =  {surf_format::SF_RGB_PALETTE, true, 8,  32, 16, 8, 8, 8, 0, 8};
const surf_format rgb4 =  {surf_format::SF_RGB_PALETTE, true, 4,  32, 16, 8, 8, 8, 0, 8};
const surf_format rgb1 =  {surf_format::SF_RGB_PALETTE, true, 1,  32, 16, 8, 8, 8, 0, 8};

template <class T>
size_t get_pitch(size_t width) { return (width*sizeof(T)+3) & ~3;}

inline size_t get_pitch_from_bpp(size_t bpp) { return (((bpp + 31) / 32) * 4);}

template<class T>
class surface
	{
	public:
	typedef T value_type;

	typedef T* pointer;
	typedef const T* const_pointer;

	typedef T& reference;
	typedef const T& const_reference;


	surface(size_t width, size_t height, size_t depth, pointer data)
		: m_width(width), m_height(height), m_depth(depth), m_pitch((width*sizeof(T)+3) & ~3), m_data(data) 
		{
		}
	~surface() {}

	void fill(value_type bkcolor) 
		{
		uchar_ptr pb = uchar_ptr(m_data);
		for (int y=m_height-1;y>=0;y--)
			{
			pointer ptr = pointer(pb);
			for(size_t x=0;x<m_width;x++)
				*ptr++ = bkcolor;
			pb += m_pitch;
			}
		}

	reference pixel(size_t x, size_t y) { 
		if(x>=m_width || y>=m_height) throw_range_error();
		uchar_ptr pb = uchar_ptr(m_data) + (m_height - 1 - y)*m_pitch;
		pointer ptr = pointer(pb);
		return  ptr[x];
		}

	const_reference pixel(size_t x, size_t y) const
		{ 
		return pixel(x,y);
		}

	value_type set_pixel(size_t x, size_t y, T v) 
		{
		reference r = pixel(x, y); 
		value_type t = r; r = v; 
		return t;
		}

	value_type get_pixel(size_t x, size_t y) const 
		{return pixel(x, y);}

	pointer get_row(size_t y) 
		{
		//if(y>=m_height) throw_range_error();
		uchar_ptr pb = uchar_ptr(m_data) + (m_height - 1 - y)*m_pitch;
		return pointer(pb);
		}

	size_t get_width() const {return m_width;}
	size_t get_height() const {return m_height;}
	size_t get_depth() const {return m_depth;}

	uchar_ptr get_buffer() {return uchar_ptr(m_data);}
	
	// argument is a surface with palette
	template <class rgbquadT>
	void fill(surface<uchar_t>& surf, rgbquadT *pquad, int n) 
		{
		for (int y=m_height-1;y>=0;y--)
			{
			pointer ptr = get_row(y);
			surface<uchar_t>::const_pointer pc = surf.get_row(y);
			for(size_t x=0;x<m_width;x++)
				{
				int cix = pc[x];
				if(cix < n) ptr[x] = pquad[cix];
				else ptr[x] = 0;
				}
			}
		}

	void blend(surface<T>& from, surface<T>& to, double prop)
		{
		prop = prop<0.0?0.0:(prop>1.0?1.0:prop);
		int weight = int(prop*256.0+0.5);
		for (int y=m_height-1;y>=0;y--)
			{
			pointer ptr = get_row(y);
			surface<T>::pointer pfrom = from.get_row(y);
			surface<T>::pointer pto = to.get_row(y);
			for(size_t x=0;x<m_width;x++)
				{
				le::trible& tfrom = pfrom[x];
				le::trible& tto = pto[x];
				ptr[x] = le::trible(
					blend(weight, tfrom.red(), tto.red()),
					blend(weight, tfrom.green(), tto.green()),
					blend(weight, tfrom.blue(), tto.blue()));
				}
			}
		}

	private:
	uchar_t blend(int w, uchar_t c1, uchar_t c2)
		{
		return (uchar_t)(c1==c2)?c1:(c1 + w*(c2-c1)/256);
		}

	void throw_range_error()
		{
		#ifdef STD_CPP
		throw std::range_error("index out of range");
		#else
		//throw "index out of range";
		#endif
		}

	size_t m_width;
	size_t m_height;
	size_t m_depth;
	size_t m_pitch;
	pointer m_data;
	};

#endif
