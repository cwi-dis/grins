#ifndef INC_IGIF
#define INC_IGIF

#ifndef INC_MFCSTRING
#include "mfcstring.h"
#endif

class GifConverter
	{
	public:
	GifConverter();
	~GifConverter();

	bool LoadGif(LPCTSTR fileNameLoad);

	int m_transparent;
	int m_tc[3];
	BYTE *m_pBmpBuffer;
	DWORD m_dwSize;

	void SaveGif();
	String m_tempFile;
	String m_errorMsg;

	private:
	BYTE *m_buf;
	UINT m_width;
	UINT m_height;
	};

#endif
