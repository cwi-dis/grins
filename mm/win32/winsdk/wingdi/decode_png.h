#ifndef INC_DECODE_PNG
#define INC_DECODE_PNG

#ifndef INC_MEMFILE
#include "../common/memfile.h"
#endif

#ifndef INC_SURFACE
#include "../common/surface.h"
#endif

#ifndef INC_PARSE_I
#include "decode_i.h"
#endif

class PngDecoder : public ImgDecoder
	{
	public:
	PngDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef);
	virtual ~PngDecoder();

	virtual bool can_decode();
	virtual DIBSurf* decode();
	};

inline PngDecoder::PngDecoder(memfile& mf, HDC hDC, ERROR_FUNCT ef)
:	ImgDecoder(mf, hDC, ef)
	{
	}

inline PngDecoder::~PngDecoder()
	{
	}

inline bool PngDecoder::can_decode()
	{
	m_mf.seekg(0);
	uchar_t sig[8];
	if(!m_mf.safe_read(sig, 8))
		return false;
	return (sig[0] == (uchar_t)137 &&
		sig[1] == (uchar_t)80 &&
		sig[2] == (uchar_t)78 &&
		sig[3] == (uchar_t)71 &&
		sig[4] == (uchar_t)13 &&
		sig[5] == (uchar_t)10 &&
		sig[6] == (uchar_t)26 &&
		sig[7] == (uchar_t)10); 
	}

inline DIBSurf* PngDecoder::decode()
	{
	HMODULE hDLL = LoadLibrary(TEXT("libpng.dll"));
	if(hDLL == NULL) 
		{
		(*m_ef)("PngDecoder::decode", "failed to locate decode library libpng.dll");
		return NULL;
		}

	(*m_ef)("PngDecoder::decode", "failed to decode image");
	return NULL;
	}


#endif // INC_DECODE_PNG
