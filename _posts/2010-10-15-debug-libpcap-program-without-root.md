---
layout: post
title: 如何避免使用 root 权限调式 libpcap 程序
---

工作原因，经常用 libpcap 写程序。

可是调式却一直是个大问题。

即便是非常麻烦地每次编译后 setuid 
gdb 也是不能调式 setuid 程序，gdb 会使 setuid 失效。
一直以来的解决办法都是原始的sudo + printf ， 而无法单步调式。实在有时候需要单步了，就 sudo eclipse 启动了
结果调式完毕之后还需要
 sudo chown cai:cai ~/workspace -R 

灰常的不爽

后来发现了 gdb-server

可以用 sudo gdb-server 启动要调式的程序，再在 eclipse 里选择 gdb/server 作为调式程序。
这样就不必为了调式而整个让 eclipse 启动到 root 环境了

可是，还是很不爽。每次调式前都要
 sudo gdb-server localhost:5000 我的程序 
 

后来，终于发现，我可以先用 dumpcap 抓取一定的包，然后保存到一个文件中.
只要把原先打开网卡的代码稍微改一下变成 
pcap_open_offline
 就可以了
而从文件开始读取，可以模拟非常巨大的网络流量，很考验处理程序.

而通过 有名管道，又可以轻易的支持 在线抓包调式。使用管道的时候经过我的测试，发现必须这样 
dumpcap -w - > /tmp/fifo 
 写才行。然后我的程序就可以把管道作为文件直接打开
发布的时候，代码再改回来，或则干脆就不改，作为一个命令行选项。