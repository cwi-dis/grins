
// Microsoft PowerPoint File Format Record Names
// Based on PowerPoint BIFF.doc (PowerPoint 97)

#ifndef INC_PPTYPES
#define INC_PPTYPES

typedef signed long	sint4;				// signed 4-byte integral value
typedef signed short sint2;				// signed 4-byte integral value
typedef unsigned long uint4;			// unsigned 4-byte integral value
typedef unsigned short uint2;			// 2-byte
typedef char bool1;						// 1-byte boolean
typedef unsigned char ubyte1;			// unsigned byte value
typedef uint2 psrType;
typedef uint4 psrSize;					// each record is preceeded by 
										// pssTypeType and pssSizeType.
typedef uint2 psrInstance;
typedef uint2 psrVersion;
typedef uint4 psrReference;				// Saved object reference

typedef unsigned long DWord;

#endif

