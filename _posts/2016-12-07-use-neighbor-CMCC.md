---
layout: post
title: 使用邻居的CMCC宽带加速
---

基于某些特殊原因，我知道邻居家的wifi密码。

但是他家信号在我家虽然能收到，但是比较弱。所以一直没用。最近从newbie获赠了一个叫 Ubnt AirMAX 的山寨产品，有个定向天线。
这使得我可以在家接收邻居家的信号了。于是就开始用啦！

先上图。

<img src="/images/fakeairmax.jpg" >

这是在阳台装好的效果。这货还支持 POE 供电，非常不错，网线到就可以干活了。

邻居家使用的是CMCC的网络，这是我要连上他家网络的主要原因。因为据说 CMCC 的出国带宽好啊! 而我呢，则是重度的墙外网络使用者。
所以想用他家的网络来加速我的国外访问。

连接的办法是 ERX -> POE交换机 -> 山寨网桥。

POE 交换机是网管交换机，所以划了单独 VLAN 给网桥。我用了 port 2 接的网桥，划分了 vlan 3389, pvid = 3389 。 由于我用的 port 7 接的 ERX。port 7 做 trunk 端口，允许通过  3389 即可。 ERX 的 eth2是接入的交换机，所以在 eth2 上创建 vlan 3389 即可。在 eth2.3389 接口上配置 ip 地址，静态 192.168.100.2 。因为邻居家是  192.168.100.0/24 的网络嘛。

然后在 ERX 上 ping 192.168.100.1 成功。意味着能连上邻居的路由器了。

接着为 eth2.3389 接口开 NAT 伪装。这是必要的。因为我不想在邻居家的路由器上配置静态路由表 —— 因为他家的路由器并不支持动态路由协议 —— 当然我也不希望我家内部的网络被他访问到。


接下来才是重点。我需要做策略路由, 要求如下：

对所有 CMCC 的ip地址，通过他家访问。
对部分 CMCC 访问更快的朝外地址，用他家访问。
但是如果他家的网络不通了，以上策略路由要立即 fallback 到使用我自己家的网络。
只对 NAS 直接执行 1:1 负载均衡做宽带叠加，把 CMCC 和我家的宽带进行叠加。因为 NAS 上跑迅雷下载，需要大带宽。
对其他不需要 CMCC 加速的地址，使用 1:1 宽带叠加我双拨的2条PPPOE线路。
但是对于网银地址，不使用叠加（防止 ip 跳动导致的登录问题）。


于是，折腾了一下 ERX 的 firewall 规则，搞定。

基本思路是，使用 ERX 自带的 load-balance 功能。 load-balance 建立3个组，叫 A  B C 吧。

A 组，包含 pppoe0 pppoe1 两条线路，做负载均衡。
B 组，包含 eth2.3389 和 pppoe0 两条，pppoe0 做 fallback-only。
C 组，包含 pppoe0 pppoe1 eth2.3389 三条线路，做负载均衡。

关键规则如下：

对 src 为 NAS 的流量，使用 C 组。

```json
 rule 60 {
     action modify
     description "use CMCC for NAS"
     modify {
         lb-group C
     }
     source {
         address 100.64.1.10
     }
 }
```

对 dst 为 cmccip 的线路，使用 B 组。

```json
 rule 70 {
     action modify
     description "use CMCC for cmcc ip"
     destination {
         group {
             network-group cmcc-ip
         }
     }
     modify {
         lb-group B
     }
 }
```

防止银行被负载均衡

```json
 rule 50 {
     action modify
     description "do not load blance on some site"
     destination {
         group {
             network-group bank
         }
     }
     modify {
         table main
     }
 }

```



默认做负载均衡

```json
 rule 999 {
     action modify
     modify {
         lb-group A
     }
 }

```

这样就搞定了。只要把相应的 IP 加到 network-group 里就可以了。
我是用的 http://bgp.he.net/AS9808 获取的 移动的 IP 段。

