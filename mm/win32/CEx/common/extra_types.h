
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_EXTRA_TYPES
#define INC_EXTRA_TYPES

#ifndef INC_STDENV
#include "stdenv.h"
#endif

typedef void (*v_callback_v)();

typedef std::pair<std::string, std::string> raw_attr_t;
typedef std::list<raw_attr_t> raw_attr_list_t;
typedef std::map<std::string, std::string> raw_attr_map_t;

typedef unsigned char uchar_t;
typedef unsigned char* uchar_ptr;

typedef unsigned short uint16_t;
typedef unsigned long uint32_t;

typedef uint32_t color_t;

// little-endian color representation
namespace le {

inline uchar_t redc(color_t rgb) {return uchar_t(rgb & 0xFF);}
inline uchar_t greenc(color_t rgb) {return uchar_t((rgb >> 8) & 0xFF);}
inline uchar_t bluec(color_t rgb) {return uchar_t((rgb >> 16) & 0xFF);}

template <class T>
inline color_t rgbc(T r, T g, T b)
	{return ((color_t)(((uchar_t)(r)|((color_t)((uchar_t)(g))<<8))|(((color_t)(uchar_t)(b))<<16)));}

struct rgbquad
	{
	uchar_t b;
	uchar_t g;
	uchar_t r;
	uchar_t a;
	};

struct trible
	{
	uchar_t b;
	uchar_t g;
	uchar_t r;

	trible() : b(0), g(0), r(0) {}
	trible(int _r, int _g, int _b) : b(_b), g(_g), r(_r) {}
	trible(uchar_t _r, uchar_t _g, uchar_t _b) : b(_b), g(_g), r(_r) {}
	
	trible(color_t rgb) : b(bluec(rgb)), g(greenc(rgb)), r(redc(rgb)) {}
	
	trible(const rgbquad& q) : b(q.b), g(q.g), r(q.r) {}
	
	BYTE blue() { return b;}
	BYTE green() { return g;}
	BYTE red() { return r;}
	};

} // namespace le (little-endian color representation)

// big-endian color representation
namespace be {

struct rgbquad
	{
	uchar_t a;
	uchar_t r;
	uchar_t g;
	uchar_t b;
	};

struct trible
	{
	uchar_t r;
	uchar_t g;
	uchar_t b;
	};

} // namespace be (big-endian color representation)



#endif // INC_EXTRA_TYPES
