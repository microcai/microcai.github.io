---
layout: post
title: 高并发服务器的静态内存分配策略
tags: [c100k, asio, boost, net, cpp]
---


asio 的 async_accept 函数在高并发的时候，会发生遗漏 accept 的情况。根本原因在于，async_accept 回调的时候，已经 监听的socket已经没有执行 accept 操作了。
解决的办法就是投递多个 async_accept. asio 的 async_\* 系列 函数通常只能投递一次，多次投递会发生未定义行为。async_accept 是为数不多的例外。

通常在写一个 server 的时候，client 是采取 accept 一个就 make_shared 一个的做法。对于大量频繁的连接请求，make_shared 很快就会成为新的瓶颈。
在读 beast 的 example/http/fast_server 的时候，发现了 beast 对这个问题的解决方案，非常的聪明。

beast 的做法就是，固定的 client 对象。每个 client 自己投递 async_accept 请求，把自己的 socket_ 投递给 async_accept。
async_accept 返回后， client 就对自己的 socket_ 执行处理， 该 read read，该 write 就 write。
直到这个 client 的请求全部处理完毕，连接也 shutdown 后， 它就再次投递 async_accept 进入下一个循环。

在这个模式下，client 对象并没有被不断的 new 出来。 client 对象的数目是固定的。他利用了 async_accept 可以多次投递的 feature。
在超大量的请求下，该模式始终不会产生频繁的内存分配和释放请求，不仅仅加快了速度，而且也极大的避免了内存碎片。

为了让这个模式调用更少的 new。 beast 定制了内存分配器。
这个定制的内存分配器，每次分配内存只是简单的一次指针移动，而不回收内存。
直到整个连接处理完毕，重置指针完成一次性释放。而这块固定的内存也是随着 client对象最初就已经固定建立了。

也就是说，这个 fast_server 在运行的过程中，除了 asio 内部可能有内存分配外，其他地方没有任何内存分配。如果定制了 asio 的内存分配器，甚至能做到整个运行过程中 0次调用 malloc。运行过程中需要的内存是完全静态分配的。

当然，不动态分配内存，缺点就是，该程序能处理的最大并发数是固定的。但是，即使动态分配内存，最大并发数就一定是无限的吗？
