---
layout: post
title: NAS 换 Gentoo
tags: [network, 10G, NAS，pcie, M2, sata]
---



freenas 使用了一阵子，发现了几个严重的问题

- 软件严重缺乏
- 插件需要使用 jails 而 jails 的网络居然不能使用宿主网络必须桥接
- 桥接导致 mlx 驱动禁用网卡 tcp offload engine
- 不支持 RDMA，atom cpu 性能弱，无法跑满万兆带宽。
- 实际上很少使用 web 管理界面，多数情况下还是 ssh 上去直接敲命令
- 性能差

要想性能好，Gentoo 少不了。于是计划 nas 改用 Gentoo。首先要做的事情就是确保 Gentoo 可以使用 ZFS。

这个呢，我就先在自己机器上折腾了。首先重新编译内核，启用 zfs，安装好 zfs 工具，接着根分区的数据先备份，然后格式化为 zfs。然后拷贝回来。重启。完美启用 zfs。

具体的迁移步骤为：

1. 首先进行规划，我的 nvme 盘有2个分区， nvme0n1p1 500M 为 EFI 分区。nvme0n1p2 117G 为 ext4 挂到 / 。首先使用 e2fsresize 命令缩小分区，然后在空闲的地方创建 nvme0n1p3 分区。 50G. 由于 liveusb 系统不支持 zfs，因此做完这些步骤后重启回原来的系统。
2. zpool create -o mountpoint=none -R /newroot Gentoo nvme0n1p3 命令创建一个池。
3. zfs create Gentoo/ROOT
4. zfs set mountpoint=/ Gentoo/ROOT
5. rsync -xav / /newroot
6. 完毕后重启，设定 root=ZFS=Gentoo/ROOT
7. 接着 zpool attach Gentoo nvme0n1p3 nvme0n1p2 命令，将原先的 ext4 所在分区直接以 mirror 模式加入 Gentoo 池。
8. 等待 resilver 完成
9. zpool detach Gentoo nvme0n1p3 把 nvme0n1p3 这个分区分离出 Gentoo 池。
10. fdisk 重新调整分区，把剩余的空间重新划给 nvme0n1p2
11. zpool attache -e Gentoo nvme0n1p2 执行完毕后， Gentoo 池的大小就占满 nvme0n1p2 分区的大小了

这样 Gentoo 池就是 117G 大小了。ext4 无损切换为了 zfs。

在确认 Gentoo 可以支持 zfs 格式后，就开始了 nas 的重装计划。

实际上， freenas 是安装到 U 盘的。因此只要再拿一个 U 盘装个 Gentoo 然后换个 U 盘重启 nas 机器即可。而不是在 nas 上搞编译装系统，导致nas过长时间的停机。

虽然最后把 U 盘放 nas 上启动的时候遇到了问题，主要是 编译优化的问题，nas 的 cpu 不支持一些指令集。而我编译安装新的 nas Gentoo 的时候编译参数没有设定好。然而 freenas 系统没有 lscpu，因此最后搞清楚 c3558 有啥 cpu feature 是费了不少功夫。

成功的在 nas 上启动 Gentoo 后， zpool import 导入 freenas 下建的池成功，就进入了比较折腾的 配置 nfs 和 samba 的步骤了。。。 没有了 webui 还确实是麻烦了不少。

好在实际上这些配置只需要进行一次。并没有频繁的修改共享目录的问题。

配置完成后， 我的 PC 上就没看到 nfs server no response.. 消息了。