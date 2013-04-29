---
layout: post
title: avbot 4.2 新功能解释和实现
---
# 新功能 - 讲笑话

这是一个早就被呼吁的功能，今天抽空实现了。笑话这个功能实现起来有2个要点：
  > 第一，这个笑话虽然是隔十分钟讲一次，可是不能打断大家的讨论，所以是出现十分钟的空闲后才发

  > 第二，这个笑话需要从网页上抓取
  
第一个要点, 使用办法就是 Asio 提供的 deadline_timer. 
设定定时器超时 10min , 但是如果有人发言, 就重设时间. 通过链接到 avbot::on_message 就可以知道有没有人发言了.

实现起来非常简单,就是在 on_message 的时候重新设定定时器.

第二,笑话要从网上抓取. 这个使用了[徒弟](http://github.com/ericsimith/avjoke)写的解析代码了. 不过咱高级,使用的是 avhttp 进行 HTTP 访问. 徒弟他不懂事, 手写 HTTP 解析.

---
# 实现

将笑话模块实现为一个 class joke,  class joke 重载了 operator(), 也就是说,是个仿函数,本身就可以作为 on_message 的 slot . class joke 重载了多个 operator() , 一个用于 on_message 的 slot , 一个用户 deadline_timer 的 Handler. 

在用作 on_message 的 slot 的 operator() 里, joke 就做了一件事: 重设 timer
在 deadline_timer 的 Handler 里, 首先判断 timer 是到期了还是取消了. 取消的 timer 啥也 不干.

到期的话 调用 joker fetcher 来下载一个 joke , 然后调用 sender 发送 joke 就可以了. sender 是一个函数对象,由 main.cpp 传入. 其实就是把 avbot::broadcast_message 做了 bind 给 joke 用, 这样就把 joke 和 avbot 解偶了.

joker fetcher 也是一个函数对象,用于下载 joke , 但是 avbot 提供的另外一个构造函数重载里允许用户传入自己写的笑话下载器.
joke 提供了一个默认的 joke fetcher, 这个 joke fetcher 就是 徒弟写的那个代码的一个 AVBOT 风格化的版本.


所以整个代码实现都是非常简单清晰易懂的. 嘿嘿.



---


