/* this file contains the actual definitions of */
/* the IIDs and CLSIDs */

/* link this file in with the server and any clients */


/* File created by MIDL compiler version 3.01.75 */
/* at Fri Dec 03 17:05:17 1999
 */
/* Compiler settings for .\nssauthen.idl:
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

const IID IID_INSSAuthenticationCallback = {0x6bf5dfc4,0x1b4d,0x11d1,{0x93,0x12,0x00,0xc0,0x4f,0xd9,0x19,0xb7}};


const IID IID_INSSAuthenticator = {0xcb27d5e6,0x3778,0x11d1,{0x8c,0x96,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


const IID IID_INSSUserAuthentication = {0x48eea71a,0x3775,0x11d1,{0x8c,0x96,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


#ifdef __cplusplus
}
#endif

