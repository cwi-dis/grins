
// The following ifdef block is the standard way of creating macros which make exporting 
// from a DLL simpler. All files within this DLL are compiled with the MP3LIBCE_EXPORTS
// symbol defined on the command line. this symbol should not be defined on any project
// that uses this DLL. This way any other project whose source files include this file see 
// MP3LIBCE_API functions as being imported from a DLL, wheras this DLL sees symbols
// defined with this macro as being exported.
#ifdef MS_NO_COREDLL
#define MP3LIB_API
#else
#ifdef MP3LIB_EXPORTS
#define MP3LIB_API __declspec(dllexport)
#else
#define MP3LIB_API __declspec(dllimport)
#endif
#endif

MP3LIB_API void mp3_lib_create_instance(void **pp);
MP3LIB_API void mp3_lib_release_instance(void *vps);

MP3LIB_API void mp3_lib_init(void *vps, int,char*);
MP3LIB_API void mp3_lib_finalize(void *vps);
MP3LIB_API int mp3_lib_decode_header(void *vps, unsigned char * inbuff, int insize, int* Freq, int* ch, int* br);
MP3LIB_API int mp3_lib_decode_buffer(void *vps, unsigned char * inbuff, int insize, char *outmemory, int outmemsize, int *done, int* inputpos);
