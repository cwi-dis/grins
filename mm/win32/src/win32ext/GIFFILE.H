////////////////////////////////////////////////////////////////////////////////
//
//	GIFFile - A C++ class to allow reading and writing of GIF Images
//
//	It is based on code from Programming for Graphics Files	by John Levine
//
//	This is free to use and modify provided proper credit is given
//
//	This reads GIF 87a and 89a, writes only 87a.
//	This writes only 8-bit GIF files. 256 colors.
//	You provide the palette and the palettized image. 
//	This does not do quantization.
//
//
// use :
//
//	Reading:
//
//	GIFFile theGifObject;
//
//	BYTE * buf;
//	buf=theGifObject.GIFReadFileToRGB(path,&width,&height);
//
//	if (buf!=NULL) {
//		// you now have a buffer of width * height RGB pixels
//		// do whatever you like with it
//	}	else {
//		// error text
//		AfxMessageBox(theGifObject.m_GIFErrorText);
//	}
//
//	//delete the buffer when you're done
//	delete [] buf;
//
///////
//
//	Writing :
//
//	GIFFile theGifThing;
//	
//	if (!theGifThing.GIFWriteFileFrom256Color(buffer,	// BYTE * of the 256-color buffer
//							filename,					// name to save as
//							m_width,					// pixels
//							m_height,					// rows
//							0,							// background color
//							red, green, blue)) {		// arrays of 256 ints each that represent the
//														// 256-color palette for this image.
//		//Error!
//		AfxMessageBox(theGifThing.m_GIFErrorText);
//	} else {
//		// success!
//	}
//
////////////////////////////////////////////////////////////////////////////////

#ifndef GIFHDRH
#define GIFHDRH

#define MAXCOLORMAPSIZE	256
#define CM_RED	0
#define CM_GREEN 1
#define CM_BLUE 2
#define UCHAR unsigned char
#define MAX_LZW_BITS	12

#define INTERLACE	0x40
#define LOCALCOLORMAP 0x80
#define BitSet(byte,bit) (((byte) & (bit))==(bit))
#define ReadOK(file,buffer,len) (fread(buffer,len,1,file)!=0)
#define LM_to_uint(a,b)	(((b)<<8)|(a))

typedef short int		code_int;	/* was int */
typedef long int		count_int;
typedef unsigned char pixval;

struct GifInfo 
	{
	unsigned int Width;
	unsigned int Height;
	unsigned char ColorMap[3][MAXCOLORMAPSIZE];
	unsigned int BitPixel;
	unsigned int ColorResolution;
	unsigned int BackGround;
	unsigned int AspectRatio;
	};

struct GifExt
	{
	int transparent;
	int delayTime;
	int inputFlag;
	int disposal;
	};
struct GifTransColor 
	{
	unsigned char c[3];
	};


static void ReadGIF (FILE*fd);
static int ReadColorMap (FILE *fd, int number, UCHAR buffer[3][MAXCOLORMAPSIZE]);
static int DoExtension (FILE *fd,int label);
static int GetDataBlock (FILE *fd, UCHAR *buf);
static int GetCode (FILE *fd, int code_size, int flag);
static int LZWReadByte (FILE *fd,int flag, int  input_code_size);

static BOOL ReadImage(	FILE *fd,
						BYTE  * bigMemBuf,
						int width, int height,
						UCHAR cmap[3][MAXCOLORMAPSIZE],
						int interlace);

#endif // GIFHDRH
//////////
//
//

class GIFFile 
{
public:
	GIFFile();
	~GIFFile();

public:
	CString m_GIFErrorText;

public:

	// write a file
	BOOL GIFWriteFileFrom256Color(BYTE  * buf,
							CString name,
							int GWidth, 
							int GHeight,
							int BackGround,
							int Red[], int Green[], int Blue[]);

	// read to RGB
	BYTE * GIFReadFileToRGB(CString path, 
							UINT *width, 
							UINT *height);

	// find size of file
	void GIFGetDimensions(CString path, 
							UINT *width, 
							UINT *height);
	int GIFGetTransparent();

private:

	void BumpPixel (  );
	int GIFNextPixel ( );
	void Putword ( int w, FILE* fp );
	void compress ( int init_bits, FILE* outfile);
	void output ( code_int code );
	void cl_block (  );
	void cl_hash ( count_int hsize );
	void writeerr (  );
	void char_init (  );
	void char_out ( int c );
	void flush_char (  );

};

