/* this file contains the actual definitions of */
/* the IIDs and CLSIDs */

/* link this file in with the server and any clients */


/* File created by MIDL compiler version 3.01.75 */
/* at Fri Dec 03 17:05:15 1999
 */
/* Compiler settings for .\nssevent.idl:
    Os (OptLev=s), W1, Zp8, env=Win32, ms_ext, c_ext
    error checks: none
*/
//@@MIDL_FILE_HEADING(  )
#ifdef __cplusplus
extern "C"{
#endif 


#ifndef __IID_DEFINED__
#define __IID_DEFINED__

typedef struct _IID
{
    unsigned long x;
    unsigned short s1;
    unsigned short s2;
    unsigned char  c[8];
} IID;

#endif // __IID_DEFINED__

#ifndef CLSID_DEFINED
#define CLSID_DEFINED
typedef IID CLSID;
#endif // CLSID_DEFINED

const IID IID_INSSEventNotification = {0x44f7d3e6,0x200c,0x11d1,{0x8c,0x94,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


const IID IID_INSSEventAuthorizationCallback = {0x44f7d3e7,0x200c,0x11d1,{0x8c,0x94,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


const IID IID_INSSEventAuthorization = {0x44f7d3e8,0x200c,0x11d1,{0x8c,0x94,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


#ifdef __cplusplus
}
#endif

