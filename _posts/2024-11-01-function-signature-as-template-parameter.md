---
layout: post
title: 类型萃取技术：函数签名当模板参数
tags: [c++, cpp, function]
---

# 序

在 [上一篇](/2024/11/01/type-erasuer.html) 文章里，我提到了 std::function 的模板参数，是一个叫**函数签名** 的东西。

什么是函数签名？

比如 main 函数，他的签名是 `int(int, char**)`。所谓函数签名，是指函数声明去掉 函数名和变量名 后得到的一个精简描述。 这个精简描述，指导编译器如何按”调用约定“产生具体的汇编指令以调用一个函数。

函数名，不过是在最后的 call 指令里，提供了具体的目标地址。

但是，如果你问 decltype(&main) 的类型是啥，其实他的类型是`int (*)(int, char**)`。

因为 &main 是 main 函数的函数指针。 函数签名是形如 R(args...) 的东西，而函数指针的类型，就是 R (*)(args...)

函数签名甚至不是一个合法的类型，你不能定义  `int(int,int) p;` 这样的一个变量。
但是你可以用 `int (*p)(int, int)` 定一个 函数指针 p, 其指向的函数，具有 `int(int, int)` 这样的签名。

那么，对于  std::function 来说，他的模板参数要怎么写，才能接受一个签名呢？

其实很简单，就把签名当成一个类型。也就是

```c++
template<typename Signature>
class function;
```

那么有人问了，这 Signature 就一个类型啊，那 function 的 括号操作符 要怎么写？

`Signature operator()(Signature)` ?

显然不对。

这括号操作符，必然是要把签名里的 返回值和参数给拆开来。

把一个类型里的具体组成部分拆出来？

哈哈！ 这技术，听起来不可思议！

其实，这就是本期的重点要介绍的屠龙级C++技术： 类型萃取。

# 模板偏特化：类型萃取的技术基石

这就不得不提，C++模板的一个偏方用法：模板偏特化。

比如，你定义了

```c++
template<typename Signature>
class function;
```

于此同时，你又定义了一个偏特化

```c++
template<typename ReturnType, typename... Args>
class function<ReturnType(Args...)>
{

};

```


那么，当用户使用 ```function<int(int, int)> ``` 的时候，
实际上编译器实例化的，正是第二个类。

也就是，按 ReturnType = int, Args = int, int 实例化
```c++
template<typename ReturnType, typename... Args>
class function<ReturnType(Args...)>
```
这个偏特化的模板类。

正常情况下，第一个模板类声明，将永远不会获得实例化的机会。这也就是为何，这个模板会变成一个没有实现的空声明。

那么，在第二个 function 的定义里，是不是，ReturnType 就拿到了？

于是他就可以用

```cpp
ReturnType operator()(Args... args) const
```

来定义他的括号操作符了。

完整来看，这个模板类定义如下

```c++
template<typename ReturnType, typename... Args>
class function<ReturnType(Args...)>
{
    ...

    ReturnType operator()(Args... args) const
    {
        ...
    }

};
```

你看，这样就把 Signature 给拆分了，萃取到了其中的 返回值和参数两部分。
这种技术，就叫类型萃取。是用 模板偏特化 这个超难用的神器 实现的。

