---
layout: post
title: avbot 结构解释
tags: [avbot]
---

avbot 由 4 大部分构成 libavbot libavlog botctl avbotrpc

       +----------+            +----------+        +----------+
       | libavlog |            | libavbot | ---+---| libwebqq |
       +----------+\         / +----------+    |   +----------+
                     main.cpp                  |   
       +----------+/         \ +----------+    |   +----------+
       |  botctl  |           \| avbotrpc |    +---| libxmpp  |  
       +----------+            +----------+    |   +----------+
                                               |
                                               |   +----------+
                                               +---+  libirc  |
                                               |   +----------+
                                               |
                                               |   +------------------+
                                               +---+  libmailexchange |
                                                   +------------------+


中间由 main.cpp 作为胶水粘合。

---

libavlog 的任务是生成日志文件，botctl 的用处是实现 .qqbot 控制指令。
avbotrcp 用于实现 JSON-RPC

# libavbot 则是核心功能。

---

libavbot 由 libwebqq libirc libxmpp libmailexchange 4个子协议组成。

libmailexchange 同时又分 libsmtp libpop3 和 libInternetMailForamt 3个小模块。

---

衔接 libavlog botctl avbotrpc 和 libavbot 的东西就是 class avbot 的一个成员 on_message.

在 main.cpp 里，包含了 mybot.on_message.connect(XXX) 调用，将 avbot 和 其他3 个模块衔接起来。 

	  // 记录到日志.
	  mybot.on_message.connect(boost::bind(avbot_log, _1, boost::ref(mybot)));
	  // 开启 bot 控制.
	  mybot.on_message.connect(boost::bind(my_on_bot_command, _1, boost::ref(mybot)));

以及 

<pre style='color:#1f1c1b;background-color:#ffffff;'>
<span style='color:#0057ae;'>static</span> <span style='color:#0057ae;'>void</span> avbot_rpc_server(<span style='color:#23a45b;'>boost::shared_ptr</span>&lt;<span style='color:#23a45b;'>boost::asio::ip::tcp::socket</span>&gt; m_socket, avbot &amp; mybot)
{
	<span style='color:#808080;'>detail::avbot_rpc_server</span>(m_socket, mybot.on_message);
}
</pre>


on_message 是一个 boost::signals , 每当 QQ/IRC/XMPP/pop3 收到消息的时候就发起这个信号。libavlog 解析这个信号，然后将消息写入日志。avbotrpc 解析这个信号，然后返回给调用者。botctl 解析这个信号，提取其中的消息，识别其中的命令，然后写入日志文件。

libavbot 则实现了消息转发和群组功能。libavbot 并不藉由自己全部实现协议，而是交给了 libwebqq libirc libmailexchange 和 libxmpp 4 个协议库去实现协议。

libwebqq 从 pidgin-lwqq 项目借用了大量的代码，然后将其从 C 语言改写为安全的 Boost 形式。使用了 avhttp  这个 avplayer 社区发起的 HTTP 库进行Web访问。

libirc 由 “猫” 贡献，非常的简单。

libxmpp 是 gloox 的一层包装。将 gloox 包装为融入 Boost.Asio 中。而无需另外的线程跑其EventLoop。libxmpp 使用了一些Hack技巧将 gloox 改造为了 可以使用 Boost.Asio. 

libmailexchange 包含了 libInternetMailForamt 库用于解析复杂的 Internet Mail Foramt, 以及两个小库用户执行 POP3 接收和 SMTP 发送。





