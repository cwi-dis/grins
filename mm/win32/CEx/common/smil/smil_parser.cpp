
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_parser.h"

#include "tree_node.h"

#include "charconv.h"

#include "windowinterface.h"

#include "smil_node.h"
#include "smil_attr_read.h"

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

	m_rootnode = new tree_node("#document");
	m_curnode = m_rootnode;
	}

parser::~parser()
	{
	if(m_rootnode != 0) 
		delete m_rootnode;
	}

// prepare for reuse
void parser::reset()
	{
	if(m_rootnode != 0)
		delete m_rootnode;
	m_rootnode = new tree_node("#document");
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

void parser::start_smil(handler_arg_type attrs)
	{
	new_node("smil", attrs);
	}

void parser::end_smil()
	{
	end_node();
	}

void parser::start_head(handler_arg_type attrs)
	{
	new_node("head", attrs);
	}

void parser::end_head()
	{
	end_node();
	}

void parser::start_meta(handler_arg_type attrs)
	{
	new_node("meta", attrs);
	}

void parser::end_meta()
	{
	end_node();
	}

void parser::start_metadata(handler_arg_type attrs)
	{
	new_node("metadata", attrs);
	}

void parser::end_metadata()
	{
	end_node();
	}

void parser::start_layout(handler_arg_type attrs)
	{
	new_node("layout", attrs);
	}

void parser::end_layout()
	{
	end_node();
	}

void parser::start_customAttributes(handler_arg_type attrs)
	{
	new_node("customAttributes", attrs);
	}

void parser::end_customAttributes()
	{
	end_node();
	}

void parser::start_customTest(handler_arg_type attrs)
	{
	new_node("customTest", attrs);
	}

void parser::end_customTest()
	{
	end_node();
	}

void parser::start_region(handler_arg_type attrs)
	{
	new_node("region", attrs);
	}

void parser::end_region()
	{
	end_node();
	}

void parser::start_root_layout(handler_arg_type attrs)
	{
	new_node("root-layout", attrs);
	}

void parser::end_root_layout()
	{
	end_node();
	}

void parser::start_viewport(handler_arg_type attrs)
	{
	new_node("topLayout", attrs);
	}

void parser::end_viewport()
	{
	end_node();
	}

void parser::start_body(handler_arg_type attrs)
	{
	new_node("body", attrs);
	}

void parser::end_body()
	{
	end_node();
	}

void parser::start_par(handler_arg_type attrs)
	{
	new_node("par", attrs);
	}

void parser::end_par()
	{
	end_node();
	}

void parser::start_seq(handler_arg_type attrs)
	{
	new_node("seq", attrs);
	}

void parser::end_seq()
	{
	end_node();
	}

void parser::start_switch(handler_arg_type attrs)
	{
	new_node("switch", attrs);
	}

void parser::end_switch()
	{
	end_node();
	}

void parser::start_excl(handler_arg_type attrs)
	{
	new_node("excl", attrs);
	}

void parser::end_excl()
	{
	end_node();
	}

void parser::start_priorityClass(handler_arg_type attrs)
	{
	new_node("priorityClass", attrs);
	}

void parser::end_priorityClass()
	{
	end_node();
	}

void parser::start_ref(handler_arg_type attrs)
	{
	new_media_node("ref", attrs);
	}

void parser::end_ref()
	{
	end_media_node();
	}

void parser::start_text(handler_arg_type attrs)
	{
	new_media_node("text", attrs);
	}

void parser::end_text()
	{
	end_media_node();
	}

void parser::start_audio(handler_arg_type attrs)
	{
	new_media_node("audio", attrs);
	}

void parser::end_audio()
	{
	end_media_node();
	}

void parser::start_img(handler_arg_type attrs)
	{
	new_media_node("img", attrs);
	}

void parser::end_img()
	{
	end_media_node();
	}

void parser::start_video(handler_arg_type attrs)
	{
	new_media_node("video", attrs);
	}

void parser::end_video()
	{
	end_media_node();
	}

void parser::start_animation(handler_arg_type attrs)
	{
	new_media_node("animation", attrs);
	}

void parser::end_animation()
	{
	end_media_node();
	}

void parser::start_textstream(handler_arg_type attrs)
	{
	new_media_node("textstream", attrs);
	}

void parser::end_textstream()
	{
	end_media_node();
	}

void parser::start_brush(handler_arg_type attrs)
	{
	new_media_node("brush", attrs);
	}

void parser::end_brush()
	{
	end_media_node();
	}

void parser::start_a(handler_arg_type attrs)
	{
	new_node("a", attrs);
	}

void parser::end_a()
	{
	end_node();
	}

void parser::start_anchor(handler_arg_type attrs)
	{
	new_node("anchor", attrs);
	}

void parser::end_anchor()
	{
	end_node();
	}

void parser::start_area(handler_arg_type attrs)
	{
	new_node("area", attrs);
	}

void parser::end_area()
	{
	end_node();
	}

void parser::start_animate(handler_arg_type attrs)
	{
	new_node("animate", attrs);
	}

void parser::end_animate()
	{
	end_node();
	}

void parser::start_set(handler_arg_type attrs)
	{
	new_node("set", attrs);
	}

void parser::end_set()
	{
	end_node();
	}

void parser::start_animateMotion(handler_arg_type attrs)
	{
	new_node("animateMotion", attrs);
	}

void parser::end_animateMotion()
	{
	end_node();
	}

void parser::start_animateColor(handler_arg_type attrs)
	{
	new_node("animateColor", attrs);
	}

void parser::end_animateColor()
	{
	end_node();
	}

void parser::start_transitionFilter(handler_arg_type attrs)
	{
	new_node("transitionFilter", attrs);
	}

void parser::end_transitionFilter()
	{
	end_node();
	}

void parser::start_param(handler_arg_type attrs)
	{
	new_node("param", attrs);
	}

void parser::end_param()
	{
	end_node();
	}

void parser::start_transition(handler_arg_type attrs)
	{
	new_node("transition", attrs);
	}

void parser::end_transition()
	{
	end_node();
	}

void parser::start_regPoint(handler_arg_type attrs)
	{
	new_node("regPoint", attrs);
	}

void parser::end_regPoint()
	{
	end_node();
	}

void parser::start_prefetch(handler_arg_type attrs)
	{
	new_node("prefetch", attrs);
	}

void parser::end_prefetch()
	{
	end_node();
	}


//
void parser::unknown_starttag(const std::string& tag, handler_arg_type attrs)
	{
	std::string msg("unknown start tag ");
	msg += tag;
	windowinterface::showmessage(TextPtr(msg.c_str()));

	new_node(tag, attrs);
	}

void parser::unknown_endtag()
	{
	end_node();
	}

//
void parser::new_node(const std::string& tag, handler_arg_type attrs)
	{
	assert(m_curnode != NULL);
	tree_node *p = new tree_node(tag, attrs);
	m_curnode->appendChild(p);
	m_curnode = p;
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

void  parser::new_media_node(const std::string& tag, handler_arg_type attrs)
	{
	assert(m_curnode != NULL);
	
	node *p = new node(tag, attrs);

	// begin, dur, end, max, min, repeatCount, repeatDur
	const char *raw_val = p->get_raw_attribute("dur");
	if(raw_val != 0)
		{
		any *pv = read_clock_value(raw_val);
		if(pv == 0) 
			windowinterface::showmessage(TEXT("invalid dur attribute"));
		else
			p->set_parsed_attr("dur", pv);
		}

	m_curnode->appendChild(p);
	m_curnode = p;
	}

void  parser::end_media_node()
	{
	if(m_curnode == m_rootnode)
		{
		// end of document
		m_curnode = NULL;
		return;
		}
	m_curnode = m_curnode->up();
	}

void parser::show_error(const std::string& msg)
	{
	windowinterface::showmessage(TextPtr(msg.c_str()));
	}

} // namespace smil
