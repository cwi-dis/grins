// CMIF_ADD
//
// kk@epsilon.com.gr
//
//
// Note that this source file contains embedded documentation.
// This documentation consists of marked up text inside the
// C comments, and is prefixed with an '@' symbol.  The source
// files are processed by a tool called "autoduck" which
// generates Windows .hlp files.
// @doc



#include "stdafx.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(DS);
IMPLEMENT_PYMODULECLASS(DS,GetDS,"DirectShow Module Wrapper Object");


#include "GraphBuilder.h"

// @object PyDS|A module wrapper object.  It is a general utility object, and is not associated with an MFC object.
BEGIN_PYMETHODDEF(DS)
	{"CreateGraphBuilder",PyIClass<IGraphBuilder,GraphBuilderCreator>::Create,1},
END_PYMETHODDEF()

DEFINE_PYMODULETYPE("PyDS",DS);

