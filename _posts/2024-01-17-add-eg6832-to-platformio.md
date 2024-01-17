---
layout: post
title: 让 PlatformIO 支持 EG6832
tags: [PIO, PlatformIO, EG6832, EGmicro]
---


近来做变频器，也研究了不少mcu。让我的代码移植到了 ESP32, ESP32S3, ESP32C3, RP2040, STM32F405, AT32F415, AT32F421。
这些 mcu 都有一个共同点： platformio 支持。其中 ESP32, ESP32S3, ESP32C3, RP2040, STM32F405 受 platform 官方支持，而
AT32F415, AT32F421 则有 雅特力 的官方 github 上开放的 platformio 支持包。

但是，如果有一款 MCU 不被 platformio 支持，官方也不给支持包，咋办？

作为一个程序员，如果IDE的底层逻辑不了解透彻，寝食难安。

好在我不是专业的嵌入式开发者。不了解就不了解吧。

直到，我准备量产我的变频器。在 “得算力者得天下” 作者的帮助下，我找到了位于宁波的一家电器厂。它为杂牌落地扇贴牌生产。我把我的变频器介绍给了它的老板。

结果碰了一鼻子灰。主要是我的变频器成本太高了。高达25元（那是按在嘉立创进行1000张小批量生产的报价）（虽然市面上最廉价的三相变频器也得三位数购买）！
低端制造业就是这样，对成本斤斤计较。虽然我25元的变频器，可以支持到 200w 的电机。但是人家电风扇只需要 20w。他现在要改用 直流电机。
直流电机的成本比变频器+交流电机的成本更低。虽然60w 的直流电机很贵，但是电风扇只要20w 就行了。 20w 的直流电机就很便宜了。所以 60w 的交流电机+变频器的方案，在12w 直流电机面前毫无招架之力。
后来我准备走的时候，遇到了给他供应12w直流电机的供应商。我向他咨询了直流电机的成本。意外的发现，他的直流电机上的控制器，成本只要6元！

# 6 元！！！

这是什么神仙成本。

其实直流电机的控制器在硬件上 = 变频器+转子位置传感器。所以是不可能比变频器更便宜的。所以，其实我的变频器也可以跑在那种 6 元的硬件上。

但是，这种 6 元的硬件，其 MCU 几乎肯定必然，都是非主流 MCU.

经过我的一番搜索，我找到了2种可以实现6元控制器的芯片方案。一种是 8051 内核+ foc 协处理器 的 FU6832, 还有一种是 arm 核的 EG6832。

名字都叫 6832 ，看来这俩果然是要抢生意。

这俩有个共同点：都没有详细资料。都需要直接联系原厂的销售代表去索取样品和资料。

EG6832 对我这种没有专门的采购主管的个人开发者来说要安心点，因为官方直接开了个淘宝店卖样品。于是下单购买，然后淘宝的客服给了我一个压缩包。然后就没有更多的技术支持了。

