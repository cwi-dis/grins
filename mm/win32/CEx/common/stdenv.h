#ifndef INC_STDENV
#define INC_STDENV

// long names trunc
#pragma warning(disable: 4786)

// signed/unsigned mismatch
#pragma warning(disable: 4018)
 
// std c++ library
#include <iterator>
#include <memory>
#include <functional>
#include <algorithm>
#include <utility>

#include <string>
#include <vector>
#include <list>
#include <map>
#include <stack>
#include <deque>

#include <limits>

// begin stdc
#include <math.h>
// end stdc

// strsteam replacement
inline std::string& operator<<(std::string& s, const char *psz) 
	{ s += psz; return s;}

inline std::string& operator<<(std::string& s, const std::string& o) 
	{ s+=o; return s;}

inline std::string& operator<<(std::string& s, int c) 
	{char sz[16];sprintf(sz,"%d",c); s+=sz; return s;}	

inline std::string& operator<<(std::string& s, double c) 
	{char sz[16];sprintf(sz,"%f",c); s+=sz; return s;}
// end of strsteam replacement

#endif // INC_STDENV

