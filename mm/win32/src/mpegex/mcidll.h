#ifndef MCIAPI_H
#define MCIAPI_H

#include <windows.h>
#include <mmsystem.h>

#define MCIAPI __declspec( dllexport )

typedef struct {
    BOOL fPlaying;
    BOOL fOpened;
    BOOL fReverse;
    BOOL fStretch;
    BOOL fNotify;
    enum { FRAMES, TIME } format;
    int  iTotalLength;
    int  iSignalSteps;
    char szFileName[256];
    HWND hWndParent;
    HWND hWndMovie;
    WORD wAVIDeviceID;
    int iSeekThere;
} MCI_AVI_STRUCT;

typedef struct {
    BOOL fPlaying;
    BOOL fOpened;        
    BOOL fNotify;    
    int  iTotalLength;
    int  iSignalSteps;
    char szFileName[256];    
    HWND hWndParent;
    WORD wMIDIDeviceID;
    int iSeekThere;
} MCI_MIDI_STRUCT;


#ifdef __cplusplus
extern "C" {
#endif

void MCIError(char *mes, MCIERROR rc);

void positionMovie(MCI_AVI_STRUCT *mciAviInfo);

BOOL AviOpen(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviPlay(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviPause(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviStop(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviClose(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviSeek(MCI_AVI_STRUCT *mciAviInfo);

BOOL MidiOpen(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiPlay(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiPause(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiStop(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiClose(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiSeek(MCI_MIDI_STRUCT *mciMidiInfo);

#ifdef __cplusplus
}
#endif

