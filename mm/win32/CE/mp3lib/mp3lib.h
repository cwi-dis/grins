
// The following ifdef block is the standard way of creating macros which make exporting 
// from a DLL simpler. All files within this DLL are compiled with the MP3LIBCE_EXPORTS
// symbol defined on the command line. this symbol should not be defined on any project
// that uses this DLL. This way any other project whose source files include this file see 
// MP3LIBCE_API functions as being imported from a DLL, wheras this DLL sees symbols
// defined with this macro as being exported.
#ifdef MP3LIB_EXPORTS
#define MP3LIB_API __declspec(dllexport)
#else
#define MP3LIB_API __declspec(dllimport)
#endif

MP3LIB_API void mp3_lib_init(int,char*);
MP3LIB_API void mp3_lib_finalize(void);
MP3LIB_API int mp3_lib_decode_header(unsigned char * inbuff, int insize, int* Freq, int* ch, int* br);
MP3LIB_API int mp3_lib_decode_buffer(unsigned char * inbuff, int insize, char *outmemory, int outmemsize, int *done, int* inputpos);
