---
layout: post
title: 中国电信原生IPv6配置
tags: [network, ipv6]
---

目前电信已经商用 ipv6 网络了，ipv6 的好处你懂得。

在继续之前，首先讲下，ipv6 同 ipv4 在配置上的不同。

对于家庭宽带，ipv4 是 pppoe 拨号的时候自动配置的。isp 给且仅给一个 ipv4 地址。
如果有多台设备需要上网，就需要使用一种叫 NAT 的技术进行网址共享。

但是 ipv6 地址有 128位那么长，世上每一粒沙子都能分配一个 ipv6 地址，意思就是分配不完的！
所以，运营商就很大方的给给你许多许多的 ipv6 地址了，也就不需要 NAT 啦！

由于不需要 NAT，因此在使用路由器共享上网的时候，配置就变得不同了。
使用 ipv4 的时候，路由器负责拨号，然后使用它自己的 DHCP服务器给局域网里的其他机器分配一个私有地址。
而到了 ipv6 的时候，情况就有所不同了，因为 ipv6 没有 NAT ，自然局域网里的机器并不需要也不能分配私有地址，而是需要获得一个全球唯一的地址。但是路由器也不是随便给你分配一个地址就行的，随机生成的地址并不一定能保证唯一性，而且也无法路由。isp 怎么能帮你路由一个随机的地址呢？
所以到了 ipv6 的时候，配置办法就变了一下。首先，路由器从 isp 获得 ipv6 地址，这个地址还是老办法，dhcp 自动获得。所以是 dhcp 从 pppoe 自动获得了 v4 和 v6 地址。这个没什么不同。
但是接下来就有不同点了。

接下来，LAN 口的地址配置开始不同了。 ipv4 是固定一个私有的 LAN 口地址，而  ipv6 则使用 dhcp-pd 这个技术从 isp 获得一个 公网地址。因为一般来说一个接口发 dhcp 请求是为了给自己获取地址，而这次，是给别的接口获得地址，所以这个叫 delegate 。又因为，isp 回给你的呢，是一个网段，而不是一般的dhcp给你一个地址。所以这个叫 prefix delegate. 

isp 给你一个网段，对电信来说，是给的一个 /60 的网段。在这个网段里，路由器自己随便 pick 一个主机地址，然后其余的就都可以做 pool 分配给 LAN 里的主机了。

因此，配置过程就是，首先 pppoe 拨号，接着 dhcp 获得 v6 地址，然后 dhcp-pd 为 LAN 获得地址。

但是，dhcp-pd 并不能为 LAN 内的主机获得地址。 LAN 内的主机如何获得地址呢？

答案是 radvd。radvd 的作用是，启动的时候找到 LAN 的地址，然后就知道 LAN 的网段了。然后把这个网段当 pool 给局域网的主机分配。为啥这样能工作呢？
因为 LAN 所在的那个网段， isp 已经分配给你的路由器了。意味着只要是那个网段的地址， isp 都会给路由到你的路由器由你的路由器再做下一跳转发。因此只要你局域网内的机器和路由器的 LAN 口在一个网段即可。


那么，配置的办法其实很简单， 就是

```bash
ubnt@ubnt:~$ configure
[edit]
ubnt@ubnt# set interfaces ethernet eth0 pppoe 0 ipv6 address autoconf
ubnt@ubnt# set interfaces ethernet eth0 pppoe 0 dhcpv6-pd rapid-commit enable
ubnt@ubnt# set interfaces ethernet eth0 pppoe 0 dhcpv6-pd pd 1 prefix-length /60
ubnt@ubnt# set interfaces ethernet eth0 pppoe 0 dhcpv6-pd pd 1 interface switch0 prefix-id 1
ubnt@ubnt# set interfaces ethernet eth0 pppoe 0 dhcpv6-pd pd 1 interface switch0 host-address ::7788
ubnt@ubnt# set interfaces ethernet eth0 pppoe 0 dhcpv6-pd pd 1 interface switch0 service slaac
ubnt@ubnt# commit; save; exit
ubnt@ubnt:~$ reboot
```

注意配置完成一定要重启。。。 这是相当长一段时间的教训啊！
