---
layout: post
title: 通知到轮询线程
tags:   [asio]
---

在腐都工作也有大半个月了。工作过程中，遇到了一个轮询+通知的消息模式。所以要轮询，是因为通知是不可靠的。
所以要通知，是因为轮询是不及时的。既要保证及时，又要保证可靠，就只能轮询和异步通知一起上。

因为异步通知的时候，会把轮询需要获得的状态一并携带上了。所以，获得通知后只是取消定时器，让轮询线程立即唤醒干活肯定是。。。 可以的但是有点浪费。如果在异步通知线程里直接调用处理呢，就要把处理的东西从轮询的线程里扣出来，这样轮询的代码就不直观了。

因为使用的是 asio 的 stackless coroutine。

不过，如果改造下 timer,  async_wait 的时候是可以2个返回值的回调呢？ 一个 ec 一个 通知的消息呢？

于是只要在 yield timer.async_wait 下面判断下 ec ，然后 yield async_pull   
如果 ec = aborted 那就不执行 yield async_pull . 直接把第二个参数看成是 async_pull 返回的。

这样就可以在不改动轮询代码的情况下，插入了异步通知。



结果伪造代码表示如下下

```c++

void operator()(boost::system::error_code ec, some_type_of_pull pulled_message)
{
	reenter(this)
	{
		while(is_timeout()) // 超时后不再轮询
		{
			timer.expires_from_now(pull_interval);
			yield timer.async_wait(*this);_
			
			if (!ec)
			{
				yield async_pull_message(object_id, *this);
			}else if(ec == boost::asio::error::opertion_aborted)
			{
				// 强行没错误！
				ec = boost::system::error_code();
			}
		
			if (ec)
			{
				// 处理轮询消息
			}		
		}	
	}
}

void wake_up(some_type_of_pull message)
{
	timer.wake_up(message);_
}


```

因为 timer 的回调的第二个参数是得万能类型，所以 timer 其实是个模板类。

```c++
template<typename TimerType, typename T>
class smart_timer
{
public:
	explicit smart_timer(boost::asio::io_service& io)
		: io(io)
		, m_timer(io)
	{}

	template<typename... TT>
	void expires_from_now(TT...  arg)
	{
		m_timer.expires_from_now(arg...);
	}

	template<typename Handler>
	void async_wait(BOOST_ASIO_MOVE_ARG(Handler) handler)
	{
		std::unique_lock<std::mutex> l(m);

		if (no_wait)
		{
			no_wait = false;
			io.post(boost::asio::detail::bind_handler(handler, boost::asio::error::make_error_code(boost::asio::error::operation_aborted), T()));
			return;
		}

		m_handler = handler;
		handler_set = true;
		m_timer.async_wait(std::bind(&smart_timer::handle_timer, this, std::placeholders::_1));
	}

	void wake_up(T arg)
	{
		std::unique_lock<std::mutex> l(m);
		if (handler_set)
		{
			handler_set = false;
			io.post(boost::asio::detail::bind_handler(m_handler, boost::asio::error::make_error_code(boost::asio::error::operation_aborted), arg));
			boost::system::error_code ignore;
			m_timer.cancel(ignore);
		}
		else
			no_wait = true;
	}

private:
	void handle_timer(boost::system::error_code ec)
	{
		std::unique_lock<std::mutex> l(m);
		if (ec == boost::asio::error::operation_aborted)
		{
			// check for wake_up parameter.
			return;
		}
		handler_set = false;
		io.post(boost::asio::detail::bind_handler(m_handler, boost::asio::error::make_error_code(boost::asio::error::interrupted), T()));
	}

private:
	boost::asio::io_service& io;
	TimerType m_timer;
	bool handler_set = false;
	bool no_wait = false;
	std::function<void(boost::system::error_code ec, T)> m_handler;
	std::mutex m;
};

```

在 coroutine 里， timer 的定义呢，是 ```smart_timer<boost::asio::steady_timer, _some_type_of_pull>_```

这样就可以了。

