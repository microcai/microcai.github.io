---
layout: post
title: 善待笔记本，启用intel集显的节能模式
---

在 XP 下用的时候，用计量插座，空闲功耗大概在 13W ~ 14W 之间。 

在 Gentoo 下用的时候，空闲功耗也在 20W 之上。 

很头痛。 

CPU 的节能已经打开，一直在 800M 最低频率运行呢！ 

恩，应该是 GPU 费电啊～～～ 有什么办法能让 intel 的 GPU 工作在节能模式呢？ 

答案是添加隐含的内核引导参数 

    i915.lvds_downclock=1 i915.i915_enable_fbc=1 i915.i915_enable_rc6=1 

神奇的参数。 

现在 Gentoo 空闲下来的时候，笔记本也是 13W ~ 14W 的功耗了。哦也 ～～ CPU 也没那么热了。 

 