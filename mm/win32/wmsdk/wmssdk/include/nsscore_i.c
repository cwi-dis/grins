/* this file contains the actual definitions of */
/* the IIDs and CLSIDs */

/* link this file in with the server and any clients */


/* File created by MIDL compiler version 3.01.75 */
/* at Fri Dec 03 17:05:12 1999
 */
/* Compiler settings for .\nsscore.idl:
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

const IID IID_INSSServerContext = {0x98999822,0x2002,0x11d1,{0x8c,0x94,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


const IID IID_INSSUserContext = {0x4639f850,0x2003,0x11d1,{0x8c,0x94,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


const IID IID_INSSPresentationContext = {0x4639f851,0x2003,0x11d1,{0x8c,0x94,0x00,0xa0,0xc9,0x03,0xa1,0xa2}};


const IID IID_INSSCommandContext = {0x33309E72,0x37CD,0x11d1,{0x9E,0x9F,0x00,0x60,0x97,0xD2,0xD7,0xCF}};


#ifdef __cplusplus
}
#endif

