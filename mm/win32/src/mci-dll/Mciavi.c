#include <windows.h>
#include <stdio.h>
#include <digitalv.h>

#include "mcidll.h"



void positionMovie(MCI_AVI_STRUCT *mciAviInfo)
{
	RECT rcMovie;		/* the rect where the movie is positioned      */
						/* for QT/W this is the movie rect, for AVI    */
						/* this is the location of the playback window */
	RECT	rcClient, rcMovieBounds;
	MCI_DGV_RECT_PARMS	mciRect;
	float aspect_ratio;
	float win_ratio;
	RECT winrc;
	//char temp[100];

	/* if there is no movie yet then just get out of here */
	if (!mciAviInfo->fOpened)
		return;

	GetClientRect(mciAviInfo->hWndParent, &rcClient);	/* get the parent windows rect */
	
	/* get the original size of the movie */
	mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_WHERE,
					(DWORD)(MCI_DGV_WHERE_SOURCE),
					(DWORD)(LPMCI_DGV_RECT_PARMS)&mciRect);
	//sprintf(temp, "Width: %d, Height: %d", mciRect.rc.right, mciRect.rc.bottom);
	//MessageBox(mciAviInfo->hWndParent, temp, "Debug", MB_OK);
	
	CopyRect( &rcMovieBounds, &mciRect.rc );	/* get it in the movie bounds rect */

	if (mciAviInfo->scale == 0) //don't stretch
	{
		// the movie's aspect ration is obtained as width/height
		aspect_ratio =(float) rcMovieBounds.right/rcMovieBounds.bottom;

		GetClientRect(mciAviInfo->hWndParent, &winrc);
		
		win_ratio = (float) (winrc.right-winrc.left)/(winrc.bottom-winrc.top);
		
		if (win_ratio>=aspect_ratio)
		{
			float width;
			long left;

			//sprintf(temp, "Width: %d, Height: %d", (winrc.right-winrc.left), (winrc.bottom-winrc.top));
			//MessageBox(mciAviInfo->hWndParent, "Big ratio", "Debug", MB_OK);
			width = aspect_ratio*(float)(winrc.bottom-winrc.top);
			left = winrc.left;

			winrc.left = (long)(winrc.left + (winrc.right - winrc.left - width)/2);
			winrc.right = (long)(winrc.right -(winrc.right - left - width)/2);
			
			if (!mciAviInfo->center)
			{
				winrc.right -= winrc.left;
				winrc.left = 0;
			}
			//sprintf(temp, "Width: %d, Height: %d", (winrc.right-winrc.left), (winrc.bottom-winrc.top));
			//MessageBox(mciAviInfo->hWndParent, temp, "Debug", MB_OK);
	
		}			
		else
		{
			float height;
			long top;
			height =  (float)(winrc.right-winrc.left)/aspect_ratio;
			top = winrc.top;
			winrc.top = winrc.top + (winrc.bottom - winrc.top)/2;
			//sprintf(temp, "Old Top: %d", winrc.top);
			//MessageBox(mciAviInfo->hWndParent, temp, "Debug", MB_OK);
			winrc.top-=(long)height/2;
			//sprintf(temp, "New Top: %d", winrc.top);
			//MessageBox(mciAviInfo->hWndParent, temp, "Debug", MB_OK);
			winrc.bottom = winrc.bottom - (winrc.bottom - top)/2;
			//sprintf(temp, "Old Bottom: %d", winrc.top);
			//MessageBox(mciAviInfo->hWndParent, temp, "Debug", MB_OK);
			winrc.bottom+=(long)height/2;
			
			if (!mciAviInfo->center)
			{
				winrc.bottom -= winrc.top;
				winrc.top = 0;
			}
			
		}
		
		
		/* reposition the playback (child) window */
		SetWindowPos(mciAviInfo->hWndMovie, HWND_TOP, winrc.left, winrc.top-GetSystemMetrics(SM_CYEDGE),
					(winrc.right-winrc.left), (winrc.bottom-winrc.top), SWP_SHOWWINDOW );

	}
	else			//stretch
	{
		rcMovie.left = (long)((rcClient.right - (rcMovieBounds.right*mciAviInfo->scale))/2); 
		rcMovie.top = (long)((rcClient.bottom - (rcMovieBounds.bottom*mciAviInfo->scale))/2); 
		rcMovie.right =  (long)(rcMovieBounds.right*mciAviInfo->scale); 
		rcMovie.bottom = (long)(rcMovieBounds.bottom*mciAviInfo->scale);
		
		if (!mciAviInfo->center)
			{
				rcMovie.left = rcMovie.top = 0;
			}

		/* reposition the playback (child) window */
		SetWindowPos(mciAviInfo->hWndMovie, HWND_TOP, rcMovie.left, rcMovie.top,
					rcMovie.right, rcMovie.bottom, SWP_SHOWWINDOW);
	}
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
						(DWORD)(MCI_OPEN_ELEMENT| MCI_DGV_OPEN_PARENT|MCI_DGV_OPEN_WS),
						(DWORD)(LPMCI_DGV_OPEN_PARMS)&mciOpen) == 0)
	{

		/* we opened the file o.k., now set up to */
		/* play it.				   */
		mciAviInfo->wAVIDeviceID = mciOpen.wDeviceID;	/* save ID */
		mciAviInfo->fOpened = TRUE;	/* a movie was opened */
				
		/* show the playback window */
		mciWindow.dwCallback = 0L;
		mciWindow.hWnd = NULL;
		mciWindow.nCmdShow = SW_HIDE;
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
		if (mciAviInfo->format==1)
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

		/* now place the movie as desired */	
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
	long			lduration;
	MCI_DGV_PLAY_PARMS	mciPlay;  

    if (mciAviInfo->fPlaying)
        return FALSE;
	
	ShowWindow(mciAviInfo->hWndMovie, SW_SHOW);

	mciAviInfo->fPlaying = TRUE;
	
	lduration = mciAviInfo->lAVIduration;
	mciPlay.dwFrom = 0;
	if (lduration<0)
		mciPlay.dwTo = (DWORD)-lduration;
	else
		mciPlay.dwTo = (DWORD)lduration;
	mciPlay.dwCallback = MAKELONG(mciAviInfo->hWndParent,0);
	//mciPlay.dwFrom = mciPlay.dwTo = 0;
	if (mciAviInfo->fNotify)
	    dwFlags = MCI_NOTIFY;
	//if (mciAviInfo->fReverse)
	//dwFlags |= MCI_DGV_PLAY_REVERSE;
	
	if (lduration != 0)
	{
		if (lduration <0)
			dwFlags = dwFlags|MCI_TO;
		else
			dwFlags = dwFlags|MCI_FROM|MCI_TO;
	}

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
	mciSendCommand(mciAviInfo->wAVIDeviceID,MCI_PAUSE, 0L, 
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

	mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_CLOSE, MCI_WAIT,
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
    //MessageBox(0, info, mes, MB_OK);
}


long AviFrame(MCI_AVI_STRUCT *mciAviInfo)
{
    MCI_DGV_STATUS_PARMS mciStatus;
    MCI_SET_PARMS mciSet;
	long position = 0; 

	/* set the movie format to frames*/
	mciSet.dwTimeFormat = MCI_FORMAT_FRAMES;
	mciSendCommand(mciAviInfo->wAVIDeviceID,
					MCI_SET, MCI_SET_TIME_FORMAT,
					(DWORD)(LPMCI_STATUS_PARMS)&mciSet);
	
	
	/* get the window handle */
	mciStatus.dwItem = MCI_STATUS_POSITION;
	mciSendCommand(mciAviInfo->wAVIDeviceID,
						MCI_STATUS, MCI_STATUS_ITEM,
						(DWORD)(LPMCI_STATUS_PARMS)&mciStatus);
	position = (long)mciStatus.dwReturn;
        
    /* set the movie format */
	mciSet.dwTimeFormat = MCI_FORMAT_MILLISECONDS;
    mciSendCommand(mciAviInfo->wAVIDeviceID,
					MCI_SET, MCI_SET_TIME_FORMAT,
					(DWORD)(LPMCI_STATUS_PARMS)&mciSet);

	return position;	
}

DWORD AviDuration(MCI_AVI_STRUCT *mciAviInfo)
{

	MCI_DGV_STATUS_PARMS mciStatus;
    DWORD length = 0; 

	mciStatus.dwItem = MCI_STATUS_LENGTH;
	mciSendCommand(mciAviInfo->wAVIDeviceID,
						MCI_STATUS, MCI_STATUS_ITEM,
						(DWORD)(LPMCI_STATUS_PARMS)&mciStatus);
	
	length = mciStatus.dwReturn;
        
    
	return length;	
}



BOOL AviUpdate(MCI_AVI_STRUCT *mciAviInfo)
{

	MCI_SEEK_PARMS mciSeek;
	long position = 0;
	
    if (mciAviInfo==NULL)
		return FALSE;
	
	if (mciAviInfo->fPlaying)
		return FALSE;
	//mciAviInfo->fPlaying = FALSE;
    position = AviFrame(mciAviInfo);
	mciSeek.dwTo = position;
    mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_SEEK, MCI_TO,
    						(DWORD)(LPMCI_SEEK_PARMS) &mciSeek);	
}


void AviSize(MCI_AVI_STRUCT *mciAviInfo, RECT* rec)
{
	MCI_DGV_RECT_PARMS	mciRect;
	
	if (!mciAviInfo->fOpened)
		return;

	mciSendCommand(mciAviInfo->wAVIDeviceID, MCI_WHERE,
					(DWORD)(MCI_DGV_WHERE_SOURCE),
					(DWORD)(LPMCI_DGV_RECT_PARMS)&mciRect);
	
	CopyRect(rec, &mciRect.rc);	
}