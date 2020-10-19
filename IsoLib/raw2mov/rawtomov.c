/*

	sample program to build raw YUV 4:2:0 QuickTime (or 3GP) files using the file format
	reference software
	
	Dave Singer, May 2006
	
*/
#include "ISOMovies.h"
#include <string.h>

#ifndef _MSC_VER
#include <sys/param.h>
#endif

#include <stdlib.h>

char infile[1024];
char outfile [1024];
u32 x_width = 176;
u32 y_height = 144;
u32 timescale = 600;
int	frameduration = 20;
int by_reference = 0;
int do_import = 1;
u32 codec_type = MP4_FOUR_CHAR_CODE( 'j', '4', '2', '0' );
int bytes_per_frame;
char codec_string[ 8 ];
int tracknumber = 1;
int startframenumber = 1;
int maxframes = 0x1000000;
int framesprocessed = 0;
char file_format = 'q';
int force = 0;

u16 color_primaries = 2;
u16 xfer_function = 2;
u16 matrix_coeffs = 2;
u16 do_nclc = 0;

MP4Err createMyMovie(  );
MP4Err createMyRawFile( );
MP4Err addMySamples( MP4Track theTrack, MP4Media theMedia, MP4Movie moov, char* fromfile );
MP4Err set_bytes_per_frame();

int main( int argc, char **argv )
{
	MP4Err err;
	int argn, x;
	char name[64];

	for (x=strlen(argv[0]); x>0; --x)
		if (argv[0][x] == '/')
			break;
	x += (x != 0);
	strcpy(name,&argv[0][x]);

	if (argc < 3) goto bail;
	if ( (((argv[1])[0]) == '-') || (((argv[2])[0]) == '-')) goto bail;
	
	strcpy(infile, argv[1]);
	strcpy(outfile,argv[2]);
	
	for (argn=3; argn<argc; argn++) {
		if ((argv[argn])[0] != '-') goto bail;
		switch ((argv[argn])[1]) {
			case 'e': do_import = 0; break;
/* #ifndef _MSC_VER */
			case 'r': by_reference = 1; break;
/* #endif */
			case 'h': 
				if (argc<=argn) goto bail;
				y_height = atoi(argv[++argn]);
				break;
			case 'w': 
				if (argc<=argn) goto bail;
				x_width = atoi(argv[++argn]);
				break;
			case 't': 
				if (argc<=argn) goto bail;
				timescale = atoi(argv[++argn]);
				break;
			case 'd': 
				if (argc<=argn) goto bail;
				frameduration = atoi(argv[++argn]);
				break;
			case 'c': 
				if (argc<=argn) goto bail;
				if (strlen( argv[++argn] ) < 4) goto bail;
				codec_type = MP4_FOUR_CHAR_CODE( (argv[argn])[0], (argv[argn])[1], (argv[argn])[2], (argv[argn])[3] );
				break;
			case 'n': 
				if (argc<=argn) goto bail;
				tracknumber = atoi(argv[++argn]);
				break;
			case 's': 
				if (argc<=argn) goto bail;
				startframenumber = atoi(argv[++argn]);
				break;
			case 'm': 
				if (argc<=argn) goto bail;
				maxframes = atoi(argv[++argn]);
				break;
			case 'f': 
				if (argc<=argn) goto bail;
				if (strlen( argv[++argn] ) < 1) goto bail;
				file_format = (argv[argn])[0];
				if (file_format=='Q') file_format='q';
				if ((file_format != '3') && (file_format != 'q')) goto bail;
				break;
			case 'p':
				if (argc<=argn) goto bail;
				color_primaries = atoi(argv[++argn]);
				do_nclc = 1;
				break;
			case 'u':
				if (argc<=argn) goto bail;
				xfer_function = atoi(argv[++argn]);
				do_nclc = 1;
				break;
			case 'x':
				if (argc<=argn) goto bail;
				matrix_coeffs = atoi(argv[++argn]);
				do_nclc = 1;
				break;
			case 'F':
				force = 1; 
				break;
			default: goto bail;
		}
	}

	err = set_bytes_per_frame(); if (err) return err;
		
	if (do_import) {
		err = createMyMovie(  );
		if (err) fprintf( stderr, "Creating %s failed %d\n", outfile, err );
		else fprintf(stderr, "%d frames imported into %s with -w %d -h %d -t %d -d %d -c '%s' -s %d -m %d%s\n",
				framesprocessed,
				outfile, x_width, y_height, timescale, frameduration, codec_string,
				startframenumber, maxframes, (by_reference ? " -r" : "") );
	}
	else 
	{
		err = createMyRawFile(  );
		if (err) fprintf( stderr, "Creating %s failed %d\n", outfile, err );
		else fprintf( stderr, "%d frames exported into %s with -w %d -h %d -t %d -d %d -c %s -s %d -m %d\n", 
				framesprocessed, outfile, x_width, y_height, timescale, frameduration, codec_string,
				startframenumber, maxframes );
	}
	
	return 0;
	
bail:
	printf("\nUsage: %s infile outfile [-w width] [-h height] [-t timescale] [-d frameduration] [-c codec4cc]\n",name);
	printf("                   [-f Q|3] [- startframenumber] [-m maxframecount] [-r]\n");

	printf("\n       %s infile outfile [-e] [-n tracknumber] [- startframenumber] [-m maxframecount]\n",name);
	return -1;
}