压缩包里是一个水泵控制器的 DEMO。虽然是个 DEMO, 但是好在这个 DEMO 是属于 “把依赖的库全带上” 的那种方案。在 third_party/* 目录里塞满各种第三方库的 cpper 会心一笑 :)

最为关键的是，他这个 demo 带上了 HAL 库。（他可没那么好心的把电机库送人。电机库是个 .lib 静态库，只见 main.c 里对电机库的调用，不见电机库的代码的啦！这世上好心的把电机库送出去的，只有 simplefoc 和 本杰明VESC。 连我都不开源，嘿嘿！）

在mcu里，所谓 HAL 库，就是把 **操作硬件寄存器** 实现某种功能给编写为一系列的 "C函数"。比如，在 AT32 的 HAL 库里，把修改 pwm 占空比所需的硬件寄存器操作，给编写成了 ```tmr_channel_value_set``` 这么一个 C API。修改 pwm 频率呢，则使用 ```tmr_period_value_set``` 就实现了。我不需要操心具体硬件的寄存器操作，更不需要知道寄存器地址。
而 ESP32 则是把同样的功能封装为 ```mcpwm_comparator_set_compare_value``` 和 ```mcpwm_timer_set_period```
雅特力和ESP32的芯片手册，不仅仅会给出寄存器的说明，也同时会介绍 HAL 库的 API 如何使用。

但是，EG6832 这个就惨了！ 他的芯片手册，居然只有硬件寄存器的描述，而 HAL 库则没有任何文档。没有就没有吧，hal库毕竟给了源码。对着手册的寄存器介绍，再看看源码，应该就知道 api 是干嘛的了。

# 编写 platformio 的支持包

既然有了 hal 库，那理论上来说，就能为 platformio 添加 eg6832 的支持了。

platformio 里，对一款 MCU 的支持，需要编写2个包。其1 为 platform-xxx 包，其二为 framework-xxx 包。

platform-xxx 包的任务是编译项目。framework-xxx 包的任务是提供 HAL 库。（以及，更关键的，提供 main 执行之前的代码。）

好在，雅特力的官方给了我一个很好的 example。于是一顿操作，[platform-egmicros](https://github.com/microcai/platform-egmicros) 就诞生了。

只要在 platform.ini 里写上

```ini
platform = https://github.com/microcai/platform-egmicros
board = genericEG6832
framework = eg32firmlib
```

就可以开始为 EG6832 写代码啦！

platform-egmicros 包其实主要的任务就是编译framework-xxx 包。编译的脚本在 [builder/frameworks/eg32firmlib.py](https://github.com/microcai/platform-egmicros/blob/master/builder/frameworks/eg32firmlib.py) 里。

因为按 platformio 的思路，一个 platform 可以使用各种 framework. 比如 裸环境，arduino 环境， freertos 环境。等等。

不同的环境，就调用 platform-xxx 包里的 builder/{framework}.py 脚本。

把 EGmicro 官方给的 demo 里的 HAL 代码扣出来，我做了个 framework-eg32firmlib 库。于是一顿编译后， .pio/build/eg6832/firmware.bin 文件顺利诞生！

HAL 库是如何启动到 main() 的？ 这个问题我就下面再讲解。

然后，这些都是板子到货之前的工作了。

# 下载遇到了问题

EGmicro 官方给的 Demo 包，里面还包括了一个给 KEIL5 IDE 使用的一个 .pack 文件。我没有用过 keil，不知道这个文件具体的作用。
但是 7z 能打开它，发现是个压缩包。于是解压之。解压后的文件，里面也有一个 HAL 库。显然，将 HAL 库 复制 到 工程里，看来是 keil 的标准做法（而且是极其愚蠢的做法）了。

其中还有个 EG32M0xx.svd 文件，这个文件看来是调试用的。openocd 需要用到它。
然后还有一个百思不得其解的文件 EG32M0xx_EFLASH_PROG.FLM

这个文件是干嘛用的呢？


# openocd 不支持 eg6832

终于等了数天，板子到了。兴冲冲的接上 swd 调试器，然后 openocd 命令一敲....

傻眼了。 openocd 不支持。还得写 target 文件。于是依葫芦画瓢写了一个。
一跑，傻眼了， openocd 提示 flash 算法不支持。

啊？？？ flash 算法？ 那是什么鬼。

==，EG32M0xx_EFLASH_PROG.FLM 这个文件是不是就是所谓的 flash 算法文件？ 所以 keil 才能对 eg6832 编程？是因为官方的 pack 文件里打包了这个 FLM 文件？

于是带着疑问研究了 openocd 的文档，一无所获。 只知道 openocd 的 flash 算法，是它自己支持的，不需要也不能靠载入某个 FLM 文件。

但是意外的发现了一个叫 pyocd 的项目。它虽然说不支持载入 FLM 文件，但是它能把 FLM 文件变成 py 代码，然后整合进去。。。 它就支持了某款 mcu 咯。

# 修改 pyocd，搞定了 EG6832 的程序下载

python 真 鸡儿 是个垃圾语言。修改 pyocd 本来应该是一个很简单的事情。结果因为py的垃圾 cache 机制，修改的 .py 文件死活没生效。
真是个垃圾语言。然后修改完毕，跑通！

顺便给官方发了个 PR 。也不知道响应时间如何。[pyOCD 改版仓库](https://github.com/microcai/pyOCD) 有需要的自取。


# ARM MCU HAL 之 启动

HAL 库主要做两件事： 1. 将寄存器操作抽象为具体的 C 函数名。方便开发和移植。2. 启动 main()

第一件事其实很好理解，因为 arm mcu 基本上采用的是 MMIO, 因此每个外设包含若干寄存器。每个寄存器就都分配一个内存地址。这样每个外设就会占用一片连续的地址。这片连续的地址，就正好编写为一个 C 结构体。结构体里每个成员变量都对应一个寄存器。然后再使用C语言的强制转换，将这个外设的寄存器首地址，直接强转为这个外设对应的结构体。
比如 定时器，在 HAL 里是一个  struct TimerDef, 然后定义 TIMER1 =  (TimerDef\*) ( 0x40020xxx ), TIMER2 =  (TimerDef\*) ( 0x40021xxx )。
这样操作寄存器，就简化为了操作 TIMER1->xxx， TIMER2->xxx 变量。

第二个事，就开始难以瞬间秒懂了。启动 main 之前，hal 库都干了啥？


最关键的是， mcu 代码是没有 OS 的，所以，hal 库，是需要知道内存布局才能工作的。不然 malloc() 调用要如何实现呢？

原来，这部分功能，是由 链接器 脚本实现的。在 hal 库里，会携带对应 mcu 的 链接器 脚本。由链接期脚本来保证，入口代码一定是放在 Flash 的第一个字节。

```ldscript

/* Entry Point */
ENTRY(Reset_Handler)

