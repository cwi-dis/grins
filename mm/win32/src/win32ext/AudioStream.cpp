// AudioStream.cpp

#define VC_EXTRALEAN
#define STRICT

#include <windows.h>
#include <mmsystem.h>

#include "AudioStream.h"

#define ASSERT(a)

// AudioStreamServices class implementation
//
////////////////////////////////////////////////////////////

// Constructor
AudioStreamServices::AudioStreamServices (void)
{
    // Initialize member data
    m_pds = NULL;
    m_hwnd = NULL;

    // It would seem to make sense to initialize DirectSound here,
    // but because there could be an error, it's best done in a
    // separate member function, ::Initialize.
}

// Destructor
AudioStreamServices::~AudioStreamServices (void)
{
    if (m_pds)
    {
        // Release DirectSound object
        m_pds->Release ();
    }
}

// Initialize
BOOL AudioStreamServices::Initialize (HWND hwnd)
{
    BOOL fRtn = SUCCESS;    // assume success

    if (m_pds == NULL)
    {
        if (hwnd)
        {
            m_hwnd = hwnd;

            // Create DirectSound object
            if (DirectSoundCreate (NULL, &m_pds, NULL) == DS_OK)
            {
                // Set cooperative level for DirectSound. Normal means our
                // sounds will be silenced when our window loses input focus.
                if (m_pds->SetCooperativeLevel (m_hwnd, DSSCL_NORMAL) == DS_OK)
                {
                    // Any additional initialization goes here
                }
                else
                {
                    // Error
                    MessageBox(GetFocus(),"Can not set cooperative level","Error",MB_OK);
                    fRtn = FAILURE;
                }
            }
            else
            {
                // Error
                MessageBox(GetFocus(),"Unable to create DirectSound object","Error",MB_OK);
                fRtn = FAILURE;
            }
        }
        else
        {
            // Error, invalid hwnd
            MessageBox(GetFocus(),"Invalid hwnd, unable to initialize services","Error",MB_OK);
            fRtn = FAILURE;
        }
    }

    return (fRtn);
}



//
// AudioStream class implementation
//
////////////////////////////////////////////////////////////

// The following constants are the defaults for our streaming buffer operation.
const UINT DefBufferLength          = 2000; // default buffer length in msec
const UINT DefBufferServiceInterval = 250;  // default buffer service interval in msec

// Constructor
AudioStream::AudioStream (void)
{
    // Initialize data members
    m_pass = NULL;
    m_pwavefile = NULL;
    m_pdsb = NULL;
    m_ptimer = NULL;
    m_fPlaying = m_fCued = FALSE;
    m_lInService = FALSE;
    m_cbBufOffset = 0;
    m_nBufLength = DefBufferLength;
    m_cbBufSize = 0;
    m_nBufService = DefBufferServiceInterval;
    m_nDuration = 0;
    m_nTimeStarted = 0;
    m_nTimeElapsed = 0;
	m_nTimeremain = 0;
	hWND=NULL;
}


// Destructor
AudioStream::~AudioStream (void)
{
    Destroy ();
}

// Create
BOOL AudioStream::Create (LPSTR pszFilename, AudioStreamServices * pass,HWND hwnd)
{
    BOOL fRtn = SUCCESS;    // assume success
    
    //ASSERT (pszFilename);
    //ASSERT (pass);

    // pass points to AudioStreamServices object
    m_pass = pass;

    if (pszFilename && m_pass)
    {
        // Create a new WaveFile object
        if (m_pwavefile = new WaveFile)
        {
            // Open given file
            if (m_pwavefile->Open (pszFilename))
            {
                // Calculate sound buffer size in bytes
                // Buffer size is average data rate times length of buffer
                // No need for buffer to be larger than wave data though
                m_cbBufSize = (m_pwavefile->GetAvgDataRate () * m_nBufLength) / 1000;
                m_cbBufSize = (m_cbBufSize > m_pwavefile->GetDataSize ()) ? m_pwavefile->GetDataSize () : m_cbBufSize;

                // Get duration of sound
                m_nDuration = m_pwavefile->GetDuration ();
				m_nTimeremain = m_nDuration;
                
                // Create sound buffer
                HRESULT hr;
                memset (&m_dsbd, 0, sizeof (DSBUFFERDESC));
                m_dsbd.dwSize = sizeof (DSBUFFERDESC);
                m_dsbd.dwBufferBytes = m_cbBufSize;
                m_dsbd.lpwfxFormat = m_pwavefile->m_pwfmt;
				m_dsbd.dwFlags = DSBCAPS_STICKYFOCUS;
                hr = (m_pass->GetPDS ())->CreateSoundBuffer (&m_dsbd, &m_pdsb, NULL);
                if (hr == DS_OK)
                {
                    hWND=hwnd;
					// Cue for playback
                    Cue ();
                }
                else
                {
                    // Error, unable to create DirectSound buffer
                    MessageBox(GetFocus(),"Error, unable to create DirectSound buffer","Error",MB_OK);
                    if (hr == DSERR_BADFORMAT)
                    {
                            MessageBox(GetFocus(),"Bad format (probably ADPCM)","Error",MB_OK);
                    }
                    
                    fRtn = FAILURE;
                }
            }
            else
            {
                // Error opening file
                MessageBox(GetFocus(),"Failed to open wave file","Error",MB_OK);
                delete (m_pwavefile);
                m_pwavefile = NULL;
                fRtn = FAILURE;
            }   

        }
        else
        {
            // Error, unable to create WaveFile object
            MessageBox(GetFocus(),"Failed to create WaveFile object","Error",MB_OK);
            fRtn = FAILURE;
        }
    }
    else
    {
        // Error, passed invalid parms
        fRtn = FAILURE;
    }

    return (fRtn);
}


