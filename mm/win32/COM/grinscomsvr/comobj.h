#ifndef INC_COMOBJ
#define INC_COMOBJ

class ComModule;

bool RegisterGRiNSPlayerAutoServer();
bool UnregisterGRiNSPlayerAutoServer();
HRESULT GetGRiNSPlayerAutoClassObject(IClassFactory** ppv, ComModule *pModule);
HRESULT CoRegisterGRiNSPlayerAutoClassObject(IClassFactory* pIFactory, LPDWORD  lpdwRegister);

#endif
