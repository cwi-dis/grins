
void Format(string& stdstr,LPCTSTR lpszFormat, ...);
int GetFormatLength(LPCTSTR lpszFormat,va_list argList);




// String MFC type formatting

struct _AFX_DOUBLE  { BYTE doubleBits[sizeof(double)]; };

#ifdef _MAC
	#define TCHAR_ARG   int
	#define WCHAR_ARG   unsigned
	#define CHAR_ARG    int
#else
	#define TCHAR_ARG   TCHAR
	#define WCHAR_ARG   WCHAR
	#define CHAR_ARG    char
#endif

#if defined(_68K_) || defined(_X86_)
	#define DOUBLE_ARG  _AFX_DOUBLE
#else
	#define DOUBLE_ARG  double
#endif

#define FORCE_ANSI      0x10000
#define FORCE_UNICODE   0x20000