MP4Err createMyMovie(  )
{
	MP4Err err;
	MP4Movie moov;
	MP4Track trak;
	MP4Media media;
	u64 mediaDuration;
	
	err = MP4NoErr;
	switch (file_format) {
		case '3':
			err = New3GPPMovie( &moov, 6 ); if (err) goto bail;
			do_nclc = 0;
			break;
		case 'q':
			err = QTNewMovie( &moov ); if (err) goto bail;
			break;
		default:
			return err;
	}

	err = MP4NewMovieTrack( moov, MP4NewTrackIsVisual, &trak ); if (err) goto bail;
	err = MJ2SetTrackDimensions(	trak, x_width, y_height );
	err = MP4NewTrackMedia( trak, &media, MP4VisualHandlerType, timescale, NULL ); if (err) goto bail;
	err = MP4BeginMediaEdits( media ); if (err) goto bail;
	err = addMySamples( trak, media, moov, infile ); if (err) goto bail;

	err = MP4EndMediaEdits( media ); if (err) goto bail;
	err = MP4GetMediaDuration( media, &mediaDuration ); if (err) goto bail;
	err = MP4InsertMediaIntoTrack( trak, 0, 0, mediaDuration, 1 ); if (err) goto bail;

	err = ISOWriteMovieToFile( moov, outfile ); if (err) goto bail;
	err = MP4DisposeMovie( moov ); if (err) goto bail;
bail:
	return err;
}

