#ifndef INC_SURFACE
#define INC_SURFACE

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


// type T properties
// operator=(const& T)
// operator=(const& rgbquadT)
// T(int r, int g, int b) family
// operator==(const trible &lhs, const trible &rhs)

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
		if(y>=m_height) return 0; // throw_range_error();
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
				value_type& tfrom = pfrom[x];
				value_type& tto = pto[x];
				ptr[x] = value_type(
					blend(weight, tfrom.red(), tto.red()),
					blend(weight, tfrom.green(), tto.green()),
					blend(weight, tfrom.blue(), tto.blue()));
				}
			}
		}

	void copy_transparent(surface<T> *from, uchar_ptr rgb, int from_dx = 0, int from_dy = 0)
		{
		value_type transp(rgb[0], rgb[1], rgb[2]);
		for (int y=m_height-1;y>=0;y--)
			{
			pointer ptr = get_row(y);
			surface<T>::pointer pfrom = from->get_row(from_dy + y);
			if(pfrom == 0) break;
			for(size_t x=0;x<m_width;x++)
				{
				value_type& tfrom = pfrom[from_dx + x];
				if(tfrom != transp)
					ptr[x] = tfrom;
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
