#include <windows.h>
#include <mmsystem.h>
#include "mcidll.h"


BOOL MidiOpen(MCI_MIDI_STRUCT *mciMidiInfo)
{
    DWORD dwResult;
    MCI_SET_PARMS set;
    MCI_OPEN_PARMS m_OpenParams;

    if (mciMidiInfo->wMIDIDeviceID != 0) {
        MidiClose(mciMidiInfo);
	}
    
    m_OpenParams.dwCallback = 0;
    m_OpenParams.wDeviceID = 0;
    m_OpenParams.lpstrDeviceType = NULL;    
    m_OpenParams.lpstrAlias = NULL;
    m_OpenParams.lpstrElementName = mciMidiInfo->szFileName;

	dwResult = mciSendCommand(0,
                              MCI_OPEN,
                              MCI_OPEN_ELEMENT, 
                              (DWORD)(LPVOID)&m_OpenParams);
    if (dwResult != 0) {
        MCIError("MCI_OPEN", dwResult);
        mciMidiInfo->wMIDIDeviceID = 0;
        return FALSE;
    }

    // Set the time format to milliseconds.

    mciMidiInfo->wMIDIDeviceID = m_OpenParams.wDeviceID;
    mciMidiInfo->fOpened = TRUE;

    set.dwTimeFormat = MCI_FORMAT_MILLISECONDS;
    dwResult = mciSendCommand(m_OpenParams.wDeviceID,
                              MCI_SET,
                              MCI_WAIT | MCI_SET_TIME_FORMAT,
                              (DWORD)(LPVOID)&set);
    if (dwResult != 0) {
        MCIError("MCI_SET_TIME_FORMAT", dwResult);
        mciMidiInfo->wMIDIDeviceID = 0;
        return FALSE;
    }

    // Cue the file so it will play with no delay.
/*
    dwResult = mciSendCommand(m_OpenParams.wDeviceID,
                              MCI_CUE,
                              MCI_WAIT,
                              (DWORD)(LPVOID)NULL);
    if ((dwResult != 0) && (dwResult!=261)) {
        MCIDLLError(dwResult);
        m_OpenParams.wDeviceID = 0;
        return FALSE;
    }
*/    
    OutputDebugString("I just Opened the file... \n");
    return TRUE;
}

BOOL MidiClose(MCI_MIDI_STRUCT *mciMidiInfo)
{
    MCI_GENERIC_PARMS gp;
    DWORD dwResult;

    if (!(mciMidiInfo->fOpened))
        return FALSE; // Already closed.

    MidiStop(mciMidiInfo); // Just in case.
    dwResult = mciSendCommand(mciMidiInfo->wMIDIDeviceID,
                              MCI_CLOSE,
                              MCI_NOTIFY,
                              (DWORD)(LPVOID)&gp);
    if (dwResult != 0) {
        MCIError("MCI_CLOSE", dwResult);
    }
    
    mciMidiInfo->wMIDIDeviceID = 0;    
    mciMidiInfo->fOpened = FALSE;
    
    OutputDebugString("I just closed the file... \n");

	return TRUE;
}

BOOL MidiPlay(MCI_MIDI_STRUCT *mciMidiInfo)
{
    MCI_PLAY_PARMS play;
    DWORD dwResult;
    DWORD dwFlags;
	long lduration;

    if (mciMidiInfo->fOpened == FALSE) 
        return FALSE; // Not open

	lduration = mciMidiInfo->lMIDIduration;
	play.dwFrom = 0;
	if (lduration<0)
		play.dwTo = (DWORD)-lduration;
	else
		play.dwTo = (DWORD)lduration;
    play.dwCallback = MAKELONG(mciMidiInfo->hWndParent,0);

    if (mciMidiInfo->fNotify)
	    dwFlags = MCI_NOTIFY;

	if (lduration != 0)
	{
		if (lduration <0)
			dwFlags = dwFlags|MCI_TO;
		else
			dwFlags = dwFlags|MCI_FROM|MCI_TO;
	}

    dwResult = mciSendCommand(mciMidiInfo->wMIDIDeviceID,
                              MCI_PLAY,
                              dwFlags,
                              (DWORD)(LPVOID)&play);
    if (dwResult != 0) {
        MCIError("MCI_PLAY", dwResult);
    }

    mciMidiInfo->fPlaying = TRUE;

    OutputDebugString("I am playing the file... \n");

	return TRUE;
}

BOOL MidiStop(MCI_MIDI_STRUCT *mciMidiInfo)
{
    DWORD dwResult;

    if (mciMidiInfo->fOpened == FALSE) 
        return FALSE; // Not open

    dwResult = mciSendCommand(mciMidiInfo->wMIDIDeviceID,
                              MCI_STOP,
                              MCI_WAIT,
                              (DWORD)(LPVOID)NULL);
    if (dwResult != 0) {
        MCIError("MCI_STOP", dwResult);
    }

    OutputDebugString("I am stoping playback... \n");
	return TRUE;
}

BOOL MidiPause(MCI_MIDI_STRUCT *mciMidiInfo)
{
    if (!(mciMidiInfo->fPlaying))
        return FALSE;

	/* tell it to pause */
	mciSendCommand(mciMidiInfo->wMIDIDeviceID,MCI_PAUSE,0L,
					(DWORD) NULL);
    
    mciMidiInfo->fPlaying = FALSE;

    return TRUE;
}

BOOL MidiSeek(MCI_MIDI_STRUCT *mciMidiInfo)
{
    MCI_SEEK_PARMS mciSeek;

    mciMidiInfo->fPlaying = FALSE;
    mciSeek.dwTo = mciMidiInfo->iSeekThere;
    mciSendCommand(mciMidiInfo->wMIDIDeviceID, MCI_SEEK, MCI_TO,
    						(DWORD)(LPMCI_SEEK_PARMS) &mciSeek);
    return TRUE;   
}