MP4Err createMyRawFile( )
{
	MP4Err err;
	MP4Movie moov;
	MP4Track trak;
	MP4Media media;
	MP4TrackReader reader;
	MP4Handle sampleH;
	MP4Handle sampleEntryH;
	u32 sd_index;
	u32 unitSize;
	s32 dts, cts;
	u32 sampleFlags;
	u64 duration, ctsl, dtsl;
	
	u32 handlerType;
	u16 theight, twidth;
	FILE* fd;
	u32 sampleSize = 0;
	u32 thisduration;
	u64 lastTime;
	int framenumber = 0;
	
	fd = fopen( outfile, "wb" );
	if (!fd) {
		fprintf(stderr, "Error: raw file %s could not be created\n",outfile);
		return MP4IOErr;
	}
	
	err = MP4NoErr;
	err = MP4OpenMovieFile( &moov, infile, MP4OpenMovieNormal ); if (err) goto bail; /* MP4OpenMovieNormal MP4OpenMovieDebug MP4OpenMovieInPlace*/
 	
	err = MP4GetMovieIndTrack( moov, tracknumber, &trak ); if (err) goto bail;
	err = MP4GetTrackMedia( trak, &media ); if (err) goto bail;
	err = MP4GetMediaHandlerDescription( media, &handlerType, NULL ); if (err) goto bail;
	err = MP4CreateTrackReader( trak, &reader ); if (err) goto bail;

	err = ISOGetMediaTimeScale( media, &timescale ); if (err) goto bail;
	err = MJ2GetTrackDimensions( trak, &x_width, &y_height );  if (err) goto bail;
	
	err = MP4NewHandle( 0, &sampleH ); if (err) goto bail;
	err = MP4NewHandle( 0, &sampleEntryH ); if (err) goto bail;

	err = ISOGetMediaSample( media, sampleH, &unitSize, 0, &dtsl, &ctsl,
 		&duration, sampleEntryH, &sd_index, &sampleFlags ); if (err) goto bail;
	cts = (int) ctsl; dts = (int) dtsl;
	
	err = ISOGetSampleDescriptionDimensions(sampleEntryH, &twidth, &theight); if (err) goto bail;
	err = ISOGetSampleDescriptionType( sampleEntryH, &codec_type); if (err) goto bail;
	if ((twidth != x_width) || (theight != y_height))
		fprintf( stderr, "Warning; track width/height [%d/%d] not same as sample entry [%d/%d]\n",
			x_width, y_height, twidth, theight);
	x_width = twidth; y_height = theight;
	set_bytes_per_frame();
	
	frameduration = (int) duration; lastTime = - duration;
	
	/* play every frame */
	for (;;)
	{
		u32 written;
		u32 this_index;
		
		err = MP4TrackReaderGetNextAccessUnit( reader, sampleH, &unitSize, &sampleFlags, &cts, &dts );
		if ( err )
		{
			if ( err == MP4EOF )
				err = MP4NoErr;
			break;
		}
		framenumber++;
		
		thisduration = dts - lastTime;
		if (thisduration != frameduration)
			fprintf( stderr, "Error; samples not constant duration; previous sample was %d ticks but this one is %d ticks\n",
				frameduration, thisduration);
		frameduration = thisduration;
		lastTime = dts;
		
		err = MP4TrackReaderGetCurrentSampleDescriptionIndex( reader, &this_index ); if (err) goto bail;
		if (this_index != sd_index)
			fprintf( stderr, "Error; samples do not have constant configuration\n");

		if ((sampleSize != 0) && (sampleSize != unitSize))
			fprintf( stderr, "Error; samples not constant size; previous sample was %d bytes but this one is %d bytes\n",
				sampleSize, unitSize);
		sampleSize = unitSize;

		if (bytes_per_frame != unitSize)
			fprintf( stderr, "Error; sample size is %d, not expected size %d\n",
				unitSize, bytes_per_frame);		

		if ((framenumber >= startframenumber) && (framenumber < (startframenumber + maxframes)))
		{
			written = fwrite( *sampleH, 1, unitSize, fd);
			if (written != unitSize) fprintf( stderr, "IO Error; sample was %d bytes but only %d bytes written\n",
				unitSize, written);
			framesprocessed++;
		} else if (framenumber >= (startframenumber + maxframes)) break;
	}
	if (fclose( fd )) {
		fprintf(stderr, "Error: raw file %s could not be closed properly\n",outfile);
		return MP4IOErr;
	}
bail:
	return err;
}

