---
layout: post
title: 协程切换为什么需要 一个 hook_function 参数.
tags: [c++, cpp, asm, context-switch, coroutine]
---

# 前言

刚刚，我将 zcontext 的 API 进行了以下修正。

从


```c
void* zcontext_swap(zcontext_t* from, zcontext_t* to, void* argument);
```

改成了

```c
typedef void* (*zcontext_swap_hook_function_t)(void*);

void* zcontext_swap(zcontext_t* from, zcontext_t* to, zcontext_swap_hook_function_t hook_function, void* argument);
```

增加了一个 hook_function。这是为何呢？这个 hook_function 又是怎么使用的呢？在什么情况下运行呢？

别着急，我一一道来。

## 需求1：自动进行栈回收

协程需要分配一个新栈。而协程执行完毕的时候，需要对分配的栈内存进行回收。
而协程自身是无法执行这个任务的。协程只有不在运行状态，他的栈才能释放。而他在运行状态下，又如何调用 free 释放自己呢？
free 本身运行也依赖栈。free 不能把自己正在使用的栈给释放了。

因此，这个需求我用了一些比较绕的方法实现了。其实就是让调度器负责回收。这就限制了调度器只能跑在主线程上。
并且调度器（主事件循环）需要和协程的代码进行一定程度的耦合。

但是为了解决内存泄漏，这个耦合也是不得不为之。其实应该有更好的解决方法的。

## 需求2：线程安全的协程切换

在多线程运行调度器的情况下，可能发生协程切换的竞争。具体情况如下：


假设运行2个线程执行 GetQueuedCompletionStatus。姑且称为 主线程A, 主线程B.
为了更好的性能，通常的做法是让线程A负责 accept, 而线程B负责处理客户端连接。如果处理客户端有瓶颈，还可以创建更多的线程处理。
这里先简化为2个线程。

系统运行若干个 Accept 协程。并且在接受一个新连接后，创建一个新的处理协程来处理新的连接。
姑且称是协程A吧。某个协程 A 拿到了一个新连接后，创建一个新的处理协程来处理新的连接。
姑且称这个刚刚创建的新协程为 协程C，这个新接受的连接对应 socket C。

好了，协程A, 接受了一个新连接，然后创建了 协程 C。此时协程 C 和协程 A ，都是在主线程 A 上运行的。

这时，我们要往socket C 上投递 WSARecv 了。此时投递是在 主线程A上进行的。由于 socket C 绑定了线程B的 IO完成端口，因此稍后
会在主线程 B 上获得完成事件。此时协程 C 是在 线程 A 上运行的。调用 WSARecv 后，紧接着就要进行“协程挂起”操作。
正常来说，线程B获得socket C 的完成事件后，就会恢复协程C。于是，协程 C 后续就在 线程 B 上运行了。

这里就发生了一个竞争事件1：就是在线程A上刚刚投递读操作。然后 B 线程马上就获得了完成事件。此时 协程C都还没来得及进行挂起。
这个竞争事件的处理很简单，在线程B上忽略它。因为协程C在进行挂起操作的时候，会先检查 overlapped 是不是已完成。如果是，就不会挂起。因此，如果IO事件完成的太快，
其实还是会在发起的线程里处理后续。

我们主要考虑的是竞争事件2：就是协程C,检查发现事件没有完成，于是就使用 zcontext_swap 将自己换出。
后面线程B获得完成事件通知后，就可以将 overlapped 上存储的 zcontext_t 对象进行幻想。也就是调用 zcontext_swap 切入协程C。
在这里，如果 线程A实际上尚处于 zcontext_swap 将协程C换出的过程中，线程B就调用 zcontext_swap 要切入协程C。

于是竞争发生了，发生了永远无法预测的行为。

### 解决竞争事件2

解决的办法是，在 overlapped 事件上设置2个 标志。一为 IO是否完成，二为 协程是否已挂起。

在获取 IO 结果的代码里，先检查 IO 是否完成。如果完成，则直接返回。如果未完成。则挂起自己。并设置 协程是否已挂起 标志。

而在事件循环里，获取到 OVERLAPPED 对象后，先设置 IO 完成标识。然后检查 协程是否挂起，是则调用 zcontext_swap 唤醒协程。

那么问题就在于，如果任务协程是先设置为 已挂起标志，后调用 zcontext_swap 挂起自身。则可能会存在另一个线程里运行的事件循环会在
协程挂起到一半的情况下要恢复它。

因此，只能是 zcontext_swap 完成后，再设置这个标志。

问题在于，zcontext_swap 完成后，当前线程就运行了另一个协程了，另一个协程也是在 zcontext_swap 这个地方返回的。
协程 A 调用 zcontext_swap 切换到了 协程B。那么协程B 还得沟通下，去把协程A的活给干一下？

