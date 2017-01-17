---
layout: post
title: 无栈协程
tags: [asio]
---

在开始之前，先来看一段代码　

<pre style='color:#1f1c1b;background-color:#ffffff;'>
<span style='color:#0057ae;'>void</span> pop3::<b>operator</b>() ( <span style='color:#0057ae;'>const</span> boost::system::error_code&amp; ec, std::size_t length )
{
	<b>using</b> <b>namespace</b> boost::asio;

	ip::tcp::endpoint endpoint;
	std::string		status;
	std::string		maillength;
	std::istream	inbuffer ( m_streambuf.get() );
	std::string		msg;

	reenter ( <b>this</b> ) {
restart:
		m_socket.reset( <b>new</b> ip::tcp::socket(io_service) );

		<b>do</b> {
<span style='color:#006e28;'>#ifndef DEBUG</span>
			<i><span style='color:#898887;'>// 延时 60s</span></i>
			_yield ::boost::delayedcallsec( io_service, <span style='color:#b08000;'>60</span>, boost::bind(*<b>this</b>, ec, <span style='color:#b08000;'>0</span>) );
<span style='color:#006e28;'>#endif</span>

			<i><span style='color:#898887;'>// dns 解析并连接.</span></i>
 			_yield boost::async_avconnect(
 				boost::proxychain(io_service).add_proxy()(boost::proxy_tcp(*m_socket, ip::tcp::resolver::query(m_mailserver, <span style='color:#bf0303;'>&quot;110&quot;</span>))),
 				*<b>this</b>);

			<i><span style='color:#898887;'>// 失败了延时 10s</span></i>
			<b>if</b> ( ec )
				_yield ::boost::delayedcallsec ( io_service, <span style='color:#b08000;'>10</span>, boost::bind(*<b>this</b>, ec, <span style='color:#b08000;'>0</span>) );
		} <b>while</b> ( ec ); <i><span style='color:#898887;'>// 尝试到连接成功为止!</span></i>

		<i><span style='color:#898887;'>// 好了，连接上了.</span></i>
		m_streambuf.reset ( <b>new</b> streambuf );
		<i><span style='color:#898887;'>// &quot;+OK QQMail POP3 Server v1.0 Service Ready(QQMail v2.0)&quot;</span></i>
		_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
		inbuffer &gt;&gt; status;

		<b>if</b> ( status != <span style='color:#bf0303;'>&quot;+OK&quot;</span> ) {
			<i><span style='color:#898887;'>// 失败，重试.</span></i>
			<b>goto</b> restart;
		}

		<i><span style='color:#898887;'>// 发送用户名.</span></i>
		_yield m_socket-&gt;async_write_some ( buffer ( std::string ( <span style='color:#bf0303;'>&quot;user &quot;</span> ) + m_mailaddr + <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span> ), *<b>this</b> );
		<b>if</b>(ec) <b>goto</b> restart;
		<i><span style='color:#898887;'>// 接受返回状态.</span></i>
		m_streambuf.reset ( <b>new</b> streambuf );
		_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
		inbuffer &gt;&gt; status;

		<i><span style='color:#898887;'>// 解析是不是　OK.</span></i>
		<b>if</b> ( status != <span style='color:#bf0303;'>&quot;+OK&quot;</span> ) {
			<i><span style='color:#898887;'>// 失败，重试.</span></i>
			<b>goto</b> restart;
		}

		<i><span style='color:#898887;'>// 发送密码.</span></i>
		_yield m_socket-&gt;async_write_some ( buffer ( std::string ( <span style='color:#bf0303;'>&quot;pass &quot;</span> ) + m_passwd + <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span> ), *<b>this</b> );
		<i><span style='color:#898887;'>// 接受返回状态.</span></i>
		m_streambuf.reset ( <b>new</b> streambuf );
		_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
		inbuffer &gt;&gt; status;

		<i><span style='color:#898887;'>// 解析是不是　OK.</span></i>
		<b>if</b> ( status != <span style='color:#bf0303;'>&quot;+OK&quot;</span> ) {
			<i><span style='color:#898887;'>// 失败，重试.</span></i>
			<b>goto</b> restart;
		}

		<i><span style='color:#898887;'>// 完成登录. 开始接收邮件.</span></i>

		<i><span style='color:#898887;'>// 发送　list 命令.</span></i>
		_yield m_socket-&gt;async_write_some ( buffer ( std::string ( <span style='color:#bf0303;'>&quot;list</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span> ) ), *<b>this</b> );
		<i><span style='color:#898887;'>// 接受返回的邮件.</span></i>
		m_streambuf.reset ( <b>new</b> streambuf );
		_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
		inbuffer &gt;&gt; status;

		<i><span style='color:#898887;'>// 解析是不是　OK.</span></i>
		<b>if</b> ( status != <span style='color:#bf0303;'>&quot;+OK&quot;</span> ) {
			<i><span style='color:#898887;'>// 失败，重试.</span></i>
			<b>goto</b> restart;
		}

		<i><span style='color:#898887;'>// 开始进入循环处理邮件.</span></i>
		maillist.clear();
		_yield	m_socket-&gt;async_read_some ( m_streambuf-&gt;prepare ( <span style='color:#b08000;'>8192</span> ), *<b>this</b> );
		m_streambuf-&gt;commit ( length );

		<b>while</b> ( status != <span style='color:#bf0303;'>&quot;.&quot;</span> ) {
			maillength.clear();
			status.clear();
			inbuffer &gt;&gt; status;
			inbuffer &gt;&gt; maillength;

			<i><span style='color:#898887;'>// 把邮件的编号push到容器里.</span></i>
			<b>if</b> ( maillength.length() )
				maillist.push_back ( status );

			<b>if</b> ( inbuffer.eof() &amp;&amp; status != <span style='color:#bf0303;'>&quot;.&quot;</span> )
				_yield	m_socket-&gt;async_read_some ( m_streambuf-&gt;prepare ( <span style='color:#b08000;'>8192</span> ), *<b>this</b> );
		}

		<i><span style='color:#898887;'>// 获取邮件.</span></i>
		<b>while</b> ( !maillist.empty() ) {
			<i><span style='color:#898887;'>// 发送　retr #number 命令.</span></i>
			msg = boost::str ( boost::format ( <span style='color:#bf0303;'>&quot;retr %s</span><span style='color:#924c9d;'>\r\n</span><span style='color:#bf0303;'>&quot;</span> ) %  maillist[<span style='color:#b08000;'>0</span>] );
			_yield m_socket-&gt;async_write_some ( buffer ( msg ), *<b>this</b> );
			<i><span style='color:#898887;'>// 获得　+OK</span></i>
			m_streambuf.reset ( <b>new</b> streambuf );
			_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
			inbuffer &gt;&gt; status;

			<i><span style='color:#898887;'>// 解析是不是　OK.</span></i>
			<b>if</b> ( status != <span style='color:#bf0303;'>&quot;+OK&quot;</span> ) {
				<i><span style='color:#898887;'>// 失败，重试.</span></i>
				<b>goto</b> restart;
			}

			<i><span style='color:#898887;'>// 获取邮件内容，邮件一单行的 . 结束.</span></i>
			_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\r\n</span><span style='color:#bf0303;'>.</span><span style='color:#924c9d;'>\r\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
			<i><span style='color:#898887;'>// 然后将邮件内容给处理.</span></i>
			process_mail ( inbuffer );
			<i><span style='color:#898887;'>// 删除邮件啦.</span></i>
			msg = boost::str ( boost::format ( <span style='color:#bf0303;'>&quot;dele %s</span><span style='color:#924c9d;'>\r\n</span><span style='color:#bf0303;'>&quot;</span> ) %  maillist[<span style='color:#b08000;'>0</span>] );
			_yield m_socket-&gt;async_write_some ( buffer ( msg ), *<b>this</b> );

			maillist.erase ( maillist.begin() );
			<i><span style='color:#898887;'>// 获得　+OK</span></i>
			m_streambuf.reset ( <b>new</b> streambuf );
			_yield	async_read_until ( *m_socket, *m_streambuf, <span style='color:#bf0303;'>&quot;</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span>, *<b>this</b> );
			inbuffer &gt;&gt; status;

			<i><span style='color:#898887;'>// 解析是不是　OK.</span></i>
			<b>if</b> ( status != <span style='color:#bf0303;'>&quot;+OK&quot;</span> ) {
				<i><span style='color:#898887;'>// 失败，但是并不是啥大问题.</span></i>
				std::cout &lt;&lt; <span style='color:#bf0303;'>&quot;deleting mail failed&quot;</span> &lt;&lt; std::endl;
				<i><span style='color:#898887;'>// but 如果是连接出问题那还是要重启的.</span></i>
				<b>if</b>(ec) <b>goto</b> restart;
			}
		}

		<i><span style='color:#898887;'>// 处理完毕.</span></i>
		_yield async_write ( *m_socket, buffer ( <span style='color:#bf0303;'>&quot;quit</span><span style='color:#924c9d;'>\n</span><span style='color:#bf0303;'>&quot;</span> ), *<b>this</b> );
		_yield ::boost::delayedcallsec ( io_service, <span style='color:#b08000;'>1</span>, boost::bind ( *<b>this</b>, ec, <span style='color:#b08000;'>0</span> ) );
		<b>if</b>(m_socket-&gt;is_open())
			m_socket-&gt;shutdown ( ip::tcp::socket::shutdown_both );
		_yield ::boost::delayedcallsec ( io_service, <span style='color:#b08000;'>1</span>, boost::bind ( *<b>this</b>, ec, <span style='color:#b08000;'>0</span> ) );
		m_socket.reset();
		std::cout &lt;&lt; <span style='color:#bf0303;'>&quot;邮件处理完毕&quot;</span> &lt;&lt; std::endl;
		_yield ::boost::delayedcallsec ( io_service, <span style='color:#b08000;'>30</span>, boost::bind ( *<b>this</b>, ec, <span style='color:#b08000;'>0</span> ) );
		<b>goto</b> restart;
	}
}
</pre>
<!--  -->

这个代码，乍一看就是同步代码嘛！而事实上它是异步的

在这个代码里，使用了　\_yield 前缀再配合　async\_\* 异步函数，使用异步实现了同步的pop3登录算法。

这个神奇的代码，神奇之处就是 reenter(this) 和　\_yield。这2个地方就是实现的全部的关键。

我在群课程里有简单的提到过协程，有兴趣的可以到　[avplayer社区讲座：协程](https://avlog.avplayer.org/3597082/%E5%8D%8F%E7%A8%8B.html) 围观。




