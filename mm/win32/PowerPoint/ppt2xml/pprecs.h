
// Microsoft PowerPoint File Format Records
// Based on PowerPoint BIFF.doc (PowerPoint 97)

#ifndef INC_PPRECS
#define INC_PPRECS

#ifndef INC_PPTYPES
#include "pptypes.h"
#endif

// PowerPoint records structs

// We should have ~160 different record structs
// What we manage to reconstruct will be appended here

// The following 4 structs are from PowerPoint BIFF.doc
struct RecordHeader
{
	psrVersion	  recVer : 4;						// may be PSFLAG_CONTAINER
	psrInstance	  recInstance : 12; 
	psrType		  recType;
	psrSize		  recLen;
};

struct PSR_CurrentUserAtom
{
	uint4  size;
	uint4  magic;  // Magic number to ensure this is a PowerPoint file.
	uint4  offsetToCurrentEdit;	 // Offset in main stream to current edit field.
	uint2  lenUserName;
	uint2  docFileVersion;
	ubyte1 majorVersion;
	ubyte1 minorVersion;
};

struct PSR_UserEditAtom
{
	sint4  lastSlideID;				// slideID
	uint4  version;					// This is major/minor/build which did the edit
	uint4  offsetLastEdit;			// File offset of last edit
	uint4  offsetPersistDirectory;  // Offset to PersistPtrs for this file version.
	uint4  documentRef;
	uint4  maxPersistWritten;		// Addr of last persist ref written to the file (max seen so far).
	sint2  lastViewType;			 // enum view type
};

struct PSR_SlidePersistAtom
{
	uint4  psrReference;
	uint4  flags;
	sint4  numberTexts;
	sint4  slideId;
	uint4  reserved;
};

// Reconstructed

// ...


#endif
