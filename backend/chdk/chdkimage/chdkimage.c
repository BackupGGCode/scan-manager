#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "live_view.h"
#include "Python.h"

typedef unsigned char uint8_t;
typedef char int8_t;


typedef struct {
	unsigned width;
	unsigned height;
	uint8_t *data;
	uint8_t *r;
	uint8_t *g;
	uint8_t *b;
	uint8_t *a;
} liveimg_pimg_t;

typedef struct {
	uint8_t r;
	uint8_t g;
	uint8_t b;
	uint8_t a;
} palette_entry_rgba_t;

typedef struct {
	uint8_t a;
	uint8_t y;
	int8_t u;
	int8_t v;
} palette_entry_ayuv_t;

typedef struct {
	int8_t v;
	int8_t u;
	uint8_t y;
	uint8_t a;
} palette_entry_vuya_t;

typedef void (*yuv_palette_to_rgba_fn)(const char *pal_yuv, uint8_t pixel,palette_entry_rgba_t *pal_rgb);

void palette_type1_to_rgba(const char *palette, uint8_t pixel, palette_entry_rgba_t *pal_rgb);
void palette_type2_to_rgba(const char *palette, uint8_t pixel, palette_entry_rgba_t *pal_rgb);
void palette_type3_to_rgba(const char *palette, uint8_t pixel, palette_entry_rgba_t *pal_rgb);

void yuv_live_to_cd_rgb(const char *p_yuv,
						unsigned buf_width, unsigned buf_height,
						unsigned x_offset, unsigned y_offset,
						unsigned width,unsigned height,
						int skip,
						uint8_t *r,uint8_t *g,uint8_t *b);

// from a540, playback mode
static const char palette_type1_default[]={
0x00, 0x00, 0x00, 0x00, 0xff, 0xe0, 0x00, 0x00, 0xff, 0x60, 0xee, 0x62, 0xff, 0xb9, 0x00, 0x00,
0x7f, 0x00, 0x00, 0x00, 0xff, 0x7e, 0xa1, 0xb3, 0xff, 0xcc, 0xb8, 0x5e, 0xff, 0x5f, 0x00, 0x00,
0xff, 0x94, 0xc5, 0x5d, 0xff, 0x8a, 0x50, 0xb0, 0xff, 0x4b, 0x3d, 0xd4, 0x7f, 0x28, 0x00, 0x00,
0x7f, 0x00, 0x7b, 0xe2, 0xff, 0x30, 0x00, 0x00, 0xff, 0x69, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00,
};

typedef struct {
	yuv_palette_to_rgba_fn to_rgba;
	unsigned num_entries;
} palette_convert_t;

// type implied from index
// TODO only one function for now
palette_convert_t palette_funcs[] = {
	{NULL,0}, 					// type 0 - no palette, we could have a default func here
	{palette_type1_to_rgba,16},	// type 1 - ayuv, 16 entries double 4 bit index
	{palette_type2_to_rgba,16}, 	// type 2 - like type 1, but with 2 bit alpha lookup - UNTESTED
	{palette_type3_to_rgba,256}, 	// type 3 - vuya, 256 entries, 2 bit alpha lookup
};

#define N_PALETTE_FUNCS (sizeof(palette_funcs)/sizeof(palette_funcs[0]))

static palette_convert_t* get_palette_convert(unsigned type) {
	if(type<N_PALETTE_FUNCS) {
		return &(palette_funcs[type]);
	}
	return NULL;
}

static unsigned get_palette_size(unsigned type) {
	palette_convert_t* convert = get_palette_convert(type);
	if(convert) {
		return convert->num_entries*4;
	}
	return 0;
}

static uint8_t clip_yuv(int v) {
	if (v<0) return 0;
	if (v>255) return 255;
	return v;
}

static uint8_t yuv_to_r(uint8_t y, int8_t v) {
	return clip_yuv(((y<<12) +          v*5743 + 2048)>>12);
}

static uint8_t yuv_to_g(uint8_t y, int8_t u, int8_t v) {
	return clip_yuv(((y<<12) - u*1411 - v*2925 + 2048)>>12);
}

static uint8_t yuv_to_b(uint8_t y, int8_t u) {
	return clip_yuv(((y<<12) + u*7258          + 2048)>>12);
}

static uint8_t clamp_uint8(unsigned v) {
	return (v>255)?255:v;
}

static int8_t clamp_int8(int v) {
	if(v>127) {
		return 127;
	}
	if(v<-128) {
		return -128;
	}
	return v;
}

