#ifndef INC_PARSE_I
#define INC_PARSE_I

struct DIBSurf
	{
	HBITMAP m_hBmp;
	surface<color_repr_t> *m_psurf;

	DIBSurf(HBITMAP hBmp = NULL, surface<color_repr_t> *psurf = NULL)
	: m_hBmp(hBmp), m_psurf(psurf) {}

	~DIBSurf()
		{
		if(m_psurf != NULL)
			delete m_psurf;
		if(m_hBmp != NULL)
			DeleteObject(m_hBmp);
		}
	surface<color_repr_t> *get_pixmap() { return m_psurf;}
	
	HBITMAP detach_handle() {HBITMAP hBmp = m_hBmp; m_hBmp = NULL; return hBmp;}
	surface<color_repr_t>* detach_pixmap() {surface<color_repr_t> *psurf = m_psurf; m_psurf = NULL; return psurf;}
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
	virtual bool is_transparent() { return false; }
	virtual void get_transparent_color(BYTE *rgb) {}

	protected:
	memfile& m_mf;
	HDC m_hDC;
	ERROR_FUNCT m_ef;
	};

inline BITMAPINFO* GetBmpInfo(int width, int height, int depth)
	{
	static BITMAPINFO bmi;
	BITMAPINFOHEADER& h = bmi.bmiHeader;
	memset(&h, 0, sizeof(BITMAPINFOHEADER));
    h.biSize = sizeof(BITMAPINFOHEADER);
    h.biWidth = width;
    h.biHeight = height;
    h.biPlanes = 1;
    h.biBitCount = depth;
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