/*++

Copyright (c) 1992  Microsoft Corporation

Module Name:

    nserror.mc

Abstract:

    Definitions for NetShow events.

Author:


Revision History:

Notes:

    This file is used by the MC tool to generate the nserror.h file

**************************** READ ME ******************************************

 Here are the commented error ranges for the Windows Media Technologies Group


 LEGACY RANGES

     0  -  199 = General NetShow errors
               
   200  -  399 = NetShow error events

   400  -  599 = NetShow monitor events

   600  -  799 = NetShow IMmsAutoServer errors

  1000  - 1199 = NetShow MCMADM errors


 NEW RANGES

  2000 -  2999 = ASF (defined in ASFERR.MC)

  3000 -  3999 = Windows Media SDK

  4000 -  4999 = Windows Media Player

  5000 -  5999 = Windows Media Server

  6000 -  6999 = Windows Media Networking (defined in NETERROR.MC)

  7000 -  7999 = Windows Media Tools

  8000 -  8999 = Windows Media Content Discovery

  9000 -  9999 = Windows Media Real Time Collaboration

 10000 - 10999 = Windows Media Digital Rights Management

**************************** READ ME ******************************************

--*/

#ifndef _NSERROR_H
#define _NSERROR_H


#define STATUS_SEVERITY(hr)  (((hr) >> 30) & 0x3)


/////////////////////////////////////////////////////////////////////////
//
// NETSHOW Success Events
//
/////////////////////////////////////////////////////////////////////////

//
//  Values are 32 bit values layed out as follows:
//
//   3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
//   1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
//  +---+-+-+-----------------------+-------------------------------+
//  |Sev|C|R|     Facility          |               Code            |
//  +---+-+-+-----------------------+-------------------------------+
//
//  where
//
//      Sev - is the severity code
//
//          00 - Success
//          01 - Informational
//          10 - Warning
//          11 - Error
//
//      C - is the Customer code flag
//
//      R - is a reserved bit
//
//      Facility - is the facility code
//
//      Code - is the facility's status code
//
//
// Define the facility codes
//
#define FACILITY_NS_WIN32                0x7
#define FACILITY_NS                      0xD


//
// Define the severity codes
//
#define STATUS_SEVERITY_WARNING          0x2
#define STATUS_SEVERITY_SUCCESS          0x0
#define STATUS_SEVERITY_INFORMATIONAL    0x1
#define STATUS_SEVERITY_ERROR            0x3


//
// MessageId: NS_S_CALLPENDING
//
// MessageText:
//
//  The requested operation is pending completion.%0
//
#define NS_S_CALLPENDING                 0x000D0000L

//
// MessageId: NS_S_CALLABORTED
//
// MessageText:
//
//  The requested operation was aborted by the client.%0
//
#define NS_S_CALLABORTED                 0x000D0001L

//
// MessageId: NS_S_STREAM_TRUNCATED
//
// MessageText:
//
//  The stream was purposefully stopped before completion.%0
//
#define NS_S_STREAM_TRUNCATED            0x000D0002L


/////////////////////////////////////////////////////////////////////////
//
// NETSHOW Warning Events
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_W_SERVER_BANDWIDTH_LIMIT
//
// MessageText:
//
//  The maximum filebitrate value specified is greater than the server's configured maximum bandwidth.%0
//
#define NS_W_SERVER_BANDWIDTH_LIMIT      0x800D0003L

//
// MessageId: NS_W_FILE_BANDWIDTH_LIMIT
//
// MessageText:
//
//  The maximum bandwidth value specified is less than the maximum filebitrate.%0
//
#define NS_W_FILE_BANDWIDTH_LIMIT        0x800D0004L


/////////////////////////////////////////////////////////////////////////
//
// NETSHOW Error Events
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_E_NOCONNECTION
//
// MessageText:
//
//  There is no connection established with the NetShow server. The operation failed.%0
//
#define NS_E_NOCONNECTION                0xC00D0005L

//
// MessageId: NS_E_CANNOTCONNECT
//
// MessageText:
//
//  Unable to establish a connection to the server.%0
//
#define NS_E_CANNOTCONNECT               0xC00D0006L

//
// MessageId: NS_E_CANNOTDESTROYTITLE
//
// MessageText:
//
//  Unable to destroy the title.%0
//
#define NS_E_CANNOTDESTROYTITLE          0xC00D0007L

//
// MessageId: NS_E_CANNOTRENAMETITLE
//
// MessageText:
//
//  Unable to rename the title.%0
//
#define NS_E_CANNOTRENAMETITLE           0xC00D0008L

//
// MessageId: NS_E_CANNOTOFFLINEDISK
//
// MessageText:
//
//  Unable to offline disk.%0
//
#define NS_E_CANNOTOFFLINEDISK           0xC00D0009L

//
// MessageId: NS_E_CANNOTONLINEDISK
//
// MessageText:
//
//  Unable to online disk.%0
//
#define NS_E_CANNOTONLINEDISK            0xC00D000AL

//
// MessageId: NS_E_NOREGISTEREDWALKER
//
// MessageText:
//
//  There is no file parser registered for this type of file.%0
//
#define NS_E_NOREGISTEREDWALKER          0xC00D000BL

//
// MessageId: NS_E_NOFUNNEL
//
// MessageText:
//
//  There is no data connection established.%0
//
#define NS_E_NOFUNNEL                    0xC00D000CL

//
// MessageId: NS_E_NO_LOCALPLAY
//
// MessageText:
//
//  Failed to load the local play DLL.%0
//
#define NS_E_NO_LOCALPLAY                0xC00D000DL

//
// MessageId: NS_E_NETWORK_BUSY
//
// MessageText:
//
//  The network is busy.%0
//
#define NS_E_NETWORK_BUSY                0xC00D000EL

//
// MessageId: NS_E_TOO_MANY_SESS
//
// MessageText:
//
//  The server session limit was exceeded.%0
//
#define NS_E_TOO_MANY_SESS               0xC00D000FL

//
// MessageId: NS_E_ALREADY_CONNECTED
//
// MessageText:
//
//  The network connection already exists.%0
//
#define NS_E_ALREADY_CONNECTED           0xC00D0010L

//
// MessageId: NS_E_INVALID_INDEX
//
// MessageText:
//
//  Index %1 is invalid.%0
//
#define NS_E_INVALID_INDEX               0xC00D0011L

//
// MessageId: NS_E_PROTOCOL_MISMATCH
//
// MessageText:
//
//  There is no protocol or protocol version supported by both the client and the server.%0
//
#define NS_E_PROTOCOL_MISMATCH           0xC00D0012L

//
// MessageId: NS_E_TIMEOUT
//
// MessageText:
//
//  There was no timely response from server.%0
//
#define NS_E_TIMEOUT                     0xC00D0013L

