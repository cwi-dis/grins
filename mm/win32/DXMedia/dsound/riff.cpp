#include <windows.h>

#include "riff.h"

RIFFFile::RIFFFile()
:	hmmio(NULL), pwfxInfo(NULL)
	{
	}

RIFFFile::~RIFFFile()
	{
	if(pwfxInfo) delete[] pwfxInfo;
	if(hmmio) mmioClose(hmmio, 0);
	}

bool RIFFFile::open(char *pszFilename)
	{
	hmmio = mmioOpen(pszFilename, NULL, MMIO_ALLOCBUF | MMIO_READ);
	if(!hmmio) return false;

	int res = mmioDescend(hmmio, &ckInRiff, NULL, 0);
	if(res != MMSYSERR_NOERROR) return false;

	if((ckInRiff.ckid != FOURCC_RIFF) || (ckInRiff.fccType != mmioFOURCC('W', 'A', 'V', 'E')))
		return false; 

    // search for 'fmt ' chunk
	MMCKINFO ckIn;
    ckIn.ckid = mmioFOURCC('f', 'm', 't', ' ');
	res = mmioDescend(hmmio, &ckIn, &ckInRiff, MMIO_FINDCHUNK);
	if(res != MMSYSERR_NOERROR) return false;
	if(ckIn.cksize < sizeof(PCMWAVEFORMAT)) return false;

	// read the 'fmt ' chunk
	PCMWAVEFORMAT pcmWaveFormat;
	int nRead = mmioRead(hmmio, (HPSTR)&pcmWaveFormat, sizeof(PCMWAVEFORMAT));
	if(nRead != sizeof(PCMWAVEFORMAT)) return false;

	// find needed extra bytes for waveformatex
	WORD cbExtraAlloc = 0;
    if(pcmWaveFormat.wf.wFormatTag != WAVE_FORMAT_PCM) 
		{
        // Read in length of extra bytes.
		nRead = mmioRead(hmmio, (LPSTR)&cbExtraAlloc, sizeof(WORD));
		if(nRead != sizeof(WORD)) return false;
		}
	pwfxInfo = (WAVEFORMATEX *) new BYTE[sizeof(WAVEFORMATEX)+cbExtraAlloc];

    // Copy the bytes from the pcm structure to the waveformatex structure
    memcpy(pwfxInfo, &pcmWaveFormat, sizeof(PCMWAVEFORMAT));
    pwfxInfo->cbSize = cbExtraAlloc;
	
	// read any extra bytes
	if(cbExtraAlloc > 0)
		{
		char *ps = (char*)(((BYTE*)&(pwfxInfo->cbSize)) + sizeof(cbExtraAlloc));
		nRead = mmioRead(hmmio, ps, cbExtraAlloc);
		if(nRead != cbExtraAlloc) return false;
		}

	// rewind
	res = mmioAscend(hmmio, &ckIn, 0);
	if(res != MMSYSERR_NOERROR) return false;

	return true;
	}


bool RIFFFile::seekToData()
	{    
	int res = mmioSeek(hmmio, ckInRiff.dwDataOffset + sizeof(FOURCC), SEEK_SET);
	if(res == -1) return false;

    ckIn.ckid = mmioFOURCC('d', 'a', 't', 'a');
	res = mmioDescend(hmmio, &ckIn, &ckInRiff, MMIO_FINDCHUNK);
	if(res != MMSYSERR_NOERROR) return false;

	return true;
	}

bool RIFFFile::readData(UINT cbRead, BYTE *pbDest, UINT *cbActualRead)
	{
	MMIOINFO mmioinfoIn;
    if(mmioGetInfo(hmmio, &mmioinfoIn, 0) != MMSYSERR_NOERROR)
		return false;

    UINT cbDataIn = cbRead;
    if (cbDataIn > ckIn.cksize) 
        cbDataIn = ckIn.cksize;   

    ckIn.cksize -= cbDataIn;
	bool bres = true;
    for(UINT cT=0;cT<cbDataIn;cT++)
		{
		// copy bytes to buffer.
        if (mmioinfoIn.pchNext == mmioinfoIn.pchEndRead)
			{
			if(mmioAdvance(hmmio, &mmioinfoIn, MMIO_READ) != MMSYSERR_NOERROR)
				{
				bres = false;
				break;
				}
            if(mmioinfoIn.pchNext == mmioinfoIn.pchEndRead)
				{
				// failed
				bres = false;
				break;
				}
			}
		// actual copy
		*((BYTE*)pbDest+cT) = *((BYTE*)mmioinfoIn.pchNext++);
        }
	if(!bres) 
		{
		*cbActualRead = 0;
		return false;
		}
	if(mmioSetInfo(hmmio, &mmioinfoIn, 0) != MMSYSERR_NOERROR)
		{
		*cbActualRead = 0;
		return false;
		}
    *cbActualRead = cbDataIn;
	return true;
	}
