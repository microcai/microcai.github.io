---
layout: post
title: 用iouring扩展asio
tags: [c++, cpp, async, iouring, io_uring, asio]
---

# 序

什么叫扩展asio？
Beast给Asio增加了 HTTP 协议，不叫扩展asio。那什么叫扩展asio？
举个例子，给 asio 的 socket 对象，基于io_uring提供的 IORING_OP_SHUTDOWN 增加 async_shutdown() 接口，就算扩展asio。因为原本asio并没有异步shutdown功能。而且这个功能并不能靠组合原有的asio接口实现。这就叫扩展asio。

扩展asio, 又不能修改asio的代码。看起来有点难办。
好在，asio的设计也是有一定的扩展性的，并非完全依赖修改源码实现扩展。
但是不可避免的，需要使用 asio::detail:: 名字空间下的非公开接口。

那么，就从 async_shutdown 开始，讲解如何扩展asio吧！

# 接口形式

不修改asio代码的大前提下，要给一个对象增加一个 async_shutdown() 的成员函数那是痴人说梦。语言上就禁了此路。

不过，有两种绕过的做法

其一。写一个新的socket对象，自 asio::ip::tcp::socket 继承。然后增加一个成员函数。缺点是所有使用 socket 的地方都得修改一下类型。有了IDE的重构大法，实际上为了能异步关闭而进行的迁移并不算特别大的工作量。但是如果有不需要牵一发而动全身的修改，会更好。
其二。写一个全局函数，接受一个 asio::ip::tcp::socket 并将他异步关闭。

第二个方法，不需要对整个项目进行大手术。只需要在需要异步关闭的地方，将原来的同步关闭 ( `socket.shutdown();`)，替换为  `co_await async_shutdown(socket, defered);`

从设计美学上来说，第二个方法更好。


# 操作系统接口

扩展asio, 并不是使用asio现有接口去实现一个功能。比如beast利用 asio现有的socket接口就能实现在其基础上增加 HTTP 协议支持。
我们要给 asio 的 socket 增加异步关闭功能，是实打实的让asio多了原本不存在的功能。那么显然，这样的功能，首先我们得问一问，操作系统支持吗？
如果操作系统不支持一个功能，我们想破天也没法给asio扩展出这个功能。

答案是，异步关闭socket只有io_uring支持了。windows 上虽然也支持异步关闭，但是需要使用 WSAEventSelect + WSAWaitForMultipleEvents + shutdown 组合使用。IOCP不支持异步关闭。没有能传 overlaped* 的 WSAShutdown 版本。


# asio 的接口组织结构

asio 暴露给用户的接口为2种对象，其一为 executor ，其二为 io_object. executor 一般而言就是 asio::io_context。而 io_object 则通常就是 socket 咯。

在使用上，一般通过绑定一个 io_context 来创建一个 socket. 然后调用 socket 的 aync_\* 系列成员函数。或者是能传入 socket 的全局 async_\*(socket,...) 函数。全局 async_\* 函数最终是通过调用一次或者多次 socket.async_\* 实现的。

## 接口背后的驱动框架

XX_object 的背后，是 XX_service 。XX_object.async_YY 的背后，实际上是对 XX_servie.async_YY 的调用。

比如 asio::stream_file 的背后，是 io_uring_file_service.

asio::basic_socket 的背后，是 io_uring_socke_service.

但是这些 XX_service 并不需要显式创建。而是在 XX_object 的构造函数里，通过一个叫 asio::use_service<XX_service>(io_context) 的方式，隐式创建并绑定。

比如，
```c++
class XX_object
{
    YY_service& yy_service;
    XX_Object_impl impl;

    XX_obcjet(io_context& io, auto... args)
        : yy_service(use_service<YY_servcie>(io))
        , impl(io, args...)
    {

    }

    auto async_XX(auto... args)
    {
        reutrn yy_service.async_XX(impl, args...);
    }
};
```

然后，XX_service 其实还可以进一步依赖更底层的 zz_service.
比如 asio::stream_file 通过 use_service<io_uring_file_service> 绑定 io_uring_file_service。
io_uring_file_service依赖 io_uring_descriptor_service，io_uring_descriptor_service 依赖 io_uring_service。

最终，io_uring_service 才是实际执行 event loop 的对象。由 io_context 根据平台各种宏定义条件编译后创建。
比如在 Linux 平台，io_context 会创建 io_uring_service。
如果是 Win 平台，则  stream_file通过 use<win_iocp_file_service> 绑定 win_iocp_file_service。
win_iocp_file_service 依赖 win_iocp_handle_service。
最终，在Win皮革难题， io_context 是 win_iocp_context 的重定义。而 win_iocp_context 会创建 win_iocp_handle_service。

如果在 linux 上使用 epoll, 则不支持  stream_file .. 所以改拿 basic_socket举例。

basic_socket 通过 use_service<reactive_socket_service> 绑定 reactive_socket_service。

reactive_socket_service 依赖 reactive_descriptor_service。
reactive_descriptor_service 又依赖 reactor . 而 reactor 是根据不同api的 typedef, 在 epoll 下， reactor = epoll_reactor.

