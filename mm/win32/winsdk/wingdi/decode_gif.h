#ifndef INC_DECODE_GIF
#define INC_DECODE_GIF

#ifndef INC_MEMFILE
#include "../common/memfile.h"
#endif

#ifndef INC_SURFACE
#include "surface.h"
#endif

#ifndef INC_PARSE_I
#include "decode_i.h"
#endif

class GifDecoder : public ImgDecoder
	{
	public:
	GifDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef);
	
	virtual ~GifDecoder();
	virtual bool can_decode();
	virtual DIBSurf *decode();
	
	virtual bool is_transparent() 
		{ return m_transparent>=0;}
	virtual void get_transparent_color(BYTE *rgb)
		{
		if(m_transparent>=0)
			{
			le::rgbquad& t = m_palette[m_transparent];
			rgb[0] = t.r;
			rgb[1] = t.g;
			rgb[2] = t.b;
			}
		}

	private:
	void parse_metadata();
	void parse_image();
	bool parse_image_pixels(int width, int height, int interlace);

	int next_block(UCHAR *m_buf);
	int next_code(int code_size, bool flag);
	int next_lzwbyte(bool flag, int input_code_size);
	void skip_block();
	int get_data_block(UCHAR *buf);

	UINT to_uint(UCHAR a, UCHAR b) { return (b<<8) | a;}

	DIBSurf *m_pdibsurf;
	le::rgbquad *m_palette;
	int m_scr_width;
	int m_scr_height;
	int m_scr_colors;

	int m_transparent;
	int m_delayTime;
	int m_inputFlag;
	int m_disposal;

	int m_curbit, m_lastbit, m_lastbyte;
	bool m_done;
	int m_last_block_size;
	UCHAR m_buf[280];

	enum {MAX_LZW_BITS = 12};
	};

inline GifDecoder::GifDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef)
:	ImgDecoder(mf, hDC, ef), 
	m_pdibsurf(NULL), m_palette(NULL),
	m_curbit(0), m_lastbit(0), m_lastbyte(0),
	m_last_block_size(-1), m_done(false),
	m_transparent(-1)
	{
	}

inline GifDecoder::~GifDecoder()
	{
	if(m_palette != NULL)
		delete[] m_palette;
	}

inline bool GifDecoder::can_decode()
	{
	m_mf.seekg(0);
	uchar_t b[16];
	if(!m_mf.safe_read(b, 6)) return false;
    return b[0] == 'G' && b[1] == 'I' && b[2] == 'F' && b[3] == '8' &&
		(b[4] == '7' || b[4] == '9') && b[5] == 'a';
	}

inline DIBSurf* GifDecoder::decode()
	{
	if(!can_decode()) return NULL;

	m_scr_width = m_mf.get_be_ushort();
	m_scr_height = m_mf.get_be_ushort();
	
	uchar_t uch = m_mf.get_byte();
	m_scr_colors = 2 << (uch & 0x07);
	int screen_color_res = ((uch & 0x70) >> 3) + 1;

	int screen_bg = m_mf.get_byte();
	int screen_aspect_ration = m_mf.get_byte();

	if(m_palette != NULL)
		{
		delete[] m_palette;
		m_palette = NULL;
		}
    if((uch & 0x80) == 0x80)
		{
		//cout << "reading global color map" << endl;
		m_palette = new le::rgbquad[m_scr_colors];
		memset(m_palette, 0, m_scr_colors*sizeof(le::rgbquad));
		for(int i=0; i<m_scr_colors;i++)
			{
			uchar_t rgb[3];
			if(!m_mf.safe_read(rgb, 3)) break;
			m_palette[i].a = 0;
			m_palette[i].r = rgb[0];
			m_palette[i].g = rgb[1];
			m_palette[i].b = rgb[2];
			}
		}
	parse_metadata();
	//cout << m_mf.size() << " bytes remaining" << endl;
	return m_pdibsurf;
	}

