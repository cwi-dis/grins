#include "stdafx.h"

// CONST FOR THIS PROJECT

// objects
#include <initguid.h>
#include "stdlib\stdcom.h"
#include "stdlib\Registrar.h"

#include "GRiNSPlayer.h"

void RegisterComObjects()
	{
	REGISTER_COM_OBJECT(GRiNSPlayer);
	}

LONG RegisterServer()
	{
	return Registrar::RegisterServer(
				module.m_hInst,
				CLSID_GRiNSPlayer,
				"GRiNSPlayer Component",
				"GRiNSPlayer",
				"GRiNSPlayer.1",
				false
				);
	}

LONG UnregisterServer()
	{
	return Registrar::UnregisterServer(
				CLSID_GRiNSPlayer,
				"GRiNSPlayer",
				"GRiNSPlayer.1",
				false
				);
	}
