#ifdef _WIN32_WCE

#include <windows.h>

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



#endif // _WIN32_WCE