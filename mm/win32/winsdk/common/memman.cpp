#include "memman.h"

// meta_memman: cleanup on exit
struct meta_memman
	{
	~meta_memman() 
		{ 
		// free all allocated pages
		memman::clear();
		}
	} 
the_meta_memman;


//static 
std::multimap<DWORD, BYTE*> memman::s_freepages;

//static 
BYTE* memman::alloc(DWORD& capacity)
	{
	// no free pages
	if(s_freepages.empty())
		{
		BYTE *begin = (BYTE*)::HeapAlloc(GetProcessHeap(), 0, capacity);
		assert(begin != 0);
		capacity = HeapSize(GetProcessHeap(), 0, begin);
		return begin;
		}
		
	std::multimap<DWORD, BYTE*>::iterator it;

	// find the first page with size not less than capacity (i.e. >= capacity)
	it = s_freepages.lower_bound(capacity);
	if(it == s_freepages.end())
		{
		// no upper bound
		// reuse larger page
		it--;
		DWORD n = (*it).first;
		BYTE *begin = (*it).second;
		s_freepages.erase(it);
		assert(n<capacity);
		begin = (BYTE*)::HeapReAlloc(GetProcessHeap(), 0, begin, capacity); 
		capacity = ::HeapSize(GetProcessHeap(), 0, begin);
		return begin;
		}

	// reuse upper bound
	assert(capacity <= (*it).first);
	capacity = (*it).first;
	s_freepages.erase(it);
	return (*it).second;
	}

//static 
void memman::free(BYTE *pb, DWORD capacity)
	{
	s_freepages.insert(std::pair<DWORD const, BYTE*>(capacity, pb));
	}

//static 
void memman::clear()
	{
	std::multimap<DWORD, BYTE*>::iterator it;
	for(it = s_freepages.begin(); it != s_freepages.end(); it++)
		HeapFree(GetProcessHeap(), 0, (*it).second);
	s_freepages.clear();
	}