//
// MessageId: NS_E_NET_WRITE
//
// MessageText:
//
//  Error writing to the network.%0
//
#define NS_E_NET_WRITE                   0xC00D0014L

//
// MessageId: NS_E_NET_READ
//
// MessageText:
//
//  Error reading from the network.%0
//
#define NS_E_NET_READ                    0xC00D0015L

//
// MessageId: NS_E_DISK_WRITE
//
// MessageText:
//
//  Error writing to a disk.%0
//
#define NS_E_DISK_WRITE                  0xC00D0016L

//
// MessageId: NS_E_DISK_READ
//
// MessageText:
//
//  Error reading from a disk.%0
//
#define NS_E_DISK_READ                   0xC00D0017L

//
// MessageId: NS_E_FILE_WRITE
//
// MessageText:
//
//  Error writing to a file.%0
//
#define NS_E_FILE_WRITE                  0xC00D0018L

//
// MessageId: NS_E_FILE_READ
//
// MessageText:
//
//  Error reading from a file.%0
//
#define NS_E_FILE_READ                   0xC00D0019L

//
// MessageId: NS_E_FILE_NOT_FOUND
//
// MessageText:
//
//  The system cannot find the file specified.%0
//
#define NS_E_FILE_NOT_FOUND              0xC00D001AL

//
// MessageId: NS_E_FILE_EXISTS
//
// MessageText:
//
//  The file already exists.%0
//
#define NS_E_FILE_EXISTS                 0xC00D001BL

//
// MessageId: NS_E_INVALID_NAME
//
// MessageText:
//
//  The file name, directory name, or volume label syntax is incorrect.%0
//
#define NS_E_INVALID_NAME                0xC00D001CL

//
// MessageId: NS_E_FILE_OPEN_FAILED
//
// MessageText:
//
//  Failed to open a file.%0
//
#define NS_E_FILE_OPEN_FAILED            0xC00D001DL

//
// MessageId: NS_E_FILE_ALLOCATION_FAILED
//
// MessageText:
//
//  Unable to allocate a file.%0
//
#define NS_E_FILE_ALLOCATION_FAILED      0xC00D001EL

//
// MessageId: NS_E_FILE_INIT_FAILED
//
// MessageText:
//
//  Unable to initialize a file.%0
//
#define NS_E_FILE_INIT_FAILED            0xC00D001FL

//
// MessageId: NS_E_FILE_PLAY_FAILED
//
// MessageText:
//
//  Unable to play a file.%0
//
#define NS_E_FILE_PLAY_FAILED            0xC00D0020L

//
// MessageId: NS_E_SET_DISK_UID_FAILED
//
// MessageText:
//
//  Could not set the disk UID.%0
//
#define NS_E_SET_DISK_UID_FAILED         0xC00D0021L

//
// MessageId: NS_E_INDUCED
//
// MessageText:
//
//  An error was induced for testing purposes.%0
//
#define NS_E_INDUCED                     0xC00D0022L

//
// MessageId: NS_E_CCLINK_DOWN
//
// MessageText:
//
//  Two Content Servers failed to communicate.%0
//
#define NS_E_CCLINK_DOWN                 0xC00D0023L

//
// MessageId: NS_E_INTERNAL
//
// MessageText:
//
//  An unknown error occurred.%0
//
#define NS_E_INTERNAL                    0xC00D0024L

//
// MessageId: NS_E_BUSY
//
// MessageText:
//
//  The requested resource is in use.%0
//
#define NS_E_BUSY                        0xC00D0025L

//
// MessageId: NS_E_UNRECOGNIZED_STREAM_TYPE
//
// MessageText:
//
//  The specified stream type is not recognized.%0
//
#define NS_E_UNRECOGNIZED_STREAM_TYPE    0xC00D0026L

//
// MessageId: NS_E_NETWORK_SERVICE_FAILURE
//
// MessageText:
//
//  The network service provider failed.%0
//
#define NS_E_NETWORK_SERVICE_FAILURE     0xC00D0027L

//
// MessageId: NS_E_NETWORK_RESOURCE_FAILURE
//
// MessageText:
//
//  An attempt to acquire a network resource failed.%0
//
#define NS_E_NETWORK_RESOURCE_FAILURE    0xC00D0028L

//
// MessageId: NS_E_CONNECTION_FAILURE
//
// MessageText:
//
//  The network connection has failed.%0
//
#define NS_E_CONNECTION_FAILURE          0xC00D0029L

//
// MessageId: NS_E_SHUTDOWN
//
// MessageText:
//
//  The session is being terminated locally.%0
//
#define NS_E_SHUTDOWN                    0xC00D002AL

//
// MessageId: NS_E_INVALID_REQUEST
//
// MessageText:
//
//  The request is invalid in the current state.%0
//
#define NS_E_INVALID_REQUEST             0xC00D002BL

//
// MessageId: NS_E_INSUFFICIENT_BANDWIDTH
//
// MessageText:
//
//  There is insufficient bandwidth available to fulfill the request.%0
//
#define NS_E_INSUFFICIENT_BANDWIDTH      0xC00D002CL

//
// MessageId: NS_E_NOT_REBUILDING
//
// MessageText:
//
//  The disk is not rebuilding.%0
//
#define NS_E_NOT_REBUILDING              0xC00D002DL

//
// MessageId: NS_E_LATE_OPERATION
//
// MessageText:
//
//  An operation requested for a particular time could not be carried out on schedule.%0
//
#define NS_E_LATE_OPERATION              0xC00D002EL

//
// MessageId: NS_E_INVALID_DATA
//
// MessageText:
//
//  Invalid or corrupt data was encountered.%0
//
#define NS_E_INVALID_DATA                0xC00D002FL

//
// MessageId: NS_E_FILE_BANDWIDTH_LIMIT
//
// MessageText:
//
//  The bandwidth required to stream a file is higher than the maximum file bandwidth allowed on the server.%0
//
#define NS_E_FILE_BANDWIDTH_LIMIT        0xC00D0030L

//
// MessageId: NS_E_OPEN_FILE_LIMIT
//
// MessageText:
//
//  The client cannot have any more files open simultaneously.%0
//
#define NS_E_OPEN_FILE_LIMIT             0xC00D0031L

//
// MessageId: NS_E_BAD_CONTROL_DATA
//
// MessageText:
//
//  The server received invalid data from the client on the control connection.%0
//
#define NS_E_BAD_CONTROL_DATA            0xC00D0032L

//
// MessageId: NS_E_NO_STREAM
//
// MessageText:
//
//  There is no stream available.%0
//
#define NS_E_NO_STREAM                   0xC00D0033L

//
// MessageId: NS_E_STREAM_END
//
// MessageText:
//
//  There is no more data in the stream.%0
//
#define NS_E_STREAM_END                  0xC00D0034L

