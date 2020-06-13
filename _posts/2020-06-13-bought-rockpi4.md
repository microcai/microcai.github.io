---
layout: post
title: 入手了一个 rock pi 4b
tags: [arm, aarch64, archlinux, pi, rockpi]
---









闲来无事，又打起了ARM的主意。Rpi3 的性能实在受不太了。毕竟只有 100M 网络。内存也就1GB。想干点啥都不行。寻思着弄个性能好点跟的上时代的 arm 板子玩玩。

先是找 archlinuxarm 看看有没有啥支持的板子。结果发现都不是啥好板子。后来搜 香蕉派的时候，发现了 rock pi。rock pi 4b 看参数，给力。于是下单了一个 4G 内存的版本。这 rock pi 最吸引我的地方是有一个 M.2 插槽，而且支持从 nvme 启动系统。终于可以丢掉渣 SD 卡了啊。

于是马上下单买了一个。



过了几天到了，把官网上提供的 debian 系统给 dd 到 nvme ssd。然后发现无法启动。

先研究 nvme 启动吧。cpu 并不支持从nvme 直接启动。或者说 cpu 内带的 bootrom 只支持 SPI/sd/emmc 三个启动方式。那么就需要先让 bootrom 载入一个 loader，这个 loader 再从 nvme 载入系统。但是我又不想插 sd卡，于是就需要有 SPI flash。

然后他这个板子是有焊接上 SPI Flash的，但是却没有烧bootlader进 Flash。

所以默认还是只能 SD卡启动。于是先把他官方提供的 ubuntu img 给 dd 到 SD 卡然后启动。

然后按照 wiki 把 spi 版的 uboot 给刷入板子上的 SPI flash。

于是 nvme 上的 debian 可以在不插 sd卡的情况下启动了。

但是！我讨厌 debian 啊！

于是最简单的做法，就是把 rootfs 给删了，把 Archlinux-aarch64-latest.tar.gz 给解压到 rootfs分区。

然后boom，可以开机进入了 arch。

but ，内核还是他 4.4 的 debian 内核。4.4 内核太老了！连 io_uring 都么有。这怎么可以，我要用 arch 自己的内核启动！

于是折腾 boot 好几天，都失败告终。一直黑屏，也不知道问题出在哪里。还自己编译了 uboot 和 内核，都失败告终。就是不能启动。

最后，最后的最后，我还是低头了，买了一个 USB TTL 线。。。。

然后果然就看到 内核的错误输出了。。。。 果断修正。。。

终于在昨天把系统折腾好了。



还有个小插曲，买的 USB TTL 线居然不支持 1.5M 波特率。。。搞的我只好重新编译 uboot 设定默认波特率为 115200. 然后才能看到 uboot 日志，修正了 extlinux.conf 的写法，然后看 kernel crash 日志，再重新编译内核。

最后，尝试了一下arch的自带内核，看到了日志，发现原来是他打的 initramfs 没有 nvme.ko .... 手动添加到配置文件里重新打包就解决了。。。 



顺便安利下 Gentoo，交叉编译内核和 uboot 的时候，本以为会很麻烦，结果 crossdev -t aarch64-linux-gnu 一条命令搞定交叉工具链。。。。。



Gentoo 果然是最适合程序员的操作系统！