/****************************************************************************
 * 
 *	rmafread.h
 *
 *	$Id$
 *
 *	Copyright ©1998 RealNetworks.
 *	All rights reserved.
 *
 *	Definition of the Interfaces for the RMFF2 File Reader SDK.
 *
 */

#ifndef _RMAFREAD_H_
#define _RMAFREAD_H_

// Prototype to create instance of RMFF2Reader object and 
// typedef to get a pointer to this function from the dll
typedef PN_RESULT (PNEXPORT_PTR FPCREATEINSTANCE) (IUnknown** /*OUT*/ ppIUnknown);
STDAPI RMACreateRMFF2Reader(IUnknown**  /*OUT*/	ppIUnknown);

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMFF2Reader
 *
 *  Purpose:
 *
 *	Interface to rmcut module
 *
 *  IRMARMFF2Reader
 *
 *  {649295B0-0C77-11d2-A1BD-0060083BE563}
 *
 */

DEFINE_GUID(IID_IRMARMFF2Reader, 
0x649295b0, 0xc77, 0x11d2, 0xa1, 0xbd, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x63);

#define CLSID_IRMARMFF2Reader IID_IRMARMFF2Reader


#undef  INTERFACE
#define INTERFACE   IRMARMFF2Reader

class MediaProperties;
class PacketHeader;
class PacketHeader1;
class Content;
class Properties;

// this struct is used to store the stream numbers for a given stream pair
typedef struct Stream_Pair
{
	UINT16 unPhysicalStream1;
	UINT16 unPhysicalStream2;
} STREAM_PAIR;

// this struct is used to store info for each unique data section
typedef struct Data_Section_Info
{
	UINT32	ulDataOffset;	
	UINT32	ulDataEnd;			// the end of this data section in the file
	UINT32	ulIndexOffset;
	UINT32	ulDataBytesRemaining;	// the number of bytes left to read
	UINT16	unPhysicalStreamNumber; // note: the interleaved data section may contain more streams
	BOOL	bInterleavedBackwardsCompatible;
} DATA_SECTION_INFO;

// this struct is used to store info about each individual physical stream
typedef struct Physical_Stream_Info
{
	MediaProperties* pMediaProperties;
	UINT16			unPhysicalStreamNumber;
	UINT16			unLogicalStreamNumber;
	UINT32			ulDataOffset;
	UINT32			ulIndexOffset;
	UINT32			ulBandwidth;
	UINT16			unKeyframeRule;		// the ASM rule for a keyframe packet
	BOOL			bInterleavedBackwardsCompatible;
	BOOL			bTaggedBackwardsCompatible;
	BOOL			bIncludeAsMultirate;
	BOOL			bOwnsDataSection;		// if TRUE, then this stream is the owner of the data section.
											// All other streams refering to the data section are virtual.
	BOOL			bOldPlayer;				// True is this stream is an ASM old player stream
} PHYSICAL_STREAM_INFO;

