
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_SMIL_PARSER
#define INC_SMIL_PARSER

#ifndef INC_XML_PARSER_ADAPTER
#include "xml/sax_handler.h"
#endif

#ifndef INC_EXTRA_TYPES
#include "extra_types.h"
#endif

template <class Node>
class tree_node;

namespace smil {

class node;

class parser : public xml::sax_handler
	{
	public:
	typedef raw_attr_map_t* handler_arg_type;

	typedef void (parser::*start_handler_t)(handler_arg_type attrs);
	typedef void (parser::*end_handler_t)();
	typedef std::pair<start_handler_t, end_handler_t> element_handler_t;
	typedef std::map<std::string, element_handler_t> handler_map_t;

	parser();
	~parser();

	void reset();
	node* detach();

	//
	void start_smil(handler_arg_type attrs);
	void end_smil();

	void start_head(handler_arg_type attrs);
	void end_head();

	void start_meta(handler_arg_type attrs);
	void end_meta();

	void start_metadata(handler_arg_type attrs);
	void end_metadata();

	void start_layout(handler_arg_type attrs);
	void end_layout();

	void start_customAttributes(handler_arg_type attrs);
	void end_customAttributes();

	void start_customTest(handler_arg_type attrs);
	void end_customTest();

	void start_region(handler_arg_type attrs);
	void end_region();

	void start_root_layout(handler_arg_type attrs);
	void end_root_layout();

	void start_viewport(handler_arg_type attrs);
	void end_viewport();

	void start_body(handler_arg_type attrs);
	void end_body();

	void start_par(handler_arg_type attrs);
	void end_par();

	void start_seq(handler_arg_type attrs);
	void end_seq();

	void start_switch(handler_arg_type attrs);
	void end_switch();

	void start_excl(handler_arg_type attrs);
	void end_excl();

	void start_priorityClass(handler_arg_type attrs);
	void end_priorityClass();

	void start_ref(handler_arg_type attrs);
	void end_ref();

	void start_text(handler_arg_type attrs);
	void end_text();

	void start_audio(handler_arg_type attrs);
	void end_audio();

	void start_img(handler_arg_type attrs);
	void end_img();

	void start_video(handler_arg_type attrs);
	void end_video();

	void start_animation(handler_arg_type attrs);
	void end_animation();

	void start_textstream(handler_arg_type attrs);
	void end_textstream();

	void start_brush(handler_arg_type attrs);
	void end_brush();

	void start_a(handler_arg_type attrs);
	void end_a();

	void start_anchor(handler_arg_type attrs);
	void end_anchor();

	void start_area(handler_arg_type attrs);
	void end_area();

	void start_animate(handler_arg_type attrs);
	void end_animate();

	void start_set(handler_arg_type attrs);
	void end_set();

	void start_animateMotion(handler_arg_type attrs);
	void end_animateMotion();

	void start_animateColor(handler_arg_type attrs);
	void end_animateColor();

	void start_transitionFilter(handler_arg_type attrs);
	void end_transitionFilter();

	void start_param(handler_arg_type attrs);
	void end_param();

	void start_transition(handler_arg_type attrs);
	void end_transition();

	void start_regPoint(handler_arg_type attrs);
	void end_regPoint();

	void start_prefetch(handler_arg_type attrs);
	void end_prefetch();

	//
	void unknown_starttag(const std::string& tag, handler_arg_type attrs);
	void unknown_endtag();

	void new_node(const std::string& tag, handler_arg_type attrs);
	void end_node();

	void  new_media_node(const std::string& tag, handler_arg_type attrs);
	void  end_media_node();

	// <<xml::sax_handler interface>>
	virtual void start_element(const char *name, const char **sattrs)
		{
		m_stack.push(name);
		handler_arg_type attrs = 0;
		if(sattrs != 0) 
			{
			attrs = new raw_attr_map_t();
			for(int i=0;sattrs[i];i+=2)
				(*attrs)[sattrs[i]] = sattrs[i+1];
			}
		handler_map_t::iterator it = m_handlers.find(name);
		if(it != m_handlers.end())
			(this->*(*it).second.first)(attrs);
		else
			unknown_starttag(name, attrs);
		}

	virtual void end_element()
		{
		handler_map_t::iterator it = m_handlers.find(m_stack.top());
		if(it != m_handlers.end())
			(this->*(*it).second.second)();
		else
			unknown_endtag();
		assert(!m_stack.empty());
		m_stack.pop();
		}

	virtual void handle_data(const char *s, int len)
		{
		}

	virtual void show_error(const std::string& report);

	//
	private:
	void set_handler(const char* psz, start_handler_t sh, end_handler_t eh)
		{ m_handlers[psz] = element_handler_t(sh, eh);}
	handler_map_t m_handlers;
	std::stack<std::string> m_stack;

	node *m_rootnode;
	node *m_curnode;
	};


} // namespace smil

#endif // INC_SMIL_PARSER

