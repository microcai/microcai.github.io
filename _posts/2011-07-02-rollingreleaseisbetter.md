---
layout: post
title: 定期发布 Release 不适合现代 Linux Distro
---

我想说，定期发布 Release 这种模式已经过时了！ 

想想看 ubuntu 的 LTS 版本是如何在生命周期结束前就过时的吧！ 

上一个 ubuntu TLS 版本，居然不包含 gtk3 , 如果要实用一点，基本上要添加一 大堆的 PPA. 
而使用 PPA 基本上就和 TLS 的理念背道而驰了。 

dabian 这样的发行版，基本上的发布前就过时了。 

! 没错。 glibc, core-utils 这样的软件需要稳定！

那么用旧一点的版本确实是比较稳定. 

问题是，gnome KDE 这样的软件，反而是新版本比较稳定。

这样 TLS 这种追求旧 版本的发行版，其实除了基础包，别的包都是在使用的不稳定版本，反而美其名 曰：stable. 

  最明显的例子， KDE 4.6 发布的时候，是 KDE 最稳定的时候，这个时候 debian 里刚刚有 KDE4 .... 最不稳定的 KDE 4 .... 恩，还美其名曰 : stable。 
  而 experimental 仓库里的 KDE 4.6, 恩， experimental, 其实才是最稳定的。 
  对于多数软件来说，大版本号最第二大，小版本号最大的软件才是最稳定的。 

    比如说， Linux, 2.6.39 显然没有 2.6.39.2 来的稳定。虽然后者是后来出现的。

dabian 的哲学来说，就是不稳定的。 定期发布 Release , 意味着必须使用稳定版本，否则就等于发布 unstable ， 这是不行的。
但是稳定版本，通常是比较新的版本，这样定期发布 Release , 意味着必须使用过时的版本。

恩，其实过时的版本包含了巨大的危险性。因为已经不再被 upstream 支持了。 

#### 你说 ， upstream 支持的版本稳定还是不支持的版本稳定呢? 只有使用 rolling update 才能解决这个问题。 

你看， KDE 4.6 一发布，没过 几天， Gentoo 里就标记为 stable , 就是不用开 ~ARCH 就能安装了。
这样的软件，自然新版本稳定。 再比对 gcc 这样的软件。 4.6.x 的 gcc 一直被 hand mask 4.5.x 的 gcc 被标记为 ~ARCH 4.4 的 stable ，不是 4.4 , 是 4.4 系列里的最后一个版本，谢谢。 而 GNOME , KDE 这样的软件，stable 的版本就是当前的最新 Release. unsable 的版本是当前最新的 -RC 版本。 
不得不说， Gentoo 在软件稳定性上比任何发行版都要做的好。 因为Gentoo有独门秘籍，rolling update. 
当然， ARCH 这样的为何 rolling update 也不稳定呢？
因为 ARCH 这样的发行版，任何软件包只能有一个版本在仓库里。
不像 Gentoo , Gentoo 可以放 N 多版本进去，任用户随意选择。 


rolling update + selectable version, 这是 Gentoo 稳定性压倒一切发行版的 同时软件又够新的秘密。