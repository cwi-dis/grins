#ifndef INC_STD
#define INC_STD


// Std headers for each platform
// Plus types defs
// for win32 for example should be 'windows.h' without any defs

// borrow from rma, platform idependent:
#include "pntypes.h" 


// STD C++ LIB (STL)
#ifdef _WIN32
#pragma warning(disable: 4786) // Long names trunc
#pragma warning(disable: 4251) // dll-interface
#endif

#if !defined(_ABIO32) || _ABIO32 == 0
#include <string>
#include <map>
using namespace std;
#else
typedef int bool;
enum { false, true, };
#endif

#endif
