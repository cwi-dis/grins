#include <windows.h>
#include <mmsystem.h> // We need the Windows MM header for the MCIERROR structure.

#ifdef __cplusplus
extern "C" {
#endif

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

#ifdef FREEZE_MCIDLL
#	define MCIAPI 
#else
#	ifdef BUILD_MCIDLL
#		define MCIAPI __declspec(dllexport)
#	else
#		define MCIAPI __declspec(dllimport)
#		ifdef _DEBUG
#			pragma comment(lib, "mcidll_d.lib")
#		else
#			pragma comment(lib, "mcidll.lib")
#		endif
#	endif
#endif

MCIAPI void MCIError(char *mes, MCIERROR rc);

MCIAPI void positionMovie(MCI_AVI_STRUCT *mciAviInfo);

MCIAPI BOOL AviOpen(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI BOOL AviPlay(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI BOOL AviPause(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI BOOL AviStop(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI BOOL AviClose(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI BOOL AviSeek(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI long AviFrame(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI DWORD AviDuration(MCI_AVI_STRUCT *mciAviInfo);
MCIAPI void AviSize(MCI_AVI_STRUCT *mciAviInfo, RECT* rec);
MCIAPI BOOL AviUpdate(MCI_AVI_STRUCT *mciAviInfo);

MCIAPI BOOL MidiOpen(MCI_MIDI_STRUCT *mciMidiInfo);
MCIAPI BOOL MidiPlay(MCI_MIDI_STRUCT *mciMidiInfo);
MCIAPI BOOL MidiPause(MCI_MIDI_STRUCT *mciMidiInfo);
MCIAPI BOOL MidiStop(MCI_MIDI_STRUCT *mciMidiInfo);
MCIAPI BOOL MidiClose(MCI_MIDI_STRUCT *mciMidiInfo);
MCIAPI BOOL MidiSeek(MCI_MIDI_STRUCT *mciMidiInfo);

#ifdef __cplusplus
}
#endif