// Destroy
BOOL AudioStream::Destroy (void)
{
    BOOL fRtn = SUCCESS;

    // Stop playback
    Stop ();

	// Release DirectSound buffer
    if (m_pdsb)
    {
        m_pdsb->Release ();
        m_pdsb = NULL;
    }

    // Delete WaveFile object
    if (m_pwavefile)
    {
        delete (m_pwavefile);
        m_pwavefile = NULL;
    }
    
    return fRtn;
}

// WriteWaveData
//
// Writes wave data to sound buffer. This is a helper method used by Create and
// ServiceBuffer; it's not exposed to users of the AudioStream class.
BOOL AudioStream::WriteWaveData (UINT size)
{
    HRESULT hr;
    LPBYTE lpbuf1 = NULL;
    LPBYTE lpbuf2 = NULL;
    DWORD dwsize1 = 0;
    DWORD dwsize2 = 0;
    DWORD dwbyteswritten1 = 0;
    DWORD dwbyteswritten2 = 0;
    BOOL fRtn = SUCCESS;

    
//  DWORD dwWriteCursor, dwPlayCursor;
//  m_pdsb->GetCurrentPosition (&dwPlayCursor, &dwWriteCursor);
//  DOUT2 ("    dwPlayCursor = %d, dwWriteCursor = %d\n\r", dwPlayCursor, dwWriteCursor);
    
    // Lock the sound buffer
    hr = m_pdsb->Lock (m_cbBufOffset, size, (void **)&lpbuf1, &dwsize1, (void **)&lpbuf2, &dwsize2, 0);
    if (hr == DS_OK)
    {
        // Write data to sound buffer. Because the sound buffer is circular, we may have to
        // do two write operations if locked portion of buffer wraps around to start of buffer.
        //ASSERT (lpbuf1);
        if ((dwbyteswritten1 = m_pwavefile->Read (lpbuf1, dwsize1)) == dwsize1)
        {
            // Second write required?
            if (lpbuf2)
            {
                if ((dwbyteswritten2 = m_pwavefile->Read (lpbuf2, dwsize2)) == dwsize2)
                {
                    // Both write operations successful!
                }
                else
                {
                    // Error, didn't read wave data completely
                    MessageBox(GetFocus(),"Error, read failure","Error",MB_OK);
                    fRtn = FAILURE;
                }
            }
        }
        else
        {
            // Error, didn't read wave data completely
            MessageBox(GetFocus(),"Error, read failure","Error",MB_OK);
            fRtn = FAILURE;
        }

        // Update our buffer offset and unlock sound buffer
        m_cbBufOffset = (m_cbBufOffset + dwbyteswritten1 + dwbyteswritten2) % m_cbBufSize;
        m_pdsb->Unlock (lpbuf1, dwbyteswritten1, lpbuf2, dwbyteswritten2);
    }
    else
    {
        // Error locking sound buffer
        MessageBox(GetFocus(),"Error, unable to lock sound buffer","Error",MB_OK);
        fRtn = FAILURE;
    }

    return (fRtn);
}


