#ifndef INC_STRREC
#define INC_STRREC

class StrRec : public vector<char*>
	{
	public:
    StrRec(const char* pString,const char* pDelims)
	:	apBuf(new char[strlen(pString)+1])
		{
		char *pBuf = apBuf.get();
		strcpy(pBuf,pString);
		char* pLook = strtok(pBuf,pDelims);
		while(pLook)
			{
			push_back(pLook);
			pLook = strtok(NULL,pDelims);
			}
		}
	private:
	auto_ptr<char> apBuf;
	};

class PropRec : public vector<char*>
	{
	public:
    PropRec(const char* pString)
	:	apBuf(new char[strlen(pString)+1])
		{
		char *pBuf = apBuf.get();
		strcpy(pBuf,pString);
		push_back(pBuf);
		char *p = strchr(pBuf,'=');
		if(p)
			{
			*p = '\0';p++;
			push_back(p);
			}
		}
	private:
	auto_ptr<char> apBuf;
	};

class Properties : public map<string, string>
	{
	bool m_bOpened;
	public:
	Properties(const char *fn)
		{
		m_bOpened = false;
		ifstream ifs(fn);
		if(ifs)
			{
			m_bOpened = true;
			char buf[512];
			while(ifs.getline(buf, 512))
				{
				PropRec r(buf);
				if(r.size()==2)
					insert(pair<string,string>(r[0],r[1]));
				}
			ifs.close();
			}
		}
	bool opened(){return m_bOpened;}
	bool haskey(const string& key){return find(key)!=end();}
	string get(const string& key){
		iterator it = find(key);
		if(it==end()) return "";
		return (*it).second;
		}
	};

#endif

