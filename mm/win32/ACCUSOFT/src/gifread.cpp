////////////////////////////////////////////////////////////
//	GIFFile - A C++ class to allow reading and writing of GIF Images
//
//	It is based on code from Programming for Graphics Files
//	by John Levine
//
//	This is free to use and modify provided proper credit is given
//
//	This reads GIF 87a and 89a.
//
//	See GIFFile.h for example
//
////////////////////////////////////////////////////////////
#include <windows.h>
#include <io.h>

#include <fcntl.h>
#include <string.h>
#include <stdio.h>
#include <conio.h>
#include <stdlib.h>
#include "giffile.h"


GifInfo GifScreen;
GifExt Gif89={-1,-1,-1,0};
GifTransColor GifTans={0,0,0};

GIFFile::GIFFile()
{
	m_GIFErrorText="No Error"; // yet
}

GIFFile::~GIFFile()
{
	// nothing
}

////////////////////////////////////////////////////////////////////////////////
//
//	char * GIFFile::GIFReadInputFile(CString path, 
//								  UINT *width, 
//								  UINT *height)
//
//	Give a path.
//	It will read the .GIF at that path, allocate a buffer and give you
//	an RGB buffer back. width and height are modified to reflect the image dim's.
//
//	m_GIFErrorText is modifed to reflect error status
//
//

BYTE * GIFFile::GIFReadFileToRGB(String path, 
								  UINT *width, 
								  UINT *height)
{
	UCHAR			buf[16]="";
	UCHAR			c;
	UCHAR			localColorMap[3][MAXCOLORMAPSIZE];
	int				useGlobalColormap;
	int				bitPixel;
	int				imageCount	=0;
	char			version[4]="xxx";
	FILE 			*fd;          
	int 			w=0;
	int				h=0;	
	int				nread;

	if (path.IsEmpty()) {
		m_GIFErrorText="No Name Given";
		return NULL;
	}

	memset(buf,0,16);
	BYTE *bigBuf;

	fd=fopen(path,"rb");
	if (fd==NULL) {                       
		m_GIFErrorText="Cant open GIF :\n" + path;
		return NULL;
	}

	// read GIF file header
	nread = fread(buf,1,6,fd);
	if (nread<6) {
		m_GIFErrorText="Error reading GIF Magic #\n"+path;
		fclose(fd);
		return NULL;
	}
	
	// need the string "GIF" in the header
	if(buf[0]!='G' || buf[1]!='I' || buf[2]!='F') {
		m_GIFErrorText="Error. Not a valid GIF file";
		fclose(fd);
		return NULL;
	}	

	strncpy(version,(char *)(buf+3),3);
	version[3]='\0';

	// only handle v 87a and 89a
	if ((strcmp(version,"87a")!=0)&&(strcmp(version,"89a")!=0)) {
		m_GIFErrorText="Error, Bad GIF Version number";
		fclose(fd);
		return NULL;
	}	

	// screen description
	nread = fread(buf,1,7,fd);
	if (nread<7) {
		m_GIFErrorText="Error, failed to GIF read screen descriptor.\nGiving up";
		fclose(fd);
		return NULL;
	}

	GifScreen.Width		=	LM_to_uint((UCHAR)buf[0],(UCHAR)buf[1]);
	GifScreen.Height	=	LM_to_uint((UCHAR)buf[2],(UCHAR)buf[3]);
	GifScreen.BitPixel	=	2 << ((UCHAR)buf[4] & 0x07);
	GifScreen.ColorResolution = ((((UCHAR)buf[4] & 0x70) >> 3) + 1);
	GifScreen.BackGround=	(UCHAR)buf[5];									// background color...
	GifScreen.AspectRatio=	(UCHAR)buf[6];
     
	// read colormaps
	if (BitSet((UCHAR)buf[4],LOCALCOLORMAP)) {
		if (!ReadColorMap(fd,GifScreen.BitPixel,GifScreen.ColorMap)) {
			m_GIFErrorText="Error reading GIF colormap";
			fclose(fd);
			return NULL;                                             
		}
	}
	

	// non-square pixels, so what?	
	if ((GifScreen.AspectRatio!=0 ) && (GifScreen.AspectRatio!=49)) {
		m_GIFErrorText="Non-square pixels in GIF image.\nIgnoring that fact...";
	}

	// there can be multiple images in a GIF file... uh?
	// what the hell do we do with multiple images?
	// so, we'll be interested in just the first image, cause we're lazy

	for(;;) {	
		// read a byte;
		if (!ReadOK(fd,&c,1)) {
			m_GIFErrorText="Unexpected EOF in GIF.\nGiving up";
			fclose(fd);
			return NULL; 
		}
	
		// image terminator
		if (c==';') {
		}
	
		if (c=='!') {
			if (!ReadOK(fd,&c,1)) {
				m_GIFErrorText="Error on extension read.\nGiving up";
				fclose(fd);
				return NULL;       
			}
			DoExtension(fd,c);
			continue;
		}
	
		if (c!=',') {
			// Ignoring c
			continue;
		}
	
		// read image header
		if (!ReadOK(fd,buf,9)) {
			m_GIFErrorText="Error on dimension read\nGiving up";
			fclose(fd);
			return NULL;                     
		}
	
		useGlobalColormap=!BitSet((UCHAR)buf[8],LOCALCOLORMAP);
	
		bitPixel=1<<(((UCHAR)buf[8]&0x07)+1);
	
	    // let's see if we have enough mem to continue?

		long bufsize;


		w = LM_to_uint((UCHAR)buf[4],(UCHAR)buf[5]);		
		h = LM_to_uint((UCHAR)buf[6],(UCHAR)buf[7]);
		
		
		if ((w<0) || (h<0)) {
			m_GIFErrorText="Negative image dimensions!\nGiving up";
			fclose(fd);
			return NULL;
		}
				
		if(w*h > 1000000)
			{
			m_GIFErrorText="Too big!\nGiving up";
			fclose(fd);
			return NULL;
			}

		bufsize=(long)w*(long)h;
		bufsize*=3;
		bigBuf= (BYTE *) new char [bufsize];
		
		if (bigBuf==NULL) {
			m_GIFErrorText="Out of Memory in GIFRead";
			fclose(fd);
			return NULL;
		}
			
	
		if (!useGlobalColormap) {
			if (!ReadColorMap(fd,bitPixel,localColorMap)) {
				m_GIFErrorText="Error reading GIF colormap\nGiving up";
				delete [] bigBuf;
				fclose(fd);
				return NULL;                     
			}
	
		 	//read image
			if (!ReadImage(fd, bigBuf, w, h, localColorMap, BitSet((UCHAR)buf[8],INTERLACE))) {
				m_GIFErrorText="Error reading GIF file\nLocalColorMap\nGiving up";
				delete [] bigBuf;
				fclose(fd);
				return NULL; 				
			}
		} else {
			if (!ReadImage(fd, bigBuf, w, h, GifScreen.ColorMap, BitSet((UCHAR)buf[8],INTERLACE))) {
				m_GIFErrorText="Error reading GIF file\nGIFScreen Colormap\nGiving up";
				delete [] bigBuf;
				fclose(fd);
				return NULL; 			
			}
		}
		break;
	}

	*width=w;
	*height=h;
	if(Gif89.transparent>=0)
		{
		if (!useGlobalColormap)
			for(int i=0;i<3;i++)GifTans.c[i]=localColorMap[i][Gif89.transparent];
		else
			for(int i=0;i<3;i++)GifTans.c[i]=GifScreen.ColorMap[i][Gif89.transparent];
		}
	fclose(fd);
	return bigBuf;
}