MP4Err addMySamples( MP4Track trak, MP4Media media, MP4Movie moov, char* the_file )
{
	MP4Err err;
	MP4Handle sampleEntryH;
	MP4Handle sampleDataH;
	MP4Handle sampleDurationH;
	MP4Handle sampleSizeH;
	u32 first_sample;
	u64 fileoffset = 0;
	u32 dref_index = 1;
	FILE* fd;
	int framenumber = 0;
	MP4Handle the_url = 0;
#ifndef _MSC_VER
	char path[PATH_MAX + 7];
#else
	char path[512];
#endif

	fd = fopen( the_file, "rb" );
	if (!fd) {
		fprintf(stderr, "Error: raw file %s could not be opened\n",outfile);
		return MP4IOErr;
	}
		
	err = MP4NoErr;
	err = MP4SetMediaLanguage( media, "und" ); if (err) goto bail;

#ifndef _MSC_VER
	if (by_reference) {
		strcpy( path, "file://" );
		realpath( infile, path + 7 );
	
		err = MP4NewHandle( strlen(path)+1, &the_url ); if (err) goto bail;
		memcpy( *the_url, path, strlen(path)+1 );
		err = ISOAddMediaDataReference( media, &dref_index, the_url, NULL ); if (err) goto bail;
	}
#else
	if (by_reference) {
		u32 i;
		char *p;
		strcpy( path, "file:///" );
		p = _fullpath( path + 8, infile, 512 - 8 );
		if (!p) {
			err = MP4IOErr;
			goto bail;
		}
		for (i=8; i<strlen(path); i++) 
			if (path[i] == '\\') path[i] = '/';
			
		err = MP4NewHandle( strlen(path)+1, &the_url ); if (err) goto bail;
		memcpy( *the_url, path, strlen(path)+1 );
		err = ISOAddMediaDataReference( media, &dref_index, the_url, NULL ); if (err) goto bail;
	}
#endif
	
	err = MP4NewHandle( 0, &sampleEntryH ); if (err) goto bail;
	err = ISONewGeneralSampleDescription( trak, sampleEntryH,
		dref_index,
		codec_type,
		NULL ); if (err) goto bail;
	err = ISOSetSampleDescriptionDimensions( sampleEntryH, (u16) x_width, (u16) y_height ); if (err) goto bail;
	
	if (do_nclc) {
		MP4Handle nclcH;
		MP4GenericAtom nclc;
		char *p;
		err = MP4NewHandle( 10, &nclcH ); if (err) goto bail;
		p = *nclcH;
		p[0] = 'n'; p[1] = 'c'; p[2] = 'l'; p[3] = 'c';
		p[4] = (color_primaries>>8) & 0xFF; p[5] = color_primaries & 0xFF;
		p[6] = (xfer_function  >>8) & 0xFF; p[7] = xfer_function & 0xFF;
		p[8] = (matrix_coeffs  >>8) & 0xFF; p[9] = matrix_coeffs & 0xFF;
		err = ISONewForeignAtom( &nclc, MP4_FOUR_CHAR_CODE('c','o','l','r'), nclcH); if (err) goto bail;
		err = ISOAddAtomToSampleDescription( sampleEntryH, nclc); if (err) goto bail;
	}
	
	err = MP4NewHandle( sizeof(u32), &sampleDurationH ); if (err) goto bail;
	*((u32*) *sampleDurationH) = frameduration;
	/* when we import YUV files, the duration per frame is constant, so we set it here and leave it alone
	   in the loop.  for variable-rate video, it will need to be adjusted for each frame */
	
	err = MP4NewHandle( bytes_per_frame, &sampleDataH ); if (err) goto bail;
	err = MP4NewHandle( sizeof(u32), &sampleSizeH ); if (err) goto bail;
	* ((u32 *) (*sampleSizeH)) = bytes_per_frame;
	
	first_sample = 1;
	
	for ( ;; )
	{
		int read_count;
		
		read_count = fread( *sampleDataH, 1, bytes_per_frame, fd );
		if (read_count < bytes_per_frame) 
		{
			if (read_count != 0) fprintf(stderr, "Warning: residual %d bytes at end of file\n", read_count );
			break;
		}
		framenumber++;
		
		if ((framenumber >= startframenumber) && (framenumber < (startframenumber + maxframes)))
		{
			if (by_reference) {
				err = MP4AddMediaSampleReference( media, fileoffset, 1, sampleDurationH, sampleSizeH, 
						( first_sample ? sampleEntryH : NULL), NULL, NULL ); if (err) goto bail;
				fileoffset += bytes_per_frame;
			}
			else
			{
				err = MP4AddMediaSamples( media, sampleDataH, 1, sampleDurationH, sampleSizeH, 
					( first_sample ? sampleEntryH : NULL), NULL, NULL ); if (err) goto bail;
			}
			first_sample = 0;
			framesprocessed++;
		} else if (framenumber >= (startframenumber + maxframes)) break;
	}
	
	if ( sampleEntryH )
	{
		err = MP4DisposeHandle( sampleEntryH ); if (err) goto bail;
		sampleEntryH = NULL;
	}
/* #ifndef _MSC_VER */
	if ( the_url )
	{
		err = MP4DisposeHandle( the_url ); if (err) goto bail;
		the_url = NULL;
	}
/* #endif */
	fclose(fd);

bail:
	return err;
}

