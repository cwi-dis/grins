#ifndef INC_WIN32EXT
#define INC_WIN32EXT

#include "moddef.h"

DECLARE_PYMODULECLASS(Cmifex);
DECLARE_PYMODULECLASS(Cmifex2);
DECLARE_PYMODULECLASS(Soundex);
DECLARE_PYMODULECLASS(Gifex);
DECLARE_PYMODULECLASS(Htmlex);
DECLARE_PYMODULECLASS(Imageex);
DECLARE_PYMODULECLASS(Midiex);
DECLARE_PYMODULECLASS(Mpegex);
DECLARE_PYMODULECLASS(Timerex);

#define DEF_EXT_PY_METHODS \
	{"GetCmifex",MCmifex::create,1},\
	{"GetCmifex2",MCmifex2::create,1},\
	{"GetSoundex",MSoundex::create,1},\
	{"GetGifex",MGifex::create,1},\
	{"GetHtmlex",MHtmlex::create,1},\
	{"GetImageex",MImageex::create,1},\
	{"GetMidiex",MMidiex::create,1},\
	{"GetMpegex",MMpegex::create,1},\
	{"GetTimerex",MTimerex::create,1},\


#endif