---
layout: post
title: NVIDIA 官方驱动支持 Optimus
---
各位，鄙人去年手贱，买了台 Optimus 的笔记本。最开始的时候用的 Bumblebee，但是觉得每
次用 optirun  非常的 egg pain。我想全局启用 NVIDIA 显卡（GT650M显卡买来不用浪费
啊！），而不是手动使用 optirun。

于是我折腾了  DRM/PRIME , 跑起了开源驱动，找到了PRIME的各种补丁，然后编译+折腾。终于
搞定。

虽然性能差了点（直到昨天我才知道，差的实现相当的大啊！）好歹比集显好多了。

前些天，NVIDIA 发布了  319.12 驱动，官方支持了 PRIME 和 xrandr 1.4  !

我乐死了，赶紧折腾。现在分享一下成功经验： PSGentoo下会easy很多。

首先，第一重要的是确保自己使用的是  3.9 内核。开启 intel 的 KMS , 去掉 nouveau 驱动。

然后确保 xorg  是最新版 !  xorg-server >= 1.13 !   
确保 xrandr 是最新版！ xrandr >= 1.4 !

然后，要使用 xf86-video-modesetting !! 而不是 xf86-video-intel ，记住！！ 很重要！

emerge xf86-video-modesetting

好了，非常关键的，需要 nvidia-drivers >= 319.12 !  

你需要做的就是 在 /etc/portage/package.unmask 解除 nvidia-drivers >= 319.12 版本的屏蔽.
然后再安装

好了，然后依据 http://us.download.nvidia.com/XFree86/Linux-x86/319.12/README/randr14.html 这个官方说明写好 xorg.conf 就可以了。

注意一下， BusID 是 使用  "02:00:0" 而 lspci 的输出是 02:00.0 ， 把这个小点换成冒号。

把 

    #！ /bin/bash
    xrandr --setprovideroutputsource modesetting NVIDIA-0
    xrandr --auto
添加到 /etc/X11/xinitrc.d/00-optimus (添加可执行权限)

eselect opengl set nvidia !!!! 很重要

搞定。

使用 modesetting 驱动而不是 intel 驱动，是因为我们只需要intel显卡执行输出，一切的 2D3D操
作都由 NVIDIA 显卡完成。实际上 就是使用 modesetting 驱动做了一个 mirror 功能，把 NVIDIA 
的内容 拷贝给 intel 显卡做输出。这个 mirror 是 硬件完成的( DMA) 不占用 CPU 时间，也没有多
次拷贝的问题，因此效率比 bumblebee 高很多。

如果需要 NVIDIA 显卡的HMDI接口外接显示器，Option "UseDisplayDevice" "none" 这个选项就
要去掉。否则要开启这个选项。

HDMI 功能也OK，多显示器很正常。

好了，使用官方的 Optimus 后才发现，我了个去，这笔记本的显卡你妹妹的快啊！操！ 比我台
式机快多了 555555555555555555

