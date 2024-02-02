---
layout: post
title: 单片机也能支持 co_await 协程啦
tags: [co_await, mcu]
---

# 序

在 [这篇文章](/2023/12/08/cooperative-multitasking-in-mcu.html) 里，我为单片机编写了一个简单的 executor。
然后利用这简单的 executor, 再搭配 Duff's device 就用上了 stackless coroutine 了。

但是，Duff's device 也有其缺陷。最明显的就是，在 ASIO_CORO_REENTER(this){ xx } 的函数体里，无法定义变量，也无法使用 switch 指令。

这挺让人头疼的。

于是，我迫切的需要一个有栈的协程。 c++23 里带的coroutine就不错。

最初的计划是移植 asio。
但是 asio 不知为何，在 arm-gcc 上遇到了诡异的语法错误。

遂放弃。直到最近，突然又想起来这件事。

然后又开始琢磨怎么写一个 awaitable。
但是实在是毫无头绪。于是准备抄一个库。

然后找到了阿里巴巴开源的 [async_simple](https://github.com/alibaba/async_simple) 库。
经过了一定的裁剪后，跑起来了。

# 阿里的代码不和谐

首先，阿里的这个协程库，我是扣了代码的。把不需要的东西都删了。但是也没有完全删干净。还有不少遗留的垃圾。
这就让本就捉襟见肘的单片机存储空间更局促了。

其次，阿里的这个代码虽然已经比 asio 的简化了很多，但是还是弯弯绕绕非常多，非常不利于分析。

所以，在[哥们](https://www.jackarain.org/) 的帮助下，整了一个更简化的[版本](https://github.com/microcai/mcu_coro_demo/tree/master/lib/mcu_coro).

正如 这个仓库里的 例子那样，使用这个协程的方法很简单，首先，需要在 `loop()` 里调用 `mcucoro::executor::system_executor().poll();`

然后，这么定义协程

```c++
mcucoro::awaitable<void> led_blinker()
{
 for(;;)
 {
  LL_GPIO_TogglePin(GPIOB, GPIO_PIN_14);
  co_await coro_delay_ms(1240);
 }
}
```

协程的返回值得是 `mcucoro::awaitable<void>` 类型，

然后使用

```cpp
mcucoro::post([](){led_blinker().get();});
```
来启动协程即可。


# 总结

有了 co_await 协程，编写 mcu 代码是如虎添翼。