void palette_type1_to_rgba(const char *palette, uint8_t pixel,palette_entry_rgba_t *pal_rgb) {
	const palette_entry_ayuv_t *pal = (const palette_entry_ayuv_t *)palette;
	unsigned i1 = pixel & 0xF;
	unsigned i2 = (pixel & 0xF0)>>4;
	int8_t u,v;
	uint8_t y;
	pal_rgb->a = (pal[i1].a + pal[i2].a)>>1;
	// TODO not clear if these should be /2 or not
	y = clamp_uint8(pal[i1].y + pal[i2].y);
	u = clamp_int8(pal[i1].u + pal[i2].u);
	v = clamp_int8(pal[i1].v + pal[i2].v);
	pal_rgb->r = yuv_to_r(y,v);
	pal_rgb->g = yuv_to_g(y,u,v);
	pal_rgb->b = yuv_to_b(y,u);
}

static const uint8_t alpha2_lookup[] = {128,171,214,255};
// like above, but with alpha lookup
void palette_type2_to_rgba(const char *palette, uint8_t pixel,palette_entry_rgba_t *pal_rgb) {
	const palette_entry_ayuv_t *pal = (const palette_entry_ayuv_t *)palette;
	unsigned i1 = pixel & 0xF;
	unsigned i2 = (pixel & 0xF0)>>4;
	int8_t u,v;
	uint8_t y;
	uint8_t a = (pal[i1].a + pal[i2].a)>>1;
	pal_rgb->a = alpha2_lookup[a&3];
	// TODO not clear if these should be /2 or not
	y = clamp_uint8(pal[i1].y + pal[i2].y);
	u = clamp_int8(pal[i1].u + pal[i2].u);
	v = clamp_int8(pal[i1].v + pal[i2].v);
	pal_rgb->r = yuv_to_r(y,v);
	pal_rgb->g = yuv_to_g(y,u,v);
	pal_rgb->b = yuv_to_b(y,u);
}

void palette_type3_to_rgba(const char *palette, uint8_t pixel,palette_entry_rgba_t *pal_rgb) {
	const palette_entry_vuya_t *pal = (const palette_entry_vuya_t *)palette;
	// special case for index 0
	if(pixel == 0) {
		pal_rgb->a = pal_rgb->r = pal_rgb->g = pal_rgb->b = 0;
		return;
	}
	pal_rgb->a = alpha2_lookup[pal[pixel].a&3];
	pal_rgb->r = yuv_to_r(pal[pixel].y,pal[pixel].v);
	pal_rgb->g = yuv_to_g(pal[pixel].y,pal[pixel].u,pal[pixel].v);
	pal_rgb->b = yuv_to_b(pal[pixel].y,pal[pixel].u);
}

void yuv_live_to_cd_rgb(const char *p_yuv,
						unsigned buf_width, unsigned buf_height,
						unsigned x_offset, unsigned y_offset,
						unsigned width,unsigned height,
						int skip,
						uint8_t *r,uint8_t *g,uint8_t *b) {
	unsigned x,row;
	unsigned row_inc = (buf_width*12)/8;
	const char *p;
	// start at end to flip for CD
	const char *p_row = p_yuv + (y_offset * row_inc) + ((x_offset*12)/8);
	for(row=0;row<height;row++,p_row += row_inc) {
		for(x=0,p=p_row;x<width;x+=4,p+=6) {
			*r = yuv_to_r(p[1],p[2]);
			*g = yuv_to_g(p[1],p[0],p[2]);
			*b = yuv_to_b(p[1],p[0]);

			*r = yuv_to_r(p[3],p[2]);
			*g = yuv_to_g(p[3],p[0],p[2]);
			*b = yuv_to_b(p[3],p[0]);
			r+=3;g+=3;b+=3;
			if(!skip) {
				// TODO it might be better to use the next pixels U and V values
				*r = yuv_to_r(p[4],p[2]);
				*g = yuv_to_g(p[4],p[0],p[2]);
				*b = yuv_to_b(p[4],p[0]);

				*r = yuv_to_r(p[5],p[2]);
				*g = yuv_to_g(p[5],p[0],p[2]);
				*b = yuv_to_b(p[5],p[0]);
				r+=3;g+=3;b+=3;
			}
		}
	}
}

/*
check framebuffer desc values, and return a descriptive error or NULL
TODO can't check total size without bpp
*/
static const char * check_fb_desc(lv_framebuffer_desc *desc) {
	if(desc->visible_width > desc->buffer_width) {
		return "width  > buffer_width";
	}
	// sanity check, this should actually be harmless
	if(desc->visible_width > desc->logical_width) {
		return "visible_width > logical_width";
	}
	if(desc->visible_height > desc->logical_height) {
		return "visible_height > logical_height";
	}
	return NULL;
}

static void convert_palette(palette_entry_rgba_t *pal_rgba,lv_data_header *frame) {
	const char *pal=NULL;
	yuv_palette_to_rgba_fn fn;
	int i;
	palette_convert_t *convert=get_palette_convert(frame->palette_type);

	if(!convert || !frame->palette_data_start) {
		convert = get_palette_convert(1);
		pal = palette_type1_default;
	} else {
		pal = ((char *)frame + frame->palette_data_start);
	}
	fn = convert->to_rgba;
	for(i=0;i<256;i++) {
		fn(pal,i,&pal_rgba[i]);
	}
}

