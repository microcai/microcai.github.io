---
layout: post
title: 重提类型擦除器
tags: [c++, cpp]
---

# 序

十年前，我曾经写过一篇有关类型擦除器的文章, [见这](/2014/04/21/type-erasure.html)。

十年后，我打算再探讨下类型擦除器。

C++ 对 多态 的支持，在核心层面，就两条： 虚继承 和 模板。

假设你要设计一个 线程池。这个池你可以“投递”各种任务进去。

什么叫”任务“呢？ 就是一段代码。于是，早期你想到，可以使用 函数指针。

于是你的 线程池长这样

```c++
class threadpool
{
	typedef void (*task_function_t)();

	std::list<task_function_t> tasks;
public:
	void post(task_function_t job);
};

```

这样的代码，有个问题，那就是你“投递” 的任务，他干活得有数据。如果投递的任务，只能是一个函数指针。
那么这个函数，就得使用“全局变量“来传递工作内容了。

所以说，这个 task ，不能是个函数指针。它得携带对象。

于是，自然的，你想到了 多态，虚函数。那么很快你就改进了第二个版本

```c++

class task
{
public:
	virtual void run() = 0;
	virtual ~task(){}
};


class threadpool
{
	std::list<task*> tasks;
public:
	void post(task* job);
};


```

显然，如果要给任务携带点状态，就可以写一个 task 对象，比如

```cpp

class some_task : public task
{
	int work_arg1;
	int work_arg2;

public:
	some_task(int arg1, int arg2);

	void run() override
	{
		// do some work with args.
	}

};

```

想要带上啥状态，一股脑的给添加到自己写的派生类里就行了。

显然，相比 函数指针，这个 task 虚基类，让你的任务可以携带状态了。这就抛弃了全局变量通信法。

但是，有一个小小的缺点，那就是, 为了使用这个线程池的功能，必须得 “派生” 一批对象。而且这些对象海都得从 task 基础。

这就是所谓的“侵入” 试设计。一个线程池的类型，到处扩散到整个项目里。

除了类型侵入，这种设计的最大问题就是，多了很多负担。要编写很多 “类”。

于是，你想到了 lambda 。 如果 能投递一个  lambda, 那么就可以少写很多的类。

例如接口变成这样

```c++
class threadpool
{
	...
public:
	template<typename Lambda>
	void post(Lambda&& lambda);
};

```

好了，这样  `pool.post([data1, data2](){  work on data} );` 写的代码就能使用了。
确实是一个巨大的进步。使用的地方少了很多类型侵入。

问题是，这 post 是个模板，这个 Lambda 可是随着调用的地方而随时变换类型的。
因此整个任务列队，可没法使用  `std::list<Lambda>` 进行存储。

因此，拿模板实现的多态，他只适合不对传入的数据进行“存储”的算法类使用（比如std::sort。调用的时候，数据就立马处理了。不需要存储为稍后使用的数据。一旦需要存储，模板就不行了。存储需要确定的大小。而一个`typename Lamba` 这个类型，可是随时随地的在变。这怎么放入容器呢？

从实现的角度而言，放入任务列队的任务，必须具有相同的类型，确定的大小。
而post 函数，是个模板，他拿到的对象，是可以具有任意类型的。

虽然说它拿到的参数可以是任意类型，但是，也不是真的“任意”类型都可以的。具体的来说，他拿到的东西 `lambda`
，必须具备接下来能对其进行的 `lambda()` 操作。也就是，是一种“仿函数”类型，而且不接受参数。

你看，所谓的任意类型，其实并不任意。他对 Lambda 类型，还是有一个“要求”的，那就是 **可调用** 和 **无形参**。至于，这个类型到底是什么类型，却没有具体要求。它可以是一个 `void (*)()` 函数指针，也可以是一个无形参的 lambda ，也可以是一个带 `void operator () ()` 运算符重载的对象。

如果我们实现一个 `class task` 类型，它不是一个模板类，而是一个确定的类型，那么它就有了固定的大小，就可以放入容器充当任务对象。然后这个对象内部，可以存储满足以上要求的 “任意类型对象”。那么，这个 class task，就叫 “**类型擦除器**”。


首先，我们知道，这个 task 对象，需要 “可调用”，对参数形式的要求，还得是 无参数。
因此，首先 task 需要一个 `void operator()() const` 这样的运算符重载。
而且， 这个 task 要能存储 “任意” 类型的对象，它的构造函数就必须是个模板函数。
于是很快， task 类的 接口声明我们就写出来了。

```c++

class task
{
public:
	template<typename T>
	task(T&&t);

	void operator()() const;
};

```
于是搭配我们的线程池，就变成了这样的接口搭配：

```c++

class task
{
public:
	template<typename T>
	task(T&&t);

	void operator()() const;
};

class threadpool
{
	std::list<task> tasks;
public:
	template<typename Callable>
	void post(Callable job)
	{
		tasks.emplace_back( task{ std::forward<Callable>(job) }  );
	}
};

```

如此一来，用户在使用的时候，即不需要使用函数指针时代那样，没地方传参数导致通信全靠全局变量。
也不用像虚函数时代那样，到处都在派生类。

这样的接口，用起来无疑是舒服，爽快的。

# 实现

那么，如何设计一个 类型擦除器呢？

