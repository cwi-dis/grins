/****************************************************************************
 *
 *  $Id$
 *
 *  Copyright (C) 1995,1996,1997 Progressive Networks, Inc.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary and confidential
 *  information of Progressive Networks, Inc.  Do not DISTRIBUTE.
 *
 *
 *  Exhaustive list of Private IID's used in IRMA interfaces
 *
 *  THIS FILE IS PRIVATE AND NOT TO BE GIVEN OUT TO THE THIRD PARTY DEVELOPERS
 *
 */

#ifndef _RMAPRIVATEIIDS_H_
#define _RMAPRIVATEIIDS_H_

/*
 *  File:
 *	rmcorgui.h
 *  Description:
 *	Interfaces used by gui to get info from core
 *  Interfaces:
 *	IID_IRMACoreGuiHook:	{00000000-b4c8-11d0-9995-00a0248da5f0}

 */
DEFINE_GUID(IID_IRMACoreGuiHook,    0x00000000, 0xb4c8, 0x11d0, 0x99, 0x95,
0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAInternalReset,    0x00000001, 0xb4c8, 0x11d0, 0x99, 0x95,
0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmbdwdth.h
 * Description:
 *    Interface used by raffplin and rmffplin to support 3.0/4.0 style
 *    Bandwidth negotiation.
 * Interfaces:
 *    IID_IRMABandwidthNegotiator: {00000100-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMABandwidthNegotiator,    0x00000100, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMABandwidthLister,        0x00000101, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmaphand.h
 *    
 * Description:
 *    Interface for PluginHandler - non-IRMA, just gimme the pointer
 *    Bandwidth negotiation.
 * Interfaces:
 *    IID_IRMAPluginHandler: {00000200-b4c8-11d0-9995-00a0248da5f0}
 *    IID_IRMAPlugin2Handler:{00000201-b4c8-11d0-9995-00a0248da5f0}
 */


#ifndef _RMAPLUGN_H_
DEFINE_GUID(IID_IRMAPluginHandler,	0x00000200, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAPlugin2Handler,	0x00000201, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
#endif
#ifndef _RMAPHAND_H_
DEFINE_GUID(IID_IRMAPlugin2HandlerEnumeratorInterface,	0x00000202, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
#endif

/*
 * File:
 *    rmartsp/pub/rtspif.h
 * Description:
 *    Interface for resend handling.
 * Interfaces:
 *    IID_IRMAPacketResend: {00000400-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMAPacketResend,     0x00000400, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmartsp/pub/rtspif.h
 * Description:
 *    Interface for Context.
 * Interfaces:
 *    IID_IRMARTSPContext: {00000401-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMARTSPContext,     0x00000401, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    pnupdate.h
 * Description:
 *    Interface for getting file objects to the RealUpdate renderer
 * Interfaces:
 *    IID_IRMAUpdateRenderer: {00000500-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMAUpdateRenderer, 0x00000500, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
/* From file pnrup/pub/pnrup.h, but related nonetheless. */
DEFINE_GUID(IID_IRMACPNRealUpdateResponse, 0x00000501, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAUpdateRendererResponse, 0x00000502, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *      rmapnets.h
 *  Description:
 *      Cloaked HTTP Network Services. Creation of cloaked Client and
 *      Server sockets.
 *  Interfaces:
 *  	IID_IRMACloakedNetworkServices	{00000600-b4c8-11d0-9995-00a0248da5f0}
 *  	IID_IRMAHTTPProxy		{00000601-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMACloakedNetworkServices, 0x00000600, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAHTTPProxy, 0x00000601, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *	rmameta.h
 *  Description:
 *	Metafile creation & navigation Interfaces
 *  Interfaces:
 *	IID_IRMAMetaTrack:    		{00000E01-0901-11d1-8B06-00A024406D59}
 *	IID_IRMAMetaGroup:    		{00000E02-0901-11d1-8B06-00A024406D59}
 *	IID_IRMAMetaLayout:		{00000E03-0901-11d1-8B06-00A024406D59}
 *	IID_IRMAMetaTuner:		{00000E04-0901-11d1-8B06-00A024406D59}
 *	IID_IRMAMetaFileFormatObject:	{00000E05-0901-11d1-8B06-00A024406D59}
 *	IID_IRMAMetaFileFormatResponse:	{00000E06-0901-11d1-8B06-00A024406D59}
 *	IID_IRMASiteLayout:		{00000E07-0901-11d1-8B06-00A024406D59}
 */
DEFINE_GUID(IID_IRMAMetaTrack,		    0x00000E01, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMAMetaGroup,		    0x00000E02, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMAMetaLayout,		    0x00000E03, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMAMetaTuner,		    0x00000E04, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMAMetaFileFormatObject,   0x00000E05, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMAMetaFileFormatResponse, 0x00000E06, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMASiteLayout,		    0x00000E07, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

/*
 *  File:
 *	rmasrc.h
 *  Description:
 *	Interfaces related to raw sources and sinks
 *  Interfaces:
 *	IID_IRMARawSourceObject:	{00001000-0901-11d1-8B06-00A024406D59}
 *	IID_IRMARawSinkObject:		{00001001-0901-11d1-8B06-00A024406D59}
 *	IID_IRMASourceFinderObject:	{00001002-0901-11d1-8B06-00A024406D59}
 *	IID_IRMASourceFinderResponse:	{00001003-0901-11d1-8B06-00A024406D59}
 */
DEFINE_GUID(IID_IRMARawSourceObject, 0x00001000, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMARawSinkObject, 0x00001001, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMASourceFinderObject, 0x00001002, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMASourceFinderResponse, 0x00001003, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

/*
 *  File:
 *	rmatbuf.h
 *  Description:
 *	Interface related TimeStamped IRMABuffers
 *  Interfaces:
 *	IID_IRMATimeStampedBuffer:	{00000700-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMATimeStampedBuffer, 0x00000700, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *	rmasmbw.h
 *  Description:
 *	Interface related the ASM Bandwidth Manager
 *  Interfaces:
 *	IID_IRMABandwidthManager:		{00000800-b4c8-11d0-9995-00a0248da5f0}
 *	IID_IRMASourceBandwidthInfo:		{00000801-b4c8-11d0-9995-00a0248da5f0}
 *	IID_IRMABandwidthManagerInput:		{00000802-b4c8-11d0-9995-00a0248da5f0}
 *	IID_IRMAStreamBandwidthNegotiator:	{00000803-b4c8-11d0-9995-00a0248da5f0}
 *  	IID_IRMAStreamBandwidthBias: 		{00000804-b4c8-11d0-9995-00a0248da5f0}
 *      IID_IRMAThinnableSource:		{00000805-b4c8-11d0-9995-00a0248da5f0}
 *      IID_IRMABandwidthNudger:		{00000806-b4c8-11d0-9995-00a0248da5f0}
 *      IID_IRMAASMProps:			{00000807-b4c8-11d0-9995-00a0248da5f0}
 *      IID_IRMAAtomicRuleChange:		{00000808-b4c8-11d0-9995-00a0248da5f0}
 *      IID_IRMAAtomicRuleGather:		{00000809-b4c8-11d0-9995-00a0248da5f0}
 *      IID_IRMAPlayerState:			{0000080A-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMABandwidthManager, 0x00000800, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMASourceBandwidthInfo, 0x00000801, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMABandwidthManagerInput, 0x00000802, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAStreamBandwidthNegotiator, 0x00000803, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAStreamBandwidthBias, 0x00000804, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAThinnableSource, 0x00000805, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMABandwidthNudger, 0x00000806, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAASMProps, 0x00000807, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAAtomicRuleChange, 0x00000808, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAAtomicRuleGather, 0x00000809, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAPlayerState,      0x0000080A, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *  	rmavctrl.c
 *  Description:
 *  	Video Control Interface
 *  Interface:
 *  	IID_IRMAVideoControl:       {00000900-b4c8-11d0-9995-00a0248da5f0}
 *
 */
DEFINE_GUID(IID_IRMAVideoControl, 0x00000900, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *      rmaxres.h
 *  Description:
 *	Cross platform resource reading class. Reads resources directly
 *	from Win32 DLL's and EXEs on any platform.
 *
 *  Interfaces:
 *	IID_IRMAXResFile	    	    {00000A00-b4c8-11d0-9995-00a0248da5f0}
 *	IID_IRMAXResource	    	    {00000A01-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMAXResFile, 		0x00000A00, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAXResource, 		0x00000A01, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *      rmarasyn.h
 *  Description:
 *	RealAudio Synchronization interface
 *
 *  Interfaces:
 *	IID_IRMARealAudioSync	    	    {00000B00-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMARealAudioSync, 	0x00000B00, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *      rmashtdn.h
 *  Description:
 *	Shut down all the plugins
 *
 *  Interfaces:
 *	IID_IRMAShutDownEverything	    {00000C00-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMAShutDownEverything, 0x00000C00, 0xb4c8, 0x11d0, 0x99, 
					0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *	rmaslta.h
 *  Description:
 *	RMA version of slta.  Simulates a live stream from file format.
 *
 *  Interfaces:
 *	IID_IRMASLTA			    {00000D00-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMASLTA,   0x00000D00, 0xb4c8, 0x11d0, 0x99, 
			    0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmagroup.h
 * Description:
 *    Interface for precache manager
 * Interfaces:
 *    IID_IRMAPreCacheMgr: {00000E00-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMAPreCacheGroupMgr,    0x00000E00, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmadataf.h
 * Description:
 *    Interface for basic data file operations
 * Interfaces:
 *    IID_IRMADataFileFactory:	{00000F00-b4c8-11d0-9995-00a0248da5f0}
 *    IID_IRMADataFile:		{00000F01-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMADataFileFactory,	0x00000F00, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMADataFile,		0x00000F01, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    memfsys.h
 * Description:
 *    Interface for basic data file operations
 * Interfaces:
 *    IID_IRMAMemoryFileContext:	{00001000-b4c8-11d0-9995-00a0248da5f0}
 *    IID_IRMAMemoryFileSystem:		{00001001-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMAMemoryFileContext,	0x00001000, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAMemoryFileSystem,	0x00001001, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmarsdbf.h
 * Description:
 *    Interface for resend buffer management
 * Interfaces:
 *    IID_IRMAResendBufferControl:	{00002B00-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMAResendBufferControl,	0x00002B00, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmatset.h
 * Description:
 *    Timeout settings interface
 * Interfaces:
 *    IID_IRMATimeoutSettings:	{950A6ED6-36D5-11d2-8F78-0060083BE561}
 */
#ifndef _RMATSET_H_
DEFINE_GUID(IID_IRMATimeoutSettings,	0x950a6ed6, 0x36d5, 0x11d2, 0x8f, 0x78, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x61);
#endif
/*
 * File:
 *    rmaspriv.h
 * Description:
 *    Interface for descriptor registration
 * Interfaces:
 *    IID_IRMADescriptorRegistration:  {00001100-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMADescriptorRegistration, 0x00001100, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 * File:
 *    rmaxrsmg.h
 * Description:
 *    Interface for external resource manager
 * Interfaces:
 *    IID_IRMAExternalResourceManager:  {00001200-b4c8-11d0-9995-00a0248da5f0}
 *    IID_IRMAExternalResourceReader:   {00001201-b4c8-11d0-9995-00a0248da5f0}
 */
DEFINE_GUID(IID_IRMAExternalResourceManager, 0x00001200, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);
DEFINE_GUID(IID_IRMAExternalResourceReader,  0x00001201, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

/*
 *  File:
 *      rmacredc.h
 *  Description:
 *	Interface for credential(username/password) cache
 *
 *  Interfaces:
 *	IID_IRMACredentialsCache		{00002B00-0901-11d1-8B06-00A024406D59}
 */

DEFINE_GUID(IID_IRMACredentialsCache,	0x00002B00, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);


/*
 *  File:
 *      rmaxml.h
 *  Description:
 *	Interface for XML parser
 *
 *  Interfaces:
 *	IID_IRMAXMLParser   		{00002D00-0901-11d1-8B06-00A024406D59}
 *	IID_IRMAXMLParserResponse	{00002D01-0901-11d1-8B06-00A024406D59}
 */

DEFINE_GUID(IID_IRMAXMLParser,		0x00002D00, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);
DEFINE_GUID(IID_IRMAXMLParserResponse,	0x00002D01, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

/*
 *  File:
 *      rmaisskd.h
 *  Description:
 *	Interface for Server list which executes the callbacks when
 *      the mutex is unlocked.
 *
 *  Interfaces:
 *    IID_IRMAThreadSafeExecutionList:   {00001501-b4c8-11d0-9995-00a0248da5f0}
 */

DEFINE_GUID(IID_IRMAThreadSafeExecutionList,  0x00001501, 0xb4c8, 0x11d0, 0x99, 0x95, 0x0, 0xa0, 0x24, 0x8d, 0xa5, 0xf0);

#endif /* _RMAPRIVATEIIDS_H_ */		    