/* Highest address of the user mode stack */
_estack = 0x20018000;    /* end of RAM */

/* Generate a link error if heap and stack don't fit into RAM */
_Min_Heap_Size = 0x200;      /* required amount of heap  */
_Min_Stack_Size = 0x400; /* required amount of stack */

/* Specify the memory areas */
MEMORY
{
FLASH (rx)      : ORIGIN = 0x08000000, LENGTH = 1000K
RAM (xrw)       : ORIGIN = 0x20000000, LENGTH = 96K
}

/* Define output sections */
SECTIONS
{
  /* The startup code goes first into FLASH */
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector)) /* Startup code */
    . = ALIGN(4);
  } >FLASH

......

```

这里摘录一个 mcu 的 链接期脚本。ENTRY(Reset_Handler) 定义了入口点。也就是整个代码，从 void Reset_Handler() 开始执行。
注意了，接下来一行是最关键的代码，任何代码都没有这行关键 ```_estack = 0x20018000;    /* end of RAM */```
这个代码，其实是定义了内存的顶部地址。在 arm mcu 里，内存会被划分为 [静态分配的变量][堆][栈] 三个区域。

```RAM (xrw)       : ORIGIN = 0x20000000, LENGTH = 96K``` 这个代码，指示了链接期在放置 .data 区的时候，地址从 0x20000000 开始，最多可以放96k.

最终，ldscript 里输出的 __bss_end__ 这个变量，就变成了 libc 里的堆的起点。堆向栈的方向增长。
这样， libc 就获得了内存布局。

启动代码，也得已布局在 0x08000000 开始的地方。由于该 mcu 将 flash 映射为 0x08000000-0x08100000，rodata 和 text 也得以顺利的摆放到正确位置。

为了让 启动代码确确实实的放置在 0x08000000 的地方，ldscript 特意首先布局 .isr_vector 到 >FLASH. 而 HAL 里，唯一一个定义为 .isr_vector section名字
的代码，就是一个 ISR 数组。数组的第一个是 栈顶， 代码如下

```C
/* Vector table */
__attribute__((section(".vector_table")))
const FUNC_IRQ __vector_handlers[] = {

    _estack,
    Reset_Handler,              // Reset Handler
    NMI_Handler,                // NMI Handler
    HardFault_Handler,          // Hard Fault Handler
    0,                          // Reserved
    0,                          // Reserved
    0,                          // Reserved
    0,                          // Reserved
    0,                          // Reserved
    0,                          // Reserved
    0,                          // Reserved

.....


};

```

定义了一个叫 __vector_handlers 的数组，数组的第一个元素，就必然会被放入 0x08000000，而这个地址，按 mcu 的手册，芯片上电后，会自动从 0x08000000 载入栈顶，0x08000004 载入指令。

0x08000004 恰恰就是 __vector_handlers 的第二个元素，也就是 Reset_Handler 的地址。
0x08000000 恰恰就是 ldscript 里设置的 _estack。

于是这么安排下，cpu 上电，就自动运行 Reset_Handler 了，而且连 栈顶都设置好了。意味着 Reset_Handler 可以直接由 C 语言编写。无需汇编指令。

Reset_Handler 的做法，其实就是初始化 libc , 然后执行 main()。

# 总结

mcu 的启动代码，需要 ld script 的搭配。ld script 巧妙的设定了 mcu 规定的指定地址的内容。而 内存大小， FLASH 大小，这些信息都是在 ldscript 里设置的。
ldscript 设置的变量，可以在代码里，按全局变量的方式直接使用。这样就完成了将 mcu 的内存布局信息传递给了 libc. 使得 mcu 里，脱离 OS 也可以继续使用 malloc/free 函数进行内存动态分配。

