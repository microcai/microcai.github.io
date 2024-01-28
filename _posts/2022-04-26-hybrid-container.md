---
layout: post
title:  异构容器
tags:   [qemu, systemd, systemd-nspawn, container, qemu-user]
---

# 路由器 引起的

路由器，基本上都是MIPS处理器。
而 PC，那铁定是 AMD64 的处理器。

因此，绝无可能把 PC 上的程序直接拷到路由器里跑。

因为 glibc 特有的 ABI 问题，也不能直接交叉编译。

gentoo 的 crossdev 工具虽然能方便的生成交叉工具链，但是编译出来的程序，放到路由器上还是会报告 glibc 的符号版本问题。

因此，我用 qemu 运行了一个 mips 的虚拟机，然后在虚拟机里编译。虚拟机里安装和 路由器相同的 os - Debian 9 MIPS。

