---
layout: post
title: 无栈协程
---

在开始之前，先来看一段代码　

<img src="/images/stacklesscoroutine.png" >

这个代码，乍一看就是同步代码嘛！而事实上它是异步的

在这个代码里，使用了　\_yield 前缀再配合　async\_\* 异步函数，使用异步实现了同步的pop3登录算法。

这个神奇的代码，神奇之处就是 reenter(this) 和　\_yield。这2个地方就是实现的全部的关键。

我在群课程里有简单的提到过协程，有兴趣的可以到　[avplayer社区讲座：协程](https://avlog.avplayer.org/3597082/%E5%8D%8F%E7%A8%8B.html) 围观。




