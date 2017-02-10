---
layout: post
title:  免费版的 PrimoCache
tags:   [iscsi, cache, fancycache]
---

去年DIY一个 NAS. 其实就是台 MINI PC. 自带一个很小的 mSATA SSD 用来装系统, 然后外接了一个大 HDD 做存储.

问题在于, 这个 大 HDD 是渣机械, 一开迅雷, 硬盘就被 100% 占用! 然后导致整个 OS 响应迟缓. 然后因为 HDD 写入速度不足, 导致迅雷下载速度 0 . 磁盘疯狂写入. 

后来下了一个 PrimoCache ( 以前叫 FancyCache ) 后, 问题解决了.

然而只有 60 天试用期. 60天过去了, 我又得回到原来的老状态了吗? 非也!
我发现了一个叫 StarWind 的 iscsi software target. 只要装了 StarWind 就可以把 PC 变成一个 iscsi 的目标存储设备.
接着, 因为装的是 Windows Server 2012 R2 系统, 所以是自带了 iscsi 发起程序的. 于是把 127.0.0.1 的目标连起来.
于是写入路径就变成了 本地磁盘 D -> windows iscsi -> 本地网络 -> StarWind -> 原本地磁盘 D 

虽然经过了多道程序的折腾, 但是因为 StarWind 提供了 写入缓存!!! 于是, 迅雷又不卡了.



StarWind 有免费版哦! 可以一直免费用下去, 没有试用期限制, nice!



