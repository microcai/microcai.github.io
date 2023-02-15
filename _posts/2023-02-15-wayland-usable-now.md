---
layout: post
title:  Wayland 已经可用
tags:   [wayland, kwin, plasma]
---

2023 年情人节, KDE 终于发布了 5 系列的最后一个版本: 等离子 5.27

经过十几年的雕琢, wayland 终于可用了.

既然 wayland 可用, 我就迫不及待的要删掉 Xorg 了.

给 xorg-server 去掉了 xorg, ```USE=-xorg emerge xorg-server```

然后 /usr/bin/Xorg 就拜拜了. 至于为啥还要编译 xorg-server, 是为了他提供的 Xwayland .

Xorg 没了后, 就可以顺利卸载 xorg-drivers xf86-video-* xf86-input-* 驱动了. Xwayland 并不使用这些驱动.

Xwayland 是不使用 Xorg 的驱动的. Xwayland 从 kwin 获得输入, 因此无需 xf86-input-* 驱动, Xwayland 本身是作为一个 wayland 客户端, 因此也不需要
xf86-video-* 驱动操作显卡. wayland 客户端用啥 GL 驱动绘制, Xwayland 也用啥 GL 驱动绘制. 驱动的自动选择交给了 libglvnd.

要同时给 Xorg 和 Mesa 写2个驱动的时代终于过去了. 虽然 Xwayland 仍然保留 X11 兼容性, 但是 Xwayland 不需要专门的驱动了.

PS: windows 其实是和 X11 一样的落后, 驱动要写2份. 一份给 GDI 调用的 2D 加速, 一份给 dx 调用的 3D 加速.

等离子体 5.27 还包括了一个非常非常重要的 fix , 就是支持了 text-input-v1 扩展协议, chrome 和一票 electron 程序, 终于不需要 xwayland 也能搞定输入法了.

也就是说, 等离子 5.27 终于把 wayland 变成了可以完全替代 X11 的东西了.
