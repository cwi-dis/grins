
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/


#ifndef INC_RE
#define INC_RE

#ifdef _WIN32_WCE
typedef long off_t;
#endif

#ifndef _REGEX_H_
#include "regex/hsregex.h"
#endif

#define REG_FAILED(err) ((err)!=0)
#define REG_SUCCEEDED(err) ((err)==0)

// preprocess regex for extensions
// we currently support only named groups
class REGroupPreproc
	{
	public:
	typedef std::string::const_iterator const_iterator;

	REGroupPreproc(const_iterator begin, const_iterator end)
	:	m_it(begin), 
		m_end(end), 
		m_nsub(0)
		{
		scan();
		}

	const std::string& get_pattern() {return m_pattern;}
	const std::map<std::string, int>& get_groups() { return m_groups;}

	private:

	void scan()
		{
		while (m_it != m_end) 
			switch(*m_it)
			{
			case '\\': scan_esc(); break;
			case '(': scan_paren(); break;
			default: m_pattern += *m_it++; break;
			}
		}
	
	// m_it is positioned at '\\'
	void scan_esc()
		{
		if(*(m_it+1) == 'd')
			{
			m_pattern += "[0-9]";
			m_it += 2;
			}
		else
			{
			m_pattern += *m_it++;
			m_pattern += *m_it++;
			}
		}

	// m_it is positioned at '('
	void scan_paren()
		{
		m_pattern += *m_it++;
		m_nsub++;
		// check for an extension
		if(*m_it == '?')
			{
			m_it++;
			scan_extension();
			}
		}

	// m_it is positioned after '?'
	void scan_extension()
		{
		if(*m_it == 'P')
			{
			m_it++;
			scan_name();
			}
		else
			{
			// ignore/bypass (will work for no arg extensions like ?:)
			m_it++;
			}
		}

	// m_it is positioned at '<'
	// on exit after '>' or eos
	void scan_name()
		{
		m_it++;
		std::string name;
		while(m_it != m_end && *m_it != '>') name += *m_it++;
		if(*m_it == '>') m_it++;
		m_groups[name] = m_nsub;
		}

	const_iterator m_it;
	const_iterator m_end;
	int m_nsub;
	std::string m_pattern;
	std::map<std::string, int> m_groups;
	};

class RE;

class REMatch
	{
	// <<public queries>>
	public:

	typedef std::pair<const char*, const char*> sub_match_t;

	// number of subex + 1 (0-index all)
	size_t size() const {return m_re_nsub + 1;}

	// 0 is all, 1 is first subex, etc
	std::string get_subex_str(int i) const 
		{
		assert(m_isvalid && i>=0 && i<=m_re_nsub);
		return std::string(m_begin+m_pmatch[i].rm_so, m_begin+m_pmatch[i].rm_eo);
		}

	// 0 is all, 1 is first subex, etc
	sub_match_t get_subex(int i) const
		{
		assert(m_isvalid && i>=0 && i<=m_re_nsub);
		return sub_match_t(m_begin+m_pmatch[i].rm_so, m_begin+m_pmatch[i].rm_eo);
		}

	std::string get_subex_str(const char *name) const 
		{
		std::map<std::string, int>::const_iterator it = m_groups.find(name);
		if(it == m_groups.end())
			return "";
		return get_subex_str((*it).second);
		}
	
	// RE access 
	// <<create>>
	protected:
	friend class RE;
    REMatch(int re_nsub, const char *begin, const char *end, const std::map<std::string, int>& groups)
	:	m_re_nsub(re_nsub), m_begin(begin), m_end(end), m_groups(groups),
		m_pmatch(new regmatch_t[re_nsub+1]), 
		m_isvalid(false)
		{
		// RE implementation requirement (REG_STARTEND)
		m_pmatch[0].rm_so = 0;
		m_pmatch[0].rm_eo = int(end-begin);
		}
	~REMatch() {if(m_pmatch) delete[] m_pmatch;}

	regmatch_t* get_data() {return m_pmatch;}
	void set_valid(bool f) {m_isvalid = f;}

	// <<data>>
	private:
	const char *m_begin;
	const char *m_end;
	size_t m_re_nsub;
	regmatch_t *m_pmatch;
	bool m_isvalid;
	const std::map<std::string, int>& m_groups;
	};


class RE
	{
	public:
	RE(const std::string& pattern);
	RE(const char *pattern);
	~RE();

	bool is_valid() const { return m_pre != 0;}
	bool match(const char *begin, const char *end);

	const REMatch *get_match() const {return m_pmatch;}
	
	bool compile();
	std::string get_last_error_str() const;

	// rare
	void free();
	int size() const;
	int get_last_error() const {return m_lasterror;}

	const std::string& get_pattern() { return m_group_preproc.get_pattern();}
	const std::map<std::string, int>& get_groups() { return m_group_preproc.get_groups();}
	
	private:
	char* eprint(int err) const;

	regex_t *m_pre;
	int m_copts;
	int m_eopts;
	REMatch *m_pmatch;
	int m_lasterror;
	REGroupPreproc m_group_preproc;
	};

inline RE::RE(const std::string& pattern)
:	m_pre(0), 
	m_group_preproc(pattern.begin(), pattern.end()),
	m_copts(REG_EXTENDED), m_eopts(REG_STARTEND),
	m_pmatch(0),
	m_lasterror(0)
	{
	compile();
	}

inline RE::RE(const char *pattern)
:	m_pre(0), 
	m_group_preproc(pattern, pattern+strlen(pattern)+1),
	m_copts(REG_EXTENDED), m_eopts(REG_STARTEND),
	m_pmatch(0),
	m_lasterror(0)
	{
	compile();
	}

inline RE::~RE()
	{
	if(m_pmatch) delete m_pmatch;
	if(m_pre!=0)
		{
		regfree(m_pre);
		delete m_pre;
		}
	}

inline bool RE::compile()
	{
	if(m_pre) free();
	m_pre = new regex_t;
	m_lasterror = regcomp(m_pre, get_pattern().c_str(), m_copts);
	if(REG_FAILED(m_lasterror))
		{
		delete m_pre;
		m_pre = 0;
		}
	return REG_SUCCEEDED(m_lasterror);
	}

inline bool RE::match(const char *begin, const char *end)
	{
	if(m_pre == 0) return false;
	if(m_pmatch) delete m_pmatch;

	m_pmatch = new REMatch(m_pre->re_nsub, begin, end, m_group_preproc.get_groups());
	m_lasterror = regexec(m_pre, begin, m_pre->re_nsub + 1, m_pmatch->get_data(), m_eopts);
	m_pmatch->set_valid(REG_SUCCEEDED(m_lasterror));

	return REG_SUCCEEDED(m_lasterror);
	}

inline void RE::free()
	{
	if(m_pmatch) 
		{
		delete m_pmatch;
		m_pmatch = 0;
		}
	if(m_pre != 0)
		{
		regfree(m_pre);
		delete m_pre;
		m_pre = 0;
		}
	}

inline int RE::size() const 
	{
	assert(m_pre != 0);
	return m_pre->re_nsub + 1;
	}

inline std::string RE::get_last_error_str() const
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
	len = regerror(REG_ITOA|err, (regex_t *)0, epbuf, sizeof(epbuf));
	assert(len <= sizeof(epbuf));
	return(epbuf);
	}

#endif // #ifndef INC_RE