//
// MessageId: NS_E_SERVER_NOT_FOUND
//
// MessageText:
//
//  The specified server could not be found.%0
//
#define NS_E_SERVER_NOT_FOUND            0xC00D0035L

//
// MessageId: NS_E_DUPLICATE_NAME
//
// MessageText:
//
//  The specified name is already in use.
//
#define NS_E_DUPLICATE_NAME              0xC00D0036L

//
// MessageId: NS_E_DUPLICATE_ADDRESS
//
// MessageText:
//
//  The specified address is already in use.
//
#define NS_E_DUPLICATE_ADDRESS           0xC00D0037L

//
// MessageId: NS_E_BAD_MULTICAST_ADDRESS
//
// MessageText:
//
//  The specified address is not a valid multicast address.
//
#define NS_E_BAD_MULTICAST_ADDRESS       0xC00D0038L

//
// MessageId: NS_E_BAD_ADAPTER_ADDRESS
//
// MessageText:
//
//  The specified adapter address is invalid.
//
#define NS_E_BAD_ADAPTER_ADDRESS         0xC00D0039L

//
// MessageId: NS_E_BAD_DELIVERY_MODE
//
// MessageText:
//
//  The specified delivery mode is invalid.
//
#define NS_E_BAD_DELIVERY_MODE           0xC00D003AL

//
// MessageId: NS_E_INVALID_CHANNEL
//
// MessageText:
//
//  The specified station does not exist.
//
#define NS_E_INVALID_CHANNEL             0xC00D003BL

//
// MessageId: NS_E_INVALID_STREAM
//
// MessageText:
//
//  The specified stream does not exist.
//
#define NS_E_INVALID_STREAM              0xC00D003CL

//
// MessageId: NS_E_INVALID_ARCHIVE
//
// MessageText:
//
//  The specified archive could not be opened.
//
#define NS_E_INVALID_ARCHIVE             0xC00D003DL

//
// MessageId: NS_E_NOTITLES
//
// MessageText:
//
//  The system cannot find any titles on the server.%0
//
#define NS_E_NOTITLES                    0xC00D003EL

//
// MessageId: NS_E_INVALID_CLIENT
//
// MessageText:
//
//  The system cannot find the client specified.%0
//
#define NS_E_INVALID_CLIENT              0xC00D003FL

//
// MessageId: NS_E_INVALID_BLACKHOLE_ADDRESS
//
// MessageText:
//
//  The Blackhole Address is not initialized.%0
//
#define NS_E_INVALID_BLACKHOLE_ADDRESS   0xC00D0040L

//
// MessageId: NS_E_INCOMPATIBLE_FORMAT
//
// MessageText:
//
//  The station does not support the stream format.
//
#define NS_E_INCOMPATIBLE_FORMAT         0xC00D0041L

//
// MessageId: NS_E_INVALID_KEY
//
// MessageText:
//
//  The specified key is not valid.
//
#define NS_E_INVALID_KEY                 0xC00D0042L

//
// MessageId: NS_E_INVALID_PORT
//
// MessageText:
//
//  The specified port is not valid.
//
#define NS_E_INVALID_PORT                0xC00D0043L

//
// MessageId: NS_E_INVALID_TTL
//
// MessageText:
//
//  The specified TTL is not valid.
//
#define NS_E_INVALID_TTL                 0xC00D0044L

//
// MessageId: NS_E_STRIDE_REFUSED
//
// MessageText:
//
//  The request to fast forward or rewind could not be fulfilled.
//
#define NS_E_STRIDE_REFUSED              0xC00D0045L

//
// IMmsAutoServer Errors
//
//
// MessageId: NS_E_MMSAUTOSERVER_CANTFINDWALKER
//
// MessageText:
//
//  Unable to load the appropriate file parser.%0
//
#define NS_E_MMSAUTOSERVER_CANTFINDWALKER 0xC00D0046L

//
// MessageId: NS_E_MAX_BITRATE
//
// MessageText:
//
//  Cannot exceed the maximum bandwidth limit.%0
//
#define NS_E_MAX_BITRATE                 0xC00D0047L

//
// MessageId: NS_E_LOGFILEPERIOD
//
// MessageText:
//
//  Invalid value for LogFilePeriod.%0
//
#define NS_E_LOGFILEPERIOD               0xC00D0048L

//
// MessageId: NS_E_MAX_CLIENTS
//
// MessageText:
//
//  Cannot exceed the maximum client limit.%0
//  
//
#define NS_E_MAX_CLIENTS                 0xC00D0049L

//
// MessageId: NS_E_LOG_FILE_SIZE
//
// MessageText:
//
//  Log File Size too small.%0
//  
//
#define NS_E_LOG_FILE_SIZE               0xC00D004AL

//
// MessageId: NS_E_MAX_FILERATE
//
// MessageText:
//
//  Cannot exceed the maximum file rate.%0
//
#define NS_E_MAX_FILERATE                0xC00D004BL

//
// File Walker Errors
//
//
// MessageId: NS_E_WALKER_UNKNOWN
//
// MessageText:
//
//  Unknown file type.%0
//
#define NS_E_WALKER_UNKNOWN              0xC00D004CL

//
// MessageId: NS_E_WALKER_SERVER
//
// MessageText:
//
//  The specified file, %1, cannot be loaded onto the specified server, %2.%0
//
#define NS_E_WALKER_SERVER               0xC00D004DL

//
// MessageId: NS_E_WALKER_USAGE
//
// MessageText:
//
//  There was a usage error with file parser.%0
//
#define NS_E_WALKER_USAGE                0xC00D004EL


/////////////////////////////////////////////////////////////////////////
//
// NETSHOW Monitor Events
//
/////////////////////////////////////////////////////////////////////////


 // Tiger Events

 // %1 is the tiger name

//
// MessageId: NS_I_TIGER_START
//
// MessageText:
//
//  The Title Server %1 is running.%0
//
#define NS_I_TIGER_START                 0x400D004FL

//
// MessageId: NS_E_TIGER_FAIL
//
// MessageText:
//
//  The Title Server %1 has failed.%0
//
#define NS_E_TIGER_FAIL                  0xC00D0050L


 // Cub Events

 // %1 is the cub ID
 // %2 is the cub name

//
// MessageId: NS_I_CUB_START
//
// MessageText:
//
//  Content Server %1 (%2) is starting.%0
//
#define NS_I_CUB_START                   0x400D0051L

//
// MessageId: NS_I_CUB_RUNNING
//
// MessageText:
//
//  Content Server %1 (%2) is running.%0
//
#define NS_I_CUB_RUNNING                 0x400D0052L

//
// MessageId: NS_E_CUB_FAIL
//
// MessageText:
//
//  Content Server %1 (%2) has failed.%0
//
#define NS_E_CUB_FAIL                    0xC00D0053L


 // Disk Events

 // %1 is the tiger disk ID
 // %2 is the device name
 // %3 is the cub ID
