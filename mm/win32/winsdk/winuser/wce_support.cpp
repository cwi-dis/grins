#ifdef _WIN32_WCE

#include <windows.h>

HMENU wce_GetSubMenu(HMENU hMenu, UINT uId, UINT uFlags)
{
  MENUITEMINFO mii;
  
  memset((char *)&mii, 0, sizeof(MENUITEMINFO));
  mii.cbSize = sizeof(MENUITEMINFO);
  mii.fMask  = MIIM_SUBMENU;
  
  if (uFlags & MF_BYPOSITION)
    GetMenuItemInfo(hMenu, uId, TRUE, &mii);
  else
    GetMenuItemInfo(hMenu, uId, FALSE, &mii);
  
  return mii.hSubMenu;
}


UINT wce_GetMenuState(HMENU hMenu, UINT uId, UINT uFlags)
{
  MENUITEMINFO mii;
  
  memset((char *)&mii, 0, sizeof(MENUITEMINFO));
  mii.cbSize = sizeof(MENUITEMINFO);
  mii.fMask  = MIIM_STATE;
  
  if (uFlags & MF_BYPOSITION)
    GetMenuItemInfo(hMenu, uId, TRUE, &mii);
  else
    GetMenuItemInfo(hMenu, uId, FALSE, &mii);
  
  return mii.fState;
}

int wce_GetMenuItemCount(HMENU hMenu)
{
  const int MAX_NUM_ITEMS = 256;
  int  iPos, iCount;
  
  MENUITEMINFO mii;
  memset((char *)&mii, 0, sizeof(MENUITEMINFO));
  mii.cbSize = sizeof(MENUITEMINFO);
  
  iCount = 0;
  for (iPos = 0; iPos < MAX_NUM_ITEMS; iPos++)
  {
    if(!GetMenuItemInfo(hMenu, (UINT)iPos, TRUE, &mii))
      break;
    iCount++;
  }
  
  return iCount;
}

UINT wce_GetMenuItemID(HMENU hMenu, int nPos)
{	
  MENUITEMINFO mii;
  memset((char *)&mii, 0, sizeof(mii));
  mii.cbSize = sizeof(mii); 
  mii.fMask  = MIIM_ID; 
  GetMenuItemInfo(hMenu, nPos, TRUE, &mii);
  
  return mii.wID; 
}


BOOL wce_ModifyMenu(HMENU   hMenu,      // handle of menu 
                    UINT    uPosition,  // menu item to modify 
                    UINT    uFlags,     // menu item flags 
                    UINT    uIDNewItem, // menu item identifier or handle of drop-down menu or submenu 
                    LPCTSTR lpNewItem) // menu item content 
{
  // Handle MF_BYCOMMAND case
  if ((uFlags & MF_BYPOSITION) != MF_BYPOSITION)
  {	
    int nMax = wce_GetMenuItemCount(hMenu);
    int nCount = 0;
    while (uPosition != wce_GetMenuItemID(hMenu, nCount) && (nCount < nMax))
      nCount++;
    uPosition = nCount;
    uFlags |= MF_BYPOSITION;
  }
  
  if (!DeleteMenu(hMenu, uPosition, uFlags))
    return FALSE;
  
  return InsertMenu(hMenu, uPosition, uFlags, uIDNewItem, lpNewItem);
}


#endif // _WIN32_WCE