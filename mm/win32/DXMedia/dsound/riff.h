#ifndef INC_RIFF
#define INC_RIFF

#ifndef _INC_MMSYSTEM
#include <mmsystem.h>
#endif

class RIFFFile
	{
	public:
	RIFFFile();
	~RIFFFile();

	bool open(char *pszFilename);
	bool seekToData();
	bool readData(UINT cbRead, BYTE *pbDest, UINT *cbActualRead);

	//private:
	HMMIO hmmio;
	MMCKINFO ckInRiff;
	MMCKINFO ckIn;
	WAVEFORMATEX *pwfxInfo;
	};

#endif

