---
layout: post
title: 微软不会起名
tags: [c++, coroutine]
---

微软不会起名，而且名字还具有极大的误导性。

先说类名：

首先，微软的协程原作者，他总是用 `Task<>` 来命名一个协程函数。但是这就是他犯的第一个错误。
因为只有 await 构成的一系列调用，那条调用链才是一个 “任务”。 也就是 asio 作者所说的 co_spawn. 只有被 spawn 出来的协程，才叫一个任务。而被 await 的函数，不能叫任务，而是”可异步等待返回的函数“。 因此 asio 作者使用 `asio::awaitable<>` 来命名，而不是 `task<>` 是十分妥帖的。

接着是 promise_type ，这个微软就是纯粹的瞎搞了。不同于 Task<> 只是出现在微软的示例代码里，promise_type 可是直接进了标准。这瞎命名带来的恶劣影响要大的多。为啥说这个不能是 promise_type 呢？ 因为这个对象存储的是 协程状态。因此 asio 使用 coro_frame 来命名，显然要更正确的。它存储的就是当前协程帧的状态数据。

最后是 final_suspend ，这个类名简直就是严重误导性的集大成者。他干的活和 suspend 毫无关系。实际上他干的恰恰不是 suspend 的活，而是 “恢复调用者” 。协程作为可等待函数，他的调用者调用了一个协程后，调用者才是真正的被 suspend 了。被调用者是执行中。处于 running 状态。当被调用者完成工作，他要 恢复 调用者，让调用者醒来继续干活。

因此， final_suspend 其实应该叫 resume_caller .

接着说 三件套函数名：

await_suspend 其实不是 挂起。协程 A 调用 协程 B, 实际上是 A 被挂起。可是代码上却是 调用 B 的 await_suspend 。这简直就是极大的误导性。当 B 对象的 await_suspend 被调用的时候，实际上恰恰是 B 被 “恢复”， B 进入了 running 状态。这个地方准确的命名，应该叫 await_setup.

await_resume 实际上不是继续。协程 B 返回给 协程 A 的时候，实际上是 协程B 完工了。恢复的其实是 A. 但是恢复 A ，调用的却是 B 的 await_resume , 这简直就是胡扯一样的名字。 应该叫 await_result ，拿到 await 结果了。

await_ready 意思其实是反过来的。而且具有极大的误导性。实际上这个 await_ready 的存在价值为 0 。 毫无意义。

还有存在于 promise_type 里的 三件套函数名：

initial_suspend/final_suspend 设计简直就是毒瘤。更正确的设计，应该是把这种东西和 awaitable 放一起。promise_type， 或者说 coro_frame , 就单纯的作为一个 “数据存储” 对象。不要携带干活的代码。虽然 c++ 的对象是数据+代码。但是这个 数据上捆绑的代码，更多的是为了实现 RAII ，而不是真的乱来，随便给代码找个对象安上。

initial_suspend 的活，应该提到 await_setup 里合并工作。 final_suspend 改到 awaitable::await_done 里完成恢复。