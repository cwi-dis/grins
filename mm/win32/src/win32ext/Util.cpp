#include "stdafx.h"

#include "win32win.h"

// Utilities 

#include "moddef.h"
DECLARE_PYMODULECLASS(Util);
IMPLEMENT_PYMODULECLASS(Util,GetUtil,"Utilities Module Wrapper Object");

// None

BEGIN_PYMETHODDEF(Util)
END_PYMETHODDEF()

DEFINE_PYMODULETYPE("PyUtil",Util);

