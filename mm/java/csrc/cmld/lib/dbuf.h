#ifndef INC_DBUF
#define INC_DBUF

// align to windows page size (4096)
#define PAGESIZE 2048

class dbuf : public list<char*>
	{
	public:
	dbuf();
	~dbuf();

	bool put(const char *buf, int len);
	int get(char *buf, int len);

	int getmsg(char *buf, int len);
	int remove(int n);

	// reading interface
	void rewind();
	int readch();
	int read(char *buf, int len);
		
	// fast but use carefully in pair
	char *getpagedata(int *len);
	void removepage();

	int findterminator(char t);
	int findterminator(char *page, int from, int to, char t);
	
	int readoff;  
	int writeoff;
	
	static void initmem();
	static void freemem();
	static char *allocpage();
	static void freepage(char *ptr);
	static list<char*> freelist;
	static int dbufblocks;
	static HANDLE hProcessHeap;
	};

#endif