MP4Err set_bytes_per_frame()
{
	u32 horiz_align_pixels = 2;
	codec_string[0] = (codec_type>>24) & 0xFF; codec_string[1] = (codec_type>>16) & 0xFF;
	codec_string[2] = (codec_type>> 8) & 0xFF; codec_string[3] =  codec_type      & 0xFF;
	codec_string[4] = 0;

	switch (codec_type) {
		case MP4_FOUR_CHAR_CODE( 'I', '4', '2', '0' ):
		case MP4_FOUR_CHAR_CODE( 'I', 'Y', 'U', 'V' ):
		case MP4_FOUR_CHAR_CODE( 'j', '4', '2', '0' ):
		case MP4_FOUR_CHAR_CODE( 'y', 'v', '1', '2' ):
			bytes_per_frame = ((x_width * y_height * 3)/2);
			break;
		case MP4_FOUR_CHAR_CODE( '2', 'v', 'u', 'y' ): 	/* icefloe */
		case MP4_FOUR_CHAR_CODE( 'y', 'u', 'v', '2' ):	/* icefloe */
			bytes_per_frame = x_width * y_height * 2;
			break;
		case MP4_FOUR_CHAR_CODE( 'r', 'a', 'w', ' ' ):
		case MP4_FOUR_CHAR_CODE( 'v', '3', '0', '8' ): 	/* icefloe */
			bytes_per_frame = x_width * y_height * 3;
			break;
		case MP4_FOUR_CHAR_CODE( 'v', '4', '0', '8' ):	/* icefloe */
		case MP4_FOUR_CHAR_CODE( 'v', '4', '1', '0' ):	/* icefloe */
			bytes_per_frame = x_width * y_height * 4;
			break;
		case MP4_FOUR_CHAR_CODE( 'y', 'u', 'v', 's' ):
		case MP4_FOUR_CHAR_CODE( 'Y', 'V', 'Y', 'U' ):
		case MP4_FOUR_CHAR_CODE( 'y', 'u', 'v', 'u' ):
			bytes_per_frame = (x_width * y_height * 2);
			break;
		case MP4_FOUR_CHAR_CODE( 'R', 'G', 'B', 'A' ):
		case MP4_FOUR_CHAR_CODE( 'A', 'B', 'G', 'R' ):
			bytes_per_frame = (x_width * y_height * 4);
			break;
		case MP4_FOUR_CHAR_CODE( 'v', '2', '1', '6' ): 		/* icefloe */
			bytes_per_frame = ((x_width * y_height * 8)/2);
			break;
		case MP4_FOUR_CHAR_CODE( 'v', '2', '1', '0' ):		/* icefloe */
			horiz_align_pixels = 48;
			if(x_width%horiz_align_pixels) bytes_per_frame = (((x_width/horiz_align_pixels) + 1) * horiz_align_pixels * y_height * 16) / 6;
			else bytes_per_frame = ((x_width * y_height * 16)/6);
			break;
		default:
			if(!force)
			{
				fprintf(stderr, "Error: unknown codec type '%s'\n",codec_string);
				return -1;
			}
			fprintf(stdout, "Warning: unknown codec type '%s'\n",codec_string);
			bytes_per_frame = x_width * y_height * 3; /* even when not supported write something (too see if we can actually play it.) */
	}
	return MP4NoErr;
}
