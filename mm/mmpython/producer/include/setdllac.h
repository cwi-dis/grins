/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1998 RealNetworks.
 *  All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Function pointer definition for SetDLLAccessPath() exported by enceng.
 */

#ifndef _SETDLLAC_H_
#define _SETDLLAC_H_

STDAPI  SetDLLAccessPath(const char* pPathDescriptor);

typedef PN_RESULT (* FPRMBUILDSETDLLACCESSPATH) (const char*);

#endif // _SETDLLAC_H_
