#include <windows.h>

typedef struct {
    BOOL fPlaying;
    BOOL fOpened;
    BOOL fReverse;
    BOOL fStretch;
    BOOL fNotify;
    int format;
    int  iTotalLength;
    int  iSignalSteps;
    char szFileName[256];
    HWND hWndParent;
    HWND hWndMovie;
    WORD wAVIDeviceID;
    int iSeekThere;
	long lAVIduration;
	float scale;
	BOOL center;
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
	long lMIDIduration;
} MCI_MIDI_STRUCT;


void MCIError(char *mes, MCIERROR rc);

void positionMovie(MCI_AVI_STRUCT *mciAviInfo);

BOOL AviOpen(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviPlay(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviPause(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviStop(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviClose(MCI_AVI_STRUCT *mciAviInfo);
BOOL AviSeek(MCI_AVI_STRUCT *mciAviInfo);
long AviFrame(MCI_AVI_STRUCT *mciAviInfo);
DWORD AviDuration(MCI_AVI_STRUCT *mciAviInfo);
void AviSize(MCI_AVI_STRUCT *mciAviInfo, RECT* rec);

BOOL MidiOpen(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiPlay(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiPause(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiStop(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiClose(MCI_MIDI_STRUCT *mciMidiInfo);
BOOL MidiSeek(MCI_MIDI_STRUCT *mciMidiInfo);

