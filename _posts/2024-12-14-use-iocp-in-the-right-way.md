---
layout: post
title: 深入异步IO 第二篇： 正确使用 IOCP，正确设计 proactor
tags: [c++, cpp, async, IOCP, proactor]
---

# 前言

干了那么多年码农，遇到 IO 从来都是写异步代码。从最初直面裸 epoll 写，到后来基本上依赖 asio 写。
最近研究 io_uring 后，试着用 io_uring 把 IOCP 那套 API 实现了。

以前呆在 asio 的舒适区，根本没关注过其他程序员对异步的理解。但是 windows 程序员是最多的，当我研究IOCP的时候，
以前被我忽略掉的那群写 IOCP 的程序员，突然进入了我的视线。

当我研究了他们对异步的一些吐槽后，才发现了一个真相：大部程序员并不懂异步。

尤其是，我由于不熟悉 IOCP，故而为了给 iocp4linux 找测试用例，而翻遍网络，寻找使用 IOCP 写成的一些网络代码示例。
能跑通它们，才算 iocp4linux 功能完成了。对吧。

结果，大部分 IOCP 的例子，虽然能跑。但是我研究了他们的代码后发现，统统都是错误的。完全没有领会到异步IO的精髓。根本就
没有真正的理解异步IO。

所以，我打算写数篇最深入剖析异步IO的引导文章，足够教会大家 真正的异步思维。

# Reactor 和 Proactor

ACE 作者当年提出了数个高性能网络IO的模型，其中将这些模型总结为 Reacto 和 Proactor。如果按字母意思翻译，
则称为 反应器 和前摄器。

但是，我更愿意使用更精准的汉语表达：多路复用模式 和 重叠IO模式。

## 多路复用模式

前一篇文章说道，要想实现单线程并发IO, 内核必须要提供的2个机制。在 多路复用模式下，要求的机制就是

**可读写状态通知** 和 **无阻塞IO操作**。

- **无阻塞IO操作** 要求内核在IO不能立即完成的情况下，不能挂起调用线程，而是返回错误。但是此时代码不应该进入无限重试，而是等待内核的通知。

- **可读写状态通知** 如果一个 IO 操作接下来可以无阻塞立即执行，则通知程序，现在可以干活而不会失败了。

比如我写一个 server，调用 read() 读取客户端发送的数据。如果客户端还未发送数据。则内核会挂起线程直到对方发送数据。然后 read 就执行成功并返回了。

这种阻塞的 IO 就要求服务端程序要创建大量的线程。每个线程服务一个客户端。而如果使用了多路复用模式。则 内核只会在某个 socket 上收到了数据的时候，才通过多路复用器的接口通知。然后应用程序再执行 read 调用，则可以 100% 立即执行成功，无需挂起。

过去，内核只能一次性通知 1024 个 socket 的可读可写状态。此接口就是传统的 select。
这意味着如果有超过 1024 个客户端，服务端就要创建线程。每个线程服务只1024个客户端。

为了剔除这个限制，后来有了理论无限个的 poll() 接口。
但是 poll 接口存在每次调用都要传递个大数组的问题。虽然破除了 select 1024 个的限制，但是性能反而下降了。*不然你以为当年为啥 select 使用 1024 固定长度的数组？ 还不是长了性能下降厉害*

于是，最终内核提供了 epoll 接口。

但是 select/poll/epoll 本质上是一回事。就是要求内核监控 哪些 socket 上有数据了。此时有数据的 socket 就可以 调用 read 而不阻塞。同时也监控哪些 socket 的发送缓冲区空了。此时调用 write 就可以立即成功而不阻塞。不同的接口，无非是对于“要监控哪些socket”这个信息，使用不同的方式告诉内核。

所以， select/poll/epoll 乃至 BSD 上的 kqueue, 都是一种东西，就是 IO多路复用器。

因此，对于 reactor 模型，程序的任务调度结构是这样的：

