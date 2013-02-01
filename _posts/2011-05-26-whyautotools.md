---
layout: post
title: 为什么你应该让你的项目使用 autotools 而不是别的编译系统
---

编写软件离不开编译。 

简单的编译，无外乎直接调用 gcc 去编译。 

简单又不简单，当源文件不止一个的时候，麻烦的事情就随之而来。 

当然，这个时候你可以选择 Makefile 

但是，如果要求你的 Makefile 支持很多标准化操作，比如 

make install DESTDIR=.... 

make dist-bzip2 

你怎么打算呢？ 

自然，你需要一个自动创建 Makefile 的工具。 

你有很多选择: 

imake 

qmake 

scons 

cmake 

然而，他们都虽然简单，却不是最终用户友好的。 

因为，最终的用户最习惯的软件编译方式就是三部曲 

./configure --options 

make 

sudo make install 

而开发人员也可以直接 make dist-bzip2 生成发布用的 tarball. 

当然，如果有嵌入式的用户，他们自然会喜欢 

./configure --host=arch-machine-os 

进行交叉编译。 

这是他们最最最熟悉的方式。 

如果你想让你的用户能马上上手知道如何编译你的软件，那么，请使用 autotools 

这是 autotools 带给你的最大的好处。别忘记，你的开发者，一开始也是用户，如果他们第一次就编译失败，他们很有可能因此走掉。 

autotools 就是一把瑞士军刀，一开始就使用autotools，能让你的项目不会到最后被编译系统拖后腿。 

记住， ebuild 文件的复杂度代表了一个软件的编译系统的友好程度。 

而简单的 ebuild 文件只可能出现于使用 autotools 的软件中。 

Autotools can be quite tricky for newcomers, but when you start using them on a daily basis you find it's a lot easier than having to deal with manual makefiles or other strange build tools such as imake or qmake, or even worse, special autotools-like build scripts that try to recognize the system they are building on. Autotools makes it simple to support new OSes and new hardware platforms, and saves maintainers and porters from having to learn how to custom-build a system to fix compilation. By carefully writing a script, developers can support new platforms without any changes at all.