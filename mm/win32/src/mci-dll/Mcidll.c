//#define MYDEBUG

#include <windows.h>
#include <digitalv.h>
#include "mcidll.h"
#ifdef MYDEBUG
#include <assert.h>
#endif

void positionMovie(MCI_AVI_STRUCT *mciAviInfo)
{
	RECT rcMovie;		/* the rect where the movie is positioned      */
						/* for QT/W this is the movie rect, for AVI    */
						/* this is the location of the playback window */
	RECT	rcClient, rcMovieBounds;
	MCI_DGV_RECT_PARMS	mciRect;

	/* if there is no movie yet then just get out of here */
	if (!mciAviInfo->fOpened)
		return;

	GetClientRect(mciAviInfo->hWndParent, &rcClient);	/* get the parent windows rect */
	
	/* get the original size of the movie */
	mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_WHERE,
					(DWORD)(MCI_DGV_WHERE_SOURCE),
					(DWORD)(LPMCI_DGV_RECT_PARMS)&mciRect);
	CopyRect( &rcMovieBounds, &mciRect.rc );	/* get it in the movie bounds rect */

	rcMovie.left = (rcClient.right/2) - (rcMovieBounds.right / 2);
	rcMovie.top = (rcClient.bottom/2) - (rcMovieBounds.bottom / 2);
	rcMovie.right = rcMovie.left + rcMovieBounds.right;
	rcMovie.bottom = rcMovie.top + rcMovieBounds.bottom;

	/* reposition the playback (child) window */
	MoveWindow(mciAviInfo->hWndMovie, rcMovie.left, rcMovie.top,
				rcMovieBounds.right, rcMovieBounds.bottom, TRUE);
}

BOOL AviOpen(MCI_AVI_STRUCT *mciAviInfo)
{
    MCI_DGV_OPEN_PARMS mciOpen;
	MCI_DGV_WINDOW_PARMS mciWindow;
	MCI_DGV_STATUS_PARMS mciStatus;
    MCI_SET_PARMS mciSet;

	if (mciAviInfo->fOpened)
		AviClose(mciAviInfo);	

                                /* Clear previous values */
    mciAviInfo->fPlaying=FALSE;
    mciAviInfo->fOpened=FALSE;
    mciAviInfo->hWndMovie=NULL;
    mciAviInfo->wAVIDeviceID=0;

	/* we have a .AVI movie to open, use MCI */
	/* set up the open parameters */
	mciOpen.dwCallback = 0L;
	mciOpen.wDeviceID = 0;
	mciOpen.lpstrDeviceType = NULL;
	mciOpen.lpstrElementName = mciAviInfo->szFileName;
	mciOpen.lpstrAlias = NULL;
	mciOpen.dwStyle = WS_CHILD;
	mciOpen.hWndParent = mciAviInfo->hWndParent;

	/* try to open the file */
	if (mciSendCommand(0, MCI_OPEN,
						(DWORD)(MCI_OPEN_ELEMENT|MCI_DGV_OPEN_PARENT|MCI_DGV_OPEN_WS),
						(DWORD)(LPMCI_DGV_OPEN_PARMS)&mciOpen) == 0)
	{

		/* we opened the file o.k., now set up to */
		/* play it.				   */
		mciAviInfo->wAVIDeviceID = mciOpen.wDeviceID;	/* save ID */
		mciAviInfo->fOpened = TRUE;	/* a movie was opened */
				
		/* show the playback window */
		mciWindow.dwCallback = 0L;
		mciWindow.hWnd = NULL;
		mciWindow.nCmdShow = SW_SHOW;
		mciWindow.lpstrText = (LPSTR)NULL;
		mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_WINDOW,
						MCI_DGV_WINDOW_STATE,
						(DWORD)(LPMCI_DGV_WINDOW_PARMS)&mciWindow);

		/* get the window handle */
		mciStatus.dwItem = MCI_DGV_STATUS_HWND;
		mciSendCommand(mciAviInfo->wAVIDeviceID,
						MCI_STATUS, MCI_STATUS_ITEM,
						(DWORD)(LPMCI_STATUS_PARMS)&mciStatus);
		mciAviInfo->hWndMovie = (HWND)mciStatus.dwReturn;
        
        /* set the movie format */
		if (mciAviInfo->format==TIME)
		    mciSet.dwTimeFormat = MCI_FORMAT_MILLISECONDS;
        else
            mciSet.dwTimeFormat = MCI_FORMAT_FRAMES;

		mciSendCommand(mciAviInfo->wAVIDeviceID,
						MCI_SET, MCI_SET_TIME_FORMAT,
						(DWORD)(LPMCI_STATUS_PARMS)&mciSet);

        /* get the movie length */
		mciStatus.dwItem = MCI_STATUS_LENGTH;
		mciSendCommand(mciAviInfo->wAVIDeviceID,
						MCI_STATUS, MCI_STATUS_ITEM,
						(DWORD)(LPMCI_STATUS_PARMS)&mciStatus);
		mciAviInfo->iTotalLength = (int)mciStatus.dwReturn;

        /* Set the signalling */
        if(mciAviInfo->iSignalSteps) {
            MCI_DGV_SIGNAL_PARMS mciSignal;
            int rc;

            mciSignal.dwCallback = MAKELONG(mciAviInfo->hWndParent,0);
            mciSignal.dwPeriod   = mciAviInfo->iSignalSteps;
            if(rc=mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_SIGNAL, MCI_DGV_SIGNAL_EVERY | MCI_DGV_SIGNAL_POSITION,
                        (DWORD)(LPMCI_DGV_SIGNAL_PARMS)&mciSignal)) {
                MCIError("MCI_SIGNAL", rc);
            }
        }

		/* now get the movie centered */	
        positionMovie(mciAviInfo);

        return TRUE;
	
	} else {

		mciAviInfo->fOpened = FALSE;
        return FALSE;
    }
}

