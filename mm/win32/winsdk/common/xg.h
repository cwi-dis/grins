#ifndef INC_XG
#define INC_XG

#include <stdexcept>

typedef unsigned char uchar_t;
typedef unsigned char* uchar_ptr;

typedef unsigned short uint16_t;
typedef unsigned long uint32_t;

typedef uint32_t color_t;

// color_encoding classification
struct color_encoding
	{
	size_t size;
	size_t red_shift;
	size_t red_mask;
	size_t green_shift;
	size_t green_mask;
	size_t blue_shift;
	size_t blue_mask;
	};

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

	// traits
	static color_encoding& get_encoding() 
		{ 
		static color_encoding e = {24, 0, 8, 8, 8, 16, 8};
		return e;
		}
	static size_t get_bits_size() { return 24;} 
	};

inline bool operator==(const trible &lhs, const trible &rhs)
	{return lhs.r == rhs.r && lhs.g == rhs.g && lhs.b == rhs.g;}
inline bool operator!=(const trible &lhs, const trible &rhs)
	{return lhs.r != rhs.r || lhs.g != rhs.g || lhs.b != rhs.b;}

struct rtrible
	{
	uchar_t r;
	uchar_t g;
	uchar_t b;
	};

//////////////
struct trible565
	{
	uint16_t v;

	trible565() : v(0) {}
	trible565(int _r, int _g, int _b) 
		{
		color_t rgb = (_b << 16) | (_g << 8) | _r ;
        v = (uint16_t)((rgb & 0xf80000)>> 8); 
        v |= (uint16_t)(rgb & 0xfc00) >> 5; 
        v |= (uint16_t)(rgb & 0xf8) >> 3;  
		}
	trible565(uchar_t _r, uchar_t _g, uchar_t _b)
		{
		color_t rgb = (_b << 16) | (_g << 8) | _r ;
        v = (uint16_t)((rgb & 0xf80000)>> 8); // red
        v |= (uint16_t)(rgb & 0xfc00) >> 5; // green
        v |= (uint16_t)(rgb & 0xf8) >> 3; // blue 
		}
	
	trible565(color_t rgb) 
		{
        v = (uint16_t)((rgb & 0xf80000) >> 8); 
        v |= (uint16_t)(rgb & 0xfc00) >> 5; 
        v |= (uint16_t)(rgb & 0xf8) >> 3;  
		}
	
	trible565(const rgbquad& q) 
		{
		color_t rgb = (q.b << 16)| (q.g << 8) | q.r ;
        v = (uint16_t)((rgb & 0xf80000) >> 8); 
        v |= (uint16_t)(rgb & 0xfc00) >> 5; 
        v |= (uint16_t)(rgb & 0xf8) >> 3;  
		}
	
	BYTE blue() { return (v & 0xf800) >> 8;}
	BYTE green() { return (v & 0x7e0) >> 2;}
	BYTE red() { return (v & 0x1f) << 3;}

	// traits
	static color_encoding& get_encoding() 
		{ 
		static color_encoding e = {16, 0, 5, 5, 6, 11, 5};
		return e;
		}
	static size_t get_bits_size() { return 16;} 
	};

inline bool operator==(const trible565 &lhs, const trible565 &rhs)
	{return lhs.v == rhs.v;}
inline bool operator!=(const trible565 &lhs, const trible565 &rhs)
	{return lhs.v != rhs.v;}


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


// surface classification (see imgformat python module for concept)
struct surf_format
	{
	color_encoding encoding;
	size_t align;
	bool bottom2top;
	};

// windows bitmaps default pitch
template <class T>
size_t get_pitch(size_t width) { return (width*sizeof(T)+3) & ~3;}

inline size_t get_pitch_from_bpp(size_t bpp, size_t width) { return (width*(bpp/8)+3) & ~3;}



// default color representation
typedef le::trible color_repr_t;



// each pixel is of type T
// pixel coordinates increase from left to right (x) and from top to bottom (y)
// some functions imply color as an argument, this is of type T (i.e pixel)