//
// MessageId: NS_I_DISK_START
//
// MessageText:
//
//  Disk %1 ( %2 ) on Content Server %3, is running.%0
//
#define NS_I_DISK_START                  0x400D0054L

//
// MessageId: NS_E_DISK_FAIL
//
// MessageText:
//
//  Disk %1 ( %2 ) on Content Server %3, has failed.%0
//
#define NS_E_DISK_FAIL                   0xC00D0055L

//
// MessageId: NS_I_DISK_REBUILD_STARTED
//
// MessageText:
//
//  Started rebuilding disk %1 ( %2 ) on Content Server %3.%0
//
#define NS_I_DISK_REBUILD_STARTED        0x400D0056L

//
// MessageId: NS_I_DISK_REBUILD_FINISHED
//
// MessageText:
//
//  Finished rebuilding disk %1 ( %2 ) on Content Server %3.%0
//
#define NS_I_DISK_REBUILD_FINISHED       0x400D0057L

//
// MessageId: NS_I_DISK_REBUILD_ABORTED
//
// MessageText:
//
//  Aborted rebuilding disk %1 ( %2 ) on Content Server %3.%0
//
#define NS_I_DISK_REBUILD_ABORTED        0x400D0058L


 // Admin Events

//
// MessageId: NS_I_LIMIT_FUNNELS
//
// MessageText:
//
//  A NetShow administrator at network location %1 set the data stream limit to %2 streams.%0
//
#define NS_I_LIMIT_FUNNELS               0x400D0059L

//
// MessageId: NS_I_START_DISK
//
// MessageText:
//
//  A NetShow administrator at network location %1 started disk %2.%0
//
#define NS_I_START_DISK                  0x400D005AL

//
// MessageId: NS_I_STOP_DISK
//
// MessageText:
//
//  A NetShow administrator at network location %1 stopped disk %2.%0
//
#define NS_I_STOP_DISK                   0x400D005BL

//
// MessageId: NS_I_STOP_CUB
//
// MessageText:
//
//  A NetShow administrator at network location %1 stopped Content Server %2.%0
//
#define NS_I_STOP_CUB                    0x400D005CL

//
// MessageId: NS_I_KILL_VIEWER
//
// MessageText:
//
//  A NetShow administrator at network location %1 disconnected viewer %2 from the system.%0
//
#define NS_I_KILL_VIEWER                 0x400D005DL

//
// MessageId: NS_I_REBUILD_DISK
//
// MessageText:
//
//  A NetShow administrator at network location %1 started rebuilding disk %2.%0
//
#define NS_I_REBUILD_DISK                0x400D005EL

//
// MessageId: NS_W_UNKNOWN_EVENT
//
// MessageText:
//
//  Unknown %1 event encountered.%0
//
#define NS_W_UNKNOWN_EVENT               0x800D005FL


 // Alerts

//
// MessageId: NS_E_MAX_FUNNELS_ALERT
//
// MessageText:
//
//  The NetShow data stream limit of %1 streams was reached.%0
//
#define NS_E_MAX_FUNNELS_ALERT           0xC00D0060L

//
// MessageId: NS_E_ALLOCATE_FILE_FAIL
//
// MessageText:
//
//  The NetShow Video Server was unable to allocate a %1 block file named %2.%0
//
#define NS_E_ALLOCATE_FILE_FAIL          0xC00D0061L

//
// MessageId: NS_E_PAGING_ERROR
//
// MessageText:
//
//  A Content Server was unable to page a block.%0
//
#define NS_E_PAGING_ERROR                0xC00D0062L

//
// MessageId: NS_E_BAD_BLOCK0_VERSION
//
// MessageText:
//
//  Disk %1 has unrecognized control block version %2.%0
//
#define NS_E_BAD_BLOCK0_VERSION          0xC00D0063L

//
// MessageId: NS_E_BAD_DISK_UID
//
// MessageText:
//
//  Disk %1 has incorrect uid %2.%0
//
#define NS_E_BAD_DISK_UID                0xC00D0064L

//
// MessageId: NS_E_BAD_FSMAJOR_VERSION
//
// MessageText:
//
//  Disk %1 has unsupported file system major version %2.%0
//
#define NS_E_BAD_FSMAJOR_VERSION         0xC00D0065L

//
// MessageId: NS_E_BAD_STAMPNUMBER
//
// MessageText:
//
//  Disk %1 has bad stamp number in control block.%0
//
#define NS_E_BAD_STAMPNUMBER             0xC00D0066L

//
// MessageId: NS_E_PARTIALLY_REBUILT_DISK
//
// MessageText:
//
//  Disk %1 is partially reconstructed.%0
//
#define NS_E_PARTIALLY_REBUILT_DISK      0xC00D0067L

//
// MessageId: NS_E_ENACTPLAN_GIVEUP
//
// MessageText:
//
//  EnactPlan gives up.%0
//
#define NS_E_ENACTPLAN_GIVEUP            0xC00D0068L


 // MCMADM warnings/errors

//
// MessageId: MCMADM_I_NO_EVENTS
//
// MessageText:
//
//  Event initialization failed, there will be no MCM events.%0
//
#define MCMADM_I_NO_EVENTS               0x400D0069L

//
// MessageId: MCMADM_E_REGKEY_NOT_FOUND
//
// MessageText:
//
//  The key was not found in the registry.%0
//
#define MCMADM_E_REGKEY_NOT_FOUND        0xC00D006AL

//
// MessageId: NS_E_NO_FORMATS
//
// MessageText:
//
//  No stream formats were found in an NSC file.%0
//
#define NS_E_NO_FORMATS                  0xC00D006BL

//
// MessageId: NS_E_NO_REFERENCES
//
// MessageText:
//
//  No reference URLs were found in an ASX file.%0
//
#define NS_E_NO_REFERENCES               0xC00D006CL

//
// MessageId: NS_E_WAVE_OPEN
//
// MessageText:
//
//  Error opening wave device, the device might be in use.%0
//
#define NS_E_WAVE_OPEN                   0xC00D006DL

//
// MessageId: NS_I_LOGGING_FAILED
//
// MessageText:
//
//  The logging operation failed. 
//
#define NS_I_LOGGING_FAILED              0x400D006EL

//
// MessageId: NS_E_CANNOTCONNECTEVENTS
//
// MessageText:
//
//  Unable to establish a connection to the NetShow event monitor service.%0
//
#define NS_E_CANNOTCONNECTEVENTS         0xC00D006FL

//
// MessageId: NS_I_LIMIT_BANDWIDTH
//
// MessageText:
//
//  A NetShow administrator at network location %1 set the maximum bandwidth limit to %2 bps.%0
//
#define NS_I_LIMIT_BANDWIDTH             0x400D0070L


