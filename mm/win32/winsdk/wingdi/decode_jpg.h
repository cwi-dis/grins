#ifndef INC_DECODE_JPG
#define INC_DECODE_JPG

#ifndef INC_MEMFILE
#include "../common/memfile.h"
#endif

#ifndef INC_SURFACE
#include "surface.h"
#endif

#ifndef INC_PARSE_I
#include "decode_i.h"
#endif

#ifndef JPEGLIB_H
// avoid macro redefinition warning
#undef HAVE_STDDEF_H
#undef HAVE_STDLIB_H
extern "C" {
#include "../../../../lib-src/jpeg/jpeglib.h"
}
#endif

class JpgDecoder : public ImgDecoder
	{
	public:
	typedef unsigned int JDIMENSION;
	typedef unsigned char JSAMPLE;
	typedef JSAMPLE* JSAMPROW;	
	typedef JSAMPROW* JSAMPARRAY;

	JpgDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef);
	virtual ~JpgDecoder();

	virtual bool can_decode();
	virtual DIBSurf* decode();

	private:
	void write_pixel_rows(j_decompress_ptr cinfo, surface<color_repr_t> *psurf);
	
	void create_buffer(int row_width);
	void free_buffer();

	JSAMPARRAY m_dbuffer;
	JDIMENSION m_dbuffer_height;
	JDIMENSION m_cur_output_row;
	};

inline JpgDecoder::JpgDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef)
:	ImgDecoder(mf, hDC, ef), 
	m_dbuffer(0), m_dbuffer_height(1),
	m_cur_output_row(0)
	{
	}

inline JpgDecoder::~JpgDecoder()
	{
	if(m_dbuffer != 0) free_buffer();
	}

inline void JpgDecoder::create_buffer(int row_width)
	{
	if(m_dbuffer != 0) free_buffer();
	m_dbuffer = new JSAMPROW[m_dbuffer_height];
	for(JDIMENSION i=0;i<m_dbuffer_height;i++)
		m_dbuffer[i] = new JSAMPLE[row_width];
	}

inline void JpgDecoder::free_buffer()
	{
	if(m_dbuffer != 0)
		{
		for(JDIMENSION i=0;i<m_dbuffer_height;i++)
			delete[] m_dbuffer[i];
		delete[] m_dbuffer;
		m_dbuffer = 0;
		}
	}

inline bool JpgDecoder::can_decode()
	{
	m_mf.seekg(0);
    uchar_t b1 = m_mf.get_byte();
    uchar_t b2 = m_mf.get_byte();
    if((b1 == 0xFF) && (b2 == 0xD8))
		return true;
	return false;
	}
inline DIBSurf* JpgDecoder::decode()
	{
	jpeg_decompress_struct cinfo;
	jpeg_error_mgr jerr;

	// Initialize the JPEG decompression object with default error handling.
	cinfo.err = jpeg_std_error(&jerr);
	jpeg_create_decompress(&cinfo);

	// Specify data source for decompression
	file_reader fr(m_mf);
	jpeg_stdio_src(&cinfo, &fr);

	// Read file header, set default decompression parameters
	int res = jpeg_read_header(&cinfo, TRUE);

	// Calculate output image dimensions so we can allocate space
	jpeg_calc_output_dimensions(&cinfo);
	
	// Start decompressor
	jpeg_start_decompress(&cinfo);
		
	JDIMENSION row_width = cinfo.output_width * cinfo.output_components;
	
	// release/create buffer
	if(m_dbuffer != 0) free_buffer();
	create_buffer(row_width);

	int width = cinfo.output_width;
	int height = cinfo.output_height;

	// create a bmp surface
	color_repr_t *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo(width, height, color_repr_t::get_bits_size());
	HBITMAP hBmp = CreateDIBSection(m_hDC, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		{
		(*m_ef)("CreateDIBSection", "");
		jpeg_destroy_decompress(&cinfo);
		return NULL;
		}

	surface<color_repr_t> *psurf = new surface<color_repr_t>(width, height, color_repr_t::get_bits_size(), pBits);

	// Process data
	m_cur_output_row = 0;
	while(cinfo.output_scanline < cinfo.output_height) 
		{
		int num_scanlines = jpeg_read_scanlines(&cinfo, m_dbuffer, m_dbuffer_height);
		if(cinfo.out_color_space == JCS_RGB && cinfo.quantize_colors != TRUE)
			write_pixel_rows(&cinfo, psurf);
		}

	// jpeg cleanup
	jpeg_finish_decompress(&cinfo);
	jpeg_destroy_decompress(&cinfo);

	return new DIBSurf(hBmp, psurf);
	}

inline void JpgDecoder::write_pixel_rows(j_decompress_ptr cinfo, surface<color_repr_t> *psurf)
	{
	JSAMPROW inptr = m_dbuffer[0];
	color_repr_t* outptr = psurf->get_row(m_cur_output_row);
	for(JDIMENSION col = 0; col < cinfo->output_width; col++) 
		{
		BYTE r = *inptr++;
		BYTE g = *inptr++;
		BYTE b = *inptr++;
		*outptr++ = color_repr_t(r, g, b);
		}
	m_cur_output_row++;
	}
	
#endif // INC_DECODE_JPG
