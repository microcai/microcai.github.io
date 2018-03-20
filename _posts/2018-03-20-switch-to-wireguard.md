---
layout: post
title: 换用wireguard
tags: [VPN, wireguard, wg, network]
---

之前把家里网络 [/2018/02/22/network-reworked.html 重新折腾] 了一下, 用的是 走socks5 代理的 tcp 协议 openvpn. socks5 代理由 shadowsocks 提供.

不过, 最近偶然在 LWN 发现了 wireguard 这个新型 VPN, 于是盘算着用起来看看效果.
结果一不小心, 发现了[https://github.com/Lochnair/vyatta-wireguard], 这个可以让我的路由器也能用 wireguard!


于是按照它的文档配置到了路由器上, 然后VPS那边也配置下.

只是把路由器表里, vtun0 换成了 wg0 就好了, 其他的不需要换. 

完了之后测试了一下速度, 比 openvpn 的时候快了很多. 毕竟 UDP 嘛. vpn 这种东西还是适合 UDP 而不是 tcp 的.
而且在跑流量的时候, ping 的延迟不会增加. 如果是 tcp 则会因为发送窗口的关系, ping 的延迟会因为流量增加而迅速增加.
对网络的体验极其不好.

当然, udp 模式的 openvpn 其实也可以, 只是 openvpn 已经被墙识别了, 不可能直接用 openvpn 啦.
wg 毕竟新鲜事物, 到墙能识别故意要很长一段时间了. 这段时间内都可以安心的啦.

PS: 一开始担心机房屏蔽 UDP 包, 结果发现可以愉快的跑, 担心是多余的啦.