static PyObject *dataToViewportRGB(PyObject *self, PyObject *args) {

	lv_data_header *frame;
	int length;
	int skip;
	int par = (skip == 1)?2:1;
	unsigned vwidth;
	unsigned dispsize;
	const char *fb_desc_err;
	int outLen;
	uint8_t * out;
	PyObject *rc;


	if(!PyArg_ParseTuple(args,"s#i",&frame,&length,&skip)) {
		return NULL;
	}

	// this is not currently an error, if sent live data without viewport selected, just return nil image
	if(!frame->vp.data_start) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	vwidth = frame->vp.visible_width/par;
	dispsize = vwidth*frame->vp.visible_height;

	// sanity check size - depends on type
	if(frame->vp.data_start + (frame->vp.buffer_width*frame->vp.visible_height*12)/8 > length) {
		PyErr_SetString(PyExc_RuntimeError,"data < buffer_width*height");
		return NULL;
	}

	fb_desc_err = check_fb_desc(&frame->vp);
	if(fb_desc_err) {
		PyErr_SetString(PyExc_RuntimeError,fb_desc_err);
		return NULL;
	}

	outLen = frame->vp.visible_width * frame->vp.visible_height;
	out = (uint8_t *) malloc(outLen*3);

	yuv_live_to_cd_rgb(
		((char *)frame)+frame->vp.data_start,
		frame->vp.buffer_width,
		frame->vp.visible_height,
		0,
		0,
		frame->vp.visible_width,
		frame->vp.visible_height,
		skip,
		out, out+1, out+2
	);

	rc = PyString_FromStringAndSize(out,outLen*3);

	free(out);

	return rc;
}

PyObject *dataToBitmapRGBA(PyObject *self, PyObject *args) {
	lv_data_header *frame;
	int length;
	int skip;
	int par;
	palette_entry_rgba_t pal_rgba[256];
	const char *fb_desc_err;
	unsigned vwidth;
	unsigned dispsize;
	int y_inc;
	int x_inc;
	int x,y;
	int height;
	uint8_t *p;
	uint8_t *r;
	uint8_t *g;
	uint8_t *b;
	uint8_t *a;
	int outLen;
	uint8_t *out;
	PyObject *rc;
	palette_entry_rgba_t *c;

	if(!PyArg_ParseTuple(args,"s#i",&frame,&length,&skip)) {
		return NULL;
	}

	// pixel aspect ratio
	par = (skip == 1)?2:1;

	if(!frame->bm.data_start) {
	    Py_INCREF(Py_None);
	    return Py_None;
	}

	// sanity check size - depends on type
	if(frame->bm.data_start + frame->bm.buffer_width*frame->bm.visible_height > length) {
		PyErr_SetString(PyExc_RuntimeError,"data < buffer_width*height");
	}

	fb_desc_err = check_fb_desc(&frame->bm);
	if(fb_desc_err) {
		PyErr_SetString(PyExc_RuntimeError,fb_desc_err);
		return NULL;
	}

	if(get_palette_size(frame->palette_type) + frame->palette_data_start > length) {
		PyErr_SetString(PyExc_RuntimeError,"data < palette size");
		return NULL;
	}

	convert_palette(pal_rgba,frame);

	vwidth = frame->bm.visible_width/par;
	dispsize = vwidth*frame->bm.visible_height;

	outLen = frame->vp.visible_width * frame->vp.visible_height;
	out = (uint8_t *) malloc(outLen*4);

	y_inc = frame->bm.buffer_width;
	x_inc = par;
	height = frame->bm.visible_height;

	p=((uint8_t *)frame + frame->bm.data_start);

	r = out;
	g = out + 1;
	b = out + 2;
	a = out + 3;

	// TODO we don't actually check the various offsets
	for(y=0;y<height;y++,p+=y_inc) {
		for(x=0;x<frame->bm.visible_width;x+=x_inc) {
			c = &pal_rgba[*(p+x)];
			*r = c->r;
			*g = c->g;
			*b = c->b;
			*a = c->a;
			r+=4;g+=4;b+=4;a+=4;
		}
	}

	rc = PyString_FromStringAndSize(out,outLen*4);

	free(out);

	return rc;
}


static PyMethodDef
module_functions[] = {
    { "dataToViewportRGB", dataToViewportRGB, METH_VARARGS, "Convert liveview data to viewport image data" },
    { "dataToBitmapRGBA", dataToBitmapRGBA, METH_VARARGS, "Convert liveview data to bitmap image data" },
    { NULL }
};

void initchdkimage(void)
{
    Py_InitModule3("chdkimage", module_functions, "Module for converting CHDK image data");
}