int GIFFile::GIFGetTransparent()
	{
	return GifScreen.BackGround;
	}

static int ReadColorMap(FILE *fd,
			int number,
			UCHAR buffer[3][MAXCOLORMAPSIZE])
{
	int 	i;
	UCHAR rgb[3];
	
	for (i=0;i < number; ++i) {
		if (!ReadOK(fd,rgb,sizeof(rgb))) {
			return FALSE;
		}
		
		buffer[CM_RED][i]=rgb[0];
		buffer[CM_GREEN][i]=rgb[1];
		buffer[CM_BLUE][i]=rgb[2];
	}	
	return TRUE;
}

static int DoExtension(FILE *fd, int label)
{
	static char buf[256];
	char	*str;

	switch(label) {
	case 0x01  :
		str="Plain Text Ext";
		break;
	case 0xff :
		str= "Appl ext";
		break;
	case 0xfe :
		str="Comment Ext";
		while (GetDataBlock(fd,(UCHAR *)buf)!=0) {
			//AfxMessageBox(buf, MB_OK | MB_ICONINFORMATION);
		}
		return FALSE;
		break;
	case 0XF9 :
		str="Graphic Ctrl Ext";
		(void)GetDataBlock(fd,(UCHAR *)buf);
		Gif89.disposal	=(buf[0]>>2)		&0x7;
		Gif89.inputFlag	=(buf[0]>>1)		&0x1;
		Gif89.delayTime	=LM_to_uint(buf[1],buf[2]);
		if ((buf[0]&0x1)!=0)
			Gif89.transparent=(UCHAR)buf[3];
	
		while (GetDataBlock(fd,(UCHAR *)buf)!=0);
		return FALSE;
		break;
	default :
		str=buf;
		sprintf(buf,"UNKNOWN (0x%02x)",label);
		break;
	}
	
	while (GetDataBlock(fd,(UCHAR *)buf)!=0);

	return FALSE;
}

