---
layout: post
title: 多WAN平衡
tags: [network, multiwan, loadbalance, asio, c++]
---

曾经我也搞了两条宽带，见 [使用邻居的CMCC网络](/2016/12/07/use-neighbor-CMCC.html) 。
然后利用路由器的loadbalance就可以使用多条线路了。
但是，问题恰恰在这里。效果并不好。因为2条宽带并不是一样容量的，对同一目标的访问速度也不尽相同。所以退而求次，选择了只把某些 cmcc 访问速度更快的目标通过 邻居网络出去。

虽然我换了一个城市，然后选择了CMCC，也没有破解邻居的电信宽带wifi密码。但是多年前的失败经历还是让我感觉需要某种自动的机制自动的探测目标网络使用哪条线路是最快的。

这就是 [smartproxy](https://github.com/microcai/smartproxy) 的了。