// NOTENOTE!!!
//
// Due to legacy problems these error codes live inside the ASF error code range
//
//
// MessageId: NS_E_NOTHING_TO_DO
//
// MessageText:
//
//  NS_E_NOTHING_TO_DO
//
#define NS_E_NOTHING_TO_DO               0xC00D07F1L

//
// MessageId: NS_E_NO_MULTICAST
//
// MessageText:
//
//  NS_E_NO_MULTICAST
//
#define NS_E_NO_MULTICAST                0xC00D07F2L


/////////////////////////////////////////////////////////////////////////
//
// NETSHOW Error Events
//
// IdRange = 200..399
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_E_MONITOR_GIVEUP
//
// MessageText:
//
//  Netshow Events Monitor is not operational and has been disconnected.%0
//
#define NS_E_MONITOR_GIVEUP              0xC00D00C8L

//
// MessageId: NS_E_REMIRRORED_DISK
//
// MessageText:
//
//  Disk %1 is remirrored.%0
//
#define NS_E_REMIRRORED_DISK             0xC00D00C9L

//
// MessageId: NS_E_INSUFFICIENT_DATA
//
// MessageText:
//
//  Insufficient data found.%0
//
#define NS_E_INSUFFICIENT_DATA           0xC00D00CAL

//
// MessageId: NS_E_ASSERT
//
// MessageText:
//
//  %1 failed in file %2 line %3.%0
//
#define NS_E_ASSERT                      0xC00D00CBL

//
// MessageId: NS_E_BAD_ADAPTER_NAME
//
// MessageText:
//
//  The specified adapter name is invalid.%0
//
#define NS_E_BAD_ADAPTER_NAME            0xC00D00CCL

//
// MessageId: NS_E_NOT_LICENSED
//
// MessageText:
//
//  The application is not licensed for this feature.%0
//
#define NS_E_NOT_LICENSED                0xC00D00CDL

//
// MessageId: NS_E_NO_SERVER_CONTACT
//
// MessageText:
//
//  Unable to contact the server.%0
//
#define NS_E_NO_SERVER_CONTACT           0xC00D00CEL

//
// MessageId: NS_E_TOO_MANY_TITLES
//
// MessageText:
//
//  Maximum number of titles exceeded.%0
//
#define NS_E_TOO_MANY_TITLES             0xC00D00CFL

//
// MessageId: NS_E_TITLE_SIZE_EXCEEDED
//
// MessageText:
//
//  Maximum size of a title exceeded.%0
//
#define NS_E_TITLE_SIZE_EXCEEDED         0xC00D00D0L

//
// MessageId: NS_E_UDP_DISABLED
//
// MessageText:
//
//  UDP protocol not enabled. Not trying %1!ls!.%0
//
#define NS_E_UDP_DISABLED                0xC00D00D1L

//
// MessageId: NS_E_TCP_DISABLED
//
// MessageText:
//
//  TCP protocol not enabled. Not trying %1!ls!.%0
//
#define NS_E_TCP_DISABLED                0xC00D00D2L

//
// MessageId: NS_E_HTTP_DISABLED
//
// MessageText:
//
//  HTTP protocol not enabled. Not trying %1!ls!.%0
//
#define NS_E_HTTP_DISABLED               0xC00D00D3L

//
// MessageId: NS_E_LICENSE_EXPIRED
//
// MessageText:
//
//  The product license has expired.%0
//
#define NS_E_LICENSE_EXPIRED             0xC00D00D4L

//
// MessageId: NS_E_TITLE_BITRATE
//
// MessageText:
//
//  Source file exceeds the per title maximum bitrate. See NetShow Theater documentation for more information.%0
//
#define NS_E_TITLE_BITRATE               0xC00D00D5L

//
// MessageId: NS_E_EMPTY_PROGRAM_NAME
//
// MessageText:
//
//  The program name cannot be empty.%0
//
#define NS_E_EMPTY_PROGRAM_NAME          0xC00D00D6L

//
// MessageId: NS_E_MISSING_CHANNEL
//
// MessageText:
//
//  Station %1 does not exist.%0
//
#define NS_E_MISSING_CHANNEL             0xC00D00D7L

//
// MessageId: NS_E_NO_CHANNELS
//
// MessageText:
//
//  You need to define at least one station before this operation can complete.%0
//
#define NS_E_NO_CHANNELS                 0xC00D00D8L


/////////////////////////////////////////////////////////////////////////
//
// NETSHOW Monitor Events
//
// IdRange = 400..599
//
// Admin Events:
//
// Alerts:
//
// Title Server:
//	 %1 is the Title Server name
//
// Content Server:
//	 %1 is the Content Server ID
//	 %2 is the Content Server name
//	 %3 is the Peer Content Server name (optional)
//
// Disks:
//	 %1 is the Title Server disk ID
//	 %2 is the device name
//	 %3 is the Content Server ID
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_E_CUB_FAIL_LINK
//
// MessageText:
//
//  Content Server %1 (%2) has failed its link to Content Server %3.%0
//
#define NS_E_CUB_FAIL_LINK               0xC00D0190L

//
// MessageId: NS_I_CUB_UNFAIL_LINK
//
// MessageText:
//
//  Content Server %1 (%2) has established its link to Content Server %3.%0
//
#define NS_I_CUB_UNFAIL_LINK             0x400D0191L

//
// MessageId: NS_E_BAD_CUB_UID
//
// MessageText:
//
//  Content Server %1 (%2) has incorrect uid %3.%0
//
#define NS_E_BAD_CUB_UID                 0xC00D0192L

//
// MessageId: NS_I_RESTRIPE_START
//
// MessageText:
//
//  Restripe operation has started.%0
//
#define NS_I_RESTRIPE_START              0x400D0193L

//
// MessageId: NS_I_RESTRIPE_DONE
//
// MessageText:
//
//  Restripe operation has completed.%0
//
#define NS_I_RESTRIPE_DONE               0x400D0194L

//
// MessageId: NS_E_GLITCH_MODE
//
// MessageText:
//
//  Server unreliable because multiple components failed.%0
//
#define NS_E_GLITCH_MODE                 0xC00D0195L

//
// MessageId: NS_I_RESTRIPE_DISK_OUT
//
// MessageText:
//
//  Content disk %1 (%2) on Content Server %3 has been restriped out.%0
//
#define NS_I_RESTRIPE_DISK_OUT           0x400D0196L

//
// MessageId: NS_I_RESTRIPE_CUB_OUT
//
// MessageText:
//
//  Content server %1 (%2) has been restriped out.%0
//
#define NS_I_RESTRIPE_CUB_OUT            0x400D0197L

//
// MessageId: NS_I_DISK_STOP
//
// MessageText:
//
//  Disk %1 ( %2 ) on Content Server %3, has been offlined.%0
//
#define NS_I_DISK_STOP                   0x400D0198L

