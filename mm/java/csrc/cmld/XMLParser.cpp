#include "stdafx.h"

#include "XMLParser.h"

#include "xmlparse/xmlparse.h"


XMLParser::XMLParser(LPCTSTR pszRoot)
:	m_xmlParser(NULL), m_strRoot(pszRoot)
	{
	}

XMLParser::~XMLParser()
	{
	freeParser();
	}

// static 
void XMLParser::startElement(void *userData, const char *name, const char **atts)
	{
	XMLParser *p = static_cast<XMLParser*>(userData);
	if(p->isRoot(name)) return;
	p->push(new Element(name, atts));
	}

// static 
void XMLParser::endElement(void *userData, const char *name)
	{
	XMLParser *p = static_cast<XMLParser*>(userData);
	if(p->isRoot(name)) return;
	Element *pel = p->top();
	p->pop();
	if(p->size()==0)
		p->putStreamElement(pel);
	else
		p->top()->appendChild(pel);
	}

// static 
void XMLParser::charData(void *userData, const XML_Char *s, int len)
	{
	XMLParser *p = static_cast<XMLParser*>(userData);
	if(p->size()) 
		{
		string str;
		for(int i=0;i<len;i++){	
			// see XmlUtf8Encode in xmltok.c
			if(s[i]=='\xC3')
				str += char(64 + (int)s[++i]);
			else
				str += s[i];
			}
		p->top()->appendCharData(str.c_str(), str.length());
		//p->top()->appendCharData(s, len);
		}
	}

// static 
int XMLParser::encoding(void *userData, const XML_Char *encName, XML_Encoding *info)
	{
	XMLParser *p = static_cast<XMLParser*>(userData);
	cout << "Unknown encoding: " << encName << endl;
	return 1;
	}

bool XMLParser::beginParsing()
	{
	if(m_xmlParser!=NULL) return true;
	m_xmlParser = XML_ParserCreate(NULL);
	XML_SetUserData(m_xmlParser, this);
	XML_SetElementHandler(m_xmlParser, XMLParser::startElement, XMLParser::endElement);
	XML_SetCharacterDataHandler(m_xmlParser, XMLParser::charData);
	XML_SetUnknownEncodingHandler(m_xmlParser, XMLParser::encoding, this);
	string s("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<");
	s << m_strRoot << ">\n";
	if (!XML_Parse(m_xmlParser, s.c_str(), s.length(), 0)) 
		{
		cerr << XML_ErrorString(XML_GetErrorCode(m_xmlParser))
			<< " at line " << XML_GetCurrentLineNumber(m_xmlParser)
			<< endl;
		return false;
		}
	return true;
	}

bool XMLParser::parse(const char *data, int len)
	{
	if(!m_xmlParser) return false;
	if (!XML_Parse(m_xmlParser, data, len, 0)) 
		{
		cerr << XML_ErrorString(XML_GetErrorCode(m_xmlParser))
			<< " at line " << XML_GetCurrentLineNumber(m_xmlParser)
			<< endl;
		restartParser();
		return false;
		}
	return true;
	}

bool XMLParser::endParsing()
	{
	bool ret = true;
	string s("</");
	s << m_strRoot << ">\n";
	if (!XML_Parse(m_xmlParser, s.c_str(), s.length(), 1)) 
		{
		cerr << XML_ErrorString(XML_GetErrorCode(m_xmlParser))
			<< " at line " << XML_GetCurrentLineNumber(m_xmlParser)
			<< endl;
		ret = false;
		}
	freeParser();
	return ret;
	}

void XMLParser::freeParser()
	{
	clear();
	if(m_xmlParser!=NULL)
		{
		XML_ParserFree(m_xmlParser);
		m_xmlParser=NULL;
		}
	}

