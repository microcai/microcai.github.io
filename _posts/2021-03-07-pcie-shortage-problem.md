---
layout: post
title: ATX 机箱明明有7个pcie槽位
tags: [PCIe, pcie, PCIE]
---

去年的 [这篇文章](/2020/12/18/nas-upgraded.html) 里我受够了嵌入式 ATOM 处理器羸弱的性能而斥巨资购买了 锐龙 5600X 作为新的NAS机器的处理器。
通过 PCIe 拆分卡<img src="/images/pcie_bifurcation.jpg" class="inline-img" style="height: 8em; display:inline-flex; width: auto;">实现了 HBA 和 10G 网卡同时接入。把主板的 pcie x16 的显卡槽给利用上了。

但是，近期发现了一些好东西，就琢磨着给NAS插上。但是想到这些好东西都需要占用主板的 PCIe 槽的时候就犯难了。
锐龙处理器一共就20条可利用的 pcie 通道（还有4条接南桥，不可利用了）。16条给了显卡槽，4条给了第一个 M.2 槽。
_PS, intel 的桌面处理器算上南桥的4条也才20条pcie通道。更糟糕_

给显卡的那条我已经用带拆分的延长器给弄成了2条 x8 的，一条接了 HBA 一条接了网卡。可是，想多接几个 pcie 设备又怎么办？

*PC 平台最大的缺陷是PCIe通道数不足。*

甚至intel就靠卖pcie通道数赚钱。

明明 ATX 标准设定了7个扩展槽位！而ATX显然是PC的标准，不是什么服务器的标准。

虽然 ATX 标准是 PCI 时代的产物，但是 PCI 进入 PCIe 时代，主板也应该是把7条PCI槽升级为7条pcie槽。而不是就变成光秃秃的秃驴，就剩下显卡一个槽，剩下的就给 pcie x1 的打发乞丐。而且凑数的 pcie 还是南桥出的，还和 SATA/M.2 有冲突，二选一。

想到这点，我突然明白了为什么有人说，*EPYC 的精髓在单路*。

<img src="/images/ROMED8-2T-2(L).jpg" width="75%">

看这个主板，齐刷刷的7条pcie多漂亮！

