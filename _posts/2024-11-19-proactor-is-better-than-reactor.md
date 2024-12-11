---
layout: post
title: 重叠IO（proactor）是最理想的IO模型
tags: [c++, cpp, async, overlaped, proactor, reactor]
---
reactor 和 proactor ， 这种毫无联系的英文专用名词，很容易把人弄晕。

回归正途，使用精确的汉语描述，而非翻译，则正确的说法是：

多路复用IO 和 重叠 IO 模式。

所谓多路复用，顾名思义，就是好几个IO复用。。。 复用了谁？复用了线程。
它对比的是最传统的UNIX网络编程： 一个连接一个线程。并发就要开多线程。连接多了，线程就多，系统压力非常大。
而多路复用，则可以让一个线程处理多个连接。这就是复用的含义。为了实现复用，首先IO是非阻塞的。因为如果阻塞了线程，其他连接上的数据不就没法处理了么。既然非阻塞，那就会出现网络数据没准备好，就一直返回 EAGAIN 错误。一直返回难道一直重试吗？显然不现实。所以就有了一个 多路复用器。这个多路复用器最早是 select() 调用。后来是 poll() 最后是 epoll().
而重叠IO,顾名思义，就是 IO 操作是重叠的。和什么重叠？当然是和你当前的线程是重叠的。
也就是，向系统提交一个 IO 操作， 系统就会在“后台”默默的干苦力，当前线程可以立即执行其他任务。不会被阻塞。他和多路复用模式的区别是，多路复用模式，如果会阻塞，内核就返回会阻塞，而不是在后台默默干活。而 重叠IO 则即不会阻塞，也不会返回“请重试”。而是在后台开始默默的进行处理。这个IO的处理，和你程序本身的逻辑，是重叠进行的。所以叫重叠IO。

话又说回来了，系统是在后台干活了，你得知道他啥时候干好了吧？总不能两眼一摸黑，不知道了吧。
因此，系统需要一个通知机制。Linux 这边，曾经有一种叫 AIO 的东西，它用 “信号” 来通知 IO 完成了。而如今 Linux 使用 io_uring 的 无锁列队 来完成通知。而 windows 则使用 一个叫“完成队列”的东西来通知，当然也可以使用 窗口消息来通知结果。

不管是 win 的窗口消息，还是linux的 AIO ，在实践中都被人抛弃不用了。因此不讨论这些。

我们讨论 IO完成端口，和 io_uring, 他们本质上是一样的，就是提供一个异步队列，然后应用层可以使用 一个或多个线程，去读取这个队列获得完成通知。每一个IO操作，都对应一个完成通知。
因此，重叠IO模式，其实和传统的编程思路是一致的：每调用一个函数，就获得一个返回值。
无非是，这个返回不是通过 ret 指令返回，返回结果也不是通过 EAX 寄存器返回。
而是存放到了一个消息队列里。

但是，操作请求和结果返回，是一一对应的。这是一种非常自然的概念。
自然而然的，在编程上，就可以设计为 IO发起 + 完成回调。
库的作用，就是封装 系统的 IO api ，然后将 IO完成消息转化为 完成回调。
有了 IO发起+完成回调。很自然的，程序就可以组织为一种 协程结构。 发起IO操作，返回一个 promise . IO完成就是让 promise 完成状态。
想同步IO结果，只要 await 这个 promise 就可以了。
非常的容易理解，而且封装起来也非常的轻松。用起来简直就是爽到high起。

所以，重叠IO 是一种更优秀的编程模型，就不言而喻了。