
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

class tree_node;

namespace smil {

class parser : public xml::sax_handler
	{
	public:
	typedef void (parser::*start_handler_t)(std::list<raw_attr_t> *pattrs);
	typedef void (parser::*end_handler_t)();
	typedef std::pair<start_handler_t, end_handler_t> element_handler_t;
	typedef std::map<std::string, element_handler_t> handler_map_t;

	parser();
	~parser();

	void reset();
	tree_node* detach();

	//
	void start_smil(raw_attr_list_t *pattrs);
	void end_smil();

	void start_head(raw_attr_list_t *pattrs);
	void end_head();

	void start_meta(raw_attr_list_t *pattrs);
	void end_meta();

	void start_metadata(raw_attr_list_t *pattrs);
	void end_metadata();

	void start_layout(raw_attr_list_t *pattrs);
	void end_layout();

	void start_customAttributes(raw_attr_list_t *pattrs);
	void end_customAttributes();

	void start_customTest(raw_attr_list_t *pattrs);
	void end_customTest();

	void start_region(raw_attr_list_t *pattrs);
	void end_region();

	void start_root_layout(raw_attr_list_t *pattrs);
	void end_root_layout();

	void start_viewport(raw_attr_list_t *pattrs);
	void end_viewport();

	void start_body(raw_attr_list_t *pattrs);
	void end_body();

	void start_par(raw_attr_list_t *pattrs);
	void end_par();

	void start_seq(raw_attr_list_t *pattrs);
	void end_seq();

	void start_switch(raw_attr_list_t *pattrs);
	void end_switch();

	void start_excl(raw_attr_list_t *pattrs);
	void end_excl();

	void start_priorityClass(raw_attr_list_t *pattrs);
	void end_priorityClass();

	void start_ref(raw_attr_list_t *pattrs);
	void end_ref();

	void start_text(raw_attr_list_t *pattrs);
	void end_text();

	void start_audio(raw_attr_list_t *pattrs);
	void end_audio();

	void start_img(raw_attr_list_t *pattrs);
	void end_img();

	void start_video(raw_attr_list_t *pattrs);
	void end_video();

	void start_animation(raw_attr_list_t *pattrs);
	void end_animation();

	void start_textstream(raw_attr_list_t *pattrs);
	void end_textstream();

	void start_brush(raw_attr_list_t *pattrs);
	void end_brush();

	void start_a(raw_attr_list_t *pattrs);
	void end_a();

	void start_anchor(raw_attr_list_t *pattrs);
	void end_anchor();

	void start_area(raw_attr_list_t *pattrs);
	void end_area();

	void start_animate(raw_attr_list_t *pattrs);
	void end_animate();

	void start_set(raw_attr_list_t *pattrs);
	void end_set();

	void start_animateMotion(raw_attr_list_t *pattrs);
	void end_animateMotion();

	void start_animateColor(raw_attr_list_t *pattrs);
	void end_animateColor();

	void start_transitionFilter(raw_attr_list_t *pattrs);
	void end_transitionFilter();

	void start_param(raw_attr_list_t *pattrs);
	void end_param();

	void start_transition(raw_attr_list_t *pattrs);
	void end_transition();

	void start_regPoint(raw_attr_list_t *pattrs);
	void end_regPoint();

	void start_prefetch(raw_attr_list_t *pattrs);
	void end_prefetch();

	//
	void unknown_starttag(const char *tag, raw_attr_list_t *pattrs);
	void unknown_endtag();

	//
	void new_node(const char *name, raw_attr_list_t *pattrs);
	void end_node();

	// <<xml::sax_handler interface>>
	virtual void start_element(const char *name, const char **attrs)
		{
		m_stack.push(name);
		raw_attr_list_t *pattrs = NULL;
		if(attrs) {
			pattrs = new raw_attr_list_t();
			for(int i=0;attrs[i];i+=2)
				pattrs->push_back(raw_attr_t(attrs[i], attrs[i+1]));
			}
		handler_map_t::iterator it = m_handlers.find(name);
		if(it != m_handlers.end())
			(this->*(*it).second.first)(pattrs);
		else
			unknown_starttag(name, pattrs);
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

	virtual void show_error(std::string& report)
		{
		}

	//
	private:
	void set_handler(const char* psz, start_handler_t sh, end_handler_t eh)
		{ m_handlers[psz] = element_handler_t(sh, eh);}
	handler_map_t m_handlers;
	std::stack<std::string> m_stack;

	tree_node *m_rootnode;
	tree_node *m_curnode;
	};


} // namespace smil

#endif // INC_SMIL_PARSER

