#include "stdafx.h"

#include "dbuf.h"

// static
list<char*> dbuf::freelist;

// static
int dbuf::dbufblocks = 0;

HANDLE dbuf::hProcessHeap=NULL; 

// init/free mem manager
struct dbufMan
	{
	dbufMan(){dbuf::initmem();}
	~dbufMan(){dbuf::freemem();}
	} dbufman;

// static
char *dbuf::allocpage()
	{
	char *p = NULL; 
	if(freelist.size())
		{
		p = freelist.front();
		freelist.erase(freelist.begin());
		}
	else
		{
		p = (char*)HeapAlloc(hProcessHeap, 0, PAGESIZE);
		if(p==NULL)
			{
			// XXX: manage out of memory situation
			cout << "Out of memory" << endl;
			}
		else
			dbufblocks++;
		}
	return p;		
	}


//static 
void dbuf::freepage(char *ptr)
	{
	freelist.push_back(ptr);
	}

//static 
void dbuf::initmem()
	{
	hProcessHeap=GetProcessHeap();
	}
	
//static 
void dbuf::freemem()
	{
	for(list<char*>::iterator it=freelist.begin();it!=freelist.end();it++)
		HeapFree(hProcessHeap, 0, (*it));
	freelist.clear();
	}

///////////////////////////////////////
dbuf::dbuf()
:	readoff(0),
	writeoff(0)
	{
	push_back(allocpage());
	}

dbuf::~dbuf()
	{
	for(iterator it=begin();it!=end();it++)
		freepage(*it);
	}

bool dbuf::put(const char *buf, int len)
	{
	// start from back page
	char *wp = back();
	char *wpp = wp+writeoff;

	// how much space do we have on this page?
	int available = PAGESIZE - writeoff;
	int chunklen = min(len, available);
	if(chunklen>0)
		memcpy(wpp, buf, chunklen);

	// update indicators
	writeoff += chunklen;
	const char *prem = buf + chunklen;
	int nrem = len - chunklen;

	// do we want a new page?
	if(nrem>0)
		{
		push_back(allocpage());
		writeoff = 0;
		// put rest on new page
		put(prem, nrem); 
		}
	return true;
	}

int dbuf::get(char *buf, int len)
	{
	// start reading from front page
	char *rp = front();
	char *rpd = rp + readoff;

	// how much we can read from this page?
	int available = (front()==back())?(writeoff-readoff):(PAGESIZE-readoff);
	// but we should not exit len
	int chunklen = min(available,len);

	// get them
	if(chunklen>0)
		memcpy(buf, rpd, chunklen);

	// and update indicators
	readoff += chunklen;
	char *bufoff = buf + chunklen;
	int spacerem = len - chunklen;

	// can we free this page?
	if(front()==back())
		{
		// no we can not free it, but reuse it
		if(writeoff==readoff)
			{
			writeoff=readoff=0;
			}
		}
	else
		{
		// we have more pages, we can discard this
		if(readoff==PAGESIZE)
			{
			// free this page
			pop_front();
			freepage(rp);
			readoff = 0;
			}
		}

	// do we have more space and data?
	// if yes get it
	available = (front()==back())?(writeoff-readoff):(PAGESIZE-readoff);
	if(spacerem && available)
		return chunklen + get(bufoff, spacerem);

	return chunklen;
	}

// same as 'get' but don't copy to buf
int dbuf::remove(int num)
	{
	// start reading from front page
	char *rp = front();
	char *rpd = rp + readoff;

	// how much we can remove from this page?
	int available = (front()==back())?(writeoff-readoff):(PAGESIZE-readoff);
	// but we should not exit n
	int chunklen = min(available,num);

	// discard them by updating indicators
	// and update indicators
	readoff += chunklen;
	int mumrem = num - chunklen;

	// can we free this page?
	if(front()==back())
		{
		// no we can not free it, but reuse it
		if(writeoff==readoff)
			{
			writeoff=readoff=0;
			}
		}
	else
		{
		// we have more pages, we can discard this
		if(readoff==PAGESIZE)
			{
			// free this page
			pop_front();
			freepage(rp);
			readoff = 0;
			}
		}

	// do we have more space and data?
	// if yes remove it
	available = (front()==back())?(writeoff-readoff):(PAGESIZE-readoff);
	if(mumrem && available)
		return chunklen + remove(mumrem);

	return chunklen;
	}

char *dbuf::getpagedata(int *len)
	{
	// getpagedata works for front page
	char *rp = front();
	*len = (front()==back())?(writeoff-readoff):(PAGESIZE-readoff);
	return rp + readoff;
	}

void dbuf::removepage()
	{
	if(front()==back())
		{
		writeoff=readoff=0;
		}
	else
		{
		char *fp=front();
		pop_front();
		freepage(fp);
		readoff = 0;
		}
	}

int dbuf::findterminator(char *p, int from, int to, char tch)
	{
	int pos = -1;
	int curpos = 0;
	
	char *rpd = p + from;

	// how much we can read from this page?
	int available = to-from;
	
	// scan them
	for(int i=0;i<available;i++)
		{
		if(*rpd++ == tch)
			{
			pos = curpos;
			break;
			}
		curpos++;
		}
	return pos;
	}

int dbuf::findterminator(char tch)
	{
	int pos = -1;
	int curpos = 0;
	for(iterator it=begin();it!=end();it++)
		{
		int from, to;
		if(it==begin()) from = readoff;
		else from = 0;
		if(*it==back()) to = writeoff;
		else to = PAGESIZE;
		int pagepos = findterminator(*it,from,to, tch);
		if(pagepos>=0)
			{
			pos = curpos + pagepos;
			break;
			}
		curpos += (to-from);
		}
	return pos;
	}


// similar to 'get' but don't copies to buf if 
// no terminator found.
// return number of bytes copied
// if terminator found but we don't have space
// then copy as much as posible
int dbuf::getmsg(char *buf, int len)
	{
	// at what pos is the terminator?
	int pos = findterminator('\n');

	if(pos==-1)
		{
		// no terminator found
		return 0;
		}

	int msglen = pos+1;
	
	// can we return all the message?
	if(msglen<=len)
		{
		return get(buf, msglen);
		}

	// return part of message and discard rest
	get(buf, len);
	remove(msglen-len);
	return len;
	}


