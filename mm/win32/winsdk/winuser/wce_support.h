#ifdef _WIN32_WCE

HMENU wce_GetSubMenu(HMENU hMenu, UINT uId, UINT uFlags);
UINT wce_GetMenuState(HMENU hMenu, UINT uId, UINT uFlags);
int wce_GetMenuItemCount(HMENU hMenu);
UINT wce_GetMenuItemID(HMENU hMenu, int nPos);
BOOL wce_ModifyMenu(HMENU   hMenu,      // handle of menu 
                    UINT    uPosition,  // menu item to modify 
                    UINT    uFlags,     // menu item flags 
                    UINT    uIDNewItem, // menu item identifier or handle of drop-down menu or submenu 
                    LPCTSTR lpNewItem); // menu item content 


#endif // _WIN32_WCE