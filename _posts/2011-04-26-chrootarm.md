---
layout: post
title: chroot to arm on an x86 Gentoo
---

在早上的邮件中，我指出 Gentoo 是如何方便的构筑交叉环境的。
现在，我要指出，我还要运行里面的arm程序！ 在 chroot 环境中，真正的把它当
作一个发行版！

我使用的是 crossdev -t arm-unknow-linux-gnueabi 编译的 arm 交叉工具链。
这时候 arm 其实被安装到了  /usr/arm-unknow-linux-gnueabi/

/usr/arm-unknow-linux-gnueabi/ 下面有完整目录结构，相当于一个 arm 发行版。

而且之后也会多了一个工具叫 arm-unknow-linux-gnueabi-emerge

我们的第一个主角就出来了。我们需要 busybox

USE="-ipv6 static -pam make-symlinks" \
        arm-unknow-linux-gnueabi-emerge busybox -av

之后我们的 /usr/arm-unknow-linux-gnueabi/ 其实已经可以作为一个基本完整的
arm 系统的根目录了。

我们需要第二个主角，一个解释器。qemu-user !

export QEMU_USER_TARGETS="arm"
export USE="-* static"
emerge qemu -av --root=/usr/arm-unknow-linux-gnueabi/ -O


这样 /usr/arm-unknow-linux-gnueabi/usr/bin/qemu-arm 就成为这个 arm 系统
的解释器了，注意，静态链接是必须的 wink.gif

接着，我们需要内核的支持
echo
':arm:M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/arm-unknow-linux-gnueabi/usr/bin/qemu-arm:'
> > /proc/sys/fs/binfmt_misc/register

当然，要需要第三个主角，一个 bash wink.gif
arm-unknow-linux-gnueabi-emerge bash -av



好了，准备工作就完成了。

chroot /usr/arm-unknow-linux-gnueabi/ /bin/bash

呵呵。 arm 结构的 bash 已经被运作起来咯 wink.gif

怎么样？
试试执行 ls wink.gif 哈哈

Good luck to every one 