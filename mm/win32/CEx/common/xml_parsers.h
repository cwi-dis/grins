#ifndef INC_XML_PARSERS
#define INC_XML_PARSERS

template <class Node>
class XMLParser 
	{
	public:
	virtual ~XMLParser() {}
	virtual void setXMLDocument(Node *p) = 0;
	virtual bool parse(const char *buf, int len, bool isFinal=false) const = 0;
	};


///////////////////////////
// Adapter for expat parser

#include "expat/expat.h"

template <class Node>
class ExpatParser : public XMLParser<Node>
	{
	public:
	ExpatParser()
	:	root(0),
		currnode(0),
		expatParser(NULL)
		{
		}
	ExpatParser(Node *r)
	:	root(r),
		currnode(r),
		expatParser(NULL)
		{
		expatParser = XML_ParserCreate(NULL);
		XML_SetUserData(expatParser, this);
		XML_SetElementHandler(expatParser, ExpatParser::startElement, ExpatParser::endElement);
		XML_SetCharacterDataHandler(expatParser, ExpatParser::charData);
		}
	virtual ~ExpatParser()
		{
		if(expatParser!=NULL)
			XML_ParserFree(expatParser);
		}

	virtual void setXMLDocument(Node *p)
		{
		root = currnode = p;
		if(expatParser!=NULL)
			XML_ParserFree(expatParser);
		expatParser = XML_ParserCreate(NULL);
		XML_SetUserData(expatParser, this);
		XML_SetElementHandler(expatParser, ExpatParser::startElement, ExpatParser::endElement);
		XML_SetCharacterDataHandler(expatParser, ExpatParser::charData);
		}

	virtual bool parse(const char *buf, int len, bool isFinal=false) const
		{
		if(!expatParser) return false;
		if (!XML_Parse(expatParser, buf, len, isFinal?1:0)) 
			{
			/*
			std::string str;
			str << XML_ErrorString(XML_GetErrorCode(expatParser))
				<< " at line " << XML_GetCurrentLineNumber(expatParser);
				*/
			return false;
			}
		return true;
		}
	
	private:
	static void startElement(void *userData, const char *name, const char **atts)
		{
		ExpatParser *p = static_cast<ExpatParser*>(userData);
		p->startElement(new Node(name, atts));
		//cout << XML_GetCurrentLineNumber(p->expatParser) << " <" << name << ">" << endl;
		}

	static void endElement(void *userData, const char *name)
		{
		ExpatParser *p = static_cast<ExpatParser*>(userData);
		p->endElement();
		//cout << XML_GetCurrentLineNumber(p->expatParser) << " </" << name << ">" << endl;
		}

	static void charData(void *userData, const char *s, int len)
		{
		ExpatParser *p = static_cast<ExpatParser*>(userData);
		if(p->currnode) p->currnode->appendCharData(s, len);
		}

	void startElement(Node *p)
		{
		currnode->appendChild(p);
		currnode = p;
		}

	void endElement()
		{
		currnode = currnode->up();
		}

	void *expatParser;
	Node *root;
	Node *currnode;
	};


#endif // INC_XML_PARSERS
