---
layout: post
title: avbot 的一些技术决定
tags: [asio, avbot]
---

avbot 早已实现最初的目标 : 提供一个机器把 IRC/XMPP和 QQ群联合起来. 让不使用QQ的人和只使用QQ的人都恩嗯畅快的交流.

现在该歇息片刻, 回顾一下这一段历程, 以及编写avbot的时候所做的一些技术决定了.


# Boost.Asio
 为什么 avbot 会使用 Boost 进行开发呢? Boost 有什么 好处? Asio 是干嘛的?

我觉得对于 Asio,  [Jack 的那篇讲座][1]  足以解释的很清楚了.  Asio 是一个非常强大的网络库. 从一开始就选择了 Asio, 让 avbot 的后续开发不仅仅变得更轻松, 更重要的是, 我从 asio 那里学到了受用不尽的财富.

# avhttp

avhttp 可以说是 avbot 催生的一个项目. 如果不是 avbot , Jack 编写 avhttp 的动力也不是那么浓. 可能会更晚的时候开始编写, 也可能就不会开始编写.

avhttp 是 Asio 思维的典型产物. 不过因为Jack个人喜好问题,  avhttp 里模板的使用还是太少了, 个人认为绝对是个遗憾.

在使用 avhttp 之前, avbot 使用的HTTP网络库是 Urdl . 是个已经死掉的项目. avbot 不得不对 Urdl 进行了修改, 才让其支持了 Cookie 和一些其他 webqq 需要用到的 HTTP 头选项.


# gloox

avbot 最初的版本只支持了  IRC 和 WebQQ. 紧接着 avbot 就实现了 XMPP 协议支持. avbot 有着严格的 单线程 要求. 因此不得不寻找能够和 Asio 进行集成的 XMPP 库.  我尝试过很多的库, 最终选定了 gloox. 

gloox 虽然并不是 Boost 和Asio 开发的, 但是通过 派生并重载其 TcpConnection 类, 在其重载的方法里我还是有办法调用 Asio 执行网络操作的.  我并不使用 gloox 自身的 IO 代码, 而是利用C++的多态机制重载掉 原来的网络  IO 代码. 这样就能使用主线程跑的 asio 为 gloox 提供网络操作. 如此以来 avbot 就可以继续单线程了.

# 协程

avbot 可以说就是协程化的单线程程序典型. 

我第一次尝试使用协程,  是在为 avbot 添加 POP3 协议处理的时候. 协程实现的 POP3 协议处理代码, 将我深深震撼了.

虽然是纯异步代码, 但是其代码简洁到比同步处理的还要少. 

在进入 reenter() 之前我就统一了错误处理, 导致写出了比同步过程还要简洁的代码.

从此之后我就愈发不可收拾. 并将许多 libwebqq 上用回调套回调的代码重写为了协程.

因为协程实在太好用了, 直接导致了我的沉迷.

**如果不是对异步的追求, 我也不会喜欢上协程吧**

# 验证码

一直以来, avbot 都是通过让好友在 IRC 输入验证码发方式对付 腾讯.

直到我的一个死对头 csslayer (写 fcitx 的那位)  \[ [恩怨参考](http://microcai.org/2013/04/06/fcitx-gpl-valation.html)   \] 开始使用 avbot. 他将avbot用在了 opensuse 的 irc 聊天室, 然后 opensuse 社区的大姐头 给我提供了一个非常有用的建议, 就是使用 印度阿三的人肉验证码服务.

这让一直在苦思冥想 机器识别算法的我豁然开朗. 于是就有了 avbot 7.0 的推出.


  [1]: /t/asio-jack-q/151/8avbot 早已实现最初的目标 : 提供一个机器把 IRC/XMPP和 QQ群联合起来. 让不使用QQ的人和只使用QQ的人都恩嗯畅快的交流.

现在该歇息片刻, 回顾一下这一段历程, 以及编写avbot的时候所做的一些技术决定了.


# Boost.Asio
 为什么 avbot 会使用 Boost 进行开发呢? Boost 有什么 好处? Asio 是干嘛的?

我觉得对于 Asio,  [Jack 的那篇讲座][1]  足以解释的很清楚了.  Asio 是一个非常强大的网络库. 从一开始就选择了 Asio, 让 avbot 的后续开发不仅仅变得更轻松, 更重要的是, 我从 asio 那里学到了受用不尽的财富.

# avhttp

avhttp 可以说是 avbot 催生的一个项目. 如果不是 avbot , Jack 编写 avhttp 的动力也不是那么浓. 可能会更晚的时候开始编写, 也可能就不会开始编写.

avhttp 是 Asio 思维的典型产物. 不过因为Jack个人喜好问题,  avhttp 里模板的使用还是太少了, 个人认为绝对是个遗憾.

在使用 avhttp 之前, avbot 使用的HTTP网络库是 Urdl . 是个已经死掉的项目. avbot 不得不对 Urdl 进行了修改, 才让其支持了 Cookie 和一些其他 webqq 需要用到的 HTTP 头选项.


# gloox

avbot 最初的版本只支持了  IRC 和 WebQQ. 紧接着 avbot 就实现了 XMPP 协议支持. avbot 有着严格的 单线程 要求. 因此不得不寻找能够和 Asio 进行集成的 XMPP 库.  我尝试过很多的库, 最终选定了 gloox. 

gloox 虽然并不是 Boost 和Asio 开发的, 但是通过 派生并重载其 TcpConnection 类, 在其重载的方法里我还是有办法调用 Asio 执行网络操作的.  我并不使用 gloox 自身的 IO 代码, 而是利用C++的多态机制重载掉 原来的网络  IO 代码. 这样就能使用主线程跑的 asio 为 gloox 提供网络操作. 如此以来 avbot 就可以继续单线程了.

# 协程

avbot 可以说就是协程化的单线程程序典型. 

我第一次尝试使用协程,  是在为 avbot 添加 POP3 协议处理的时候. 协程实现的 POP3 协议处理代码, 将我深深震撼了.

虽然是纯异步代码, 但是其代码简洁到比同步处理的还要少. 

在进入 reenter() 之前我就统一了错误处理, 导致写出了比同步过程还要简洁的代码.

从此之后我就愈发不可收拾. 并将许多 libwebqq 上用回调套回调的代码重写为了协程.

因为协程实在太好用了, 直接导致了我的沉迷.

**如果不是对异步的追求, 我也不会喜欢上协程吧**

# 验证码

一直以来, avbot 都是通过让好友在 IRC 输入验证码发方式对付 腾讯.

直到我的一个死对头 csslayer (写 fcitx 的那位)  \[ [恩怨参考](http://microcai.org/2013/04/06/fcitx-gpl-valation.html)   \] 开始使用 avbot. 他将avbot用在了 opensuse 的 irc 聊天室, 然后 opensuse 社区的大姐头 给我提供了一个非常有用的建议, 就是使用 印度阿三的人肉验证码服务.

这让一直在苦思冥想 机器识别算法的我豁然开朗. 于是就有了 avbot 7.0 的推出.


  [1]: /t/asio-jack-q/151/8
