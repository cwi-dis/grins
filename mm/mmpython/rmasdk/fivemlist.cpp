#include "pncom.h"
#include "pntypes.h"
#include "fivemlist.h"

FiveMinuteNode::FiveMinuteNode()
: m_pData(0)
, m_pNext(0)
{
}

FiveMinuteNode::~FiveMinuteNode()
{
}

FiveMinuteList::FiveMinuteList()
: m_pHead(0)
, m_pLast(0)
, m_pTail(0)
, m_ulNumElements(0)
{
}

FiveMinuteList::~FiveMinuteList()
{
}


UINT32
FiveMinuteList::Count()
{
    return m_ulNumElements;
}

void
FiveMinuteList::AddHead(void* p)
{
    FiveMinuteNode* pNode = new FiveMinuteNode;
    pNode->m_pData = p;
    pNode->m_pNext = m_pHead;
    m_pHead = pNode;
    if (!pNode->m_pNext)
    {
	m_pTail = pNode;
    }
    m_ulNumElements++;
}

void
FiveMinuteList::Add(void* p)
{
    FiveMinuteNode* pNode = new FiveMinuteNode;
    pNode->m_pData = p;
    pNode->m_pNext = NULL;

    if (m_pTail)
    {
	m_pTail->m_pNext = pNode;
	m_pTail = pNode;
    }
    else
    {
	m_pHead = pNode;
	m_pTail = pNode;
    }
    m_ulNumElements++;
}


void*
FiveMinuteList::GetFirst()
{
    if (!m_pHead)
	return 0;

    m_pLast = m_pHead;
    return m_pHead->m_pData;
}

void*
FiveMinuteList::GetNext()
{
    if (!m_pLast)
	return 0;

    if (!m_pLast->m_pNext)
    {
	m_pLast = 0;
	return 0;
    }

    m_pLast = m_pLast->m_pNext;
    return m_pLast->m_pData;
}

void*
FiveMinuteList::RemoveHead()
{
    m_pLast = 0;
    if (!m_pHead)
	return 0;

    void* pRet = m_pHead->m_pData;
    FiveMinuteNode* pDel = m_pHead;
    m_pHead = m_pHead->m_pNext;
    delete pDel;
    m_ulNumElements--;
    if (!m_pHead)
    {
	m_pTail = 0;
    }

    return pRet;
}

void*
FiveMinuteList::GetLast()
{
    if (!m_pTail)
	return 0;

    return m_pTail->m_pData;
}

ListPosition
FiveMinuteList::GetHeadPosition()
{
    return m_pHead;
}

ListPosition
FiveMinuteList::GetNextPosition(ListPosition lp)
{
    if (!lp)
	return 0;

    return lp->m_pNext;
}

void
FiveMinuteList::InsertAfter(ListPosition lp, void* p)
{
    if (!lp)
	return;

    FiveMinuteNode* pNode = new FiveMinuteNode;
    pNode->m_pData = p;
    pNode->m_pNext = lp->m_pNext;
    lp->m_pNext = pNode;
    if (lp == m_pTail)
    {
	m_pTail = pNode;
    }
    m_ulNumElements++;
}

void*
FiveMinuteList::RemoveAfter(ListPosition lp)
{
    if (!lp)
	return 0;

    FiveMinuteNode* pDel;
    pDel = lp->m_pNext;
    if (!pDel)
    {
	return 0;
    }

    void* pRet = pDel->m_pData;
    lp->m_pNext = pDel->m_pNext;
    if (m_pTail == pDel)
    {
	m_pTail = lp;
    }
    delete pDel;
    m_ulNumElements--;
    return pRet;
}

void*
FiveMinuteList::GetAt(ListPosition lp)
{
    if (!lp)
	return 0;

    return lp->m_pData;
}
