#include "stdafx.h"
#include "stdlib/stdcom.h"

#include "GRiNSPlayer.h"

GRiNSPlayer::GRiNSPlayer()
	{
	REGISTER_COM_INTERFACE(IGRiNSPlayer);
	}

GRiNSPlayer::~GRiNSPlayer()
	{
	}

HRESULT __stdcall GRiNSPlayer::Open(wchar_t *szName)
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayer::Play()
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayer::Stop()
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayer::Pause()
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayer::OnEvent(wchar_t *wszEvent)
	{
	return S_OK;
	}

HRESULT __stdcall GRiNSPlayer::SetAttribute(wchar_t *wszAttr)
	{
	return S_OK;
	}

