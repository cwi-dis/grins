#ifndef INC_TREE_NODE
#define INC_TREE_NODE

template <class Node>
class TreeIterator 
	{
	public:

	typedef Node* treeiter;

	typedef std::pair<treeiter, bool> value_type;
	
	TreeIterator()
		: currit(0), move(&TreeIterator::down) {}
	
	TreeIterator(treeiter it)
		: currit(it), move(&TreeIterator::down) {}

	TreeIterator(const TreeIterator& other)
		:	currit(other.currit), move(other.move) {}

	const TreeIterator& operator=(const TreeIterator& other){
		if(&other!=this){
			currit = other.currit; 
			move = other.move;
			}
		return *this;
		}

	friend bool operator==(const TreeIterator& lhs, const TreeIterator& rhs)
		{return lhs.currit==rhs.currit;}
	friend bool operator!=(const TreeIterator& lhs, const TreeIterator& rhs)
		{return lhs.currit!=rhs.currit;}

	void operator++() {if(move)(this->*move)();}
	void operator++(int) {if(move)(this->*move)();}

	value_type operator*() {return value_type(currit, (move==&TreeIterator::down));}
	
	operator int() {return move?1:0;}

	private:
	void down() {
		treeiter it = currit->down();
		if(it) currit = it;
		else move = &TreeIterator::next;
		}

	void next() {
		treeiter it = currit->next();
		if(it){
			currit = it;
			move = &TreeIterator::down;
			}
		else {
			move = &TreeIterator::up;
			(this->*move)();
			}
		}

	void up() {
		treeiter it = currit->up();
		if(it) {
			currit = it;
			move = &TreeIterator::next;
			}
		else {
			currit = it;
			move = 0;
			}
		}

	treeiter currit;
	void (TreeIterator::*move)();
	};

class TreeNode
	{
	public:
	typedef const TreeNode iterator_arg;
	typedef TreeIterator<iterator_arg> iterator;
	typedef const TreeIterator<iterator_arg> const_iterator;

	typedef std::pair<std::string, std::string> attribute;

	TreeNode(const char *name=NULL, const char **attrs=NULL)
	:	m_name(name?name:""),
		m_parent(NULL),
		m_child(NULL),												   
		m_next(NULL)
		{
		m_beginit = iterator(this);
		if(attrs) {
			for(int i=0;attrs[i];i+=2)
				m_attrs.push_back(std::pair<std::string, std::string>(attrs[i], attrs[i+1]));
			}
		}
	
	~TreeNode()
		{
		TreeNode *e = m_child;
		if(e)
			{
			TreeNode *tmp = e;
			e = e->m_next;
			delete tmp;
			while(e)
				{
				TreeNode *tmp = e;
				e = e->m_next;
				delete tmp;
				}
			}
		}
	int appendCharData(const char *data, int len)
		{
		if(len) m_data.append(data, len);
		return m_data.size();
		}
	
	// tree builder method
	void appendChild(TreeNode* child);
		
	const char *getName() const {return m_name.c_str();}
	const char *getData() const {return m_data.c_str();}

	int getDataSize() const {return m_data.size();}
	const char *getAttribute(const char *name) const;
	const std::list<attribute>& getAttributes() const {return m_attrs;}
	void getChildren(std::list<const TreeNode*>& l) const;
	void getChildren(std::list<const TreeNode*>& l, const char *name) const;
	const TreeNode *getFirstChild(const char *name) const;
	TreeNode *getFirstChild(const char *name);
	std::string xmlrepr() const;

	iterator begin() {return m_beginit;}
	const_iterator begin() const {return (const_iterator)m_beginit;}

	iterator end() {return m_endit;}
	const_iterator end() const {return (const_iterator)m_endit;}

	const TreeNode *down() const {return m_child;}
	const TreeNode *up() const {return m_parent;}
	const TreeNode *next() const {return m_next;}

	TreeNode *down()  {return m_child;}
	TreeNode *up()  {return m_parent;}
	TreeNode *next()  {return m_next;}

	private:
	const TreeNode *getChild() const {return m_child;}
	const TreeNode *getNext() const {return m_next;}			
	void setChild(TreeNode *e){m_child=e;}
	void setNext(TreeNode *e){m_next=e;}
	
	std::string m_name;
	TreeNode *m_child;												   
	TreeNode *m_next;
	TreeNode *m_parent;

	iterator m_beginit;
	iterator m_endit;

	std::string m_data;
	std::list<attribute> m_attrs;
	};

inline void TreeNode::appendChild(TreeNode* child)
	{
	if(!m_child) 
		m_child = child;
	else
		{
		TreeNode *e = m_child;
		while(e->m_next) e = e->m_next;
		e->m_next = child;
		}
	child->m_parent = this;
	child->m_endit = iterator(this);
	}

inline const char *TreeNode::getAttribute(const char *name) const 
	{
	std::list< std::pair<std::string, std::string> >::const_iterator it = m_attrs.begin();
	while(it!=m_attrs.end()) {
		if((*it).first == name)
			return (*it).second.c_str();
		}
	return "";
	}

inline void TreeNode::getChildren(std::list<const TreeNode*>& l) const
	{
	const TreeNode *e = getChild();
	if(!e) return;
	l.push_back(e);
	while((e=e->getNext())) l.push_back(e);
	}

inline void TreeNode::getChildren(std::list<const TreeNode*>& l, const char *name) const
	{
	const TreeNode *e = getChild();
	if(!e) return;
	if(e->m_name==name)l.push_back(e);
	while((e=e->getNext())) if(e->m_name==name) l.push_back(e);
	}

inline const TreeNode *TreeNode::getFirstChild(const char *name) const
	{
	const TreeNode *e = getChild();
	if(!e) return NULL;
	if(e->m_name==name)return e;
	while((e=e->getNext())) if(e->m_name==name) return e;
	return NULL;
	}

inline TreeNode *TreeNode::getFirstChild(const char *name)
	{
	TreeNode *e = m_child;
	if(!e) return NULL;
	if(e->m_name==name) return e;
	while((e=e->m_next)) if(e->m_name==name) return e;
	return NULL;
	}


inline std::string TreeNode::xmlrepr() const {
	std::string s(m_name);
	std::list< std::pair<std::string, std::string> >::const_iterator it = m_attrs.begin();
	while(it!=m_attrs.end()) {
		s += " ";
		s += (*it).first;
		s += "=\"";
		s += (*it).second;
		s += "\"";
		it++;
		}
	return s;
	}

#endif // INC_TREE_NODE