//
// MessageId: NS_I_CATATONIC_FAILURE
//
// MessageText:
//
//  Disk %1 ( %2 ) on Content Server %3, will be failed because it is catatonic.%0
//
#define NS_I_CATATONIC_FAILURE           0x800D0199L

//
// MessageId: NS_I_CATATONIC_AUTO_UNFAIL
//
// MessageText:
//
//  Disk %1 ( %2 ) on Content Server %3, auto online from catatonic state.%0
//
#define NS_I_CATATONIC_AUTO_UNFAIL       0x800D019AL

//
// MessageId: NS_E_NO_MEDIA_PROTOCOL
//
// MessageText:
//
//  Content Server %1 (%2) is unable to communicate with the Media System Network Protocol.%0
//
#define NS_E_NO_MEDIA_PROTOCOL           0xC00D019BL


//
// Advanced Streaming Format (ASF) codes occupy MessageIds 2000-2999
//
// See ASFErr.mc for more details - please do not define any symbols
// in that range in this file.
//


/////////////////////////////////////////////////////////////////////////
//
// Windows Media Audio SDK Errors
//
// IdRange = 3000-3199
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_E_INVALID_INPUT_FORMAT
//
// MessageText:
//
//  The input audio format must be a valid, PCM audio format.%0
//
#define NS_E_INVALID_INPUT_FORMAT        0xC00D0BB8L

//
// MessageId: NS_E_MSAUDIO_NOT_INSTALLED
//
// MessageText:
//
//  The MSAudio codec is not installed on this system.%0
//
#define NS_E_MSAUDIO_NOT_INSTALLED       0xC00D0BB9L

//
// MessageId: NS_E_UNEXPECTED_MSAUDIO_ERROR
//
// MessageText:
//
//  An unexpected error occured with the MSAudio codec.%0
//
#define NS_E_UNEXPECTED_MSAUDIO_ERROR    0xC00D0BBAL

//
// MessageId: NS_E_INVALID_OUTPUT_FORMAT
//
// MessageText:
//
//  The MSAudio codec does not support the specified output format.%0
//
#define NS_E_INVALID_OUTPUT_FORMAT       0xC00D0BBBL

//
// MessageId: NS_E_NOT_CONFIGURED
//
// MessageText:
//
//  The object must be fully configured before audio samples can be processed.%0
//
#define NS_E_NOT_CONFIGURED              0xC00D0BBCL

//
// MessageId: NS_E_PROTECTED_CONTENT
//
// MessageText:
//
//  The content is protected and cannot be opened at this time.%0
//
#define NS_E_PROTECTED_CONTENT           0xC00D0BBDL

//
// MessageId: NS_E_LICENSE_REQUIRED
//
// MessageText:
//
//  A playback license is required to open this content.%0
//
#define NS_E_LICENSE_REQUIRED            0xC00D0BBEL

//
// MessageId: NS_E_TAMPERED_CONTENT
//
// MessageText:
//
//  This content has been tampered with and cannot be opened.%0
//
#define NS_E_TAMPERED_CONTENT            0xC00D0BBFL

//
// MessageId: NS_E_LICENSE_OUTOFDATE
//
// MessageText:
//
//  The license is to open this content has expired.%0
//
#define NS_E_LICENSE_OUTOFDATE           0xC00D0BC0L

//
// MessageId: NS_E_LICENSE_INCORRECT_RIGHTS
//
// MessageText:
//
//  The requested rights prevent the content from being opened.%0
//
#define NS_E_LICENSE_INCORRECT_RIGHTS    0xC00D0BC1L

//
// MessageId: NS_E_AUDIO_CODEC_NOT_INSTALLED
//
// MessageText:
//
//  The requested audio codec is not installed on this system.%0
//
#define NS_E_AUDIO_CODEC_NOT_INSTALLED   0xC00D0BC2L

//
// MessageId: NS_E_AUDIO_CODEC_ERROR
//
// MessageText:
//
//  An unexpected error occurred with the audio codec.%0
//
#define NS_E_AUDIO_CODEC_ERROR           0xC00D0BC3L

//
// MessageId: NS_E_VIDEO_CODEC_NOT_INSTALLED
//
// MessageText:
//
//  The requested video codec is not installed on this system.%0
//
#define NS_E_VIDEO_CODEC_NOT_INSTALLED   0xC00D0BC4L

//
// MessageId: NS_E_VIDEO_CODEC_ERROR
//
// MessageText:
//
//  An unexpected error occurred with the video codec.%0
//
#define NS_E_VIDEO_CODEC_ERROR           0xC00D0BC5L

//
// MessageId: NS_E_INVALIDPROFILE
//
// MessageText:
//
//  The Profile is invalid.%0
//
#define NS_E_INVALIDPROFILE              0xC00D0BC6L

//
// MessageId: NS_E_INCOMPATIBLE_VERSION
//
// MessageText:
//
//  A new version of the SDK is needed to play the requested content.%0
//
#define NS_E_INCOMPATIBLE_VERSION        0xC00D0BC7L

//
// MessageId: NS_S_REBUFFERING
//
// MessageText:
//
//  The requested operation has caused the source to rebuffer.%0
//
#define NS_S_REBUFFERING                 0x000D0BC8L

//
// MessageId: NS_S_DEGRADING_QUALITY
//
// MessageText:
//
//  The requested operation has caused the source to degrade codec quality.%0
//
#define NS_S_DEGRADING_QUALITY           0x000D0BC9L



/////////////////////////////////////////////////////////////////////////
//
// Windows Media Server Errors
//
// IdRange = 5000 - 5999
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_E_REDIRECT
//
// MessageText:
//
//  The client is redirected to another server.%0
//
#define NS_E_REDIRECT                    0xC00D1388L

//
// MessageId: NS_E_STALE_PRESENTATION
//
// MessageText:
//
//  The streaming media description is no longer current.%0
//
#define NS_E_STALE_PRESENTATION          0xC00D1389L


 // Namespace Errors

//
// MessageId: NS_E_NAMESPACE_WRONG_PERSIST
//
// MessageText:
//
//  Attempt to create a persistent namespace node under a transient parent node.%0
//
#define NS_E_NAMESPACE_WRONG_PERSIST     0xC00D138AL

//
// MessageId: NS_E_NAMESPACE_WRONG_TYPE
//
// MessageText:
//
//  Unable to store a value in a namespace node of different value type.%0
//
#define NS_E_NAMESPACE_WRONG_TYPE        0xC00D138BL

//
// MessageId: NS_E_NAMESPACE_NODE_CONFLICT
//
// MessageText:
//
//  Unable to remove the root namespace node.%0
//
#define NS_E_NAMESPACE_NODE_CONFLICT     0xC00D138CL

