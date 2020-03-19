---
layout: post
title: 根分区 ZFS 化
tags: [network, 10G, NAS，NFS, diskless]
---



自从用 freenas 接触到了 ZFS, 我就爱上了 ZFS , 变得愈发不可收拾.  50买了2个 320G 的二手盘放公司玩 raidz. 

只是拿 zfs 挂数据的话, 只要编译好 zfs 内核模块和 zfs 命令行工具即可. 但是,如果要 zfs 当 root 文件系统的话, 则免不了一番折腾.

为啥呢? 因为 zfs 不同于 legacy 文件系统, 他是集卷管理于一身的.

