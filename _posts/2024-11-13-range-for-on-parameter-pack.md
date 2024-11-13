---
layout: post
title: 可变模板参数包迭代
tags: [c++, cpp, for, template, variadic]
---

# 序

如果你写了一个模板函数，模板函数里使用了 可变参数。比如你写了个

```c++
template<typename... Args>
int print(Args... args);
```

那么，要如何去访问这些可变的参数呢？

### 方法 1

使用递归法。比如定义2个 print, 一个是单参数的，另一个是 2个模板参数的。


```c++
template<typename Arg>
int print(Arg arg);

template<typename Arg1, typename... Args>
int print(Arg1 arg1, Args... args)
{
	print(arg1);
	print(args...);
}

```

在可变参的 print 里， 它首先将第一个参数调用了单参数版的 print. 接着把剩下的参数调用自身。

如果剩下的参数就一个了，那么编译器也是匹配到单参数版的 print 从而结束递归。

### 方法 2

使用 **折叠表达式**


```c++
template<typename... Args>
int print(Args... args)
{
	(print_one(args), ...);
}

```

在这个方法里，```(print_one(args), ...);```就是所谓的 **折叠表达式**。 它的意思就是把 前面的 重复一下。每次重复的时候，各使用参数包里的一个参数。

### 方法 3

打包进 std::tuple 后使用。比如


```c++
template<typename... Args>
int print_tuple(std::tuple<Args...> tuple_arg)
{
	// ???
}

template<typename... Args>
int print(Args... args)
{
	print_tuple(std::forward_as_tuple(args...));
}
```

吼吼，那么问题来了， tuple 版本要怎么实现？

其实又回到了  递归 或者折叠表达式 的老路上了。

# 参数包上的 for 循环

折叠表达式的语法并不讨喜。而且只能对每个参数做一模一样的活，因此灵活性欠佳。递归的话，逻辑非常的晦涩难懂。因为它是用递归去实现循环。

因此，我提出了一种新的语法格式，就是让 for 循环可以用在参数包上。 语法如下


```
for ( auto or typename   identifier  : parameter_pack  )
{

}
```

如果 parameter_pack 是类型列表，则使用 typename 比如

```c++
template<typename... Args>
int print(Args... args)
{
	for (typename arg_type : Args...)
	{
		if constexpr (std::is_same_v<arg_type, int>)
		{
			//
		}
	}
}
```

如果 parameter_pack 是形参列表，则使用 auto ，比如

```c++
template<typename... Args>
int print(Args... args)
{
	for (auto arg : Args...)
	{
		if constexpr ( is_printable<decltype(arg)> )
		{
			print_one(arg);
		}
		else
		{
			// ...
		}
	}
}
```

# 优势

比 **折叠表达式** 更容易编写和理解。能表达的意思也更加完善。而且配合 static if 还能实现 折叠表达式 无法实现的选择性操作。
for 内部还能使用 break 提前终止迭代。

比如对 tuple 的访问，也会非常直观

```c++

template<typename... Args>
int do_with_tuple(std::tuple<Args...> tuple_var)
{
	for (auto INDEX : std::make_index_sequence<std::tuple_size<tuple_var>{}>())
	{
		auto var = std::get<INDEX>(tuple_var);

		// do with var

	}
}


```


# 编译器实现

编译器需要对 for 循环进行完整展开。因为循环的容器是 参数包, 其内容编译期已知。

对包含 break 和 contine 的 循环体，可以在展开后，使用 goto 进行跳转。

简单来说，就是这个语法糖是完全可实现的，而且并不麻烦。


