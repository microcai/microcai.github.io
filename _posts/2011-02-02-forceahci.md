---
layout: post
title: force AHCI without BIOS
---

For long time, I've been using IDE mode for SATA.
长久以来，我一直在用SATA的IDE模式。

but, SATA-II 's 300MB/s transfer rate and  NCQ features are missing .
但是 ，SATA-II 的 300MB/s 速度和 NCQ 功能都用不上了。

So I decide to use AHCI.
于是我打定主意用 AHCI 了。

But there is no AHCI option in my BIOS setup. What a fuck! I'm sure ICH8 is capable of AHCI.
但是 BIOS 设置里却米有 AHCI ! what a fuck ! 但是我确信ICH8芯片组有 AHCI 功能。

I googled a  lot, but only one that try to modify NVRAM directly and then AHCI is enabled.
我搜了很多，只有一个人直接修改 NVRAM 启用了 AHCI.

But , some one in LKML uses setpci and fakephp to force set AHCI mode and rescan PCI bus to use ahci driver.
Linux邮件列表有人用setpci配合fakephp强制设置了AHCI模式重扫描PCI总线后用上了 ahci

But, I tryed but result as machine panic.
我用一下，死机了。

Googling , and found that grub2 also has setpci . What a hope!
继续搜发现grub2 也有 setpci 命令？。希望来了么？

recompile a kernel with AHCI only , and use lspci to remember pci address of my ICH8 SATA controller.
重新编译内核，只启用 AHCI 驱动，使用 lspci 记下 SATA 控制器的 PCI 地址。


reboot, and enter grub command line. 
重启到 grub 命令模式。

after excute setpci -d 8086:2828 90.b=40, machine hang
执行 setpci -d 8086:2828 90.b=40 后死机。

reboot, and enter grub command line. 
重启到 grub 命令模式。

excute setpci -d 8086:2828 90.b=40 after linux /vmlinux-ahci , machine boot , and desktop showsup!
linux  /vmlinux-ahci 加载内核后执行 setpci -d 8086:2828 90.b=40 ， 机器成功启动，桌面出现。

dmesg | grep NCQ 
dmesg | grep NCQ 

YES!, NCQ (31/32) , no longer NCQ (0/32) ， NCQ was enabled! AHCI was enabled!
是的 ，出现 NCQ (31/32) , 而不再是 NCQ (0/32), NCQ 启用了！ AHCI 启用啦！ 