#ifndef INC_DECODE_BMP
#define INC_DECODE_BMP

#ifndef INC_MEMFILE
#include "../common/memfile.h"
#endif

#ifndef INC_SURFACE
#include "surface.h"
#endif

#ifndef INC_PARSE_I
#include "decode_i.h"
#endif

class BmpDecoder : public ImgDecoder
	{
	public:
	BmpDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef);
	virtual ~BmpDecoder();
	virtual bool can_decode();
	virtual DIBSurf* decode();
	};

inline BmpDecoder::BmpDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef)
:	ImgDecoder(mf, hDC, ef)
	{
	}

inline BmpDecoder::~BmpDecoder()
	{
	}

inline bool BmpDecoder::can_decode()
	{
	m_mf.seekg(0);
	BITMAPFILEHEADER bfh;
	if(m_mf.read((BYTE*)&bfh, sizeof(bfh)) != sizeof(bfh))
		return false;
	char* ptr = (char*)&bfh.bfType;
	if(*ptr!='B' || *++ptr != 'M')
		return false;
	return true;
	}

inline DIBSurf* BmpDecoder::decode()
	{
	m_mf.seekg(0);
	BITMAPFILEHEADER bfh;
	if(m_mf.read((BYTE*)&bfh, sizeof(bfh)) != sizeof(bfh))
		{
		(*m_ef)("CreateDIBSurfaceFromFile", "not a valid BMP");
		return NULL;
		}

	char* ptr = (char*)&bfh.bfType;
	if (*ptr!='B' || *++ptr!='M')
		{
		(*m_ef)("CreateDIBSurfaceFromFile", "not a valid BMP");
		return NULL;
		}
	
	BITMAPINFOHEADER bmi;
	if(m_mf.read((BYTE*)&bmi, sizeof(bmi)) != sizeof(bmi))
		{
		(*m_ef)("CreateDIBSurfaceFromFile", "not a valid BMP");
		return NULL;
		}
	if(bmi.biCompression != BI_RGB)
		{
		(*m_ef)("CreateDIBSurfaceFromFile", "unsupported compressed BMP format");
		return NULL;
		}
	if(bmi.biBitCount != 24 && bmi.biBitCount != 16 && bmi.biBitCount != 8)
		{
		(*m_ef)("CreateDIBSurfaceFromFile", "unsupported bits per pixel BMP");
		return NULL;
		}

	int width = bmi.biWidth;
	int height = bmi.biHeight;
	int depth = bmi.biBitCount;
	if (bmi.biSizeImage == 0) 
		bmi.biSizeImage = get_pitch_from_bpp(depth, width)*height;

	color_repr_t *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo(width, height, color_repr_t::get_bits_size());
	HBITMAP hBmp = CreateDIBSection(m_hDC, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		{
		(*m_ef)("CreateDIBSection", "");
		return NULL;
		}
	surface<color_repr_t> *psurf = new surface<color_repr_t>(width, height, color_repr_t::get_bits_size(), pBits);

	m_mf.seekg(sizeof(bfh) + bmi.biSize);
	if(depth == 24 && color_repr_t::get_bits_size() == 24)
		{
		memcpy(psurf->get_buffer(), m_mf.rdata(), bmi.biSizeImage);
		}
	else if(depth == 24 && color_repr_t::get_bits_size() == 16)
		{
		}
	else if(depth == 8)
		{
		if(bmi.biClrUsed == 0) bmi.biClrUsed = 1 << depth;
		le::rgbquad *pquad = new le::rgbquad[bmi.biClrUsed];
		m_mf.read((BYTE*)pquad, sizeof(le::rgbquad)*bmi.biClrUsed);
		surface<uchar_t> surf8(width, height, depth, m_mf.rdata());
		psurf->fill(surf8, pquad, bmi.biClrUsed);
		delete[] pquad;
		}
	return new DIBSurf(hBmp, psurf);
	}


#endif // INC_DECODE_BMP
