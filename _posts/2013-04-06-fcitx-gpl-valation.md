---
layout: post
title: fcitx 违反了 GPL2 ? (更新, 已解决)
---

fcitx 是 yuking 的作品。 一直以来都是以 GPL2 协议发布。

yuking 后来将维护权交给了 csslayer. csslayer 开始了 fcitx 4.X 系列的维护工作。

最近我查看了fcitx 4 的协议， 发现 fcitx4 将自己的协议降级了。而且降级并没有说明获得过 yuking 和其他贡献者的同意。

按照 GPL2 的协议， 升级(就是变得比GPL2 还要严格，比如升级到 GPL3)是被允许的。 但是降级（也就是提出了可以不遵守GPL2的例外）显然是不被允许的。

按照通行法则，软件作者具备更改授权的权利。那么 csslayer 具备这个更改授权的权利么？
那就要看 fcitx 是不是 csslayer 的个人作品了。如果 fcitx 包含了许多人的工作，那么 csslayer 要更改 fcitx 的协议就必须获得所有 fcitx 贡献者的首肯。

明显 fcitx 4 更改协议的时候并没有获得yuking 和其他贡献者的同意。如果确实获得了他们的同意，我希望 csslayer 能公开声明获得了他们的同意。


---

# 更新

傲慢的 csslayer 承认了错误，向 yuking 获得了同意。参考 [这个邮件](http://uploads.csslayer.info/uploads/mail/mail.mbox)

现在 fcitx 应该没什么大问题了。



