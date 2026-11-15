---
layout: post
title: NAS 的 pcie 短缺问题
tags: [network, 10G, NAS，pcie, M2, sata]
---

万兆网卡到货后，迫不及待的插上主板开机。

当时就注意到了一个问题，怎么有一个 SATA 控制器变成了 2port controller 了。也就是说只有6个 sata 口了。

然后和 pc 开始 iperf 测速。发现速度居然只有刚刚超过 2Gbps！！！
什么鬼？

然后把 pc 上的那个卡换了个插槽，换到 pcie x16 的显卡插槽上了。原来是我这个卡放到了最后一个 pcie 2.0 x2 的插槽上（物理形态是 x16)

再测，发现速度也是在  4Gbps 上下。然后进 nas 的 bios 发现， 我去！坑死我了。

原来这个主板的 pcie 和 sata 是2选1通道的。 配置模式是 pcie x4 + sata x4, pcie x2 + sata x6, 或者 sata x8 但是禁用 pcie .

我去，原来我只能折腾4盘位nas！ 一开始是 sata x8 但是只要 pcie 上插了卡，默认就是 pcie x2 + sata x6 模式。手动调节为 pcie x4 + sata x4 模式 后进系统， 果然达到了 9.4Gbps 的速度，然后改了 MTU 到 9000 就变成了 9.8Gbps 的速度了。

被这个主板坑死了。居然只能4盘位！！！！ 那么问题来了，群灰 DS1918+ 为啥不提供万兆，就是这个原因！诶！


等等，这个主板还有个 NVME 的插槽，这个好像是独享的带宽，没有和别的插槽共享。。。。

于是买了这个玩意

<img src="/images/m2_to_sata.jpg" >

最终还是达成了 8 盘位 + 万兆。

当然，目前只插了2个盘。

