// stdenv.h

#ifndef INC_STDENV

#  ifdef min
#     undef min
#  endif
#  ifdef max
#     undef max
#  endif

// long names trunc
#pragma warning(disable: 4786)

// std c++ library
#include <iterator>
#include <memory>
#include <functional>
#include <algorithm>
#include <utility>
#include <typeinfo>

#include <exception>
#include <stdexcept>
#include <new>

#include <iostream>
#include <fstream>
#include <iomanip>
#include <sstream>

#include <string>
#include <vector>
#include <list>
#include <map>
#include <stack>

#include <cassert>

#endif // INC_STDENV

