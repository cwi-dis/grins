
/*  Temporary: 
	will be replaced as soon as we build a mac like resource module
*/

static PyObject *PyString_FromMacHandle(Handle data)
{
	PyObject *_res = NULL;
	char state = HGetState(data);
	HLock(data);
	_res = PyString_FromStringAndSize(*data, GetHandleSize(data));
	HUnlock(data);
	HSetState(data, state);
	return _res;
}

static PyObject *MediaObj_GetAudioMediaSampleDescription(MediaObject *_self, PyObject *_args)
{
	PyObject *_res = NULL;
	long index;
	SampleDescriptionHandle descH = (SampleDescriptionHandle)NewHandle(0);
	if (!PyArg_ParseTuple(_args, "l", &index))
		return NULL;
	GetMediaSampleDescription(_self->ob_itself, index, descH);
	SoundDescription* p = (SoundDescription*)(*descH);
	if(p==NULL) {
		PyErr_SetString(PyMac_GetOSErrException(), "GetMediaSampleDescription failed");
		return NULL;
		}
	_res = PyDict_New();
	PyMapping_SetItemString(_res, "descSize", PyInt_FromLong(int(p->descSize)));
	PyMapping_SetItemString(_res, "dataFormat", OSType_FromLong(p->dataFormat));
	PyMapping_SetItemString(_res, "resvd1", PyInt_FromLong(int(p->resvd1)));
	PyMapping_SetItemString(_res, "resvd2", PyInt_FromLong(int(p->resvd2)));
	PyMapping_SetItemString(_res, "dataRefIndex", PyInt_FromLong(int(p->dataRefIndex)));
	PyMapping_SetItemString(_res, "version", PyInt_FromLong(int(p->version)));
	PyMapping_SetItemString(_res, "revlevel", PyInt_FromLong(int(p->revlevel)));
	PyMapping_SetItemString(_res, "vendor", PyInt_FromLong(int(p->vendor)));
	PyMapping_SetItemString(_res, "numChannels", PyInt_FromLong(int(p->numChannels)));
	PyMapping_SetItemString(_res, "sampleSize", PyInt_FromLong(int(p->sampleSize)));
	PyMapping_SetItemString(_res, "compressionID", PyInt_FromLong(int(p->compressionID)));
	PyMapping_SetItemString(_res, "packetSize", PyInt_FromLong(int(p->packetSize)));
	PyMapping_SetItemString(_res, "sampleRate", PyMac_BuildFixed(p->sampleRate));
	DisposeHandle((Handle)descH);
	return _res;
}

static PyObject *MediaObj_GetAudioMediaSample(MediaObject *_self, PyObject *_args)
{
	PyObject *_res, *_tobj = NULL;
	OSErr _err = noErr;
	Handle dataOut = NewHandle(0);
	long maxSizeToGrow = 0;
	long size;
	TimeValue time;
	TimeValue sampleTime;
	TimeValue durationPerSample;
	SampleDescriptionHandle descH = (SampleDescriptionHandle)NewHandle(0);
	long sampleDescriptionIndex;
	long maxNumberOfSamples;
	long numberOfSamples;
	short sampleFlags;
	if (!PyArg_ParseTuple(_args, "ll", &time, &maxNumberOfSamples))
		return NULL;
	_err = GetMediaSample(_self->ob_itself,
	                      dataOut,
	                      maxSizeToGrow,
	                      &size,
	                      time,
	                      &sampleTime,
	                      &durationPerSample,
	                      descH,
	                      &sampleDescriptionIndex,
	                      maxNumberOfSamples,
	                      &numberOfSamples,
	                      &sampleFlags);
	if (_err != noErr) return PyMac_Error(_err);
	_tobj = PyString_FromMacHandle(dataOut);
	_res = Py_BuildValue("lllllhO",
	                     size,
	                     sampleTime,
	                     durationPerSample,
	                     sampleDescriptionIndex,
	                     numberOfSamples,
	                     sampleFlags, _tobj);
	Py_DECREF(_tobj);
	DisposeHandle(dataOut);
	DisposeHandle((Handle)descH);
	return _res;
}

#define APPEND_WIN_MediaObj_methods \
	{"GetAudioMediaSampleDescription", (PyCFunction)MediaObj_GetAudioMediaSampleDescription, 1,\
	"() -> (SoundDescription tuple)"},\
	{"GetAudioMediaSample", (PyCFunction)MediaObj_GetAudioMediaSample, 1,\
	"(TimeValue time, long maxNumberOfSamples) -> (long size, TimeValue sampleTime, TimeValue durationPerSample, long sampleDescriptionIndex, long numberOfSamples, short sampleFlags, string data)"},