DECLARE_INTERFACE_(IRMARMFF2Reader, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    // *** IRMARMFF2Reader methods ***
 
	// ***	Basic Interface ***
 
	// returns the version number of the input file. 1 == .rm1 file, 2 == .rm2 file
	STDMETHOD(GetFileVersion) (THIS_
				UINT32* pulVersion) PURE;                   

	// opens the specified .rm file
	STDMETHOD(Open) (THIS_
				const char* szFileName) PURE;  

	// closes the .rm file
	STDMETHOD(Close) (THIS) PURE;  

	// seeks to the specifed time in the specified data section. Returns in pulActualTime the
	// actual time that was seeked to.
	STDMETHOD(DataSectionSeek) (THIS_
				UINT16 unIndex, UINT32 ulTimeRequested, UINT32* pulActualTime) PURE;  

	STDMETHOD(InterleavedAudioDataSectionSeek) (THIS_
				DATA_SECTION_INFO* pDataSectionInfo, UINT32 ulTimeRequested, UINT32* pulActualTime) PURE;

	STDMETHOD(DataSectionSeek) (THIS_
				DATA_SECTION_INFO* pDataSectionInfo, UINT32 ulTimeRequested, UINT32* pulActualTime) PURE;  
	// Gets the size of the largest packet you will
	// encounter in this file. You can use this
	// to allocate your packet reading buffer.
	STDMETHOD(GetMaxPacketSize) (THIS_
				UINT32* pulMaxSize) PURE;

	// reads from the currently active interleaved backwards compatible section. Use this
	// method to read from the data section if the bInterleavedBackwardsCompatible in the
	// corresponding PHYSICAL_STREAM_INFO or DATA_SECTION_INFO is TRUE. If you are copying
	// this file using crmfile2.cpp to write the file, then you will need to read and write
	// all of the interleaved packets first.
	STDMETHOD(ReadPacket) (THIS_
			PacketHeader* pPacketInfo,UINT8* pData,UINT32 ulBufSize,UINT32* pulDataLength) PURE;  

	// reads from the currently active data section. You make a data section active by using
	// the DataSectionSeek function. This implementation of a RMFF file reader only 
	// supports reading from one data section at a time since it is used mainly for the
	// editing of .rm files. Use this method to read from the data section if the 
	// bInterleavedBackwardsCompatible in the corresponding PHYSICAL_STREAM_INFO or 
	// DATA_SECTION_INFO is FALSE.
	STDMETHOD(ReadPacket1) (THIS_
			PacketHeader1* pPacketInfo1,UINT8* pData,UINT32 ulSize,UINT32* pulDataLength) PURE;  

	// returns the number of physical streams in the file
	STDMETHOD(GetNumPhysicalStreams) (THIS_
			UINT16* p_unNumStreams) PURE;

	// returns the number of physical streams in the interleaved section of the file
	STDMETHOD(GetNumInterleavedPhysicalStreams) (THIS_
			UINT16* p_unNumStreams) PURE;

	// returns the PHYSICAL_STREAM_INFO struct specified by index
	STDMETHOD(GetIndexedPhysicalStreamInfo) (THIS_
					UINT16 unIndex, PHYSICAL_STREAM_INFO** pStreamInfo) PURE;

	// returns the PHYSICAL_STREAM_INFO struct specified by stream number
	STDMETHOD(GetPhysicalStreamInfo) (THIS_
					UINT16 unStreamNum, PHYSICAL_STREAM_INFO** pStreamInfo) PURE;

	// returns the number of logical streams in the file
	STDMETHOD(GetNumLogicalStreams) (THIS_
			UINT16* punNumStreams) PURE;

	// returns the number of paired physical streams (Uber Rules) in the file
	STDMETHOD(GetNumPairedStreams) (THIS_
			UINT16* punNumStreams) PURE;

	// returns the stream numbers of the paired streams (Uber Rules) specified by the index parameter
	STDMETHOD(GetIndexedPairedStreamNums) (THIS_
			UINT16 unIndex, UINT16* punPhysicalStream1, UINT16* punPhysicalStream2) PURE;

	// returns the number of unique data sections in the file
	STDMETHOD(GetNumDataSections) (THIS_
			UINT16* punNumDataSections) PURE;

	// returns the stream numbers of the paired streams (Uber Rules) specified by the index parameter
	STDMETHOD(GetIndexedDataSectionInfo) (THIS_
			UINT16 unIndex, DATA_SECTION_INFO** pDataSectionInfo) PURE;

	// returns the DATA_SECTION_INFO struct of the interleaved data section
	STDMETHOD(GetInterleavedDataSectionInfo) (THIS_
			DATA_SECTION_INFO** pDataSectionInfo) PURE;

	// returns the DATA_SECTION_INFO struct specified by stream number
	STDMETHOD(GetDataSectionInfo) (THIS_
					UINT16 unStreamNum, DATA_SECTION_INFO** pDataSectionInfo) PURE;

	// returns the property flags (Selective Record, MobilePlay etc.)
	STDMETHOD(GetPropertyFlags) (THIS_
			UINT16* punFlags) PURE;

	// returns the Property Header
	STDMETHOD(GetPropertiesHeader) (THIS_
			Properties** pPropertyHeader) PURE;

	// returns the Content Header Info (Title, Author, Copyright, etc.)
	STDMETHOD(GetContentHeader) (THIS_
			Content** pContentHeader,UINT32* pnContentSize) PURE;

	// returns the end time of the file
	STDMETHOD(GetEndTime) (THIS_
			UINT32* pnEndTime) PURE;
};


#endif //_RMAFREAD_H_