// WriteSilence
//
// Writes silence to sound buffer. This is a helper method used by
// ServiceBuffer; it's not exposed to users of the AudioStream class.
BOOL AudioStream::WriteSilence (UINT size)
{
    HRESULT hr;
    LPBYTE lpbuf1 = NULL;
    LPBYTE lpbuf2 = NULL;
    DWORD dwsize1 = 0;
    DWORD dwsize2 = 0;
    DWORD dwbyteswritten1 = 0;
    DWORD dwbyteswritten2 = 0;
    BOOL fRtn = SUCCESS;

    // Lock the sound buffer
    hr = m_pdsb->Lock (m_cbBufOffset, size, (void **)&lpbuf1, &dwsize1, (void **)&lpbuf2, &dwsize2, 0);
    if (hr == DS_OK)
    {
        // Get silence data for this file format. Although word sizes vary for different
        // wave file formats, ::Lock will always return pointers on word boundaries.
        // Because silence data for 16-bit PCM formats is 0x0000 or 0x00000000, we can
        // get away with writing bytes and ignoring word size here.
        BYTE bSilence = m_pwavefile->GetSilenceData ();
        
        // Write silence to sound buffer. Because the sound buffer is circular, we may have to
        // do two write operations if locked portion of buffer wraps around to start of buffer.
        memset (lpbuf1, bSilence, dwsize1);
        dwbyteswritten1 = dwsize1;
            
        // Second write required?
        if (lpbuf2)
        {
            memset (lpbuf2, bSilence, dwsize2);
            dwbyteswritten2 = dwsize2;
        }
            
        // Update our buffer offset and unlock sound buffer
        m_cbBufOffset = (m_cbBufOffset + dwbyteswritten1 + dwbyteswritten2) % m_cbBufSize;
        m_pdsb->Unlock (lpbuf1, dwbyteswritten1, lpbuf2, dwbyteswritten2);
    }
    else
    {
        // Error locking sound buffer
        MessageBox(GetFocus(),"Error, unable to lock sound buffer","Error",MB_OK);
        fRtn = FAILURE;
    }

    return (fRtn);
}


// GetMaxWriteSize
//
// Helper function to calculate max size of sound buffer write operation, i.e. how much
// free space there is in buffer.
DWORD AudioStream::GetMaxWriteSize (void)
{
    DWORD dwWriteCursor, dwPlayCursor, dwMaxSize;

    // Get current play position
    if (m_pdsb->GetCurrentPosition (&dwPlayCursor, &dwWriteCursor) == DS_OK)
    {
        if (m_cbBufOffset <= dwPlayCursor)
        {
            // Our write position trails play cursor
            dwMaxSize = dwPlayCursor - m_cbBufOffset;
        }

        else // (m_cbBufOffset > dwPlayCursor)
        {
            // Play cursor has wrapped
            dwMaxSize = m_cbBufSize - m_cbBufOffset + dwPlayCursor;
        }

    }
    else
    {
        // GetCurrentPosition call failed
        //ASSERT (0);
        dwMaxSize = 0;
    }

    return (dwMaxSize);
}


