---
layout: post
title: 一个Sqrt函数再次引发的血案
---

这些神人啊，开平方居然有这么快的算法！！！
于是我决定看看 glibc 是怎么实现的！
如果 glibc 比较慢，我一定要改成神人的算法重新编译 glibc ！！！

等等！先写一个程序测试两种算法的速度 

	#include <math.h>

	float magic_sqrt(float number)
	{
	    long i;
	    float x, y;
	    const float f = 1.5F;

	    x = number * 0.5F;
	    y  = number;
	    i  = * ( long *)    & y  ;
	    i  = 0x5f3759df - ( i >>  1 wink.gif     ;
	    y  = * ( float * wink.gif    & i  ;
	    y  = y * ( f - ( x * y * y wink.gif wink.gif ;
	    y  = y * ( f - ( x * y * y wink.gif wink.gif ;
	    return number * y;
	}
	#define TIMES 2000000000
	int main(int argc, char argv[0])
	{
		unsigned int i;
	  if(argv[1]=='s')
	  {
	    for(i=0;i < TIMES; i++)
	    {
		  sqrt(200.0);
	    }
	  }else
	  {
	    for(i=0;i < TIMES; i++)
	    {
		  magic_sqrt(200.0);
	    }
	  }
	  return 0;
	} 
	

然后用 time ./a.out s 和 time ./a.out m 来测验两个开发算法的速度。
哥震惊了！！！ 一样快！！！莫非 glibc 也使用了神一样的 ... ?????

于是经过漫长时间的下载， 解压 ， grep 之后，我终于找到了我要的 glibc 中实现开方算法的文件

sysdeps/x86_64/fpu/e_sqrt.c

哥再次震惊了！哥再次吐血了！！！

居...居...居居然 ..... 只有一条指令 


	double
	__ieee754_sqrt (double x)
	{
	  double res;

	  asm ("sqrtsd %0, %1" : "=x" (res) : "x" (x));

	  return res;
	} 
	
看来以后我可以放心的使用 glibc 的数学函数了 ... 事实证明， glibc 总是使用的最快的方法。