//
// MessageId: NS_E_NAMESPACE_NODE_NOT_FOUND
//
// MessageText:
//
//  Could not find the specified namespace node.%0
//
#define NS_E_NAMESPACE_NODE_NOT_FOUND    0xC00D138DL

//
// MessageId: NS_E_NAMESPACE_BUFFER_TOO_SMALL
//
// MessageText:
//
//  The buffer supplied to hold namespace node string is too small.%0
//
#define NS_E_NAMESPACE_BUFFER_TOO_SMALL  0xC00D138EL

//
// MessageId: NS_E_NAMESPACE_TOO_MANY_CALLBACKS
//
// MessageText:
//
//  Callback list on a namespace node is at maximum size.%0
//
#define NS_E_NAMESPACE_TOO_MANY_CALLBACKS 0xC00D138FL

//
// MessageId: NS_E_NAMESPACE_DUPLICATE_CALLBACK
//
// MessageText:
//
//  Attempt to register an already-registered callback on a namespace node.%0
//
#define NS_E_NAMESPACE_DUPLICATE_CALLBACK 0xC00D1390L

//
// MessageId: NS_E_NAMESPACE_CALLBACK_NOT_FOUND
//
// MessageText:
//
//  Could not find callback in namespace when attempting to remove callback.%0
//
#define NS_E_NAMESPACE_CALLBACK_NOT_FOUND 0xC00D1391L

//
// MessageId: NS_E_NAMESPACE_NAME_TOO_LONG
//
// MessageText:
//
//  The length of a namespace node name exceeds the allowed maximum length.%0
//
#define NS_E_NAMESPACE_NAME_TOO_LONG     0xC00D1392L

//
// MessageId: NS_E_NAMESPACE_DUPLICATE_NAME
//
// MessageText:
//
//  Cannot create a namespace node which already exists.%0
//
#define NS_E_NAMESPACE_DUPLICATE_NAME    0xC00D1393L

//
// MessageId: NS_E_NAMESPACE_EMPTY_NAME
//
// MessageText:
//
//  The name of a namespace node cannot be a null string.%0
//
#define NS_E_NAMESPACE_EMPTY_NAME        0xC00D1394L

//
// MessageId: NS_E_NAMESPACE_INDEX_TOO_LARGE
//
// MessageText:
//
//  Finding a child namespace node by index failed because the index exceeded the number of children.%0
//
#define NS_E_NAMESPACE_INDEX_TOO_LARGE   0xC00D1395L

//
// MessageId: NS_E_NAMESPACE_BAD_NAME
//
// MessageText:
//
//  The name supplied for a namespace node is not valid.%0
//
#define NS_E_NAMESPACE_BAD_NAME          0xC00D1396L


 // Cache Errors

//
// MessageId: NS_E_CACHE_ORIGIN_SERVER_NOT_FOUND
//
// MessageText:
//
//  The specified origin server cannot be found.%0
//
#define NS_E_CACHE_ORIGIN_SERVER_NOT_FOUND 0xC00D1398L

//
// MessageId: NS_E_CACHE_ORIGIN_SERVER_TIMEOUT
//
// MessageText:
//
//  The specified origin server does not respond.%0
//
#define NS_E_CACHE_ORIGIN_SERVER_TIMEOUT 0xC00D1399L

//
// MessageId: NS_E_CACHE_NOT_BROADCAST
//
// MessageText:
//
//  The internal code for HTTP status code 412 Precondition Failed due to not broadcast type.%0
//
#define NS_E_CACHE_NOT_BROADCAST         0xC00D139AL

//
// MessageId: NS_E_CACHE_CANNOT_BE_CACHED
//
// MessageText:
//
//  The internal code for HTTP status code 403 Forbidden due to not cacheable.%0
//
#define NS_E_CACHE_CANNOT_BE_CACHED      0xC00D139BL

//
// MessageId: NS_E_CACHE_NOT_MODIFIED
//
// MessageText:
//
//  The internal code for HTTP status code 304 Not Modified.%0
//
#define NS_E_CACHE_NOT_MODIFIED          0xC00D139CL


 // Publishing Point Errors
//
// MessageId: NS_E_CANNOT_REMOVE_PUBPOINT
//
// MessageText:
//
//  The Publishing Point can not be removed.%0
//
#define NS_E_CANNOT_REMOVE_PUBPOINT      0xC00D139DL



/////////////////////////////////////////////////////////////////////////
//
// Windows Media Tools Errors
//
// IdRange = 7000 - 7999
//
/////////////////////////////////////////////////////////////////////////

//
// MessageId: NS_E_BAD_MARKIN
//
// MessageText:
//
//  The Mark In time should be greater than 0 and less than Mark Out time: %1.%0
//
#define NS_E_BAD_MARKIN                  0xC00D1B58L

//
// MessageId: NS_E_BAD_MARKOUT
//
// MessageText:
//
//  The Mark Out time should be greater than Mark In time: %1.%0
//
#define NS_E_BAD_MARKOUT                 0xC00D1B59L

//
// MessageId: NS_E_NOMATCHING_MEDIASOURCE
//
// MessageText:
//
//  No matching media source is found in source group %1.%0
//
#define NS_E_NOMATCHING_MEDIASOURCE      0xC00D1B5AL

//
// MessageId: NS_E_UNSUPPORTED_SOURCETYPE
//
// MessageText:
//
//  Unsupported source type.%0
//
#define NS_E_UNSUPPORTED_SOURCETYPE      0xC00D1B5BL

//
// MessageId: NS_E_TOO_MANY_AUDIO
//
// MessageText:
//
//  No more than 1 audio input is allowed.%0
//
#define NS_E_TOO_MANY_AUDIO              0xC00D1B5CL

//
// MessageId: NS_E_TOO_MANY_VIDEO
//
// MessageText:
//
//  No more than 2 video inputs are allowed.%0
//
#define NS_E_TOO_MANY_VIDEO              0xC00D1B5DL

//
// MessageId: NS_E_NOMATCHING_ELEMENT
//
// MessageText:
//
//  No matching element is found in the list.%0
//
#define NS_E_NOMATCHING_ELEMENT          0xC00D1B5EL

//
// MessageId: NS_E_MISMATCHED_MEDIACONTENT
//
// MessageText:
//
//  The profile's media content doesn't match the media content defined in the source group.%0
//
#define NS_E_MISMATCHED_MEDIACONTENT     0xC00D1B5FL

//
// MessageId: NS_E_CANNOT_DELETE_ACTIVE_SOURCEGROUP
//
// MessageText:
//
//  Cannot remove an active source group from the source group collection while encoder is currently running.%0
//
#define NS_E_CANNOT_DELETE_ACTIVE_SOURCEGROUP 0xC00D1B60L

