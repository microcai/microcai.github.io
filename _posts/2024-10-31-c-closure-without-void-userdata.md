---
layout: post
title: 不需要void*user_data的闭包封装
tags: [c, closure]
---

一般来说，如果 C api 接受一个回调，通常会额外允许设置一个 void* 的回调参数。
用户可以把一些额外的参数用这个 void* 传给回调函数。
比如

```c
typedef void (*read_function_t)(const char* read_buf, int read_size, void* user_data);

int register_read_callback(read_function_t on_read_function, void* user_data);
```

这样，用户在回调函数里，就可以使用 user_data 这个参数，获取额外的状态信息。

但是，也有一些古早时代的 C api, 没有办法设置 user_data。 比如：

```c
typedef void (*read_callback_t)(const char* read_buf, int read_size);
int set_read_callback(read_callback_t on_read);
```

那么回调函数里，就只能拿到库作者设定好的回调信息了。 自己也没有办法传递别的信息给回调处理函数。

这，必然是库作者的无能，缺陷。是必须要改进的。

但是，没办法，如果你不得不使用这样的一个无能库，咋办呢？有什么办法传  user_data 进去呢？

比如，有没有办法实现这样的一个包装器，对上面的 API ，可以做到这样封装

```c++
auto read_cb = lamba_to_c([&捕获其他状态](const char* read_buf, int read_size)
{  。。。 处理代码，可以访问 捕获的变量 });

//正常来说， 带捕获的 lambda 是没法 cast 成一个 C 指针的。。。 但是有了这个 魔法，它就可以了。
set_read_callback(static_cast<read_callback_t>(read_cb));
```

似乎这样的封装对付烂 C API非常给力。只是看起来并不容易实现。

对 lambda 来说，它本质上是个函数对象。也就是重载了 operator() 的一个匿名类。所以，只要想办法给这个类的 this 找到传递的方式，这个包装器就能实现。
如果 C 库本来就支持 `void* user_data` ，那么这样的一个包装器显然并不难写。问题在于，如果 C 库不支持 user_data 参数呢？


# 思路

其实，还有一个办法，可以传递 user_data, 那就是回调函数本身。
一般来说，回调函数是用户编写的一个函数，这个函数编译后，只会有一份代码。因此设置回调的时候，回调函数的地址是个 constexpr。

如果把 user_data 和回调函数本身的“代码” 绑定，则可以为每一个 user_data 都 “创建” 出一个单独的回调函数。

这个“动态创建” 出来的函数，他可以在代码里，直接获取到 user_data , 然后再转而调用真正的回调函数，携带上user_data参数。

具体做法是：

编译一个 stub 代码，这个代码和 user_data 的数据一起，作为一个 新的 回调函数创建出来。新的函数长这样

```
new_cb_code:
    get_user_data_relative_to_InstructionPointer # 获取相对当前代码指针偏移了几个字节的 user_data
    call real_cb_with_user_data
    db user_data <-- user_data 存此处
end
```

这段代码，必须是 “可重定位的”，可以随便复制，任意放置执行。使用的时候，把这个代码作为模板，和 user_data 数据进行拼接。动态的在堆上创建出一个新的函数。

然后，折断代码被 不支持 user_data的库 调用的时候，使用 “程序计数器寄存器” 进行相对寻址，找到 user_data 数据，然后跳转到真正的，带 user_data 参数要求的回调函数里。


用汇编来表示，这个代码应该这样

```asm
dynamic_callback:
    mov rax, [rip+17] ; 此指令 7 个字节，取得 user_data 存入 rax 寄存器
    nop ; 1 个字节
    jmp [rip+2]; // 此指令 6 个字节，直接跳转执行 cb_function_wrapper
    nop ; 1 个字节
    nop ; 1 个字节
    .qword cb_function_wrapper // 8 字节存储带 user_data 的回调
    .qword user_data // 8 字节存储 user_data
```
一共32个字节。使用时，每次复制一份新的代码，然后将最后的2个8 字节，填入相应指针。
然后折断代码的起始地址，就可以作为 C 库的 回调函数指针使用了。

注意的是， cb_function_wrapper 还不是真正的回调函数。因为它需要从 rax 寄存器获取 user_data.
这个 cb_function_wrapper 这么写

```cpp
static void cb_function_wrapper(const char* read_buf, int read_size)
{
    std::function<void(const char* read_buf, int read_size)>* user_data;
    asm("\t mov %%rax,%0" : "=r"(user_data));

    (*user_data)(read_buf, read_size);
    delete user_data;
}
```

这里， user_data 是 std::function,它把真正的用户的 lambda 给包起来了。

执行完毕，还得删了 user_data;

ooops,user_data 删了， dynamic_callback 这段动态代码没删。会有内存泄漏的。

为了简化内存管理，我们把 user_data 所代表的，用户编写的那个 lambda , 和 动态生成的代码，合并到一起存储。

于是，我们获得了一个这样的类