根据使不使用 io_uring, io_context 会创建 io_uring_service 或者 reactor. 而 reactor 本身又是条件编译的 typedef ，原类型可以有  epoll_reactor, kqueue_reactor, select_reactor, poll_reactor。

用一个图来表示关系如下：

```
YY_Object -> use_service<YY_Service> -> .. -> use_service<platform_proactor_service>
                                                            ^
                                                           / \reactor_xx_service
                                                          |   |
io_context -> platform_io_context -> platform_proactor   /     \ platform_reactor
                                  \                              |
                                   -----------------------------/
```

如果要实现 async_shudtown , 显然需要实现一个 io_uring_shutdown_service, 并且这个 io_uring_shutdown_service 同时再依赖 io_uring_service。
在  io_uring_shutdown_service 里实现一个 async_shutdown 的方法。然后向 io_uring_service 投递 相应的SQE (io_uring 术语。表示 请求队列的一个条目)。

## io_uring_service 的互操作

要向 io_uring_service 投递一个 SQE, 做法并不是非常显而易见的。这涉及到 io_uring 的流程和 io_uring_service 的总体设计。
就目前来说，io_uring_service 有一个 start_op() 的接口。用他投递一个 io_uring_operation* 对象就实现了投递异步操作。

因此，我们需要实现一个 io_uring_shutdown_op ，并派生自 io_uring_operation。
然后实现 3个静态成员： do_prepare/do_perform/do_complete，并将3个静态成员的指针传给基类io_uring_operation 的构造函数。

当 io_uring_shutdown_op 被投递的时候，io_uring_service 会分别调用 do_perform/do_prepare/do_perform/do_complete。
do_perform 在我们这里，直接返回io_uring_service传来的 bool after_completion。
在 do_prepare 里，io_uring_service会传来一个待填写的 sqe, 我们调用 io_uring_prep_shutdown 即可。
在 do_complete 里，我们将operation* base （ io_uring_operation 的基类，所以也等于是 io_uring_shutdown_op 的基类）强转
为 io_uring_shutdown_op ， 然后就可以调用里面持有的 handler 回调函数。
这样就完成了一次 异步流程。

再梳理一次：

```

async_shutdown(socket, handler) [代码视角]
    -> io_uring_shutdown_service.async_shutdown
    -> io_uring_service->start_op( new io_uring_shutdown_op (socket, handler ))
    -> io_uring_shutdown_op::do_complete
    -> handler(error_code)  aka coro.resume()
```

以上为协程视角，下面是分拆为2个阶段的异步+回调视角下发生的

```
异步发生的 initiate 阶段：
async_shutdown(socket, handler)
    -> io_uring_shutdown_service.async_shutdown
    -> io_uring_service->start_op( new io_uring_shutdown_op (socket, handler ))
      -> op_queue->push( io_uring_shutdown_op )

异步发生的 callback 阶段
    io_contect::run
    -> io_uring_service->run (批量 submit 阶段)
    -> op_queue->submit
     -> io_uring_shutdown_op::do_prepare
      -> io_uring_prep_shutdown
    -> io_uring_service->run (等待完成列队阶段)
     ->io_uring_shutdown_op::do_complete
     ->handler

```

## 一些需要绕过的注意事项


`io_uring_service::start_op` 需要一个 per_io_object_data 。而这个 per_io_object_data 必须通过 io_uring_service::register_io_object 分配并注册。
使用完毕还必须得通过 io_uring_service::deregister_io_object和 io_uring_service::cleanup_io_object清理。

但是严格来说，我们实现的 async_shutdown 并不需要一个 per_io_object_data。实际上 win_iocp_service 投递 overlaped 的时候也不需要一个 per_io_object_data，不知道 asio 作者的思路。目前只能假装调用 register_io_object 分配一个。
因此这导致 async_shutdown 不能成为一个全局函数。只能给它搭一个对象。

考虑到将来封装的不少 io_uring 的 OP 都有类似的情况（不需要真正的一个 io_object 就能使用），因此计划中的 io_uring_shutdown_service 就改名为
io_uring_misc_service。然后创建一个全局的 class misc 对象。

也就是
```
async_shutdown -> misc.async_shutdowm -> io_uring_misc_service->async_shutdown
```

这样多绕一圈。

# 成品

## misc 对象

```c++
struct misc
{
	boost::asio::detail::io_object_impl<io_uring_misc_service, boost::asio::any_io_executor> impl_;

	misc(boost::asio::io_context& io): impl_(0, io.get_executor()){}

	template<typename Executor>
	misc(Executor&& ex): impl_(0, std::forward<Executor>(ex)) {}

	template<typename Socket, typename CompletionToken>
	auto async_shutdown(Socket& s, boost::asio::socket_base::shutdown_type how, CompletionToken&& token)
	{
		return boost::asio::async_initiate<CompletionToken, void(boost::system::error_code)>(
			[this, &s, how](auto&& handler) mutable
		{
			impl_.get_service().async_shutdown(impl_.get_implementation(), s.native_handle(), how, std::move(handler));
		}, token);
	}
};
```

