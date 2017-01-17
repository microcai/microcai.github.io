---
layout: post
title: 内核要集成glibc么
tags: [kernel]
---

往往内核添加了一个功能， glibc 要花很久才会用上。本来linux 那边为这个功能是否进入内核已经吵半天了，glibc
这边又要为是否使用这个内核新特性再次吵架半天 (glibc 不是 Linux 专有的，还得考虑 BSD (虽然人家也不用 glibc)
SysV Windows(诶，这没办法) ， 还有 sun 那消亡的 *** , 还有, 自家的 Hurd  wink.gif
然后，总之，这样新特性让人的接受上。。。 太慢了。

说近点的，fnotify glibc还没有对应的包装函数呢，futex 和 NPTL 又是花了许久才进入主流的。libc 是 app
和内核的桥梁，libc 理应快速跟上内核的接口变化 .. 但是 ... ... glibc 和 内核不是一块开发的，所以，这只是理想罢了。
glibc 还要去兼容不同版本的内核呢！
而内核也要去兼容不同版本的 glibc . 双方都背负了太多的历史包袱。glibc 至今保留 LinuxThreads
兼容2.4版本的古老内核。Linux
对已经没用，甚至有bug（接口的问题导致一些bug是必须的）的系统调用也必须保留，随知道用户会用哪个版本的glibc呢？虽然新的glibc
会使用新的调用，但是提供和老的调用一致的 API 来兼容，但是，用户只升级内核而不升级 glibc 是常有的事情. .. 就算升级了
glibc ... 你新版本的 glibc 一定就用上内核的新接口？！？！？！？！ 还是再等几年等 glibc 的开发者吵架结束吧

于是乎，Linux 的大牛们再次使出绝招： 让 libc 变成 VDSO 进驻内核。

{
这里普及一下 VDSO 这个小知识，知道的人跳过，不知道的人读一下 biggrin.gif
VDSO 就是 Virtual Dynamic Shared Object ... 就是内核提供的虚拟的 .so , 这个 .so
文件不在磁盘上，而是在内核里头。
内核把包含某 .so 的内存页在程序启动的时候映射入其内存空间，对应的程序就可以当普通的 .so 来使用里头的函数。比如 syscall()
这个函数就是在 linux-vdso.so.1 里头的，但是磁盘上并没有对应的文件. 可以通过 ldd /bin/bash 看看
}

这样，随内核发行的 libc (注意，VDSO只是随内核发行，没有在内核空间运行，这个不会导致内核膨胀。)
就唯一的和一个特定版本的内核绑定到一起了。这样内核和libc都不需要为兼容多个不同版本的对方而写太多的代码 ... 引入太多的 bug 了

当然， libc 不当当有到内核的接口，还有很多常用的函数，这些函数不需要
特别的为不同版本的内核小心编写，所以，我估计Linux上会出现两个 libc , 一个 libc 在内核，只是系统调用的包裹，另一个
libc 还是普通的 libc ， 只是这个 libc 再也不需要花精力去配合如此繁多的 kernel 了 .....

姑且一个叫  klibc, 一个叫 glibc :
... printf() 这些的还在 glibc  。 open() , read() , write(), socket()
这些却不再是 glibc 的了，他们在 klibc 。 
