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
#undef HAVE_STDDEF_H
#undef HAVE_STDLIB_H
extern "C" {
#include "../../../../lib-src/jpeg/jpeglib.h"
}
#define HAVE_STDDEF_H
#define HAVE_STDLIB_H
#endif

namespace jpeg
	{
	typedef jpeg_error_mgr* (*std_error_fn)(jpeg_error_mgr *err);
	typedef void  (*CreateDecompress_fn)(j_decompress_ptr cinfo, int version, size_t structsize);
	typedef void (*stdio_src_fn)(j_decompress_ptr cinfo, FILE * infile);
	typedef int (*read_header_fn)(j_decompress_ptr cinfo, boolean require_image);
	typedef void (*calc_output_dimensions_fn)(j_decompress_ptr cinfo);
	typedef boolean (*start_decompress_fn)(j_decompress_ptr cinfo);
	typedef JDIMENSION (*read_scanlines_fn)(j_decompress_ptr cinfo, JSAMPARRAY scanlines, JDIMENSION max_lines);
	typedef boolean (*finish_decompress_fn)(j_decompress_ptr cinfo);
	typedef void (*destroy_decompress_fn)(j_decompress_ptr cinfo);

	std_error_fn std_error;
	CreateDecompress_fn CreateDecompress;
	stdio_src_fn stdio_src;
	read_header_fn read_header;
	calc_output_dimensions_fn calc_output_dimensions;
	start_decompress_fn start_decompress;
	read_scanlines_fn read_scanlines;
	finish_decompress_fn finish_decompress;
	destroy_decompress_fn destroy_decompress;
	void create_decompress(j_decompress_ptr cinfo)
		{
		CreateDecompress(cinfo, JPEG_LIB_VERSION,(size_t) sizeof(jpeg_decompress_struct));
		}
	bool init(HMODULE hDLL)
		{
		std_error = (std_error_fn)GetProcAddress(hDLL, TEXT("jpeg_std_error"));
		CreateDecompress = (CreateDecompress_fn)GetProcAddress(hDLL, TEXT("jpeg_CreateDecompress"));
		stdio_src = (stdio_src_fn)GetProcAddress(hDLL, TEXT("jpeg_stdio_src"));
		read_header = (read_header_fn)GetProcAddress(hDLL, TEXT("jpeg_read_header"));
		calc_output_dimensions = (calc_output_dimensions_fn)GetProcAddress(hDLL, TEXT("jpeg_calc_output_dimensions"));
		start_decompress = (start_decompress_fn)GetProcAddress(hDLL, TEXT("jpeg_start_decompress"));
		read_scanlines = (read_scanlines_fn)GetProcAddress(hDLL, TEXT("jpeg_read_scanlines"));
		finish_decompress = (finish_decompress_fn)GetProcAddress(hDLL, TEXT("jpeg_finish_decompress"));
		destroy_decompress = (destroy_decompress_fn)GetProcAddress(hDLL, TEXT("jpeg_destroy_decompress"));
		return ((std_error != NULL) && 
			(CreateDecompress != NULL) &&
			(stdio_src != NULL) &&
			(read_header != NULL) &&
			(calc_output_dimensions != NULL) &&
			(read_scanlines != NULL) &&
			(finish_decompress != NULL) &&
			(destroy_decompress != NULL));
		}
	};

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
	void write_pixel_rows(j_decompress_ptr cinfo, surface<le::trible> *psurf);

	JSAMPARRAY m_dbuffer;
	JDIMENSION m_dbuffer_height;
	JDIMENSION m_cur_output_row;
	};

inline JpgDecoder::JpgDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef)
:	ImgDecoder(mf, hDC, ef), 
	m_dbuffer(NULL), m_dbuffer_height(1),
	m_cur_output_row(0)
	{
	}

inline JpgDecoder::~JpgDecoder()
	{
	for(JDIMENSION i=0;i<m_dbuffer_height;i++)
		delete[] m_dbuffer[i];
	delete[] m_dbuffer;
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
DIBSurf* JpgDecoder::decode()
	{
	HMODULE hDLL = LoadLibrary(TEXT("libjpeg.dll"));
	if(hDLL == NULL) 
		{
		(*m_ef)("JpgDecoder::decode", "failed to locate decode library libjpeg.dll");
		return NULL;
		}
	if(!jpeg::init(hDLL))
		{
		FreeLibrary(hDLL);
		(*m_ef)("JpgDecoder::decode", "failed to initialize libjpeg.dll");
		return NULL;
		}
	if(m_mf.get_handle() == INVALID_HANDLE_VALUE)
		{
		FreeLibrary(hDLL);
		(*m_ef)("JpgDecoder::decode", "invalid file handle");
		return NULL;
		}

	jpeg_decompress_struct cinfo;
	jpeg_error_mgr jerr;

	// Initialize the JPEG decompression object with default error handling.
	cinfo.err = jpeg::std_error(&jerr);
	jpeg::create_decompress(&cinfo);

	// Specify data source for decompression
	jpeg::stdio_src(&cinfo, (FILE *) m_mf.get_handle());

	// Read file header, set default decompression parameters
	int res = jpeg::read_header(&cinfo, TRUE);

	// Calculate output image dimensions so we can allocate space
	jpeg::calc_output_dimensions(&cinfo);
	
	// Start decompressor
	jpeg::start_decompress(&cinfo);
		
	JDIMENSION row_width = cinfo.output_width * cinfo.output_components;
	
	// release/create buffer
	if(m_dbuffer != NULL)
		{
		for(JDIMENSION i=0;i<m_dbuffer_height;i++)
			delete[] m_dbuffer[i];
		delete[] m_dbuffer;
		m_dbuffer = NULL;
		}
	m_dbuffer_height = 1;
	m_dbuffer = new JSAMPROW[m_dbuffer_height];
	for(JDIMENSION i=0;i<m_dbuffer_height;i++)
		m_dbuffer[i] = new JSAMPLE[row_width];

	int width = cinfo.output_width;
	int height = cinfo.output_height;

	// create a bmp surface
	le::trible *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo24(width, height);
	HBITMAP hBmp = CreateDIBSection(m_hDC, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		{
		(*m_ef)("CreateDIBSection", "");
		return NULL;
		}
	surface<le::trible> *psurf = new surface<le::trible>(width, height, 24, pBits);

	// Process data
	m_cur_output_row = 0;
	while(cinfo.output_scanline < cinfo.output_height) 
		{
		int num_scanlines = jpeg::read_scanlines(&cinfo, m_dbuffer, m_dbuffer_height);
		if(cinfo.out_color_space == JCS_RGB && cinfo.quantize_colors != TRUE)
			write_pixel_rows(&cinfo, psurf);
		}

	// cleanup
	jpeg::finish_decompress(&cinfo);
	jpeg::destroy_decompress(&cinfo);
	FreeLibrary(hDLL);
	return new DIBSurf(hBmp, psurf);
	}

void JpgDecoder::write_pixel_rows(j_decompress_ptr cinfo, surface<le::trible> *psurf)
	{
	JSAMPROW inptr = m_dbuffer[0];
	le::trible* outptr = psurf->get_row(m_cur_output_row);
	for(JDIMENSION col = 0; col<=cinfo->output_width;col++) 
		{
		le::trible t;
		t.r = *inptr++;
		t.g = *inptr++;
		t.b = *inptr++;
		*outptr++ = t;
		}
	m_cur_output_row++;
	}
	
#endif // INC_DECODE_JPG
