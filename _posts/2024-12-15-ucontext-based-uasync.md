---
layout: post
title: 基于 ucontext + iocp4linux 的超简协程库
tags: [c++, cpp, async, IOCP, proactor, ucontext]
---

虽然说，使用 异步最佳的实践是使用协程。

然而 c++20 的协程并不总是可用的。总不能说，不能更新编译器的地方就不配写代码吧。

因此，我在上一篇文章里说道，可以继续忍受回调地狱。或者使用有栈协程。

当然，如果使用 asio ， 那么一切问题都不存在。asio 支持 有栈协程，无栈协程，daff‘s device 协程，还有最基础的，回调模式。
asio 简直就是个“宇宙级” 的异步库。

然而，asio 也并不总是可用。

于是，基于 ucontext 的一个超简协程库就应运而生。

首先，这个不是一个独立的库，他其实顺手带在 uasync 里。作为  universal_fiber.h 头文件提供。

就隐藏在 iocp4linux 的 example 代码里。
见 [echo_server_stackfull.c](https://github.com/microcai/iocp/blob/master/example/echo_server/echo_server_stackfull.c)

没错，这次是个 C 代码。尽管我非常讨厌 C。

这个库，只是为了演示如何将 proactor 和有栈协程给结合起来。虽然我本人建议最好使用 c++20 的协程。但是总有人是升级不了编译器的。
因此我再三思考后，决定还是写一个小 demo 来演示 proactor 和有栈协程 如何极便捷的结合。

对于这么一个简单的 echo server 例子，作为对比，同文件夹下的 echo_server_callback.cpp 就是基于回调的。可以直观感受下，基于回调和基于协程的代码可读性。

# 先看有栈和无栈例子对比

这个是 echo server 左边有栈协程和右边无栈协程的 accept 循环的代码对比
![img](/images/ucontext_code4.png)

不能说毫无差别，简直可以说是一模一样

也就是说有栈和无栈，是只存在底层工作机制的差异

没有使用上的差异。

这就是 universal_fiber.h 和 universal_async.hpp 的威力。

关于那个无栈协程 universal_async.hpp 的分析，参考 [这篇文章](https://microcai.org/2024/12/08/super-lightweight-iocp-coroutine.html)

今天我们分析这个有栈协程库。

正如我前面分析的，观察一个网络库，入口点永远是“事件循环”。一个网络库的事件循环，决定了他的上限。

由于 run_event_loop() 两个库是一模一样的。因此我们分析有差异的 process_overlapped_event。

![img](/images/ucontext_code1.png)

在获取 OVERLAPPED* 对象然后派发他的完成事件时，

OVERLAPPED\*被强转为 FiberOVERLAPPED\* 对象。
然后调用 swapcontext 切换到里面存在的 target 
 就把 overlapped 对象绑定的协程给复活了。

没有其他代码了，异常的简单。

但是，在 swapcontext 的时候，为何要 使用一个 self 对象，然后又把 __current_yield_ctx 指向 self. 完事后，又为何恢复回去呢？
这个 __current_yield_ctx 是一个 全局变量，目的是方便 

![img](/images/ucontext_code2.png)

这个代码里，使用 swapcontext 回到事件循环。


可以看到， universal_fiber.h 的 接口，是和 universal_async.h 的接口几乎是复刻的。

比如 无栈协程版的接口是这样的：
![img](/images/ucontext_code3.png)

除一个是 C++ 语言机制做的无栈协程，另一个是 C语言+底层汇编弄出来的有栈协程。
都说协程，所以用起来是没太大区别的。忽略掉一些语法导致的差异，基本上程序逻辑是毫无差别的。

