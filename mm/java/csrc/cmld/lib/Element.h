#ifndef INC_ELEMENT
#define INC_ELEMENT

// Optimizations: memory, read only

class Element
	{
	public:
	Element(const char *name, const char **atts=NULL)
	:	m_name(name?name:"error"),
		m_child(NULL),												   
		m_next(NULL)
		{
		for(int i=0;atts[i];i+=2)
			m_attrs[atts[i]]=atts[i+1];
#ifdef _DEBUG
		s_elementCounter++;
#endif
		}
	
	~Element()
		{
#ifdef _DEBUG
		s_elementCounter--;
#endif
		Element *e = m_child;
		if(e)
			{
			Element *tmp = e;
			e = e->m_next;
			delete tmp;
			while(e)
				{
				Element *tmp = e;
				e = e->m_next;
				delete tmp;
				}
			}
		}
	int appendCharData(const char *data, int len)
		{
		//if(len>0 && data[len-1]=='\n') len--;
		if(len) m_data.append(data, len);
		return m_data.size();
		}
	
	void appendChild(Element* child);
		
	const char *getName() const {return m_name.c_str();}
	const char *getData() const {return m_data.c_str();}
	const char *getXMLQuotedData();
	int getDataSize() const {return m_data.size();}
	const char *getAttribute(const char *name) const;
	const map<string, string>& getAttributes() const {return m_attrs;}
	void getChildren(list<const Element*>& l) const;
	void getChildren(list<const Element*>& l, const char *name) const;
	const Element *getFirstChild(const char *name) const;

	static const char* XMLQuote(string& s);
	static  const string Element::XMLQuote(LPCTSTR psz);

	
#ifdef _DEBUG
	static int s_elementCounter;
#endif
	
	private:
	const Element *getChild() const {return m_child;}
	const Element *getNext() const {return m_next;}			
	void setChild(Element *e){m_child=e;}
	void setNext(Element *e){m_next=e;}
	
	string m_name;
	string m_data;
	map<string, string> m_attrs;
	Element *m_child;												   
	Element *m_next;

	// cache quoted data so that they are computed once
	string m_xmlQuotedData;
	};


inline void Element::appendChild(Element* child)
	{
	if(!m_child) 
		m_child = child;
	else
		{
		Element *e = m_child;
		while(e->m_next) e = e->m_next;
		e->m_next = child;
		}
	}

inline const char *Element::getAttribute(const char *name) const 
	{
	map<string, string>::const_iterator i=m_attrs.find(name); 
	return (i!=m_attrs.end())?(*i).second.c_str():"";
	}


inline void Element::getChildren(list<const Element*>& l) const
	{
	const Element *e = getChild();
	if(!e) return;
	l.push_back(e);
	while((e=e->getNext())) l.push_back(e);
	}

inline void Element::getChildren(list<const Element*>& l, const char *name) const
	{
	const Element *e = getChild();
	if(!e) return;
	if(e->m_name==name)l.push_back(e);
	while((e=e->getNext())) if(e->m_name==name) l.push_back(e);
	}

inline const Element *Element::getFirstChild(const char *name) const
	{
	const Element *e = getChild();
	if(!e) return NULL;
	if(e->m_name==name)return e;
	while((e=e->getNext())) if(e->m_name==name) return e;
	return NULL;
	}

inline const char *Element::getXMLQuotedData()
	{
	string& s = m_xmlQuotedData;
	if(s.size()!=0) return s.c_str();
	for(int i=0;i<m_data.length();i++)
		{
		char ch = m_data.at(i);
        if(ch=='<') s+="&lt;";
        else if(ch=='>') s+="&gt;";
        else if(ch=='&') s+="&amp;";
        else s+=ch;
		}
	return s.c_str();
	}

inline const char* Element::XMLQuote(string& s)
	{
	string sc(s);
	s="";
	for(int i=0;i<sc.length();i++)
		{
		char ch = sc.at(i);
        if(ch=='<') s+="&lt;";
        else if(ch=='>') s+="&gt;";
        else if(ch=='&') s+="&amp;";
        else s+=ch;
		}
	return s.c_str();
	}
inline const string Element::XMLQuote(LPCTSTR psz)
	{
	string sc(psz);
	string s;
	for(int i=0;i<sc.length();i++)
		{
		char ch = sc.at(i);
        if(ch=='<') s+="&lt;";
        else if(ch=='>') s+="&gt;";
        else if(ch=='&') s+="&amp;";
        else s+=ch;
		}
	return s;
	}

#endif

