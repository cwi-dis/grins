#ifndef INC_COMOBJ
#define INC_COMOBJ

class GRiNSPlayerComModule;

bool RegisterGRiNSPlayerAutoServer();
bool UnregisterGRiNSPlayerAutoServer();
HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule);
HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  lpdwRegister);

HRESULT GetGRiNSPlayerMonikerClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule);
HRESULT CoRegisterGRiNSPlayerMonikerClassObject(IClassFactory* pIFactory, LPDWORD  pdwRegister);

void GRiNSPlayerAutoAdviceNewPeerWnd(int docid, int wndid, int w, int h, const char *title);
void GRiNSPlayerAutoAdviceClosePeerWnd(int docid, int wndid);
void GRiNSPlayerAutoAdviceSetCursor(int id, char *cursor);
void GRiNSPlayerAutoAdviceSetDur(int id, double dur);
void GRiNSPlayerAutoAdviceSetPos(int id, double pos);
void GRiNSPlayerAutoAdviceSetSpeed(int id, double speed);
void GRiNSPlayerAutoAdviceSetState(int id, int st);
void GRiNSPlayerAutoAdviceSetFrameRate(int docid, int fr);

#endif