这种做法太抽象了。本来不同的协程干的活就是不相干的。现在却要让协程和协程之间还紧密耦合。
那对协程B来说，他 zcontext_swap 返回的时候，上一个运行的协程，可不一定是 协程A, 那协程B是不是要在zcontext_swap的后面，紧跟着写上百八十号代码，
分别处理不同前任的工作？

好吧，也只能这样。好在 zcontext_swap 有一个参数，协程A 调用 zcontext_swap 切换到协程B, 它带了一个参数。这个参数就会变成 协程B 调用zcontext_swap 的返回值。
也就是说，zcontext_swap 确实做到了，获取前任的信息。

因此，在每个 zcontext_swap 的后面，实际上我都会跟上这样的代码：

```c
auto pre_task_info = zcontext_swap(self, target, 0);
if (pre_task_info)
{
    free(pre_task_info);
}
```

是的，这就是之前，我 解决 需求1 的做法。就是让后任处理前任。平时 zcontext_swap 调用传的都是 0. 维度在协程死亡前，它会把自己的栈地址传给 zcontext_swap。
于是后任，就顺利的清理掉了前任。

这个机制还可以继续扩展，增加更多复杂的代码，实现后任为前任处理更多的事情。。。

但是，这意味着每个 zcontext_swap 调用的地方，都要 重复处理前任的代码。

要是这个工作，在 zcontext_swap 内部就处理掉就好了！

# 解决

对啊，zcontext_swap 内部要是能在新协程的上下文里，执行一段代码后再返回到目标协程。那么就可以把解决问题的代码，给保留到本协程的代码里。而不是泄漏的到处都是。

于是，对 需求1 的解决方案变成了这样：

```c

void coroutine_func(coroutine_task *task)
{
    // 调用用户的协程代码.
    task->user_coroutine_function();

    // 转到 next 协程，并释放  task 对象. task 对象被释放的同时也会释放掉本协程的栈.
    zcontext_swap(task->ctx, task->next, free_task, task);

    // 这里不会被运行到, 加个 terminiate 调用
    std::terminate();
}

```

这样， free_task 这样的工作，就不会泄漏到别地方。

而对需求2 的解决方案变成了这样

```c

int wait_overlapped(FiberOVERLAPPED* ov)
{
    // FiberOVERLAPPED 派生自 OVERLAPPED

    ((FiberOVERLAPPED*)arg)->resume_state = 1;

    if (ov->ready)
    {
        return ov->bytes_transfered;
    }

    auto update_overlapped_resume_state = [](void* arg)
    {
        ((FiberOVERLAPPED*)arg)->resume_state = 2;
        return arg;
    };

    zcontext_swap(ov->coro_ctx, g_main_loop_coro, update_overlapped_resume_state, ov);

    return ov->bytes_transfered;
}

```

而主事件循环，则变得不会带上一堆代码处理“前任”了。

```c

int main_loop()
{

    for(;;)
    {
        GetQueuedCompletionStatus(...)

        (FiberOVERLAPPED*)lpOverlapped->ready = 1;

        if ( ((FiberOVERLAPPED*)arg)->resume_state != 0)
        {
            while (2 != ((FiberOVERLAPPED*)lpOverlapped->resume_state))
            {}

            zcontext_swap(g_main_loop_coro, (FiberOVERLAPPED*)lpOverlapped->coro_ctx, 0, 0);
        }

    }

}

```

如此一来，各自的代码都干净起来了。

# 总结

由此可见，如果一个 swap 函数，可以多接受一个参数，用来在刚刚切换完栈后干一些扫尾工作，则可以极大的简化使用者的代码结构。

微软的 SwitchToFiber 看起来就一个参数，非常简单。实则让协程相互之间缺乏关联。于是很多东西得靠全局变量+协程本地存储来做。
ucontext 和 微软的Fiber没有特别差异。

Boost.Context 里带的名为 fcontext_t 的接口，则多了一个切换的时候相互传的参数。最初 zcontext 就是模仿的 fcontext。
准确的来说，是我先实现了 zcontext ，然后去研究 fcontext, 发现英雄所见略同的和 fcontext 在设计理念上撞车了。

> 在十天前我在 [这篇](https://microcai.org/2024/12/18/why-boost-fcontext-is-fast.html) 文章里，就提到我先写了
个 zcontext 然后发现和 fcontext 如出一辙。

现在，我更进一步，把 zcontext 升级了，zcontext 将是最好的 有栈协程上下文切换API.

注意，我说，这是“有栈协程上下文切换API”，而不是有栈协程本身。

因为，一个**有栈协程**，必须得和 异步 IO 搭配起来。
也就是说，一个**有栈协程上下文切换API** + 利用这个API封装的一个异步IO库，才等于**协程库**。

事实上 iocp 这个库里带的 universal_fiber.hpp，就是个协程库。而 zcontext 是它支持的 众多 上下文切换API 中的一个。使用不同的上下文切换API, 自然有不同的一些做法配合。

在众多的切换api里，最好用的是 zcontext，其次是 fcontext ，然后是 Fiber 。 最差的是 ucontext。

