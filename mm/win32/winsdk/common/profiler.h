#ifndef INC_UTIL_PROFILER
#define INC_UTIL_PROFILER

#pragma warning(disable: 4786) // long names trunc (debug)
#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <string>

class profiler 
	{
	public:
	profiler(const char* section, DWORD threadhold = 0)
	:	m_section(section), m_threadhold(threadhold), m_begin(GetTickCount()) {}
	
	~profiler()
		{
		DWORD dt = GetTickCount() - m_begin;
		if(dt > m_threadhold)
			printf("%d msecs in %s\n", dt, m_section.c_str());
		}
	private:
	DWORD m_begin;
	DWORD m_threadhold;
	std::string m_section;
	};

#endif // INC_UTIL_PROFILER
