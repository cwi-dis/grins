#ifndef INC_COMOBJ
#define INC_COMOBJ

class GRiNSPlayerComModule;

bool RegisterGRiNSPlayerAutoServer();
bool UnregisterGRiNSPlayerAutoServer();
HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule);
HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  lpdwRegister);

void GRiNSPlayerAutoAdviceSetSize(int id, int w, int h);
void GRiNSPlayerAutoAdviceSetCursor(int id, char *cursor);
void GRiNSPlayerAutoAdviceSetDur(int id, double dur);
void GRiNSPlayerAutoAdviceSetPos(int id, double pos);
void GRiNSPlayerAutoAdviceSetSpeed(int id, double speed);
void GRiNSPlayerAutoAdviceSetState(int id, int st);

#endif
