---
layout: post
title: 我为什么喜欢用协程
tags: [c++, asio]
---

查看过 avbot 代码的人都知道, avbot 到处都是协程. 用句 ACG 的话来说,  *博士是**协程控***

那么, 为啥我会那么喜欢使用协程呢? 答案是协程大大简化了编程, 尤其是内存管理.

## 协程简化了内存管理

*写过异步程序的人都知道, 编写异步代码最容易犯的错就是内存泄露了.*

asio的无栈协程通过 **闭包** 的形式, 将异步过程所要操作的资源绑定到 **闭包** 上, 并使用 shared_ptr 对这些资源执行引用计数管理. 当最后一个回调执行完毕后, shared_ptr 确保了资源的正确释放. 对于 copyable 的资源, 甚至直接作为 **闭包** 的一部分, 让资源随着闭包被 ASIO 拷贝, 释放, 拷贝, 释放, 最终最后一个**闭包**完成使命, 彻底撤销.

下面这个是 QQ 登陆过程的一个协程代码

```c++
// qq 登录办法-验证码登录
class login_vc_op : boost::asio::coroutine{
public:
	typedef void result_type;

	login_vc_op(boost::shared_ptr<qqimpl::WebQQ> webqq, std::string _vccode, webqq::webqq_handler_t handler)
		: m_webqq(webqq), vccode(_vccode), m_handler(handler)
	{
		std::string md5 = webqq_password_encode(m_webqq->m_passwd, vccode, m_webqq->m_verifycode.uin);

		// do login !
		std::string url = boost::str(
							  boost::format(
								  "%s/login?u=%s&p=%s&verifycode=%s&"
								  "webqq_type=%d&remember_uin=1&aid=%s&login2qq=1&"
								  "u1=http%%3A%%2F%%2Fweb.qq.com%%2Floginproxy.html"
								  "%%3Flogin2qq%%3D1%%26webqq_type%%3D10&h=1&ptredirect=0&"
								  "ptlang=2052&from_ui=1&pttype=1&dumy=&fp=loginerroralert&"
								  "action=2-11-7438&mibao_css=m_webqq&t=1&g=1")
							  % LWQQ_URL_LOGIN_HOST
							  % m_webqq->m_qqnum
							  % md5
							  % vccode
							  % m_webqq->m_status
							  % APPID
						  );

		m_stream = boost::make_shared<avhttp::http_stream>(boost::ref(m_webqq->get_ioservice()));
		m_stream->request_options(
			avhttp::request_opts()
			(avhttp::http_options::cookie, m_webqq->m_cookies.lwcookies)
			(avhttp::http_options::connection, "close")
		);

		m_buffer = boost::make_shared<boost::asio::streambuf>();

		avhttp::async_read_body(*m_stream, url, *m_buffer, *this);
	}

	// 在这里实现　QQ 的登录.
	void operator()(boost::system::error_code ec, std::size_t bytes_transfered)
	{
		std::istream response( m_buffer.get());
		if( ( check_login( ec, bytes_transfered ) == 0 ) && ( m_webqq->m_status == LWQQ_STATUS_ONLINE ) )
		{
			m_webqq->m_clientid = generate_clientid();
			//change status,  this is the last step for login
			// 设定在线状态.
			m_webqq->change_status(LWQQ_STATUS_ONLINE, *this);
		}else
		{
			using namespace boost::asio::detail;
			m_webqq->get_ioservice().post(bind_handler(m_handler, ec));
		}
	}
	// 登录完成 后的后续操作
	void operator()(const boost::system::error_code& ec)
	{
		using namespace boost::asio::detail;
		if(ec)
		{
			m_webqq->get_ioservice().post(bind_handler(m_handler, ec));
			return;
		}
		else
		{
			BOOST_ASIO_CORO_REENTER(this)
			{
				//polling group list
				BOOST_ASIO_CORO_YIELD m_webqq->update_group_list(*this);

				// 每 10 分钟修改一下在线状态.
				lwqq_update_status(m_webqq, m_webqq->m_cookies.ptwebqq);

				m_webqq->m_group_msg_insending = !m_webqq->m_msg_queue.empty();

				if( m_webqq->m_group_msg_insending )
				{
					boost::tuple<std::string, std::string, WebQQ::send_group_message_cb> v = m_webqq->m_msg_queue.front();
					boost::delayedcallms( m_webqq->get_ioservice(), 500, boost::bind( &WebQQ::send_group_message_internal, m_webqq->shared_from_this(), boost::get<0>( v ), boost::get<1>( v ), boost::get<2>( v ) ) );
					m_webqq->m_msg_queue.pop_front();
				}

				m_webqq->get_ioservice().post(bind_handler(m_handler, ec));
			}
		}
	}
private:
	std::string webqq_password_encode( const std::string & pwd, const std::string & vc, const std::string & uin)
	{
  //              ... 代码略 ...
	}

private:
	int check_login(boost::system::error_code & ec, std::size_t bytes_transfered)
	{
  //              ... 代码略 ...
	}

private:
	boost::shared_ptr<qqimpl::WebQQ> m_webqq;
	webqq::webqq_handler_t m_handler;

	read_streamptr m_stream;
	boost::shared_ptr<boost::asio::streambuf> m_buffer;
	std::string vccode;
};
```

在这个协程里, 有的**闭包**成员被 shared_ptr 管理, 有的没有. 
这些资源, 统统都没有使用显式的内存管理, 而是让这些对象随着闭包的撤销被自动的析构.

因为 ASIO 直接拷贝了 **闭包** 所以每次调用 asyn_* 簇的函数的时候, 当前闭包对象都被拷贝,  随后当前闭包被析构.

新生的闭包一直就存在 ASIO 的列队里, 直到操作完成. 然后被重新调用.  这就是 asio 协程的远离. 对象通过不停的拷贝而自我更新, 一直生存在 ASIO 的列队之中. 最后一次完成回调后, 对象就真正死去了.

# 少编写回调函数

协程的另一个作用就是可以少编写回调函数. 只要写一个闭包, 通过协程的 "多个入口多个出口" 的形式就可以 共享一个 **闭包** 而无须编写大量的 回调函数.

当然, 这也和 asio 对回调函数的形式进行了高度统一 的功劳是分不开的.


# 看起来像同步逻辑

虽然代码执行的时候是异步的, 但是如果抛开 yield 关键字不看, 整个代码俨然就是一个同步的逻辑.
这大大的简化了开发! 大大的简化了逻辑设计! 