```c++

void event_loop()
{
    for(;;)
    {
        auto events = poll_events();

        for (auto ev :events)
        {
            if (ev.event & READABLE)
            {
                //调用无阻塞读取.
                read(ev.fd, buf);
                // 调用事件绑定对象的 on_read 回调
                ev.obj->on_read(buf);
            }
            if (ev.event & WRITEABLE)
            {
                // 发送绑定对象的待发送数据
                auto write_data = ev.obj->write_bufs.pop();
                write(ev.fd, write_data);
                if (ov.obj->write_bufs.empty())
                {
                    // 无待发送数据，取消 可写监控
                    remove_write_poll(ev.fd);
                }
            }
        }
    }
}

````

注意到 reactor 模型的特点了没？

事件循环，除了 获取事件，派发事件，还要负责 IO！
虽然说无阻塞IO不会导致阻塞。基本上就相当于把内核里的数据拷贝到用户空间。
但是事情多了，这大量的拷贝也是相当的耗时的。

这还不是主要问题，毕竟这个IO如果真那么费时，可以通过使用独立的 “IO线程” 执行。

最重要的是，在写入上。

发现了一个重点没？reactor模型下，网络库自身需要维护一个“发送缓冲区”。

这就导致了一个现象： 相当一部分reactor模型的网络库，其 ”发送“ 操作是没有返回值的。

这种现象，可不单单存在于一些初学者写的网络库里。连大名鼎鼎的 libuv, 被 nodejs 所使用的 网络库，
他的 uv_write 也是没有返回值的。 发送数据约等于石沉大海。

这就是当年很多人批评  TCP 协议其实一点也不可靠的由来。

但是，在 reactor 模型下， 发送如何有返回值呢？
毕竟发送是异步的，有返回值岂不是得同步发？

有了，改以下发送的代码。这么写：

```c++

if (ev.event & WRITEABLE)
{
    // 发送绑定对象的待发送数据
    auto write_data = ev.obj->write_bufs.pop();
    int number_of_bytes_written = write(ev.fd, write_data.data);
    // 调用发送完成回调.
    write_data.cb(number_of_bytes_written);
    if (ov.obj->write_bufs.empty())
    {
        // 无待发送数据，取消 可写监控
        remove_write_poll(ev.fd);
    }
}

```

加个回调嘛。问题解决。

==， 好像哪里不对劲。。

虽然 使用的 reactor 模式的操作系统 API, 但是这意味着库的用户面对的接口是这样的

socket.async_write(buffer, callback);

这，一个 IO发起，然后一个回调通知，这 它娘的不是 proactor 模型嘛？？？？？

所以说，为了正确的实现网络库，最终都会走向 proactor。

reactor 实际上就是一种拍脑袋想出来的残废模型。

既然写入操作需要一个IO发起，一个完成回调。那么读取操作呢？

比如我调用一个 RPC 接口，发送一个调用请求，然后等待读取一个请求返回。这是非常自然的程序逻辑。

然而在 on_read 模式下，事情就变了。因为 on_read 是处于“无时不刻，随时待发”状态的。意味着
on_read 会在任何意想不到的时间被调用。。

甚至当你调用多个不同的 RPC 接口，则 on_read 要处理的逻辑就会无限增长。

是的， on_read 模式，仅仅是让 reactor 网络库的 事件循环，看起来简单的点。然而却极大的增加了业务代码的处理复杂度。
业务代码需要处理 on_read “随时被调用” 这么一个情况。编写一个这样的 回调，其难度不亚于编写操作系统的中断处理函数。

同时也要注意到， on_read 是在 事件循环中被调用的。而那个 on_read 是在一个 大的 for 循环里，对 “每一个收到数据包的 socket 都要调用“。 这导致如果 on_read 回调本身耗时过长，会导致其他待处理的连接处于 ”饥饿“ 状态。

所以，既然 发送 操作已经变成 proactor 模型，为何继续守着 on_read 模式呢？

很自然的，读取也可以使用一个 发起+一个回调的方式。

然后你会豁然开朗。发现异步编程原来如此轻松！

# 重叠IO模式

相信在上一个小节里，大家已经完全接受了 发送操作使用 发起+回调 的模式。为何对读取，也必须使用发起+回调的模式呢？

当理论不够明朗的时候，就进行案例分析。

首先，我们思考一个典型的 proxy 逻辑： 把 socket A 收到的数据，发给 socket B。 把 socket B 收到的数据，发给 socket A。同时干的叫双向代理，只干一个方向的是单向代理。两个方向都干，但是同一时间只能激活一个方向的，叫半双工代理。比如 HTTP 代理就是个典型的半双工代理。而 websocket 代理就是双向代理。

正如上一篇文章里所言，遇事不决，先用同步IO。

如果使用同步 IO, 则每个方向各需要一个线程。代码里只要写一份，运行的时候两个参数对调创建2个线程即可。
所以我们看一个方向的线程代码如何处理：


```c++

