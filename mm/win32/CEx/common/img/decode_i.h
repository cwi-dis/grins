
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_PARSE_I
#define INC_PARSE_I

struct DIBSurf
	{
	HBITMAP m_hBmp;
	surface<le::trible> *m_psurf;

	DIBSurf(HBITMAP hBmp = NULL, surface<le::trible> *psurf = NULL)
	: m_hBmp(hBmp), m_psurf(psurf) {}

	~DIBSurf()
		{
		if(m_psurf != NULL)
			delete m_psurf;
		if(m_hBmp != NULL)
			DeleteObject(m_hBmp);
		}
	surface<le::trible> *get_pixmap() { return m_psurf;}
	
	HBITMAP detach_handle() {HBITMAP hBmp = m_hBmp; m_hBmp = NULL; return hBmp;}
	surface<le::trible>* detach_pixmap() {surface<le::trible> *psurf = m_psurf; m_psurf = NULL; return psurf;}
	};

typedef void (*ERROR_FUNCT)(const char *, const char *);

class ImgDecoder
	{
	public:
	ImgDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef)
	:	m_mf(mf), m_hDC(hDC), m_ef(ef) {}
	
	virtual ~ImgDecoder() {}
	virtual bool can_decode() = 0;
	virtual DIBSurf* decode() = 0;

	protected:
	memfile& m_mf;
	HDC m_hDC;
	ERROR_FUNCT m_ef;
	};

inline BITMAPINFO* GetBmpInfo24(int width, int height)
	{
	static BITMAPINFO bmi;
	BITMAPINFOHEADER& h = bmi.bmiHeader;
	memset(&h, 0, sizeof(BITMAPINFOHEADER));
    h.biSize = sizeof(BITMAPINFOHEADER);
    h.biWidth = width;
    h.biHeight = height;
    h.biPlanes = 1;
    h.biBitCount = 24;
    h.biCompression = BI_RGB;
    h.biSizeImage = 0;
    h.biXPelsPerMeter = 0;
    h.biYPelsPerMeter = 0;
    h.biClrUsed = 0;
    h.biClrImportant = 0;
	memset(&bmi.bmiColors[0], 0, sizeof(RGBQUAD));
	return &bmi;
	}


#endif // INC_PARSE_I