inline void GifDecoder::parse_metadata()
	{
	UCHAR ext_buf[256];
	while(true) 
		{
		uchar_t blockType = m_mf.get_byte();
		if(blockType == 0x2c) 
			{ 
			//cout << "Image Descriptor" << endl;
			parse_image();
			return;
			}
		else if (blockType == 0x21)
			{
			//cout << "Extension block" << endl;
			uchar_t label = m_mf.get_byte();
			if (label == 0xf9) 
				{ 
 				//cout << "Graphics Control Extension" << endl;
				if(get_data_block(ext_buf)>0)
					{
					m_disposal= (ext_buf[0]>>2)	& 0x7;
					m_inputFlag	= (ext_buf[0]>>1) & 0x1;
					m_delayTime	= to_uint(ext_buf[1], ext_buf[2]);
					if((ext_buf[0] & 0x1) != 0)
						m_transparent = ext_buf[3];
					}
				skip_block();
				} 
			else if (label == 0x1) 
				{ 
 				//cout << "Plain text extension" << endl;
				skip_block();
				}
			else if (label == 0xfe) 
				{ 
  				//cout << "Comment extension" << endl;
				skip_block();
				}
			else if (label == 0xff) 
				{ 
  				//cout << "Application extension" << endl;
				skip_block();
				}
			else 
				{ 
    			//cout << "Unknown extension" << endl;
				skip_block();
				}
			}
		else 
			{
			;//throw "unknown blockType";
			}
		} 
	}

inline void GifDecoder::skip_block()
	{
	int length = 0;
	do	{
		length = m_mf.get_byte();
		m_mf.skip(length);
		} while (length > 0);
	}

inline int GifDecoder::get_data_block(UCHAR *buf)
	{
	int length = m_mf.get_byte();
	if(m_mf.read(buf, length) != length)
		return -1;
	return length;
	}

