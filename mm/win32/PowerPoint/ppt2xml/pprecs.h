
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

////////////////////////////
// Constructed

struct PSR_GPointAtom
{
	sint4 x;
	sint4 y;
};
typedef PSR_GPointAtom PSR_GLPointAtom;

struct PSR_GRatioAtom
{
	sint4 numer;
	sint4 denom;
};

struct PSR_GRColorAtom
{
	ubyte1 red;
	ubyte1 green;
	ubyte1 blue;
	ubyte1 index;
};
typedef PSR_GRColorAtom PSR_GRColor;

struct PSR_GRectAtom
{
	sint4 left;
	sint4 top;
	sint4 right;
	sint4 bottom;
};

struct PSR_GScalingAtom
{
	PSR_GRatioAtom x;
	PSR_GRatioAtom y;
};

struct PSR_GuideAtom
{
	sint4 type;
	sint4 pos;
};

struct PSR_HeaderMCAtom
{
	sint4 position;
};

struct PSR_HeadersFooterDateAtom
{
	sint2 formatId;
	uint2 flags;
};

struct PSR_Int4ArrayAtom
{
	uint4 size;
	uint4 elements[1];
};

struct PSR_InteractiveInfoAtom
{
	uint4 soundRef;
	uint4 exHyperlinkID;
	ubyte1 action;
	ubyte1 oleVerb;
	ubyte1 jump;
	ubyte1 flags;
	ubyte1 hyperlinkType;
};

enum Action 
{
	NoAction = 0,
	MacroAction = 1,
	RunProgramAction = 2,
	JumpAction = 3,
	HyperlinkAction = 4,
	OLEAction = 5,
	MediaAction = 6,
	CustomShowAction = 7
};

enum Jump
{
	NoJump = 0,
	NextSlide = 1,
	PreviousSlide = 2,
	FirstSlide = 3,
	LastSlide = 4,
	LastSlideViewed = 5,
	EndShow = 6
};

enum ListInstance 
{
	DocInfoList = 12,
	DocMasterList = 11,
	DocSlideList = 10, 
	Embedees = 18,
	GroupElementList = 15,
	GuideListElement = 56,
	ListElement = 16,
	OEInfoListElement = 17,
	OElements = 20,
	SchemeListElement = 55,
	SlideElementListElement = 19
};

struct PSR_NotesAtom
{
	sint4 slideId;
};

struct PSR_OEPlaceholderAtom
{
	ubyte1 placeholderId;
	ubyte1	size;
	uint2 padding;
	uint4 placementId;
};

struct PSR_GAngleAtom
{
	sint4 rotation;
};

struct PSR_OEShapeAtom
{
	sint4 index;
	sint4 adjust;
	bool1 flip;
	ubyte1 padding[3];
	PSR_GRectAtom bounds;
	PSR_GAngleAtom	rotation;
	sint4 curIndex;
	bool1 hasTextInfo;
	bool1 hasExtInfo;
	ubyte1 padding2[2];
};


#endif
