---
layout: post
title: 链接到 ucrtbase.dll
tags: [c++, cpp, ucrt, mingw, llvm]
---

使用 vc6.0 以后的 VS 编译器，最恼火的一点就是生成的 exe 依赖 msvcrXXX.dll。
其中 XXX 是个版本号。而且 msvcrXXX.dll 系统是不自带的。

于是每个 exe 都得带上 vcredist.exe 安装程序。

过于蛋疼。

正统的解决方法是改使用静态C库。

但是会带来二进制体积暴涨的问题。

十分的怀念 VC6.0 可以生成exe 依赖 msvcrt.dll， 不带版本号那种。而不带版本号的那个，每个 windows 都会自带。

有比较多的偏门方式，可以在 vc6 以后的版本继续链接到 msvcrt.dll 。但是一来是偏方，而来在 vs2017 以后这些偏方也没用了。

后来对此也不甚钻研了，直接无脑静态链接了。

最近，突然又关心起 msvcrt 问题，因为用了下 LLVM MinGW。然后在 readme 里看到了 UCRT 介绍。

UCRT？ UCRT 是啥？

原来微软也发现大家不爽带版本号的 msvcrXXX.dll。于是用 C++ 以 extern "C" 的方式重写了它的 C 运行时。
这个重写的新C运行时就是 UCRT。每个 win 都会带上。名为 ucrtbase.dll 和 Debug 版的 ucrtbased.dll。

连这个UCRT的，还有新的 vcruntimeXXX.dll。而过去 C++ 运行时是 msvcpXXX.dll 。

这个 UCRT 和过去的 msvcrt.dll 相比一个最显著的区别，是他可以让静态版的 c++ 运行时用上动态版的 C 运行时。

而之前的老 C库，是 动态C++库必须使用动态 C 库。静态 C++库必须使用静态 C库。

于是，使用 UCRT 则可以实现虽然c++运行时库还是静态的但是至少把标准C运行时给它动态链接了。起码能缩小几百KB的二进制体积。
而且大家都用动态C运行时库，可以解决跨DLL的接口兼容问题。

如果是 vs2022 则默认已经是使用 ucrt 了。

只不过还是老一套的 静态搭静态的规矩。也就是 静态 c++ 库搭配静态 C 库。

在 cmake 里，启用方式就是

```
if (MSVC)
    add_link_options("/NODEFAULTLIB:libucrt.lib;libucrtd.lib")
    link_libraries(ucrt$<$<CONFIG:Debug>:d>.lib)
endif()
```

libucrt.lib 是静态 C 运行时，而 ucrt.lib 是动态的。去掉 libucrt.lib 改用 ucrt.lib 就可以了。

不过很诡异的是， ucrtd.lib 会连接到 ucrtbased.dll ，而 ucrt.lib 则看起来还是静态的。导入表里没有 ucrtbase.dll

如果使用 llvm-mingw 项目的 clang 编译器，则可以实现 release 版本确实连接 ucrtbase.dll

![img](/images/ucrtbase.dll.png)

然后导入表里没有 api-ms-*.dll 了。

