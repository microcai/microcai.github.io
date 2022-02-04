---
layout: post
title:  Future 和 Promise 的区别
tags:   [Promise, Future, C++]
---

promise 和 yield 的区别是什么？

其实区别大了去了

yield 虽然写异步看起来像同步，爽了。

但是强制了必须等待 io 的模型。

yield async io, 必须 io 完成，你的协程才能进一步执行

和原来同步模式的线程io是一样的。必须 io完成你的线程才能继续。

promise 则不然。 promise 可以在需要等待io结果的地方再 yield，结果出来以前可以执行其他操作

在线程时代，也有一个和 promise 的作用非常类似的东西，就是 future。

future 从未流行过。

promise 之于协程，如 std.future 之于线程。然而 future 不流行，因为同步 IO 的写法已经过时了。
现在是异步的天下。

虽然看起来有点标题党，但是 future 确实就是线程版的Promise. Promise 是为了更的在异步环境里重叠异步操作。
future则试图给同步的线程模型里赛点异步的东西。
这种硬塞就好像你给五菱宏光mini ev 塞五连杆悬挂一样，人家根本就用不上。真用上的，还会买五菱宏光吗？
