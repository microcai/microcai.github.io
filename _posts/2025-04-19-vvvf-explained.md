---
layout: post
title: 变频器原理和设计指导
tags: [VVVF, PCB]
---


# 从 Buck 降压电路说起


![](/images/basic_buck.png)

上图为一个基本的 Buck 降压电路。 Q1 和 Q2 是互补的两个 MOS/IGBT 管。

所谓互补，是两个同时只有一个会导通。要么是 Q1 打开，要么是 Q2 打开。

Q1 关闭的时候， Q2 必须打开。Q1 打开的时候，Q2 必须关闭。

Q1 和 Q2 可以使用一个 PWM 信号控制。

那么 pwm 信号的占空比，就决定了 Q1 打开的时间占比。也就决定了 OUTPUT 输出端的电压占 总 电压的比。

OUTPUT 处的电压 = VCC * pwm 占空比。

记住这个。


# 两路 Buck 降压电路

将上述降压电路复制成2份，就构成了一个逆变器。

为何呢？

看图

![](/images/buck_as_H_bridge.png)


两个 Buck 电路，输出 OUTPUTA 和 OUTPUTB 。

如果 OUTPUTA 的电压 > OUTPUTB 的电压。那么对于接到 OUTPUTA和OUTPUTB的负载来说，电流就会从 OUTPUTA流出，经过负载后，流入 OUTPUTB.

如果 OUTPUTA 的电压 < OUTPUTB 的电压。那么对于接到 OUTPUTA和OUTPUTB的负载来说，电流就会从 OUTPUTB流出，经过负载后，流入 OUTPUTA.


也就是说，对负载来说，OUTPUTA + OUTPUTB 就相当于是一个交流电源。

这种2个 buck 构成的就是所谓的 “逆变桥” 了。这2个 buck 降压电路，则称为 左半桥和右半桥。

一般来说，如果要输出正弦波交流电，交替的让其中一桥输出 0 电压。另一个桥输出半个 sin 波。

所谓输出 0 电压，指的是打开 下管，关闭上管。
所谓输出半个 sin波，是指 只输出 sin 正弦波为正的那半个周期。

而输出 sin波的方法就是，在每个 pwm 周期里，调节 pwm 的占空比。 pwm 占空比的调节方法就是计算 sin 。假设 pwm 周期是 18khz ，输出 50hz 交流电，那么正好，每个 pwm 周期，为 1 度。
每个完整的 sin 波形，由 360 个 pwm 脉冲构成。 于是 直接一个 自增的 i 变量。 pwm = sin( i 度)。 i=i+1; 以上2行代码，每个 pwm 周期执行一次。每次执行用于设定本次 pwm 的占空比。


这样就可以输出按 sin 规律变化的 pwm 占空比了。

# 三路 Buck 降压电路

如果将上文提到的 Buck 降压电路复制成3分呢？
那就得到了一种叫 “三相逆变桥” 的电路。


![](/images/3pharse_full_bridge.png)


这三个 Buck 电路，就可以输出三相交流电了。

当然，需要对 3个半桥的 PWM 占空比进行控制才能实现。

以上就是变频器的硬件原理了。 至于如何输出 3路 pwm 波形使得 6 个 IGBT 能实现 三相逆变，可以看我往期的文章。