int splice_socket(int socketA, int socketB)
{
    int total_write = 0;
    char buffer[BUF_SIZE];

    for (;;)
    {
        int readsize = read(socketA, buffer, BUF_SIZE);
        if (readsize == 0)
            return total_write;
        int write_size = write(socketB, buffer, readsize);
        if (write_size >0)
            total_write += write_size;
        else
            return total_write;
    }
}

```


如果直接使用 proactor 模式的代码，则会陷入回调地狱：

忽略后面 total_write 和 buffer 参数，那是用来做“状态保存的” 一种简易闭包技巧。

```c++
void splice_socket(int socketA, int socketB, callback_t callback,
    int total_write = 0, std::shared_ptr<char> buffer = new char[BUF_SIZE])
{
    // 读
    async_read(socketA, buffer.get(), BUF_SIZE, [=](auto readsize)
    {
        if (readsize == 0)
        {
            // 完成
            callback(total_write);
            return;
        }

        // 写
        async_write(socketB, buffer.get(), [=](auto write_size)
        {
            if (write_size >0)
            {
                total_write += write_size;

                // 继续投递自身，实现 循环
                // 注意此时补全的2个参数。
                splice_socket(socketA, socketB, callback, total_write, buffer);
                return;
            }
            else
            {
                // 完成
                callback(total_write);
                return;
            }

        });


    });
}

```

代码量明显的就比 同步模式增加了。
但是带来的优势就是无需创建线程了。系统资源的占用就少了。
这对需要代理大量连接的服务器来说，节约系统资源就是节约票子。

但是，有没有简单的方法呢？ 有啊！上协程！

```c++

coro_task<int> splice_socket(int socketA, int socketB)
{
    int total_write = 0;
    char buffer[BUF_SIZE];

    for (;;)
    {
        int readsize = co_await async_read(socketA, buffer, BUF_SIZE);
        if (readsize == 0)
            co_return total_write;
        int write_size = co_await async_write(socketB, buffer, readsize);
        if (write_size >0)
            total_write += write_size;
        else
            co_return total_write;
    }
}

