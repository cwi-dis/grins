/* this file contains the actual definitions of */
/* the IIDs and CLSIDs */

/* link this file in with the server and any clients */


/* File created by MIDL compiler version 3.01.75 */
/* at Fri Dec 03 17:05:13 1999
 */
/* Compiler settings for .\propmap.idl:
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

const IID IID_IEnumPropertyMap = {0xc733e4a1,0x576e,0x11d0,{0xb2,0x8c,0x00,0xc0,0x4f,0xd7,0xcd,0x22}};


const IID IID_IPropertyMap = {0xc733e4a2,0x576e,0x11d0,{0xb2,0x8c,0x00,0xc0,0x4f,0xd7,0xcd,0x22}};


#ifdef __cplusplus
}
#endif

