#ifndef INC_XG
#define INC_XG

//  (C) Copyright Kleanthis Kleanthous 2001.  
//  Permission to copy, use, modify, sell and distribute this software
//  is granted provided this copyright notice appears in all copies.  

namespace xg {

typedef unsigned long color_t;
typedef unsigned char uchar_t;
typedef unsigned short ushort_t;
typedef unsigned long ulong_t;

struct trible
	{
	uchar_t b;
	uchar_t g;
	uchar_t r;
	};

struct rtrible
	{
	uchar_t r;
	uchar_t g;
	uchar_t b;
	};

struct quad
	{
	uchar_t r;
	uchar_t g;
	uchar_t b;
	uchar_t a;
	};

template <class T>
inline color_t rgbc(T r, T g, T b)
	{return ((color_t)(((uchar_t)(r)|((ushort_t)((uchar_t)(g))<<8))|(((color_t)(uchar_t)(b))<<16)));}
inline uchar_t redc(color_t rgb) {return ((uchar_t)(rgb));}
inline uchar_t green(color_t rgb) {return ((uchar_t)(((ushort_t)(rgb)) >> 8));}
inline uchar_t bluec(color_t rgb) {return ((uchar_t)((rgb)>>16));}

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
		pointer ptr = _data;
		pointer end = ptr + w * h;
		while(ptr != end) *ptr++ = bkcolor;
		}

	surface(size_t w, size_t h, const_pointer buffer)
		: _width(w), _height(h), _data(new T[w*h]) 
		{
		memcpy(_data, buffer, w*h*sizeof(T));
		}

	surface(const surface& other)
		: _width(other.get_width()), _height(other.get_height()), _pixelmap(new pixel_t[other.size()])
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
		pointer ptr = _data;
		pointer end = ptr + size();
		while(ptr != end) *ptr++ = bkcolor;
		}

	bool save_as_bmp(const char *pszFilename) const;

	reference operator[](size_t pos) {return _data[pos];}
	const_reference operator[](size_t pos) const {return _data[pos];}

	reference pixel(size_t x, size_t y) {
		if(x>=_width || y>=_height) throw "index out of range"; 
		return _data[x+_width*y];
		}
	const_reference pixel(size_t x, size_t y) const {return (const_reference)at(x, y);}

	value_type set_pixel(size_t x, size_t y, T v) {reference r =_data[x+_width*y]; value_type t = r; r = v; return t;}
	value_type get_pixel(size_t x, size_t y) const {return _data[x+_width*y];}

	size_t get_width() const {return _width;}
	size_t get_height() const {return _height;}
	size_t size() const {return _width*_height;}
	size_t memsize() const {return _width*_height*sizeof(value_type);}
	const_pointer get_cdata() const {return _data;}
	const_pointer get_crow(size_t row) const 
		{
		if(row>=_height) throw "index out of range"; 
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
	ushort_t bfType;
	ulong_t bfSize;
	ushort_t bfReserved1;
	ushort_t bfReserved2;
	ulong_t bfOffBits;
	};
#ifdef WIN32
#include <poppack.h>
#endif

struct bitmap_info_header
	{
    ulong_t biSize;
    long  biWidth;
    long biHeight;
    ushort_t biPlanes;
    ushort_t biBitCount;
	ulong_t biCompression;
	ulong_t biSizeImage;
	long biXPelsPerMeter;
	long biYPelsPerMeter;
	ulong_t biClrUsed;
	ulong_t biClrImportant;
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
	infohdr.biCompression = 0; // BI_RGB;
	infohdr.biSizeImage = 0;
	infohdr.biClrUsed = 0;

	FILE* fp = fopen(pszFilename, "wb");
	if(fp == NULL) return false;

	fwrite(&filehdr, sizeof(bitmap_file_header), 1, fp);
	fwrite(&infohdr, sizeof(bitmap_info_header), 1, fp);

	int pitch = (_width*3+3) & ~3;
	trible* bmpbuffer = new trible[_width+1];
	trible* p = bmpbuffer+_width;
	p->b = p->g = p->r = 0;
	for (int row=_height-1;row>=0;row--)
		{
		pointer ptr = _data + row*_width;
		trible* buf = bmpbuffer;
		for (size_t col=0;col<_width;col++)
			{
			rtrible *p = (rtrible*)ptr;
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

} // namespace xg

#endif