task 的构造函数里，它被安排接受“任意”类型，因此，大小是不固定的。
这种大小不固定的东西，打小谭浩强就告诉我们，必须进行“动态分配”。
所以，task 对传入的参数，必须得进行一波 “动态构造”。那么我们这么设计可行？

```c++

class task
{
	void * m_obj_stor;
public:
	template<typename T>
	task(T&&t)
	{
		m_obj_stor = malloc(sizeof (t));
		memcpy(m_obj_stor, &t, sizeof (t));
	}

	void operator()() const;
};

```

显然，使用了 memcpy 导致 T 对象，必须得是可以用 memcpy 复制的对象。可是一开始可没说它多了个“能被memcpy复制”的这个要求啊？ lambda 对象能被 memcpy 复制吗？函数对象，真的能被 memcpy 复制而没有其他副作用吗？

显然不对。所以，这地方不能使用memcpy, 而是应该使用 placement new 操作符。

```c++
	template<typename T>
	task(T&&t)
	{
		m_obj_stor = malloc(sizeof (t));
		new (m_obj_stor) T(std::forward<T>(t));
	}
```

这样，编译器会自动的安排调用 T 类型的 移动构造/拷贝构造 函数。完成将 t 对象移动or复制到m_obj_stor 的工作。好了，构造问题解决。

接下来的问题是，`void operator()() const;` 该怎么实现呢？
因为 m_obj_stor 是个 void* 指针，它所有的类型信息都被**抹除**了。

要知道，只有构造函数能访问 `typename T` 这个类型，而其他地方都没有了 T 类型信息。

这意味着，`void operator()() const;` 对着 `void* m_obj_stor` 只能 *俩眼一摸黑*。

那可不行啊！！！！！如果 m_obj_stor 是个虚类就好了，好歹有类型。

明白！这么干如何？


```c++
class task
{
	struct task_base
	{
		virtual ~task_base(){}
		virtual void operator()() const{}
	};

	task_base * m_obj_stor;
public:
	template<typename T>
	task(T&&t)
	{
		m_obj_stor = new ???
	}

	~task()
	{
		delete m_obj_stor;
	}

	void operator()() const
	{
		m_obj_stor->operator()();
	}
};


```

这么一来，除了 构造，析构和调用，就全都实现了！看起来，我们只要在 构造的地方，自动的构建一个 task_base 的派生类就可以了，因为构造函数，是能访问 T 类型的。

```c++
	template<typename T>
	task(T&&t)
	{
        struct task_impl : public task_base
        {
            // ???
        };

        m_obj_stor = new task_impl{std::forward<T>(t)};
	}
```

task_impl 由于使用的是内嵌定义，因此它也是能访问 T 类型的。所以写完整是这样的

```c++

class task
{
	struct task_base
	{
		virtual ~task_base(){}
		virtual void operator()() const{}
	};

	task_base * m_obj_stor;

public:
	template<typename T>
	task(T&&t)
	{
        struct task_impl : public task_base
        {
            T m_obj;

            task_impl(T&& t)
                : m_obj(std::forward<T>(t))
            {
            }

            void operator()() const override
            {
                m_obj();
            }
        };
        m_obj_stor = new task_impl{std::forward<T>(t)};
	}

	~task()
	{
		delete m_obj_stor;
	}

	void operator()() const
	{
		m_obj_stor->operator()();
	}
};

```

于是，借着“古老”的虚函数，搭配先进的“模板”，一个极为先进和强大的 **类型擦除器** 就这么诞生了。

当然，为了能顺利放入容器，这个 task 类型，还得写上 “移动构造”，适应 STL 容器对对象的 “可移动” 需求。

# 轮子

既然，**可调用对象** 这种类型进行类型擦除，是个极为普遍迫切的需求，那么 STL 显然不会缺席。
因此， STL 里也提供了一个 std::function 类型，干的就是这种容纳一切可调用对象的需求。

因为“可调用” 这个需求，本身也会随着“参数多样性”扩展，于是 std::function 本身，又是一个模板。
我们研究了半天的 task, 其实功能上，和  `std::function<void()>` 是完全等价的。

std::function 的模板参数，居然是一种叫 “函数签名” 的东西。

其实 上古时代，function 的设计是这么使用的 `funtion0<返回类型>` `function1<返回类型，参数1类型>` `function2<返回类型，参数1类型，参数2类型>` 。。。 洋洋洒洒，写满几十个  function 类型。

像 `std::function<int (int, double)>` 这样的非常**直观**的模板参数写法，其实要到 c++11 以后才能实现。所以很多人批评 c++ 进化的越来越复杂，其实那都是不懂的人瞎BB。懂的人都知道，C++ 的一切改进，都是为了让这个语言变得更**易用**。

那么，不自己发明轮子，其实更简化了 线程池的设计，改进后变成这样

```c++
class threadpool
{
	using task = std::function<void()>;
	std::list<task> tasks;
	std::vector<std::thread> workers;
	mutable std::mutex mutex;
public:
	void post(task job);
};
```

整个类，没有一个模板，于是，可以正常的 实现 头文件和实现分离。也不会增加编译时间，不会导致二进制膨胀......

其实看完 task 的写法，就明白了 `std::function<void()>` 是怎么实现类型擦除的, 但是， std::fuction 是怎么实现模板参数里，是个 “函数签名” 这种东西的呢？？？？？？？有时间我再写啦！