// ServiceBuffer
//
// Routine to service buffer requests initiated by periodic timer.
//
// Returns TRUE if buffer serviced normally; otherwise returns FALSE.
BOOL AudioStream::ServiceBuffer (void)
{
    BOOL fRtn = TRUE;
	
	// Check for reentrance
    if (InterlockedExchange (&m_lInService, TRUE) == FALSE)
    {
        // Not reentered, proceed normally
        
        // Maintain elapsed time count
        m_nTimeElapsed = timeGetTime () - m_nTimeStarted;

		m_nTimeStarted += m_nTimeElapsed;
		m_nTimeremain -= m_nTimeElapsed;
//      DOUT1 ("m_nTimeElapsed = %d msec\n\r", m_nTimeElapsed);
		
        // Stop if all of sound has played
        if (m_nTimeElapsed < m_nTimeremain) 
        {
			// All of sound not played yet, send more data to buffer
            DWORD dwFreeSpace = GetMaxWriteSize ();

            // Determine free space in sound buffer
            if (dwFreeSpace)
            {
                // See how much wave data remains to be sent to buffer
                DWORD dwDataRemaining = m_pwavefile->GetNumBytesRemaining ();
                if (dwDataRemaining == 0)
                {
                    // All wave data has been sent to buffer
                    // Fill free space with silence
                    if (WriteSilence (dwFreeSpace) == FAILURE)
                    {
                        // Error writing silence data
                        fRtn = FALSE;
                        //ASSERT (0);
                        MessageBox(GetFocus(),"WriteSilence failed","Error",MB_OK);
                    }
                }
                else if (dwDataRemaining >= dwFreeSpace)
                {
                    // Enough wave data remains to fill free space in buffer
                    // Fill free space in buffer with wave data
                    if (WriteWaveData (dwFreeSpace) == FAILURE)
                    {
                        // Error writing wave data
                        fRtn = FALSE;
                        ASSERT (0);
                        MessageBox(GetFocus(),"WriteWaveData failed","Error",MB_OK);
                    }
                }
                else
                {
                    // Some wave data remains, but not enough to fill free space
                    // Send wave data to buffer, fill remainder of free space with silence
                    if (WriteWaveData (dwDataRemaining) == SUCCESS)
                    {
                        if (WriteSilence (dwFreeSpace - dwDataRemaining) == FAILURE)
                        {
                            // Error writing silence data
                            fRtn = FALSE;
                            ASSERT (0);
                            MessageBox(GetFocus(),"WriteSilence failed","Error",MB_OK);
                        }
                    }
                    else
                    {
                        // Error writing wave data
                        fRtn = FALSE;
                        ASSERT (0);
                        MessageBox(GetFocus(),"WriteWaveData failed","Error",MB_OK);
                    }
                }
            }
            else
            {
                // No free space in buffer for some reason
                DWORD dwDataRemaining = m_pwavefile->GetNumBytesRemaining ();
                if (dwDataRemaining == 0)
				{
					Stop ();
					
					PostMessage(hWND, MM_MCINOTIFY, 1, 1);

					m_nTimeStarted = 0;
					m_nTimeElapsed = 0;
					m_nTimeremain = m_nDuration;
				}
				fRtn = FALSE;
            }
        }
        else
        {
            // All of sound has played, stop playback
            Stop ();

			PostMessage(hWND, MM_MCINOTIFY, 1, 1);

			//delete (m_ptimer);
            //m_ptimer = NULL;

            //m_fPlaying = FALSE;
			
			//m_fCued = FALSE;

			m_nTimeStarted = 0;
			m_nTimeElapsed = 0;
			m_nTimeremain = m_nDuration;
        }

        // Reset reentrancy semaphore
        InterlockedExchange (&m_lInService, FALSE);
    }
    else
    {
        // Service routine reentered. Do nothing, just return
        fRtn = FALSE;
    }
    return (fRtn);
}


// Cue
void AudioStream::Cue (void)
{
    if (!m_fCued)
    {
        // Reset buffer ptr
        m_cbBufOffset = 0;

        // Reset file ptr, etc
        m_pwavefile->Cue ();

        // Reset DirectSound buffer
        m_pdsb->SetCurrentPosition (0);

        // Fill buffer with wave data
        WriteWaveData (m_cbBufSize);
        
        m_fCued = TRUE;
    }
}


// Play
void AudioStream::Play (void)
{
    if (m_pdsb)
    {
        // If playing, stop
        //if (m_fPlaying)
        //{
            //Stop ();
        //} 

        // Cue for playback if necessary
        if (!m_fCued)
        {
            Cue ();
        }

        // Begin DirectSound playback
        m_nTimeStarted = timeGetTime ();
		HRESULT hr = m_pdsb->Play (0, 0, DSBPLAY_LOOPING);
        
		if (hr == DS_OK)
        {
            
            // Kick off timer to service buffer
            m_ptimer = new Timer ();
            if (m_ptimer)
            {
                m_ptimer->Create (m_nBufService, m_nBufService, DWORD (this), TimerCallback);
            }
            else
            {
            }

            // Playback begun, no longer cued
            m_fPlaying = TRUE;
            //m_fCued = FALSE;
        }
        else
        {
            m_nTimeStarted = 0;
			MessageBox(GetFocus(),"Error, play failed","Error",MB_OK);
        }
    }
}

// Timer callback for Timer object created by ::Play method.
BOOL AudioStream::TimerCallback (DWORD dwUser)
{
    // dwUser contains ptr to AudioStream object
    AudioStream * pas = (AudioStream *) dwUser;

    return (pas->ServiceBuffer ());
}

// Stop
void AudioStream::Stop (void)
{
    if (m_fPlaying)
    {
        m_nTimeElapsed = timeGetTime () - m_nTimeStarted;

		m_nTimeStarted += m_nTimeElapsed;
		m_nTimeremain -= m_nTimeElapsed;
		
		// Stop DirectSound playback
        m_pdsb->Stop ();

        // Delete Timer object
        delete (m_ptimer);
        m_ptimer = NULL;

        m_fPlaying = FALSE;
    }
}

