
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_XML_PARSERS
#define INC_XML_PARSERS

#ifndef INC_XML_PARSER_ADAPTER
#include "xml/sax_handler.h"
#endif

///////////////////////////
// Adapter for expat parser

#include "expat/expat.h"

class ExpatParser
	{
	public:
	ExpatParser(xml::sax_handler *handler)
	:	m_handler(handler),
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

	virtual bool parse(const char *buf, int len, bool isFinal = false) const
		{
		if(!expatParser) return false;
		if (!XML_Parse(expatParser, buf, len, isFinal?1:0)) 
			{
			std::string str;
			str << XML_ErrorString(XML_GetErrorCode(expatParser))
				<< " at line " << XML_GetCurrentLineNumber(expatParser);
			m_handler->show_error(str);
			return false;
			}
		return true;
		}
	
	private:
	static void startElement(void *userData, const char *name, const char **attrs)
		{
		ExpatParser *p = static_cast<ExpatParser*>(userData);
		p->m_handler->start_element(name, attrs);
		}

	static void endElement(void *userData, const char *name)
		{
		ExpatParser *p = static_cast<ExpatParser*>(userData);
		p->m_handler->end_element();
		}

	static void charData(void *userData, const char *s, int len)
		{
		ExpatParser *p = static_cast<ExpatParser*>(userData);
		p->m_handler->handle_data(s, len);
		}
	void *expatParser;
	xml::sax_handler *m_handler;
	};


#endif // INC_XML_PARSERS