BOOL AviPlay(MCI_AVI_STRUCT *mciAviInfo)
{
	DWORD			dwFlags;
	MCI_DGV_PLAY_PARMS	mciPlay;  

    if (mciAviInfo->fPlaying)
        return FALSE;

	mciAviInfo->fPlaying = TRUE;
		
	mciPlay.dwCallback = MAKELONG(mciAviInfo->hWndParent,0);
	mciPlay.dwFrom = mciPlay.dwTo = 0;
	if (mciAviInfo->fNotify)
	    dwFlags = MCI_NOTIFY;
	if (mciAviInfo->fReverse)
		dwFlags |= MCI_DGV_PLAY_REVERSE;
	
	mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_PLAY, dwFlags,
	                (DWORD)(LPMCI_DGV_PLAY_PARMS)&mciPlay);
    return TRUE;
}

BOOL AviPause(MCI_AVI_STRUCT *mciAviInfo)
{
	MCI_DGV_PAUSE_PARMS	mciPause;

    if (!(mciAviInfo->fPlaying))
        return FALSE;

	/* tell it to pause */
	mciSendCommand(mciAviInfo->wAVIDeviceID,MCI_PAUSE,0L,
					(DWORD)(LPMCI_DGV_PAUSE_PARMS)&mciPause);
    
    mciAviInfo->fPlaying = FALSE;

    return TRUE;
}

BOOL AviStop(MCI_AVI_STRUCT *mciAviInfo)
{
    AviPause(mciAviInfo);
    
    return TRUE;
}

BOOL AviClose(MCI_AVI_STRUCT *mciAviInfo)
{
	MCI_GENERIC_PARMS  mciGeneric;

    if (mciAviInfo->fPlaying)
        AviStop(mciAviInfo);

	mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_CLOSE, 0L,
	                 (DWORD)(LPMCI_GENERIC_PARMS)&mciGeneric);

	mciAviInfo->fPlaying = FALSE;		// can't be playing any longer
	mciAviInfo->fOpened = FALSE;	// no more movies open   

    return TRUE;
}

BOOL AviSeek(MCI_AVI_STRUCT *mciAviInfo)
{
    MCI_SEEK_PARMS mciSeek;

    mciAviInfo->fPlaying = FALSE;
    mciSeek.dwTo = mciAviInfo->iSeekThere;
    mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_SEEK, MCI_TO,
    						(DWORD)(LPMCI_SEEK_PARMS) &mciSeek);
    return TRUE;
}

void MCIError(char *mes, MCIERROR rc)
{
    char info[256];

    mciGetErrorString(rc, info, sizeof(info));
    MessageBox(0, info, mes, MB_OK);
}
