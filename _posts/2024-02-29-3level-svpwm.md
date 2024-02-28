---
layout: post
title: 三电平 SVPWM
tags: [SVPWM, 三电平]
---

炸机了。

制作低压变频器的时候，从未出现过炸机。但是，在高压变频器上，出现了。MOS管直接炸开。pcb铜箔炸飞。

究其原因，还是因为mos关闭时候产生的尖峰电压。

在研究解决方案的时候，碰到了三电平拓扑。

三电平拓扑输出三相电需使用12个 MOS 管。

那么问题来了，12个MOS管，如何控制呢？

其实，不用修改 svpwm 算法。 svpwm 算法在最终，会输出 A B C 三相的 pwm 值。

在传统2电平拓扑里，这3个 pwm值，就直接幅值给硬件驱动，产生6路pwm 了。

在3电平拓扑里，这3个 pwm 值，要转而变成 2个 pwm 定时器的12路 pwm 。


具体做法为，使用2个定时器。这2个定时器都需要开启6路pwm互补输出模式。对x相来说，有 Qxh1, Qxh2, Qxl1, Qxl2 四个开关。
其中， Qxh1 和 Qxl1 使用1号定时器对应通道。，Qxh2 和 Qxl2 使用2号定时器对应通道。

对 X 相来说，如果传入的 pwm 值 < 50%, 则，定时器1 的通道输出上管关，下管常开，定时器2的 上下通道输出按 pwm值\*2。
如果传入的 pwm 值 >= 50%, 则定时器 2 下管关。 上管常开，1号定时器上下通道输出按 (pwm-0.5)\*2。

比如下面这个代码

```c++
// duty range from [0-1]
void set_pwm(float duty_A, float duty_B, float duty_C)
{
    if (mode == TWO_LEVEL_SVPWM)
    {
        driver_set_pwm(TIM1, channel1, duty_A * period);
        driver_set_pwm(TIM1, channel2, duty_B * period);
        driver_set_pwm(TIM1, channel3, duty_C * period);
    }
    else if (mode == THREE_LEVEL_SVPWM)
    {
        if (duty_A < 0.5)
        {
            driver_set_pwm(TIM1, channel1, 0); // 下管常开
            driver_set_pwm(TIM2, channel1, duty_A* 2 * perid_count);
        }
        else
        {
            driver_set_pwm(TIM2, channel1, perid_count); // 上管常开
            driver_set_pwm(TIM1, channel1, (duty_A - 0.5)*2 * perid_count);
        }


        if (duty_B < 0.5)
        {
            driver_set_pwm(TIM1, channel2, 0); // 下管常开
            driver_set_pwm(TIM2, channel2, duty_B* 2 * perid_count);
        }
        else
        {
            driver_set_pwm(TIM2, channel2, perid_count); // 上管常开
            driver_set_pwm(TIM1, channel2, (duty_B - 0.5)*2 * perid_count);
        }


        if (duty_C < 0.5)
        {
            driver_set_pwm(TIM1, channel3, 0); // 下管常开
            driver_set_pwm(TIM2, channel3, duty_C* 2 * perid_count);
        }
        else
        {
            driver_set_pwm(TIM2, channel3, perid_count); // 上管常开
            driver_set_pwm(TIM1, channel3, (duty_C - 0.5)*2 * perid_count);
        }
    }
}

```

这个代码就实现了3电平 svpwm 输出。而三相duty的计算方式和之前的并无不同。

