---
layout: post
title: 模板的模板
tags: [template, c++]
---

在编写 ucoro 的时候，曾经对一个模板类的成员函数犯难了。那就是等待器三件套之一的 await_suspend 函数。

我为`template<typename T> class awaitable` 的三件套使用这样一个模板签名

```c++
template<typename PromiseType>
auto await_suspend(std::coroutine_handle<PromiseType> h);
```

其中，这个 PromiseType 必须得是 `awaitable<T>::promise_type` (也就是 `awaitable_promise<T>` ) 的其中一个实例。

按前C++ 时代的做法，这个成员函数应该这么写

```c++
template<typename Any>
auto await_suspend(std::coroutine_handle<awaitable_promise<Any>> h);
```

这种写法，可以保证接收到的 h 参数，其 Promise 类型必然是 awaitable_promise 的一个参数化实例。

但是，与此同时，我还希望要为 std::coroutine_handle<void> 这样的通用参数写一个单独的处理代码。

于是，使用按前C++ 时代的做法，我需要写2个 await_suspend， 他们分别是

```c++
template<typename Any>
auto await_suspend(std::coroutine_handle<awaitable_promise<Any>> h);

auto await_suspend(std::coroutine_handle<> h);
```

对这两个类型的 promise handle, 各自有一套不同的处理代码。

但是，老王提出了不同意见。他认为，std::coroutine_handle 在标准库里，就一种表示方式，那就是
```c++
template<typename PromiseType>
class std::coroutine_handle;
```

他批评我说，```std::coroutine_handle<awaitable_promise<Any>>``` 这样的写法不直观。而且还写了两个 await_suspend
到底哪个在干活，得多费脑细胞。

后来，函数签名恢复成了

```c++
template<typename PromiseType>
auto await_suspend(std::coroutine_handle<PromiseType> h);
```

但是，使用了 enable_if 之类的模板技巧，外加在 awaitable_promise 里添加一些辅助佐料，实现了
```c++
template<typename Any>
auto await_suspend(std::coroutine_handle<awaitable_promise<Any>> h);
```

相同的作用。主要目的，就是为了让 coroutine_handle 的模板参数是 PromiseType。这样一眼就看明白的东西。

但是，明明 `std::coroutine_handle<awaitable_promise<Any>>` 就能实现的东西，为啥还要引入 enable_if 就为了继续
使用 `std::coroutine_handle<PromiseType>` 呢？相比嵌套的 <<>> 我觉得 enable_if 更复杂。

我要寻找更通用更一眼看明白的代码！

于是，我思考，能不能写出这样一类模板元编程

```c++
template<typename PromiseType>
auto await_suspend(std::coroutine_handle<PromiseType> h);
{
    if constexpr ( is_instance_of<PromiseType, awaitable_promise> )
    {
        // handle h as std::coroutine_handle<awaitable_promise<Any>>
    }
    else
    {
        // handle h as std::coroutine_handle<void>
    }
}
```

这里，is_instance_of 判断了 PromiseType 这个类型，是不是 `awaitable_promise<T>` 这个模板的一个参数化实例。

这样，这个代码极其的简化了，而且要做的事情一目了然。await_suspend 也只有一个，没有多个重载。

那么问题的关键在于，这里，`is_instance_of<U,T>` 这样的类型判断真的能写出来吗？

由于 awaitable_promise 具有特定的成员变量，所以只要检查是否有那个成员变量，也能判断吧？

于是，最初我的 is_instance_of 是更具体的 is_instance_of_awaitable_promise, 具体实现如下

```c++
template<typenme T>
concept is_instance_of_awaitable_promise = requires (T a)
{
    { a.local_ } -> std::same_as<std::shared_ptr<std::any>>;
    { a.continuation_ } -> std::same_as<std::coroutine_handle<>>;
}
```

使用的时候，是
```c++
template<typename PromiseType>
auto await_suspend(std::coroutine_handle<PromiseType> h);
{
    if constexpr ( is_instance_of_awaitable_promise<PromiseType> )
    {
        // handle h as std::coroutine_handle<awaitable_promise<Any>>
    }
    else
    {
        // handle h as std::coroutine_handle<void>
    }
}
```

但是，我对 is_instance_of_awaitable_promise 始终是不满意的。
因为我更希望的是，直接判断 PromiseType 是不是 awaitable_promise 的一种。

而不是它恰好有两个成员变量对的上号。

哪怕有两个成员变量对的上号，它就一定是 awaitable_promise 吗？

如果我修改了 awaitable_promise 的成员变量，是不是还得记得修改 is_instance_of_awaitable_promise的判断？
这还增加了心智负担。

于是我心心念念要改进这个地方的代码。

终于有一天，在一个人的 blog 上找到了 [解决方法](https://indii.org/blog/is-type-instantiation-of-template/)

于是抄录之。于是我心心念念的代码总算完成了。


从我以上的心路历程可以看出来，c++ 程序员都是有强迫症的。他们不仅仅要代码实现特定功能，还得要让代码“看起来”赏心悦目。
没错，虽然 `is_instance_of` 的具体实现是非常的不赏心悦目的，但是
`if constexpr ( is_instance_of<PromiseType, awaitable_promise> )`
是赏心悦目的。具体原因是因为 is_instance_of 是属于模板元编程实现的基础组件的范畴，只要名字给力，用法给力。实现是可以看不懂的。
`if constexpr ( is_instance_of<PromiseType, awaitable_promise> )` 是属于业务逻辑，必须要赏心悦目。

虽然代码赏心悦目了，但是 is_instance_of 具体是咋个原理，我看完他的blog也没研究明白。

诶。