```

哇塞～！ 和同步的代码一模一样有木有？除了增加的  co_await 关键字，还有使用 async_read/async_write 这种协程版本的 API.

整个程序的逻辑是如此顺畅。基于回调的代码瞬间不香了！！！

后面我会讲，为啥协程要求底层库必须为 proactor 。

现在讲下，为何 reactor 很难写好 proxy。

首先，因为 传统的 reactor 的 发送操作是没有返回值的。
因此 proxy 对收到的数据，会无脑发送。而不管对端是不是已经网络拥塞收不过来了。
在极端情况下， socketA 以每秒 100M/s 的速度接收数据， 而 socketB 只能以 1MB/s 的速度发送数据，这就会导致 proxy 服务器内存爆炸。

所以，任何正确的 reactor ，其发送代码也必须，只能，是 proactor 的。

那么，为何，on_read 模式无法用于编写 proxy 呢？

还是在内存使用上。

由于 on_read 模式下，读取是无条件的。哪怕 接收到数据后，使用了 proactor 的模式发送，on_read 仍然是不断的接收数据。
而发送不出去的数据只能堆积在 proxy 的内存里。最终内存爆炸。

因此，on_read 必须“有条件的调用”。

所谓 有条件的 on_read , 不就是当代码调用一次 async_read , 才会有一次读取的回调吗？

这不就是 proactor？？

这，读取也得 proactor 化啊！！！！

现在明白了吧？ reactor 模式下，根本无法实现正确的应用逻辑。

因此，正确实现的网络库，必须，也只能是 proactor 模型的。

有人问，那我不是写 proxy ， on_read 是不是就能用了呢？

## 处理粘包

要回答这个问题，就请回忆一下，在网络编程领域一个非常热门的话题，如何处理粘包。

处理粘包在通信协议上的手段
无非2种：

    1. 文本协议使用 换行为包结束标志
    2. 二进制协议使用  长度+数据 的方式定义一个包

剩下的都是这2种的变体，就不赘述。

先拿简单的二进制来讲，如果简单的都无非处理，那么难的就更麻烦了。

在 同步IO 和 proactor 模型里，处理粘包都是非常简单的。先读取包头。然后读取剩余部分

```c++

int read_a_packet(int fd, char* buffer)
{
    // 本代码忽略错误处理。只暂时逻辑.
    int pkt_size = 0;
    read(fd, &pkt_size, sizeof(int));
    int read_size = 0;
    do{
        int read_ret = read(fd, buffer + read_size, pkt_size - read_size);
        read_size += read_ret;
    }while(read_size < pkt_size);
    return pkt_size;
}

```

而异步，则只需要将  read 换成  co_await async_read ，其他的逻辑是完全一致的。


那么，在 reactor 模型下，要怎么在 on_read 里处理粘包呢？？？

```c
void on_read(char* buffer, int size)
{
    // 这个 buffer 如果 同时包含 了 上一个包的一部分， 和下一个包的一部分
    // 要如何高效，正确的，将 粘包给 摘 出来呢？？？？？

    // 只处理了粘包还不够，还得处理业务逻辑，又要怎么把业务逻辑塞进 on_read 里
    // 还保持代码的可读性和可维护性呢？
}
```


是不是突然脑子给干烧了。在同步IO和 proactor 异步的模式下，异常简单的代码，到了 on_read 下居然开始举步维艰。

## 协程的底层必须是 proactor

好了，回答前面几个小节的时候的一个问题，为何一定要使用 proactor 模型才能使用协程。

注意到我前面举的几个例子了吗？

协程版和同步IO版本，是使用相同的代码逻辑。只是在调用 IO 操作的地方，需要使用 co_await 关键字，同时需要调用和同步版本**功能等价**的协程版本。

这意味着，协程要求当 api 完成 （指 co_await 返回了一个返回值）的时候，数据是已经“读取完毕”了的。

也就是说， co_await IO发起（）， 意思就是 发起一个 IO 然后挂起协程，并在 IO完成回调里，将协程恢复。

看，协程库要求底层库，必须是 发起IO+完成回调 这种形式的。
也就是，必须是 proactor。

## 编译器不支持协程怎么办？ reactor 会更好吗？

前面说过， reactor 实际上更本无法编写逻辑正确的代码，或者代价极大。

所以，从“正确性”的角度而言，proactor 是必需品。如果协程不可用，则可以考虑替代方案

  1. 老老实实处理回调地狱

  2. 使用有栈协程


实际上，上一篇文章里就讲过，线程就是内核调度的 有栈协程。

能用线程的语言，都能使用有栈协程。有栈协程无非是在用户代码的层面进行调度，而不是操作系统来调度。