int IsZeroDataBlock=FALSE;
static int GetDataBlock(FILE *fd, UCHAR *buf)
{
	UCHAR count;

	if (!ReadOK(fd,&count,1)) {
		//m_GIFErrorText="Error in GIF DataBlock Size";
		return -1;
	}

	IsZeroDataBlock=count==0;

	if ((count!=0) && (!ReadOK(fd,buf,count))) {
		//m_GIFErrorText="Error reading GIF datablock";
		return -1;
	}
	return count;
}

static int GetCode(FILE *fd, int code_size, int flag)
{
	static UCHAR buf[280];
	static int curbit, lastbit, done, last_byte;
	int i,j,ret;
	UCHAR count;

	if (flag) {
		curbit=0;
		lastbit=0;
		done=FALSE;
		return 0;
	}

	if ((curbit+code_size) >=lastbit) {
		if (done) {
			if (curbit >=lastbit) {
				//m_GIFErrorText="Ran off the end of my bits";
				return 0;
			}
			return -1;
		}
		buf[0]=buf[last_byte-2];	
		buf[1]=buf[last_byte-1];

		if ((count=GetDataBlock(fd,&buf[2]))==0)
			done=TRUE;

		last_byte=2+count;

		curbit=(curbit - lastbit) + 16;

		lastbit = (2+count)*8;
	}
	ret=0;
	for (i=curbit,j=0; j<code_size;++i,++j)
		ret|=((buf[i/8]&(1<<(i% 8)))!=0)<<j;

	curbit+=code_size;

	return ret;
}

static int LZWReadByte(FILE *fd, int flag, int input_code_size)
{
	static int fresh=FALSE;
	int code, incode;
	static int code_size, set_code_size;
	static int max_code, max_code_size;
	static int firstcode, oldcode;
	static int clear_code, end_code;

	static unsigned short  next[1<<MAX_LZW_BITS];
	static UCHAR  vals[1<<MAX_LZW_BITS];
	static UCHAR  stack [1<<(MAX_LZW_BITS+1)];
	static UCHAR  *sp;
	
	register int i;

	if (flag) {
		set_code_size=input_code_size;
		code_size=set_code_size+1;
		clear_code=1<<set_code_size;
		end_code = clear_code+1;
		max_code = clear_code+2;
		max_code_size=2*clear_code;

		GetCode(fd,0,TRUE);

		fresh=TRUE;
	
		for(i=0;i<clear_code;++i) {
			next[i]=0;
			vals[i]=i;
		}

		for (;i<(1<<MAX_LZW_BITS);++i)
			next[i]=vals[0]=0;
	
		sp=stack;

		return 0;
		} else if (fresh) {
			fresh=FALSE;
			do {
				firstcode=oldcode=GetCode(fd,code_size,FALSE);
			} while (firstcode==clear_code);
			return firstcode;
		}

		if (sp > stack)
			return *--sp;

		while ((code= GetCode(fd,code_size,FALSE)) >=0) {
			if (code==clear_code) {
				for (i=0;i<clear_code;++i) {
					next[i]=0;
					vals[i]=i;
				}
				for (;i<(1<<MAX_LZW_BITS);++i)	
					next[i]=vals[i]=0;
				code_size=set_code_size+1;
				max_code_size=2*clear_code;
				max_code=clear_code+2;
				sp=stack;
				firstcode=oldcode=GetCode(fd,code_size,FALSE);
				return firstcode;
			} else if (code==end_code) {
				int count;
				UCHAR buf[260];
		
				if (IsZeroDataBlock)
					return -2;

				while ((count=GetDataBlock(fd,buf)) >0);

				if (count!=0)
					//AfxMessageBox("Missing EOD in GIF data stream (common occurrence)",MB_OK);
				return -2;	
			}

			incode = code;

			if (code >= max_code) {
				*sp++=firstcode;
				code=oldcode;
			}

			while (code >=clear_code) {
				*sp++=vals[code];
				if (code==(int)next[code]) {
					//m_GIFErrorText="Circular table entry, big GIF Error!";
					return -1;
				}
				code=next[code];
			}

			*sp++ = firstcode=vals[code];

			if ((code=max_code) <(1<<MAX_LZW_BITS)) {
				next[code]=oldcode;
				vals[code]=firstcode;
				++max_code;
				if ((max_code >=max_code_size) &&
					(max_code_size < (1<<MAX_LZW_BITS))) {
					 max_code_size*=2;
					++code_size;
				}
			}

		oldcode=incode;

		if (sp > stack)
			return *--sp;
	}
	return code;
}   


