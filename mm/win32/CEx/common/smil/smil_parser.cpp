
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_parser.h"

#include "tree_node.h"

#include "charconv.h"

#include "windowinterface.h"

namespace smil {

parser::parser()
: 	m_rootnode(0),
	m_curnode(0)
	{
	set_handler("smil", &parser::start_smil, &parser::end_smil);
	set_handler("head", &parser::start_head, &parser::end_head);
	set_handler("meta", &parser::start_meta, &parser::end_meta);
	set_handler("metadata", &parser::start_metadata, &parser::end_metadata);
	set_handler("layout", &parser::start_layout, &parser::end_layout);
	set_handler("customAttributes", &parser::start_customAttributes, &parser::end_customAttributes);
	set_handler("customTest", &parser::start_customTest, &parser::end_customTest);
	set_handler("region", &parser::start_region, &parser::end_region);
	set_handler("root-layout", &parser::start_root_layout, &parser::end_root_layout);
	set_handler("topLayout", &parser::start_viewport, &parser::end_viewport);
	set_handler("viewport", &parser::start_viewport, &parser::end_viewport);
	set_handler("body", &parser::start_body, &parser::end_body);
	set_handler("par", &parser::start_par, &parser::end_par);
	set_handler("seq", &parser::start_seq, &parser::end_seq);
	set_handler("switch", &parser::start_switch, &parser::end_switch);
	set_handler("excl", &parser::start_excl, &parser::end_excl);
	set_handler("priorityClass", &parser::start_priorityClass, &parser::end_priorityClass);
	set_handler("ref", &parser::start_ref, &parser::end_ref);
	set_handler("text", &parser::start_text, &parser::end_text);
	set_handler("audio", &parser::start_audio, &parser::end_audio);
	set_handler("img", &parser::start_img, &parser::end_img);
	set_handler("video", &parser::start_video, &parser::end_video);
	set_handler("animation", &parser::start_animation, &parser::end_animation);
	set_handler("textstream", &parser::start_textstream, &parser::end_textstream);
	set_handler("brush", &parser::start_brush, &parser::end_brush);
	set_handler("a", &parser::start_a, &parser::end_a);
	set_handler("anchor", &parser::start_anchor, &parser::end_anchor);
	set_handler("area", &parser::start_area, &parser::end_area);
	set_handler("animate", &parser::start_animate, &parser::end_animate);
	set_handler("set", &parser::start_set, &parser::end_set);
	set_handler("animateMotion", &parser::start_animateMotion, &parser::end_animateMotion);
	set_handler("animateColor", &parser::start_animateColor, &parser::end_animateColor);
	set_handler("transitionFilter", &parser::start_transitionFilter, &parser::end_transitionFilter);
	set_handler("param", &parser::start_param, &parser::end_param);
	set_handler("transition", &parser::start_transition, &parser::end_transition);
	set_handler("regPoint", &parser::start_regPoint, &parser::end_regPoint);
	set_handler("prefetch", &parser::start_prefetch, &parser::end_prefetch);
	}

parser::~parser()
	{
	delete m_rootnode;
	}

// prepare for resuse
void parser::reset()
	{
	if(m_rootnode != 0)
		delete m_rootnode;
	m_rootnode = new tree_node();
	m_curnode = m_rootnode;
	}

// get ownership of root node
tree_node* parser::detach()
	{
	tree_node *temp = m_rootnode;
	m_rootnode = 0;
	m_curnode = 0;
	return temp;
	}

/////////////////
// element handlers

void parser::start_smil(raw_attr_list_t *pattrs)
	{
	new_node("smil", pattrs);
	}

void parser::end_smil()
	{
	end_node();
	}

void parser::start_head(raw_attr_list_t *pattrs)
	{
	new_node("head", pattrs);
	}

void parser::end_head()
	{
	end_node();
	}

void parser::start_meta(raw_attr_list_t *pattrs)
	{
	new_node("meta", pattrs);
	}

void parser::end_meta()
	{
	end_node();
	}

void parser::start_metadata(raw_attr_list_t *pattrs)
	{
	new_node("metadata", pattrs);
	}

void parser::end_metadata()
	{
	end_node();
	}

void parser::start_layout(raw_attr_list_t *pattrs)
	{
	new_node("layout", pattrs);
	}

void parser::end_layout()
	{
	end_node();
	}

void parser::start_customAttributes(raw_attr_list_t *pattrs)
	{
	new_node("customAttributes", pattrs);
	}

void parser::end_customAttributes()
	{
	end_node();
	}

void parser::start_customTest(raw_attr_list_t *pattrs)
	{
	new_node("customTest", pattrs);
	}

void parser::end_customTest()
	{
	end_node();
	}

void parser::start_region(raw_attr_list_t *pattrs)
	{
	new_node("region", pattrs);
	}

void parser::end_region()
	{
	end_node();
	}

void parser::start_root_layout(raw_attr_list_t *pattrs)
	{
	new_node("root-layout", pattrs);
	}

void parser::end_root_layout()
	{
	end_node();
	}

void parser::start_viewport(raw_attr_list_t *pattrs)
	{
	new_node("topLayout", pattrs);
	}

void parser::end_viewport()
	{
	end_node();
	}

void parser::start_body(raw_attr_list_t *pattrs)
	{
	new_node("body", pattrs);
	}

void parser::end_body()
	{
	end_node();
	}

void parser::start_par(raw_attr_list_t *pattrs)
	{
	new_node("par", pattrs);
	}

void parser::end_par()
	{
	end_node();
	}

void parser::start_seq(raw_attr_list_t *pattrs)
	{
	new_node("seq", pattrs);
	}

void parser::end_seq()
	{
	end_node();
	}

void parser::start_switch(raw_attr_list_t *pattrs)
	{
	new_node("switch", pattrs);
	}

void parser::end_switch()
	{
	end_node();
	}

void parser::start_excl(raw_attr_list_t *pattrs)
	{
	new_node("excl", pattrs);
	}

void parser::end_excl()
	{
	end_node();
	}

void parser::start_priorityClass(raw_attr_list_t *pattrs)
	{
	new_node("priorityClass", pattrs);
	}

void parser::end_priorityClass()
	{
	end_node();
	}

void parser::start_ref(raw_attr_list_t *pattrs)
	{
	new_node("ref", pattrs);
	}

void parser::end_ref()
	{
	end_node();
	}

void parser::start_text(raw_attr_list_t *pattrs)
	{
	new_node("text", pattrs);
	}

void parser::end_text()
	{
	end_node();
	}

void parser::start_audio(raw_attr_list_t *pattrs)
	{
	new_node("audio", pattrs);
	}

void parser::end_audio()
	{
	end_node();
	}

void parser::start_img(raw_attr_list_t *pattrs)
	{
	new_node("img", pattrs);
	}

void parser::end_img()
	{
	end_node();
	}

void parser::start_video(raw_attr_list_t *pattrs)
	{
	new_node("video", pattrs);
	}

void parser::end_video()
	{
	end_node();
	}

void parser::start_animation(raw_attr_list_t *pattrs)
	{
	new_node("animation", pattrs);
	}

void parser::end_animation()
	{
	end_node();
	}

void parser::start_textstream(raw_attr_list_t *pattrs)
	{
	new_node("textstream", pattrs);
	}

void parser::end_textstream()
	{
	end_node();
	}

void parser::start_brush(raw_attr_list_t *pattrs)
	{
	new_node("brush", pattrs);
	}

void parser::end_brush()
	{
	end_node();
	}

void parser::start_a(raw_attr_list_t *pattrs)
	{
	new_node("a", pattrs);
	}

void parser::end_a()
	{
	end_node();
	}

void parser::start_anchor(raw_attr_list_t *pattrs)
	{
	new_node("anchor", pattrs);
	}

void parser::end_anchor()
	{
	end_node();
	}

void parser::start_area(raw_attr_list_t *pattrs)
	{
	new_node("area", pattrs);
	}

void parser::end_area()
	{
	end_node();
	}

void parser::start_animate(raw_attr_list_t *pattrs)
	{
	new_node("animate", pattrs);
	}

void parser::end_animate()
	{
	end_node();
	}

void parser::start_set(raw_attr_list_t *pattrs)
	{
	new_node("set", pattrs);
	}

void parser::end_set()
	{
	end_node();
	}

void parser::start_animateMotion(raw_attr_list_t *pattrs)
	{
	new_node("animateMotion", pattrs);
	}

void parser::end_animateMotion()
	{
	end_node();
	}

void parser::start_animateColor(raw_attr_list_t *pattrs)
	{
	new_node("animateColor", pattrs);
	}

void parser::end_animateColor()
	{
	end_node();
	}

void parser::start_transitionFilter(raw_attr_list_t *pattrs)
	{
	new_node("transitionFilter", pattrs);
	}

void parser::end_transitionFilter()
	{
	end_node();
	}

void parser::start_param(raw_attr_list_t *pattrs)
	{
	new_node("param", pattrs);
	}

void parser::end_param()
	{
	end_node();
	}

void parser::start_transition(raw_attr_list_t *pattrs)
	{
	new_node("transition", pattrs);
	}

void parser::end_transition()
	{
	end_node();
	}

void parser::start_regPoint(raw_attr_list_t *pattrs)
	{
	new_node("regPoint", pattrs);
	}

void parser::end_regPoint()
	{
	end_node();
	}

void parser::start_prefetch(raw_attr_list_t *pattrs)
	{
	new_node("prefetch", pattrs);
	}

void parser::end_prefetch()
	{
	end_node();
	}


//
void parser::unknown_starttag(const char *tag, raw_attr_list_t *pattrs)
	{
	std::basic_string<TCHAR> msg(TEXT("unknown start tag "));
	msg += TextPtr(tag);
	showmessage(msg.c_str());
	new_node(tag, pattrs);
	}

void parser::unknown_endtag()
	{
	end_node();
	}

//
void parser::new_node(const char *name, raw_attr_list_t *pattrs)
	{
	if(m_curnode != NULL)
		{
		tree_node *p = new tree_node("smil", pattrs);
		m_curnode->appendChild(p);
		m_curnode = p;
		}
	}

void parser::end_node()
	{
	if(m_curnode == m_rootnode)
		{
		// end of document
		m_curnode = NULL;
		return;
		}
	m_curnode = m_curnode->up();
	}

void parser::show_error(std::string& msg)
	{
	showmessage(TextPtr(msg.c_str()));
	}

} // namespace smil