// 9 bytes header + color_map + data
inline void GifDecoder::parse_image()
	{
	uint16_t imageLeftPosition = m_mf.get_be_ushort();
	uint16_t imageTopPosition = m_mf.get_be_ushort();
    uint16_t imageWidth = m_mf.get_be_ushort();
    uint16_t imageHeight = m_mf.get_be_ushort();

	uchar_t packedFields = m_mf.get_byte();
    bool localColorTableFlag = (packedFields & 0x80) != 0;
    bool interlaceFlag = (packedFields & 0x40) != 0;
    bool sortFlag = (packedFields & 0x20) != 0;
    int numLCTEntries = 1 << ((packedFields & 0x7) + 1);
	if(localColorTableFlag)
		{
		// read color table
		// numLCTEntries colors
		//cout << "has local color table" << endl;
		m_mf.skip(numLCTEntries*3);
		}
	//else cout << "uses global color table" << endl;
	//cout << "ImageDescription: " << imageWidth << "x" << imageHeight << endl;

	color_repr_t *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo(imageWidth, imageHeight, color_repr_t::get_bits_size());
	HBITMAP hBmp = CreateDIBSection(NULL, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		{
		return;
		}
	surface<color_repr_t> *psurf = new surface<color_repr_t>(imageWidth, imageHeight, color_repr_t::get_bits_size(), pBits);
	m_pdibsurf = new DIBSurf(hBmp, psurf);
	parse_image_pixels(imageWidth, imageHeight, interlaceFlag);
	uchar_t img_terminator = m_mf.get_byte(); // read ';'
	//cout << "image" << char(img_terminator) << endl;
	}

inline int GifDecoder::next_block(UCHAR *buf)
	{
	UCHAR count = m_mf.get_byte();
	m_last_block_size = count;
	m_mf.read(buf, count);
	return count;
	}

inline int GifDecoder::next_code(int code_size, bool flag)
	{
	int i,j;
	UCHAR count;

	if(flag) 
		{
		m_curbit=0;
		m_lastbit=0;
		m_done = false;
		return 0;
		}

	if ((m_curbit+code_size) >= m_lastbit) 
		{
		if (m_done) 
			{
			if (m_curbit >= m_lastbit) 
				{
				//throw "Ran off the end of bits";
				return 0;
				}
			return -1;
			}
		m_buf[0] = m_buf[m_lastbyte-2];	
		m_buf[1] = m_buf[m_lastbyte-1];

		count = next_block(&m_buf[2]);
		if(count == 0) m_done = true;

		m_lastbyte = 2 + count;

		m_curbit = (m_curbit - m_lastbit) + 16;

		m_lastbit = (2 + count) * 8;
		}

	int ret=0;
	for (i=m_curbit,j=0; j<code_size;++i,++j)
		ret |= ((m_buf[i/8]&(1<<(i% 8)))!=0)<<j;
	m_curbit += code_size;
	return ret;
	}

inline int GifDecoder::next_lzwbyte(bool flag, int input_code_size)
	{
	static bool fresh = false;
	int code, incode;
	static int code_size, set_code_size;
	static int max_code, max_code_size;
	static int firstcode, oldcode;
	static int clear_code, end_code;

	static unsigned short  next[1 << MAX_LZW_BITS];
	static UCHAR  vals[1 << MAX_LZW_BITS];
	static UCHAR  stack[1 << (MAX_LZW_BITS+1)];
	static UCHAR  *sp;
	
	int i;

	if (flag) 
		{
		set_code_size = input_code_size;
		code_size = set_code_size + 1;
		clear_code = 1 << set_code_size;
		end_code = clear_code + 1;
		max_code = clear_code+2;
		max_code_size = 2*clear_code;

		next_code(0, true);

		fresh = TRUE;
	
		for(i=0;i<clear_code;++i) 
			{
			next[i]=0;
			vals[i]=i;
			}

		for (;i<(1<<MAX_LZW_BITS);++i)
			next[i]=vals[0]=0;
	
		sp=stack;

		return 0;
		} 
	else if (fresh) 
		{
		fresh = false;
		do	{
			firstcode = oldcode = next_code(code_size, false);
			} while (firstcode == clear_code);
		return firstcode;
		}

	if (sp > stack)
		return *--sp;

	while ((code = next_code(code_size, false)) >=0) 
		{
		if (code == clear_code) 
			{
			for (i=0;i<clear_code;++i) 
				{
				next[i]=0;
				vals[i]=i;
				}
			for (;i<(1<<MAX_LZW_BITS);++i)	
				next[i] = vals[i] = 0;
			code_size = set_code_size + 1;
			max_code_size = 2*clear_code;
			max_code = clear_code+2;
			sp = stack;
			firstcode = oldcode = next_code(code_size, false);
			return firstcode;
			} 
		else if (code == end_code) 
			{
			int count;
			UCHAR m_buf[260];
		
			if (m_last_block_size == 0)
				return -2;
			
			while ((count = next_block(m_buf)) >0);

			if (count != 0)
				return -2;	
			}

		incode = code;

		if (code >= max_code) 
			{
			*sp++=firstcode;
			code=oldcode;
			}

		while (code >=clear_code) 
			{
			*sp++=vals[code];
			if (code==(int)next[code]) 
				{
				//throw "Circular table entry";
				return -1;
				}
			code=next[code];
			}

		*sp++ = firstcode=vals[code];

		if ((code=max_code) <(1<<MAX_LZW_BITS)) 
			{
			next[code]=oldcode;
			vals[code]=firstcode;
			++max_code;
			if ((max_code >=max_code_size) &&
				(max_code_size < (1<<MAX_LZW_BITS))) 
				{
				 max_code_size*=2;
				++code_size;
				}
			}

		oldcode = incode;

		if (sp > stack)
			return *--sp;
		}
	return code;
	}   


inline bool GifDecoder::parse_image_pixels(int width, int height, int interlace)
	{
	surface<color_repr_t> *psurf = m_pdibsurf->get_pixmap();
	UCHAR c = m_mf.get_byte();
	int color;
	int xpos=0, ypos=0, pass=0;

	if (next_lzwbyte(true, c) < 0) 
		{
		return false;
		}
	
	while( (color = next_lzwbyte(false, c)) >= 0) 
		{
		color_repr_t rgb(m_palette[color]);
		psurf->set_pixel(xpos, ypos, rgb);
		++xpos;
		if(xpos==width) 
			{
			xpos=0;
			if (interlace) 
				{
				switch(pass) 
					{
					case 0:
					case 1: ypos+=8; break;
					case 2: ypos+=4; break;
					case 3: ypos+=2; break;
					}

				if (ypos>=height) 
					{
					++pass;
					switch (pass) 
						{
						case 1: ypos=4;break;
						case 2: ypos=2;break;
						case 3: ypos=1;break;
						default : goto fini;
						}
					}
				} 
			else 
				{
				++ypos;
				}
			}
		if (ypos >= height)
			break;
		}

	fini:
	if (next_lzwbyte(false, c)>=0) 
		{
		}
	return true;
	}

#endif // INC_DECODE_GIF