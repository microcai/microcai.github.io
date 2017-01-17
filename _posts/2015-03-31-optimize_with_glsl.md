---
layout: post
title: GLSL加速 YUV 显示
tags: [opengl]
---

通常来说，视频都是使用 YUV 格式编码的。YUV 最符合人眼的结构，因为人眼对亮度要比对颜色敏感的多。 YUV 将颜色分成一个 亮度信号和2个色差信号。于是就可以使用更多的bit数去编码亮度信号。在同样的每像素比特位数下，YUV 能比 RGB 保留更多的信息。

But YUV 要在 PC 屏幕上显示，不那么友好。需要转成 RGB 格式。网上一搜一大把，这里就不贴转换公式了。

将YUV转换为 RGB 时，是像素独立的。每个像素都可以独立转换，因此可以被大规模并行。所以 YUV 最佳的转换地方还是在 GPU 上。不适合在 CPU 上转。

非常可惜的是， OpenGL 是基于 RGBA 的。在opengl里无法直接使用YUV。

But，先知已经考虑到了这点，先知给 OpenGL 加了一道通用计算的能力。这道通用计算能力就叫 .. 额.. Shader。（为啥中文译名叫着色器呢？）

Shader 简单的来说就是一小段跑在 GPU 上的代码。这些代码针对每一个提交的顶点和每一个最终屏幕像素并行执行。
处理顶点数据的就是顶点着色器。处理屏幕像素的就是像素着色器了。

因此, 将 YUV2RGB 的公式写成一个 shader, 就能实现在 GPU 上并发转格式了.


```GLSL
vec3 yuv2rgb(in vec3 yuv)
{
	// YUV offset
	// const vec3 offset = vec3(-0.0625, -0.5, -0.5);
	const vec3 offset = vec3(-0.0625, -0.5, -0.5);
	// RGB coefficients
	const vec3 Rcoeff = vec3( 1.164, 0.000,  1.596);
	const vec3 Gcoeff = vec3( 1.164, -0.391, -0.813);
	const vec3 Bcoeff = vec3( 1.164, 2.018,  0.000);

	vec3 rgb;

	yuv = clamp(yuv, 0.0, 1.0);

	yuv += offset;

	rgb.r = dot(yuv, Rcoeff);
	rgb.g = dot(yuv, Gcoeff);
	rgb.b = dot(yuv, Bcoeff);
	return rgb;
}

```

输入为一个 vec3 的向量, 返回 vec3 向量. 这个转换对每个像素并发的执行.


于是, 只要将解码好的视频, Y U V 3个通道分别绑定为3个贴图, 然后在 shader 里访问, 转换成 RGB 就可以了.


```glsl

uniform sampler2D texY; // Y
uniform sampler2D texU; // U
uniform sampler2D texV; // V

varying vec2 vary_tex_cord;

vec3 yuv2rgb(in vec3 yuv);

vec3 get_yuv_from_texture(in vec2 tcoord)
{
	vec3 yuv;
	yuv.x = texture(texY, tcoord).r;
	// Get the U and V values
	yuv.y = texture(texU, tcoord).r;
	yuv.z = texture(texV, tcoord).r;
	return yuv;
}

vec4 mytexture2D(in vec2 tcoord)
{
	vec3 rgb, yuv;
	yuv = get_yuv_from_texture(tcoord);
	// Do the color transform
	rgb = yuv2rgb(yuv);
	return vec4(rgb, 1.0);
}

out vec4 out_color;

void main()
{
	// That was easy. :)
	out_color = mytexture2D(vary_tex_cord);
}


```

完成

