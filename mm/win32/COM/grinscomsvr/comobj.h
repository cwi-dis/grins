#ifndef INC_COMOBJ
#define INC_COMOBJ

class GRiNSPlayerComModule;

bool RegisterGRiNSPlayerAutoServer();
bool UnregisterGRiNSPlayerAutoServer();
HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule);
HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  lpdwRegister);
void GRiNSPlayerAutoAdviceSetSize(int id, int w, int h);
void GRiNSPlayerAutoAdviceSetCursor(int id, char *cursor);
void GRiNSPlayerAutoAdviceNewPeerWindow(int id, int w, int h, int objid);

#endif