```cpp
struct cb_function_wrapper
{
    unsigned char _trunk_code[32];
    std::function<void(const char* read_buf, int read_size)>* user_function;

    static void trunk_call_user_function(const char* read_buf, int read_size)
    {
        void * __this;
        asm("\t mov %%rax,%0" : "=r"(__this));

        reinterpret_cast<cb_function_wrapper*>(__this)->user_function(read_buf, read_size);
        delete __this;
    }

    cb_function_wrapper(std::function<void(const char* read_buf, int read_size)> user_func)
        : user_function(user_func)
    {
        // 把模板代码复制到 _trunk_code
        // 并且更新 _trunk_code 的最后2个 指针
    }

    operator read_callback_t()
    {
        return reinterpret_cast<read_callback_t>(_trunk_code);
    }
}

```
cb_function_wrapper 里面的 _trunk_code 就是上文讲到的32个字节的机器代码。

这样，cb_function_wrapper 就实现了，把没有 user_data 的 C 库 API, 也能转化为
支持使用 lambda 作为回调了。

# 模板化，通用化

但是，C 库的回调种类是何其的多！总不能每种回调都写一个 包装器吧。
所以，这时候我们需要祭出模板大法。

```c++
template<typename Signature>
struct c_function_ptr;

template<typename Signature>
struct dynamic_function;

template<typename R, typename... Args>
class dynamic_function
{
	typedef R (* function_ptr ) (Args...);

	static R do_invoke(Args... args)
	{
		void* _rax;
		asm("\t mov %%rax,%0" : "=r"(_rax));

		dynamic_function * _this = reinterpret_cast<dynamic_function*>(_rax);

		return (*_this)(args...);
	}

	void * operator new (std::size_t size)
	{
		return ExecutableAllocator{}.allocate(size);
	}

	void operator delete (void* ptr, std::size_t size)
	{
		return ExecutableAllocator{}.deallocate(ptr, size);
	}

	template<typename LambdaFunction>
	explicit dynamic_function(LambdaFunction&& lambda)
		: ref_count(2)
		, user_function(std::forward<LambdaFunction>(lambda))
	{
		static constinit unsigned char machine_code_template [] = {
			0x90, 0x48, 0x8d, 0x05, 0xf8, 0xff, 0xff, 0xff, // nop; lea rax, [rip-8]
			0xff, 0x25, 0x02, 0x00, 0x00, 0x00, 0x90, 0x90, // jmp [rip+2]; nop; nop
			0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // c_function_ptr::do_invoke() address
		};

		void * wrap_func_ptr = reinterpret_cast<void*>(&do_invoke);

		memcpy(_jit_code, machine_code_template, 16);
		memcpy(_jit_code + 16, &wrap_func_ptr, 8);
	}

	operator function_ptr ()
	{
		return reinterpret_cast<function_ptr>(this->_jit_code);
	}

	R operator()(Args... args)
	{
		auto a = make_scoped_exit([this]()
		{
			unref();
		});

		return user_function(args...);
	}

	void unref()
	{
		if (ref_count.fetch_sub(1) == 1)
		{
			delete this;
		}
	}

	friend class c_function_ptr<R(Args...)>;

	unsigned char _jit_code[24];
	std::atomic_int ref_count;
	std::function<R(Args...)> user_function;
};

```

此时， _jit_code 和 user_function 放到一个类里，一次性的分配出来了。
因此，机器代码也稍作了修改，用 `lea rax, [rip-8]` 直接获得 _jit_code 的地址。而 _jit_code
的地址，就是这个类的 this 指针。

因为 __jit_code 必须放在可执行的内存区域里，因此这个类，必须动态创建。并且使用 ExecutableAllocator 分配内存。
并且整个类都声明为 private 防止用户创建。必须通过 friend class c_function_ptr 使用。

c_function_ptr 的代码如下

```c++
template<typename Signature>
struct c_function_ptr;

template<typename R, typename... Args>
struct c_function_ptr<R(Args...)>
{
	using wrapper_class = dynamic_function<R(Args...)>;

	wrapper_class * _impl;

	template<typename LambdaFunction>
	explicit c_function_ptr(LambdaFunction&& lambda)
	{
		_impl = new wrapper_class(std::forward<LambdaFunction>(lambda));
	}

	typedef R (* function_ptr ) (Args...);

	operator function_ptr ()
	{
		return static_cast<function_ptr>(* _impl);
	}

	void no_auto_destory()
	{
		_impl->ref_count = 0;
	}

	void destory()
	{
		delete _impl;
		_impl = nullptr;
	}

	~c_function_ptr()
	{
		if (_impl)
			_impl->unref();
	}
};
```

使用的代码如下：（还是使用 set_read_callback 为例）

```c++

auto read_cb = c_function_ptr<read_callback_t>([&捕获其他状态](const char* read_buf, int read_size)
{  。。。 处理代码，可以访问 捕获的变量 });

// NOTE：如果 set_read_callback 是一次设置，永久使用，则调用这个
// 如果是每次设置只回调一次，则不调用
// read_cb.no_auto_destory();

//正常来说， 带捕获的 lambda 是没法 cast 成一个 C 指针的。。。 但是有了这个 魔法，它就可以了。
set_read_callback(static_cast<read_callback_t>(read_cb));

```

好了，大功告成。 set_read_callback 这样的 C API ，即便不能设置user_data，也能使用 lambda当回调使用了。
