#ifndef _FIVEMLIST_H
#define _FIVEMLIST_H


class FiveMinuteNode
{
public:
    FiveMinuteNode();
    ~FiveMinuteNode();
    void* m_pData;
    FiveMinuteNode* m_pNext;
};

typedef FiveMinuteNode* ListPosition;

    
class FiveMinuteList
{
public:
    FiveMinuteList();
    ~FiveMinuteList();

    void AddHead(void*);
    void Add(void*);
    void* GetFirst();
    void* GetNext();
    void* GetLast();
    void* RemoveHead();
    UINT32 Count();

    ListPosition GetHeadPosition();
    ListPosition GetNextPosition(ListPosition);
    void InsertAfter(ListPosition, void*);
    void* RemoveAfter(ListPosition);
    void* GetAt(ListPosition);

private:
    FiveMinuteNode* m_pLast;
    FiveMinuteNode* m_pHead;
    FiveMinuteNode* m_pTail;
    UINT32 m_ulNumElements;
};

#endif