template<class T>
class surface
	{
	public:
	typedef T value_type;

	typedef T* pointer;
	typedef const T* const_pointer;

	typedef T& reference;
	typedef const T& const_reference;

	surface(size_t w, size_t h)
		: _width(w), _height(h), _data(new T[w*h]) 
		{
		}

	surface(size_t w, size_t h, value_type bkcolor)
		: _width(w), _height(h), _data(new T[w*h]) 
		{
		fill(bkcolor);
		}

	surface(size_t w, size_t h, const_pointer buffer)
		: _width(w), _height(h), _data(new T[w*h]) 
		{
		memcpy(_data, buffer, w*h*sizeof(T));
		}

	surface(const surface& other)
	:	_width(other.get_width()), _height(other.get_height()), _data(new T[other.size()])
		{
		memcpy(_data, other.get_cdata(), other.memsize());
		}

	const surface& operator=(const surface& other)
		{
		if(&other != this)
			{
			if(other.size() != size())
				{
				delete[] _data;
				_data = new T[other.size()];
				}
			_width = other.get_width();
			_height = other.get_height();
			memcpy(_data, other.get_cdata(), other.memsize());
			}
		return *this;
		}

	~surface(){delete[] _data;}

	void fill(value_type bkcolor) 
		{
		if(bkcolor == 0)
			memset(_data, 0, _width*_height*sizeof(T));
		else
			{
			pointer ptr = _data;
			pointer end = ptr + _width*_height;
			while(ptr != end) *ptr++ = bkcolor;
			}
		}

	bool save_as_bmp(const char *pszFilename) const;

	reference operator[](size_t pos) {return _data[pos];}
	const_reference operator[](size_t pos) const {return _data[pos];}

	reference pixel(size_t x, size_t y) { 
		if(x>=_width || y>=_height)
			throw std::range_error("index out of range");
		return _data[x+_width*y];
		}
	const_reference pixel(size_t x, size_t y) const
		{ 
		return const_reference(reference(pixel(x,y)));
		}

	value_type set_pixel(size_t x, size_t y, T v) 
		{reference r =_data[x+_width*y]; value_type t = r; r = v; return t;}
	value_type get_pixel(size_t x, size_t y) const 
		{return _data[x+_width*y];}

	size_t get_width() const {return _width;}
	size_t get_height() const {return _height;}
	size_t size() const {return _width*_height;}
	size_t memsize() const {return _width*_height*sizeof(value_type);}

	const_pointer get_cdata() const {return _data;}
	pointer get_row(size_t row) const 
		{
		if(row>=_height) throw std::range_error("index out of range"); 
		return _data+_width*row;
		}

	private:
	size_t _width;
	size_t _height;
	pointer _data;
	};

typedef surface<long> xsurface;


// packed structure
#ifdef WIN32
#include <pshpack2.h>
#endif
struct bitmap_file_header 
	{
	uint16_t bfType;
	uint32_t bfSize;
	uint16_t bfReserved1;
	uint16_t bfReserved2;
	uint32_t bfOffBits;
	};
#ifdef WIN32
#include <poppack.h>
#endif

struct bitmap_info_header
	{
    uint32_t biSize;
    long  biWidth;
    long biHeight;
    uint16_t biPlanes;
    uint16_t biBitCount;
	uint32_t biCompression;
	uint32_t biSizeImage;
	long biXPelsPerMeter;
	long biYPelsPerMeter;
	uint32_t biClrUsed;
	uint32_t biClrImportant;
	};

template<class T>
bool surface<T>::save_as_bmp(const char *pszFilename) const
	{
	bitmap_file_header filehdr;
	memset(&filehdr, 0, sizeof(bitmap_file_header));
	*((char*)&filehdr.bfType) = 'B';
	*(((char*)&filehdr.bfType)+1) = 'M';
	filehdr.bfOffBits = sizeof(bitmap_file_header) + sizeof(bitmap_info_header);
	
	bitmap_info_header infohdr;
	memset(&infohdr, 0, sizeof(bitmap_info_header));
	infohdr.biSize = sizeof(bitmap_info_header);
	infohdr.biWidth    = _width;
	infohdr.biHeight   = _height;
	infohdr.biPlanes   = 1;
	infohdr.biBitCount = 24;
	infohdr.biCompression = 0; // == BI_RGB;
	infohdr.biSizeImage = 0;
	infohdr.biClrUsed = 0;

	FILE* fp = fopen(pszFilename, "wb");
	if(fp == NULL) return false;

	fwrite(&filehdr, sizeof(bitmap_file_header), 1, fp);
	fwrite(&infohdr, sizeof(bitmap_info_header), 1, fp);

	int pitch = (_width*3+3) & ~3;
	le::trible* bmpbuffer = new le::trible[_width+1];
	le::trible* p = bmpbuffer+_width;
	p->b = p->g = p->r = 0;

	for (int row=_height-1;row>=0;row--)
		{
		pointer ptr = _data + row*_width;
		le::trible* buf = bmpbuffer;
		for(size_t col=0;col<_width;col++)
			{
			le::rtrible *p = (le::rtrible*)ptr;
			buf->r = p->r;
			buf->g = p->g;
			buf->b = p->b;
			ptr++;
			buf++;
			}
		fwrite(bmpbuffer, 1, pitch, fp);
		}
	fclose(fp);
	return true;
	}

#endif

