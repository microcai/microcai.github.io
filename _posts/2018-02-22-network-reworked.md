---
layout: post
title: 网络重新配置
tags:   [EdgeOS, home, network, VPN, shadowsocks]
---

一直以来, 我用的都是基于 ss-redir 和 ipset + iptables 透明代理方式的科学上网. 但是 iptables 方式的上网, 其实还是不如 ChinaRoute 配合 VPN 来的爽. 因为只有 TCP 连接能被透明代理出去, UDP 和 ICMP 协议统统不能.

但是 openvpn 这种协议实在是太过招摇, 所以早就被方校长盯上了. 不可不可.

后来, 我想到了openvpn 可以透过纸飞机的代理再去连接远程服务器, 这样一来, 就解决了 openvpn 过墙问题.

于是直接在服务器上安装 openvpn 然后设定为使用 tcp 协议, 监听 127.0.0.1 地址.

然后在路由器上配置 openvpn , 只要配置文件里设定 socks-proxy xxx:1080 , 然后 remote 为 127.0.0.1 1189 就好了.
因为路由器是 ubnt ER-X, 自带 openvpn , 只需要自己编译 ss 就好, 不过因为最近买了个 群晖的 NAS, 于是懒得折腾交叉编译 ss 了, 直接在 NAS 上用 opkg install shadowsocks-libev 安装了纸飞机. 路由器上使用 NAS 上的 ss 代理就好了.

vtun0 网卡正常上线并获取到ip地址后, 先 ping 下 vtun0 的网关 10.8.0.1 , 发现是 OK 的. 接下来就是配置 route 了.

其实这个时候有2个办法配置路由表. 一个办法是使用 ChinaRoute 脚本. 让 openvpn 拨上后自动执行.
另一个办法呢, 还是使用 ipset + policy route.

chinaroute 这个, 任何路由器都能用, 这里讲下 ipset 和 policy route 在 ubnt 的路由器上如何使用.

虽然底层实现就是 iptables 做 rt-mark 然后用非默认的 route table 做路由, 但是ubnt把这套机制给简化了.

首先是在 protocol.static.table. 下面设定一个过墙用的路由表. 这个路由表很简单, 就只有一条 默认路由到 vtun0.

<code>
set protocols static table 10 description "route to VPN"
set protocols static table 10 interface-route 0.0.0.0/0 next-hop-interface vtun0
</code>

注意, 因为使用的是 tun 模式, 所以是 interface-route, 如果是 tap 模式,则是 ```set protocols static table 10 route 0.0.0.0/0 next-hop 10.8.0.1```

因为 tun 是点对点设备, 只要指定下一跳的接口, 而 tap 是虚拟以太网卡, 需要指定网关的 ip 地址.

这样就设定了一个 id 是 10 的路由表, 表里只有一条到 VPN 的默认路由.

这个在普通 Linux 里, 设定的方式似乎是在 /etc/iproute2/rt_tables 里配置. 略微麻烦.

接着, 设定防火墙, 让 匹配某个 ipset 的包都通过 10 号路由表出去. 如果在 Wizard 向导里, 启用了 2WAN 负载均衡的话, 这个时候会已经创建好一个叫 balance 的 防火墙规则.
规则的rule xx 之类的, 都是负载均衡的规则. 执行次序是数字从小到大. 这里我插入了个编号 60  的规则


<code>
set firewall modify balance rule 60 action modify
set firewall modify balance rule 60 modify table 10
set firewall modify balance rule 60 destination group address-group gfwlist
set firewall modify balance rule 60 description "use vtun0 to route gfwlist"
</code>

这条规则的意思是, 匹配目的地址为 gfwlist 组, 使用 10 号路由表.

在 EdgeOS 里, address-group network-group 之类的都是使用 ipset 实现的. 所以, 只要在 firewall 里弄个 gfwlist 地址组, 就会有个 gfwlist 的 ipset. 不需要在 EdgeOS 的配置里填入地址, 稍后我们用 dnsmasq 填入 ipset. 使用 ```set firewall group address-group gfwlist``` 这个命令建立 gfwlist 这个地址组.

如果么使用wizard搞 load balance, 则不会有这个  balance 规则. 可以自己建立. ```set firewall modify balance``` 就建立了.
然后需要在 switch0 里, 导入这个规则.  ```set interfaces switch switch0 firewall in modify balance``` 这个意思是, 所有从 switch0 收到的包(这里in的意思), 都要经过 balance 这条规则修改.

接下来是让 dnsmasq 填入 ipset. 使用的方法是 gfwlist2ipset 这个脚本, 生成一个 dnsmasq-ipset.conf 文件, 丢到路由器的 /etc/dnsmasq.d/ 目录下就可以了.

对了, 别忘记, 如果 gfwlist2ipset 用的 8.8.8.8 这个外网dns, 要使用 ```set protocols static interface-route 8.8.8.8/32 next-hop-interface vtun0``` 这条命令, 给 8.8.8.8 地址设定下路由, 使用 vtun0 接口出去. 同样的, 如果是 tap 类型的设备, 要使用 ```set protocols static route 8.8.8.8/32 next-hop 10.8.0.1```

