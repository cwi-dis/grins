#ifndef INC_IGIF
#define INC_IGIF

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
	CString m_tempFile;

	private:
	BYTE *m_buf;
	UINT m_width;
	UINT m_height;
	};

#endif
