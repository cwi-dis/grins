

static PyObject *MediaObj_GetAudioMediaSampleDescription(MediaObject *_self, PyObject *_args)
{
	long index;
	SoundDescription sd;
	memset(&sd, 0, sizeof(SoundDescription));
	sd.descSize = sizeof(SoundDescription);
	SampleDescriptionPtr p1 = (SampleDescriptionPtr)&sd;
	SampleDescriptionHandle descH = (SampleDescriptionHandle)&p1;
	if (!PyArg_ParseTuple(_args, "l", &index))
		return NULL;
	GetMediaSampleDescription(_self->ob_itself, index, descH);
	SoundDescription* p = (SoundDescription*)(*descH);
	if(p==NULL)
		return NULL;
	return Py_BuildValue("iiiiiiiiiiiii", 
		p->descSize,				   /* total size of SoundDescription including extra data */
		p->dataFormat,                 /* sound format */
 		p->resvd1,                     /* reserved for apple use. set to zero */
		p->resvd2,                     /* reserved for apple use. set to zero */
		p->dataRefIndex,
 		p->version,                    /* which version is this data */
 		p->revlevel,                   /* what version of that codec did this */
		p->vendor,                     /* whose  codec compressed this data */
 		p->numChannels,                /* number of channels of sound */
 		p->sampleSize,                 /* number of bits per sample */
 		p->compressionID,              /* unused. set to zero. */
		p->packetSize,                 /* unused. set to zero. */
		p->sampleRate);                /* sample rate sound is captured at */

}


#define APPEND_WIN_MediaObj_methods \
	{"GetAudioMediaSampleDescription", (PyCFunction)MediaObj_GetAudioMediaSampleDescription, 1,\
	"() -> (SoundDescription tuple)"},
