#include <windows.h>
#include <stdio.h>
#include "igif.h"

#include "GifFile.h"
#include "BmpFile.h"

extern GifInfo GifScreen;
extern GifExt Gif89;
extern GifTransColor GifTans;


GifConverter::GifConverter()
:	m_buf(NULL),m_pBmpBuffer(NULL)
	{
	}

GifConverter::~GifConverter()
	{
	if(m_buf) delete [] m_buf;
	if(m_pBmpBuffer) delete[] m_pBmpBuffer;

	if(!m_tempFile.IsEmpty())
		::DeleteFile(m_tempFile);
	}

bool GifConverter::LoadGif(LPCTSTR fileName)
	{
	if (m_buf) 
		{
		delete [] m_buf;
		m_buf=NULL;
		}
	if (m_pBmpBuffer) 
		{
		delete [] m_pBmpBuffer;
		m_pBmpBuffer=NULL;
		}

	GIFFile theGif;
	
	// read the GIF to a packed buffer of RGB bytes
	Gif89.transparent=-1;
	m_buf=theGif.GIFReadFileToRGB(fileName, 
						&m_width, 
						&m_height);
	if (m_buf==NULL) 
		{
		m_errorMsg = theGif.m_GIFErrorText;
		return false;
		}

	BMPFile theBmp;
	// swap red and blue for display
	if(!theBmp.BGRFromRGB(m_buf,m_width, m_height))
		return false;

	// flip for display
	if(!theBmp.VertFlipBuf(m_buf, m_width * 3, m_height))
		return false;

	m_pBmpBuffer = theBmp.SaveBMP2Mem(m_buf,m_width, m_height,&m_dwSize);
	m_transparent=Gif89.transparent;
	for(int i=0;i<3;i++) m_tc[i]=GifTans.c[i];
	return true;
	}

void GifConverter::SaveGif()
	{
	char buf[MAX_PATH],path[MAX_PATH];
	BOOL brc = ::GetTempPath(sizeof(path),path);
	UINT rc=GetTempFileName(path,"gif",0,buf);
	m_tempFile=buf;
	BMPFile theBmp;
	theBmp.SaveBMP(m_tempFile,m_buf,m_width, m_height);
	}