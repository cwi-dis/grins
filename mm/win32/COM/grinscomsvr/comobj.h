#ifndef INC_COMOBJ
#define INC_COMOBJ

class GRiNSPlayerComModule;

bool RegisterGRiNSPlayerAutoServer();
bool UnregisterGRiNSPlayerAutoServer();
HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, GRiNSPlayerComModule *pModule);
HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  lpdwRegister);
void GRiNSPlayerAutoAdviceSetSize(int id, int w, int h);

#endif