注意到 io_object_impl，它可以简化 misc 对象和 service 对象的编码。可以看到一个 impl_ 对象就免去了 per_io_object_data 的管理。

在 misc 对着的 async_shutdown 成员函数里，它通过 impl_.get_serivce() 获得了 io_uring_misc_service 的引用。
从而调用了 io_uring_misc_service::async_shutdown

# io_uring_misc_service 对象

```c++

class io_uring_misc_service : public boost::asio::detail::execution_context_service_base<io_uring_misc_service>
{
public:
	// The native type of a descriptor.
	typedef int native_handle_type;

	// The implementation type of the descriptor.
	class implementation_type : private boost::asio::detail::noncopyable
	{
	public:
		// Default constructor.
		implementation_type()
		{
		}

	private:
		// Only this service will have access to the internal values.
		friend class io_uring_misc_service;
		// Per I/O object data used by the io_uring_service.
		boost::asio::detail::io_uring_service::per_io_object_data io_object_data_;
	};

	// Constructor.
	io_uring_misc_service(boost::asio::execution_context& context)
		: boost::asio::detail::execution_context_service_base<io_uring_misc_service>(context)
		, io_uring_service_(boost::asio::use_service<boost::asio::detail::io_uring_service>(context))
	{
		io_uring_service_.init_task();
	}

	// Destroy all user-defined handler objects owned by the service.
	void shutdown(){}

	// Construct a new descriptor implementation.
	void construct(implementation_type& impl)
	{
		impl.io_object_data_ = 0;
		io_uring_service_.register_io_object(impl.io_object_data_);
	}

	// Destroy a descriptor implementation.
	void destroy(implementation_type& impl)
	{
		io_uring_service_.deregister_io_object(impl.io_object_data_);
		io_uring_service_.cleanup_io_object(impl.io_object_data_);
	}

	// submit op as sqe
	void submit_op(implementation_type& impl, boost::asio::detail::io_uring_operation* op)
	{
    	io_uring_service_.start_op(1, impl.io_object_data_, op, false);
	}

private:
	// The io_uring_service that performs event demultiplexing for the service.
	boost::asio::detail::io_uring_service& io_uring_service_;

	// Cached success value to avoid accessing category singleton.
	const boost::system::error_code success_ec_;

protected:
	using io_uring_operation = boost::asio::detail::io_uring_operation;
	using operation = boost::asio::detail::operation;

	template<typename Handler>
	struct io_uring_shutdown_op : public io_uring_operation
	{
		BOOST_ASIO_DEFINE_HANDLER_PTR(io_uring_shutdown_op);
		Handler handler_;

		int fd;
		int how;

		io_uring_shutdown_op(const boost::system::error_code& ec, int fd, int how, Handler&& handler)
			: io_uring_operation(ec, &do_prepare, &do_perform, &do_complete)
			, handler_(std::forward<Handler>(handler))
			, fd(fd)
			, how(how)
		{
		}

		static void do_prepare(io_uring_operation* base, ::io_uring_sqe* sqe)
		{
			auto o = static_cast<io_uring_shutdown_op*>(base);
			::io_uring_prep_shutdown(sqe, o->fd, o->how);
		}

		static bool do_perform(io_uring_operation* base, bool after_completion)
		{
			return after_completion;
		}

		static void do_complete(void* owner, operation* base, const boost::system::error_code&,
								std::size_t /*bytes_transferred*/)
		{
			// Take ownership of the handler object.
			BOOST_ASIO_ASSUME(base != 0);
			auto* o(static_cast<io_uring_shutdown_op*>(base));

			ptr p = {boost::asio::detail::addressof(o->handler_), o, o};

			BOOST_ASIO_HANDLER_COMPLETION((*o));

			// Make a copy of the handler so that the memory can be deallocated before
			// the upcall is made.
			boost::asio::detail::binder1<Handler, boost::system::error_code> handler(o->handler_, o->ec_);
			p.h = boost::asio::detail::addressof(handler.handler_);
			p.reset();

			handler();
		}
	};

public:
	template<typename Handler>
	void async_shutdown(implementation_type& impl, int fd, boost::asio::socket_base::shutdown_type how, Handler&& handler)
	{
		// Allocate and construct an operation to wrap the handler.
		typedef io_uring_shutdown_op<Handler> op;
		typename op::ptr p = {boost::asio::detail::addressof(handler), op::ptr::allocate(handler), 0};

		p.p = new (p.v) op(success_ec_, fd, how, std::move(handler));
		submit_op(impl, p.p);
		p.p = p.v = 0;
	}
};


```

用例：

```c++
asio::awaitable<...> some_code(...)
{
    ...
	misc m{co_await boost::asio::this_coro::executor};
	co_await m.async_shutdown(socket, boost::asio::socket_base::shutdown_both, boost::asio::use_awaitable);
    ...
}

```

所以，扩展 asio 支持更多的 io_uring 操作的方法就是照着 io_uring_shutdown_op 然后扩展出来。

