---
layout: post
title: 真正的重叠IO
tags: [c++, cpp, async, overlaped]
---

不知有没有人想过，为何微软将windows 的异步API称为“重叠IO”而不是异步IO。

在我看来，重叠IO和异步IO的区别，主要在于发起IO后的动作。

重叠IO, 发起 IO 后，继续执行应用层的逻辑。应用可以选择在任何何时的地点再选择同步（阻塞等待 or 异步等待）IO的结果。
异步IO, 发起 IO 后，立即挂起当前业务逻辑（也就是立即非阻塞等待 IO 结果），回到事件循环，以便执行其他业务逻辑。

放到协程的设计角度，重叠 IO 相当于这样使用

```js

async function do_read()
{
    let read_promise = file.read(...);

    ... 干点不依赖 IO 结果的事情

    let read_result = await read_promise;
    ... 干需要 IO 操作结果的事情
}

```


而异步 IO, 则是这样使用

```c

awaitable<void> function do_read()
{
    auto read_result = co_await file.async_read(...);

    // do other logic.
}

```

可以看出来，重叠 IO 在发出 IO 操作后，可以继续执行其他逻辑。只有当确实需要数据的时候，再进行等待。
而异步IO模式下，发出IO后，必须立即挂起当前协程等待IO完成。

那么，这两种差异，对现实中的程序有什么影响呢？

我们先考虑一个最简单的应用： 静态 web 服务器。

在静态web服务器里，最核心的处理逻辑，就是找到用户要下载的文件，然后将文件发送给客户端。伪代码如下

```c++

awaitable<int> handle_send_file(auto target, auto socket)
{
    char buffer[65536];

    fs::file f(target, flags::binary|flags::open);

    long total = 0;

    for(;;)
    {
        auto read_size = co_await f.async_read_some(buffer);
        if (read_size == 0)
            break;
        total += co_await socket.async_write_some(buffer, read_size);
    }

    co_return total;
}


```

在这个代码里，主要的逻辑就是 循环读取文件，然后发送。

看起来似乎好像逻辑很清洗明了。

但是实际上这个逻辑是错误的。

因为这会导致 “磁盘读取” 和 “网络发送” 两个操作交替进行。二者无法同时进行，导致各自的 IO 利用率只有一半。

这其实就是 异步IO带来的问题。要解决这个问题，得使用 重叠IO. 我们看下重叠 IO 是如何操作的：


```js

async function handle_send_file(target, socket)
{
    let file = await fs::open(target);

    let buf1 = new Buffer(65526);
    let buf2 = new Buffer(65526);
    let buf[] = {buf1, buf2};

    let read_size = await file.read(buf[0]);
    let cur_buf = 0;
    let next_buf = 1;
    let total_write = 0;

    for(;read_size;)
    {
        let send_promise = socket.send(buf[cur_buf], read_size);
        let read_next_buffer_promise = file.read(buf[next_buf]);

        [ send_bytes , read_size ] =  await Promise.all([send_promise, read_next_buffer_promise]);
        total_write += send_bytes;
        if (read_size == 0)
            break;
        swap(cur_buf, next_buf);
    }

    return total_write;

}

```

在重叠IO模式下，网络发送和磁盘读取会同时进行。充分挖掘 IO 的潜力。绝对不浪费 IO 吞吐量。

那么，如果已经使用了 c++ 协程，要怎么才能做到 重叠 IO 呢？

由于 c++ 协程的设计缺陷，c++ 协程只有在被 co_await 的时候，才真正开始执行。而不是创建的时候执行。

> 为防止杠精说，c++ 协程通过设置 initual_suspend 也能实现 创建的时候开始执行。问题是，作为一个 协程IO库，你的操作
> 系统底层是使用的“事件通知”+回调函数实现的。因此必须获得当前协程的睡眠句柄，才能进行在回调处理里唤醒协程这样的操作。
> 而当前协程的句柄，就必须得通过 co_await 调用才能拿到。也就是说，如果在没拿到协程句柄的情况下，就发起 IO 操作，
> 就要实现复杂的 “稍后获得协程句柄后提交给已经挂入系统IO回调列队的回调函数” 逻辑。这个逻辑非常难以编写。并且有潜在的
> 并发和数据竞争问题。

因此，c++协程，其实真正模拟出来的编程模型，是 “用户调度的线程 + 非阻塞IO”。发起 IO 操作，协程框架就得 挂起当前的用户态线程（**协程**），然后调度别的用户态线程执行。

这意味着，并发的IO操作，就必须靠 多协程（多个用户态线程）实现。

所以，使用 c++ 协程实现发送文件的逻辑，需要创建一个读取和一个写入协程，并且中间使用一个支持协程的消息列队传递数据。
如此编写，才能实现 读写的并发（也就是重叠）。

```c++

awaitable<int> send_coro(auto& socket, auto& buffer_queue)
{
    long total_write = 0 ;

    for (;;)
    {
        auto buffer = co_await buffer_queue.async_read();
        if (buffer.size == 0)
            break;
        total_write += co_await socket.async_write_some(buffer.data, buffer.size);
    }

    co_return total_write;
}

awaitable<int> read_coro(auto file, auto& buffer_queue)
{
    long total_read = 0;

    std::array<char, 65536> buffer[2];
    int cur_buf = -1;

    for (;;)
    {
        cur_buf = (cur_buf + 1 )%2;
        auto read_size = co_await file.async_read(buffer[cur_buf]);
        total_read += read_size;

        // 列队长度只有1, 多了就会阻塞，而如果 是空列队，就不会阻塞。立即返回
        // 从而马上开始下一个 buffer 的读取
        co_await buffer_queue.async_write( { buffer[cur_buf].data(), read_size } );
        if (read_size == 0)
            break;
    }

    co_return total_read;
}

awaitable<int> handle_send_file(auto target, auto socket)
{
    // queue size = 1
    // 意思是空列队的 投递会立即成功。否则等待消费者
    coro_queue buffer_queue{1};

    // 打开文件
    fs::file f(target, flags::binary|flags::open);

    // 额外创建一个读取的协程
    create_task_detached(read_coro(file, buffer_queue) );
    // 使用本协程直接执行写协程
    co_return co_await send_coro(file, buffer_queue);
}

```

对 asio 来说，幸好 asio 提供了这个 支持 协程读写的消息列队，而且可以限制列队长度为1。
对 c++ 协程这种不支持重叠IO的模式来说，要跑满 IO 就必须得开2个协程，一读一写。其实同步IO也是一样的，要跑2个线程，一读一写。
好在协程创建的开销远低于线程。协程列队的开销也低于线程使用的异步队列。
但是，都不如不需要列队的重叠IO来的更好。
