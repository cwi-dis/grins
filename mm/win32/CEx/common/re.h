
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/


#ifndef INC_RE
#define INC_RE

#ifdef _WIN32_WCE
//#include <windef.h>
//#include <types.h>
typedef long off_t;
#endif

#ifndef _REGEX_H_
#include "regex/hsregex.h"
#endif

#define REG_FAILED(err) ((err)!=0)
#define REG_SUCCEEDED(err) ((err)==0)

class RE;

class REMatch
	{
	// <<public queries>>
	public:
	size_t size() const {return m_ngroups;}

	int begin() const 
		{assert(m_isvalid); return m_pmatch[0].rm_so;}
	int end() const 
		{assert(m_isvalid); return m_pmatch[0].rm_eo;}

	int begin(int i) const 
		{assert(m_isvalid && i<m_ngroups); return m_pmatch[i+1].rm_so;}

	int end(int i) const 
		{assert(m_isvalid && i<m_ngroups); return m_pmatch[i+1].rm_eo;}

	std::string get_group(const char* pstr) const 
		{return std::string(pstr+begin(), pstr+end());}

	std::string get_group(const char* pstr, int i) const 
		{return std::string(pstr+begin(i), pstr+end(i));}

	// RE access 
	// <<create>>
	protected:
	friend class RE;
    REMatch(int ngroups, int begin=-1, int end=-1)
	:	m_ngroups(ngroups), m_pmatch(new regmatch_t[ngroups+1]), 
		m_isvalid(false)
		{
		if(begin>=0 && end>=begin)
			{
			m_pmatch[0].rm_so = begin;
			m_pmatch[0].rm_eo = end;
			}
		}
	~REMatch() {if(m_pmatch) delete[] m_pmatch;}

	regmatch_t* getData() {return m_pmatch;}
	void setValid(bool f) {m_isvalid = f;}

	// <<data>>
	private:
	size_t m_ngroups;
	regmatch_t *m_pmatch;
	bool m_isvalid;
	};

class RE
	{
	public:
	RE();
	RE(const char *pattern);
	RE(const std::string& pattern);
	~RE();

	void setPattern(const char *pattern) {m_pattern = pattern;}
	void setPattern(const std::string& pattern) {m_pattern = pattern;}
	bool compile();

	bool match(const char *psz, int begin=-1, int end=-1);

	const REMatch *getMatch() const {return m_pmatch;}
	
	std::string getLastErrorString() const;
	const std::string& getPattern() const {return m_pattern;}

	// rare
	void free();
	int size() const;
	int getLastError() const {return m_lasterror;}

	private:
	char* eprint(int err) const;

	regex_t *m_pre;
	std::string m_pattern;
	int m_copts;
	int m_eopts;
	REMatch *m_pmatch;
	int m_lasterror;
	};

inline RE::RE()
:	m_pre(NULL),
	m_copts(REG_EXTENDED), m_eopts(0),
	m_pmatch(NULL),
	m_lasterror(0)
	{
	}

inline RE::RE(const char *pattern)
:	m_pre(NULL), m_pattern(pattern),
	m_copts(REG_EXTENDED), m_eopts(0),
	m_pmatch(NULL),
	m_lasterror(0)
	{
	compile();
	}
inline RE::RE(const std::string& pattern)
:	m_pre(NULL), m_pattern(pattern),
	m_copts(REG_EXTENDED), m_eopts(0),
	m_pmatch(NULL),
	m_lasterror(0)
	{
	compile();
	}

inline RE::~RE()
	{
	if(m_pmatch) delete m_pmatch;
	if(m_pre!=NULL)
		{
		regfree(m_pre);
		delete m_pre;
		}
	}

inline bool RE::compile()
	{
	if(m_pre) free();
	m_pre = new regex_t;
	m_lasterror = regcomp(m_pre, m_pattern.c_str(), m_copts);
	if(REG_FAILED(m_lasterror))
		{
		delete m_pre;
		m_pre = NULL;
		}
	return REG_SUCCEEDED(m_lasterror);
	}

inline bool RE::match(const char *psz, int begin/*=-1*/, int end/*=-1*/)
	{
	assert(m_pre!=NULL);
	if(m_pmatch) delete m_pmatch;
	m_pmatch = new REMatch(m_pre->re_nsub, begin, end);
	int eopts = m_eopts;
	if(begin>=0 && end>=begin) eopts |= REG_STARTEND;
	else eopts &= ~REG_STARTEND;
	m_lasterror = regexec(m_pre, psz, m_pmatch->size()+1, m_pmatch->getData(), eopts);
	m_pmatch->setValid(REG_SUCCEEDED(m_lasterror));
	return REG_SUCCEEDED(m_lasterror);
	}

inline void RE::free()
	{
	if(m_pmatch) 
		{
		delete m_pmatch;
		m_pmatch = NULL;
		}
	if(m_pre!=NULL)
		{
		regfree(m_pre);
		delete m_pre;
		m_pre = NULL;
		}
	}

inline int RE::size() const 
	{
	assert(m_pre!=NULL);
	return m_pre->re_nsub;
	}

inline std::string RE::getLastErrorString() const
	{
	if(REG_SUCCEEDED(m_lasterror)) return "OK";
	char pszerr[256];
	char erbuf[128];
	int len = regerror(m_lasterror, m_pre, erbuf, sizeof(erbuf));
	sprintf(pszerr, "error %s, %d/%d `%s'\n",
			eprint(m_lasterror), len, sizeof(erbuf), erbuf);
	return pszerr;
	}

inline char* RE::eprint(int err) const
	{
	static char epbuf[100];
	size_t len;
	len = regerror(REG_ITOA|err, (regex_t *)NULL, epbuf, sizeof(epbuf));
	assert(len <= sizeof(epbuf));
	return(epbuf);
	}

#endif // #ifndef INC_RE
