#ifndef INC_DCT
#define INC_DCT

int mpeg2audio_dct64(float *a, float *b, float *c);
int mpeg2audio_dct36(float *inbuf, float *o1, float *o2, float *wintab, float *tsbuf);
int mpeg2audio_dct12(float *in,float *rawout1,float *rawout2,register float *wi,register float *ts);

struct mpeg2audio_t;
int mpeg2audio_imdct_init(mpeg2audio_t *audio);

#endif // INC_DCT