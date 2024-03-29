---
layout: post
title:  更高采样率，更低成本
tags : [audio]
---

在继续本文之前，容我提出一个摩尔定律的推论： 离摩尔定律越近，发展越快，成本越低；反之，离摩尔定律越远，发展就越缓慢，成本也难以下降。

\[待续\]

---
 === 2023 年 12月 21 日填坑 ===

没想到，当年的一篇文章，我居然没完成。挖坑了这么久。

这次来回填。

---

在玄学HIFI领域，是反摩尔定律的。

数字音频，是个跨领域的行业。一方面，他是数字化的。一只脚在摩尔定律统治的领域。 另一只脚则是在一个传统的音像行业。

快速发展的摩尔领域，就容易导致劈叉越来越严重。然后就扯到蛋了。

一方面，摩尔统治下的半导体，性能指数级提升。ADC芯片能实现的采样率，很快就从 44.1khz 到了 25Ghz 以上。

另一方面，传统的音像行业坚守 44.1khz 的本心不动摇。传统行业的坚守，也让 ADC 芯片的从业者，分化为了两个阵营。一个是摩尔阵营，一个是音响阵营。

摩尔阵营的 ADC，每 18个月，价格降低一半。或者相同的价格能买到翻倍的采样率。

音响阵营，实行的是稳定供货策略。一个 44.1khz 的 ADC, 他打着保票说，这个芯片能供货30年以上，而且绝对不乱涨价。

二者之间还有一个心照不宣的秘密：摩尔阵营的ADC绝对不染指音响市场。

于是市面上，你能花一两块钱的价格买到的芯片，里面内赠的ADC能达到100khz采样速度，还能采集十几个通道。

但是如果你要采集的是区区20khz 带宽的信号，就必须买专门的44.1kz 采样率的ADC。这个ADC，价格从几十元到上万元不等。


在  44.1khz 成为标准的年代。1.44MB/s 的码率异常惊人。耗尽一台个人电脑的全部存储空间，无法记录一秒的声音。

但是，时间未过几年。个人电脑单是RAM的容量，都能放下数张CD光盘了。 就别提硬盘的容量了。更是指数级提升。

按理说，音响制作领域，完全可以使用更高的采样率，更大的码率制作音频。

但是，44.1khz 依旧统治世界。从 VCD 到 DVD ， 再到 BD。
整个媒体文件里，音频信息所占用的数据量比例，不断的下降。到 BD 时代，整个 25GB 容量的光盘里，音频信息只有数百MB。与 VCD 时代相比，只有略微的提升。这略微的提升，还是因为 BD 使用了更多的声道，而不是更高的采样率。

声音的原始数据量，已经从巨量变成了无足轻重。 无损压缩的音频，突然成了主流。

摩尔定律界的人，已经嫌弃音频的数据量太小了。填不满巨大的存储空间。不得不劝大家不要压缩声音了。再压缩，硬盘厂都要倒闭了。

声音，从一开始的大山，变成了一粒尘埃。

但是。音响界的人不这么看。声音他必须得是大山。我不允许摩尔定律碾压声音。不允许！

其实，主动远离摩尔定律，何止是 HIFI 行业。还有单片机行业。

[这篇](/2023/12/11/mcu-industry-myth.html)写的，就讲了单片机行业拒绝摩尔定律。

原来其实9年前，我就已经发现了拒绝摩尔，拒绝发展的行业。今天算是来回填了。


那么回到最初的标题，更高的采样率，为何会带来更低的成本？

因为数字滤波器，比模拟滤波器有更高的阻带抑制度。而且成本随着摩尔定律不断下降。

所以，即使声音无需更高的采样率“存储” 也应该使用更高的采样率进行录制。 然后使用越来越廉价的数字滤波器（其实就是一段代码）将超过20khz 的信号过滤的干干净净。而对20khz 以下的信号原汁原味的保留。

这不比使用 44.1khz 的采样率，然后绞尽脑汁的设计滤波电路过滤掉20khz 以上信号的方案成本更低？

何况非 44.1khz 的 ADC，价格只是 44.1kz 的 ADC 价格的万分之一。

但是，这样的摩尔方案，他不 HIFI。因为他廉价。不配获得hifi玄学大佬的承认。

正如可移植性代码，不配获得单片机大佬的承认。必须强绑定平台。绑定到具体型号。才算好代码。