//
// MessageId: NS_E_AUDIODEVICE_BUSY
//
// MessageText:
//
//  Cannot open specified audio capture device because it is in use right now.%0
//
#define NS_E_AUDIODEVICE_BUSY            0xC00D1B61L

//
// MessageId: NS_E_AUDIODEVICE_UNEXPECTED
//
// MessageText:
//
//  Cannot open specified audio capture device because unexpected error occurred.%0
//
#define NS_E_AUDIODEVICE_UNEXPECTED      0xC00D1B62L

//
// MessageId: NS_E_AUDIODEVICE_BADFORMAT
//
// MessageText:
//
//  Audio capture device doesn't support specified audio format.%0
//
#define NS_E_AUDIODEVICE_BADFORMAT       0xC00D1B63L

//
// MessageId: NS_E_VIDEODEVICE_BUSY
//
// MessageText:
//
//  Cannot open specified video capture device because it is in use right now.%0
//
#define NS_E_VIDEODEVICE_BUSY            0xC00D1B64L

//
// MessageId: NS_E_VIDEODEVICE_UNEXPECTED
//
// MessageText:
//
//  Cannot open specified video capture device because unexpected error occurred.%0
//
#define NS_E_VIDEODEVICE_UNEXPECTED      0xC00D1B65L


/////////////////////////////////////////////////////////////////////////
//
// DRM Specific Errors
//
// IdRange = 10000..10999
/////////////////////////////////////////////////////////////////////////
//
// MessageId: NS_E_DRM_TOO_MANY_OPEN_CONNECTIONS
//
// MessageText:
//
//  There are too many concurrent connections to DRM.%0
//
#define NS_E_DRM_TOO_MANY_OPEN_CONNECTIONS 0xC00D2710L

//
// MessageId: NS_E_DRM_INVALID_APPLICATION
//
// MessageText:
//
//  The application calling DRM has an invalid data description.%0
//
#define NS_E_DRM_INVALID_APPLICATION     0xC00D2711L

//
// MessageId: NS_E_DRM_LICENSE_STORE_ERROR
//
// MessageText:
//
//  Unable to initialize the DRM license store.%0
//
#define NS_E_DRM_LICENSE_STORE_ERROR     0xC00D2712L

//
// MessageId: NS_E_DRM_SECURE_STORE_ERROR
//
// MessageText:
//
//  Unable to initialize the DRM secure store.%0
//
#define NS_E_DRM_SECURE_STORE_ERROR      0xC00D2713L

//
// MessageId: NS_E_DRM_LICENSE_STORE_SAVE_ERROR
//
// MessageText:
//
//  Unable to save license to the DRM license store.%0
//
#define NS_E_DRM_LICENSE_STORE_SAVE_ERROR 0xC00D2714L

//
// MessageId: NS_E_DRM_SECURE_STORE_UNLOCK_ERROR
//
// MessageText:
//
//  Unable to unlock the DRM secure store.%0
//
#define NS_E_DRM_SECURE_STORE_UNLOCK_ERROR 0xC00D2715L

//
// MessageId: NS_E_DRM_INVALID_CONTENT
//
// MessageText:
//
//  Content type not supported by DRM.%0
//
#define NS_E_DRM_INVALID_CONTENT         0xC00D2716L

//
// MessageId: NS_E_DRM_UNABLE_TO_OPEN_LICENSE
//
// MessageText:
//
//  Unable to open license store item in DRM.%0
//
#define NS_E_DRM_UNABLE_TO_OPEN_LICENSE  0xC00D2717L

//
// MessageId: NS_E_DRM_INVALID_LICENSE
//
// MessageText:
//
//  Invalid license in the DRM license store.%0
//
#define NS_E_DRM_INVALID_LICENSE         0xC00D2718L

//
// MessageId: NS_E_DRM_INVALID_MACHINE
//
// MessageText:
//
//  License is not intended to play on this machine.%0
//
#define NS_E_DRM_INVALID_MACHINE         0xC00D2719L

//
// MessageId: NS_E_DRM_LICENSE_EVAL_FAILED
//
// MessageText:
//
//  DRM failed to evaluate the license.%0
//
#define NS_E_DRM_LICENSE_EVAL_FAILED     0xC00D271AL

//
// MessageId: NS_E_DRM_ENUM_LICENSE_FAILED
//
// MessageText:
//
//  DRM failed to enumerate licenses in the store.%0
//
#define NS_E_DRM_ENUM_LICENSE_FAILED     0xC00D271BL

//
// MessageId: NS_E_DRM_INVALID_LICENSE_REQUEST
//
// MessageText:
//
//  The DRM content has invalid license request XML.%0
//
#define NS_E_DRM_INVALID_LICENSE_REQUEST 0xC00D271CL

//
// MessageId: NS_E_DRM_UNABLE_TO_INITIALZE
//
// MessageText:
//
//  Unable to initialize DRM client.%0
//
#define NS_E_DRM_UNABLE_TO_INITIALZE     0xC00D271DL

//
// MessageId: NS_E_DRM_UNABLE_TO_AQUIRE_LICENSE
//
// MessageText:
//
//  Unable to aquire a license.%0
//
#define NS_E_DRM_UNABLE_TO_AQUIRE_LICENSE 0xC00D271EL

//
// MessageId: NS_E_DRM_INVALID_LICENSE_ACQUIRED
//
// MessageText:
//
//  Invalid license acquired.%0
//
#define NS_E_DRM_INVALID_LICENSE_ACQUIRED 0xC00D271FL

//
// MessageId: NS_E_DRM_NO_RIGHTS
//
// MessageText:
//
//  You do not have the rights to unlock the content.%0
//
#define NS_E_DRM_NO_RIGHTS               0xC00D2720L

//
// MessageId: NS_E_DRM_KEY_ERROR
//
// MessageText:
//
//  DRM is unable to initialize the keys.%0
//
#define NS_E_DRM_KEY_ERROR               0xC00D2721L

//
// MessageId: NS_E_DRM_ENCRYPT_ERROR
//
// MessageText:
//
//  DRM is unable to encrypt the content.%0
//
#define NS_E_DRM_ENCRYPT_ERROR           0xC00D2722L

//
// MessageId: NS_E_DRM_DECRYPT_ERROR
//
// MessageText:
//
//  DRM is unable to decrypt the content.%0
//
#define NS_E_DRM_DECRYPT_ERROR           0xC00D2723L

//
// MessageId: NS_E_DRM_LICENSE_PREVENTS_STORING
//
// MessageText:
//
//  The license does not allow saving.%0
//
#define NS_E_DRM_LICENSE_PREVENTS_STORING 0xC00D2724L

//
// MessageId: NS_E_DRM_LICENSE_INVALID_XML
//
// MessageText:
//
//  The license contains invalid XML.%0
//
#define NS_E_DRM_LICENSE_INVALID_XML     0xC00D2725L


#endif _NSERROR_H

