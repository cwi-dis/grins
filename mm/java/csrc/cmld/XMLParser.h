#ifndef INC_XMLPARSER
#define INC_XMLPARSER

#ifndef INC_ELEMENT
#include "lib/Element.h"
#endif

#ifndef XmlParse_INCLUDED
#include "xmlparse\xmlparse.h"
#endif

class XMLParser : public stack<Element*>
	{
	public:
	XMLParser(LPCTSTR pszRoot);
	~XMLParser();

	bool beginParsing();
	bool parse(const char *data, int len);
	bool endParsing();
	list<Element*>& getCommands(){return m_cmdstream;}
	
	private:
	static void startElement(void *userData, const char *name, const char **atts);
	static void endElement(void *userData, const char *name);
	static void charData(void *userData, const char *s, int len);
	static int encoding(void *userData, const char *encName, XML_Encoding *info);

	void freeParser();
	void restartParser() {freeParser();beginParsing();}
	void *m_xmlParser;
	
	void putStreamElement(Element *e){m_cmdstream.push_back(e);}

	void clear(){while(!empty()){delete top();pop();}}
	
	list<Element*> m_cmdstream;

	bool isRoot(const char *name) {return strcmpi(name,m_strRoot.c_str())==0;}
	string m_strRoot;
	};

#endif
