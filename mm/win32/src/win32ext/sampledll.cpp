#define VC_EXTRALEAN
#define STRICT

#include <afxwin.h>
#include <mmsystem.h>
#include "audiostream.h"

#define _SNDDLL_
#include "sampledll.h"

static AudioStreamServices *mainsound;
static CFrameWnd* hWnd=NULL;

struct samples{
	HWND hwnd;
	AudioStream* sample;
	BOOL reserved;
};

static samples sounds[10];
static BOOL firsttime=TRUE;
//static AudioStream *sample;




SNDAPP void initmainsound()
{
	hWnd=new CFrameWnd;
	hWnd->Create( NULL, " ");
	
	mainsound = new AudioStreamServices;
    if (mainsound)
    {
        mainsound->Initialize (hWnd->m_hWnd);
    }
   
	createsound();
}


SNDAPP void createsound()
{
	int i;
	for(i=0;i<10;i++) 
	{
		sounds[i].sample = new AudioStream;
		sounds[i].hwnd = NULL;
		sounds[i].reserved = FALSE;
	}
}


SNDAPP int createsound(HWND hwnd,LPSTR filename)
{
	int i;

	if(firsttime)
	{
		firsttime = FALSE;
		initmainsound();
	}

	for(i=0;i<10;i++)
	{
	 if(sounds[i].reserved==FALSE)
	 {
		sounds[i].sample->Create(filename,mainsound,hwnd);
	    sounds[i].hwnd = hwnd;
		sounds[i].reserved = TRUE;
		break;
	 }
	}
	
	return i;
}

SNDAPP void playsound(int i)
{
    if(sounds[i].sample)
	{
		PostMessage(sounds[i].hwnd, MM_MCINOTIFY, 2, 1);
		sounds[i].sample->Play();
	}
}

SNDAPP void stopsound(int i)
{
    if(sounds[i].sample)
	{
	 sounds[i].sample->Stop();
	 //PostMessage(sounds[i].hwnd, MM_MCINOTIFY, 1, 1); for pause
	}
}

SNDAPP void closesound()
{
    int i;
	for(i=0;i<10;i++) sounds[i].sample->Destroy();
	if(mainsound) delete mainsound;
	firsttime=TRUE;
	//ASSERT(0);
	delete hWnd;
	hWnd=NULL;
	//DestroyWindow(hWnd.m_hWnd);
}

SNDAPP void closesound(int i)
{
   sounds[i].reserved = FALSE;
}