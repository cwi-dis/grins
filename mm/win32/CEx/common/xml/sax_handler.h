/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_XML_SAX_HANDLER
#define INC_XML_SAX_HANDLER

namespace xml {

class sax_handler
	{
	public:
	virtual ~sax_handler(){}
	virtual void start_element(const char *name, const char **atts) = 0;
	virtual void end_element() = 0;
	virtual void handle_data(const char *s, int len) = 0;
	// ...
	virtual void show_error(const std::string& report) = 0;
	};


} // namespace xml


#endif  // INC_XML_SAX_HANDLER
