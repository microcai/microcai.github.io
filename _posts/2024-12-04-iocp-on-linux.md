---
layout: post
title: IOCP 移植到Linux上
tags: [c++, cpp, async, iouring, io_uring, IOCP]
---

# 序

windows 高性能IO使用的是 proactor 模型，而古代 Linux 上则是 reactor 模型。

因此跨平台的网络库，通常会选择实现为其中一种模型，然后在另一个平台上使用模拟。
比如 asio 使用 proactor 模型。Linux 上使用 epoll 模拟。
又比如 libevent 使用 reactor 模型， windows 上使用 iocp 模拟。

而将 iocp 模拟为 epoll 的库，就是 [wepoll](https://github.com/piscisaureus/wepoll) 了。

但是，reactor 比较是一种比较落后的模型。因此，进行跨平台封装为 proactor 实际上是更先进的做法。

虽然已经有 asio 这种 proactor 库了，但是毕竟 asio 是一个比较重量级的库。一种轻量级的 proactor 库
也是非常有市场的。

更何况，既然有 wepoll 这种把 Linux api 弄到 windows 上的库，那没有 Linux IOCP 就说不过去了。

于是我决定，开发一个 Linux 版的 IOCP 库。这样方便使用 IOCP 开发的各种软件可以方便的迁移到 Linux 平台。而无需重写。

# 如何实现呢？

如果是在很久以前，这件事其实还是比较复杂的。然而，嘿嘿。从 linux 5.1 开始，一个崭新的名为 io_uring 的系统接口诞生了。

io_uring 实现的模型，恰恰就是 proactor。

于是, 用 io_uring 实现 IOCP 就大幅简化了。

IOCP 的核心，是一个利用 `GetQueuedCompletionStatus` 驱动的事件处理。`GetQueuedCompletionStatus` 从 内核获取完成事件，
并派发完成事件到对应的处理代码。
而使用 io_uring 的程序员，恰恰也是同一个逻辑，使用 io_uring_wait_cqe 等待并获取完成事件，然后派发完成事件到对应的处理代码。

初始化则有 `CreateIoCompletionPort`， 而 同样 io_uring 这边的初始化是用的 `io_uring_init_queue`


| IOCP 接口    | io_uring 对应 |
| -------- | ------- |
| GetQueuedCompletionStatus  | io_uring_wait_cqe    |
| CreateIoCompletionPort | io_uring_queue_init    |
| WSAOVERLAPPED* | io_uring_sqe_set_data    |
| WSASend    |  io_uring_prep_sendmsg  |
| WSARecv    |  io_uring_prep_recvmsg  |
| AcceptEx   |  io_uring_prep_accept  |
| PostQueuedCompletionStatus   |  io_uring_prep_msg_ring  |
|ReadFile | io_uring_prep_readv |
|WriteFile | io_uring_prep_writev |


IOCP 的接口， io_uring 都有完美对应的实现。

# 核心实现逻辑

分2部分。其一为 列队的维护，其二为 IO 的发起操作。

对应 IO 的发起操作，比如 WSASend 可以映射为 io_uring_prep_sendmsg + io_uring_submit

实现起来非常简单。主要就是个工作量问题。不用动脑子。

列队维护，则需要考虑的就是，如何将 WSAOVERLAPPED* 和 io_uring 的完成机制给绑定起来。

基本的逻辑是，构造一个 io_uring_operation 结构，内部存储一个 WSAOVERLAPPED* 指针。

io_uring_operation 每次发起 IO 操作的时候分配出来。并使用 io_uring_sqe_set_data 绑定到当前 IO操作上。

在 io_uring_wait_cqe 获取到完成事件后，使用 io_uring_cqe_get_data 取回 `io_uring_operation*`

然后就可以把其中存储的 WSAOVERLAPPED* 返回给 GetQueuedCompletionStatus 的调用者。

使用 io_uring_operation 结构体而不是直接把 WSAOVERLAPPED* 赋值给 io_uring_sqe_set_data 的原因是，
一些 IO 操作需要“绑定”一些上下文，这些额外的上下文就可以放到 io_uring_operation 里一起绑定起来。比如 io_uring 进行 IO 时常需要的 struct iovec 对象。


# 源码

[iocp4linux](https://github.com/microcai/iocp)