static BOOL ReadImage(	FILE *fd,
						BYTE  * bigMemBuf,
						int width, int height,
						UCHAR cmap[3][MAXCOLORMAPSIZE],
						int interlace)
{
	UCHAR c;
	int color;
	int xpos=0, ypos=0, pass=0;
	long curidx;

	if (!ReadOK(fd,& c,1)) {
		return FALSE;
	}

	if (LZWReadByte(fd,TRUE,c)<0) {
		return FALSE;
	}
	
	while ((color=LZWReadByte(fd,FALSE,c))>=0) {
        curidx=(long)xpos+(long)ypos*(long)width;
        curidx*=3;     
        
		*(bigMemBuf+curidx)=cmap[0][color];
		*(bigMemBuf+curidx+1)=cmap[1][color];
		*(bigMemBuf+curidx+2)=cmap[2][color];				

		++xpos;
		if (xpos==width) {
			xpos=0;
			if (interlace) {
				switch (pass) {
				case 0:
				case 1:
					ypos+=8; break;
				case 2:
					ypos+=4; break;
				case 3:
					ypos+=2; break;
				}

				if (ypos>=height) {
					++pass;
					switch (pass) {
					case 1: ypos=4;break;
					case 2: ypos=2;break;
					case 3: ypos=1;break;
					default : goto fini;
					}
				}
			} else {
				++ypos;
			}
		}
		if (ypos >=height)
			break;
	}

fini :

	if (LZWReadByte(fd,FALSE,c)>=0) {

	}
	return TRUE;
}

//
//	gets image dimensions
//	returns -1,-1 on bad read
//

void GIFFile::GIFGetDimensions(String path, UINT *width, UINT *height)
{
	UCHAR			buf[16];
	UCHAR			c;
	char			version[4];
	FILE 			*fd;          
	int 			w=0;
	int				h=0;	
	
	if (_access(path,0)!=0) {
		*width=(UINT)-1;*height=(UINT)-1;
		return;
	}
	
	fd=fopen(path,"rb");
	if (fd==NULL) {                       
		*width=(UINT)-1;*height=(UINT)-1;
		return;
	}

	// read GIF file header
	if (!ReadOK(fd,buf,6))
		goto bail;

	// need the string "GIF" in the header
	if (strncmp((char *)buf,"GIF",3)!=0)
		goto bail;

	strncpy(version,(char *)(buf+3),3);
	version[3]='\0';

	// only handle v 87a and 89a
	if ((strcmp(version,"87a")!=0)&&(strcmp(version,"89a")!=0))
		goto bail;

	// screen description
	if (!ReadOK(fd,buf,7))
		goto bail;

	GifScreen.Width		=	LM_to_uint((UCHAR)buf[0],(UCHAR)buf[1]);
	GifScreen.Height	=	LM_to_uint((UCHAR)buf[2],(UCHAR)buf[3]);
	GifScreen.BitPixel	=	2<<((UCHAR)buf[4]&0x07);
	GifScreen.ColorResolution=((((UCHAR)buf[4]&0x70)>>3)+1);
	GifScreen.BackGround=	(UCHAR)buf[5];									// background color...
	GifScreen.AspectRatio=	(UCHAR)buf[6];
            

	// read colormaps
	if (BitSet((UCHAR)buf[4],LOCALCOLORMAP))
		if (!ReadColorMap(fd,GifScreen.BitPixel,GifScreen.ColorMap))
			goto bail;                                         
 
	if (!ReadOK(fd,&c,1))
		goto bail;

	if (c!=',')
		goto bail;

	// read image header
	if (!ReadOK(fd,buf,9))
		goto bail;                    
	
	*width=LM_to_uint((UCHAR)buf[4],(UCHAR)buf[5]);		
	*height=LM_to_uint((UCHAR)buf[6],(UCHAR)buf[7]);
		
	if ((*width<0) || (*height<0))
		goto bail;

	// good
	fclose(fd);
	return;

bail:      
	// bad
	fclose(fd);
	*width=(UINT)-1;*height=(UINT)-1;
	return;
}
                                                                          
