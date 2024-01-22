---
layout: post
title: 编译期对象构造优化 .bss 为 .rodata
tags: [constexpr, construct, c++]
---

# 问题

为了提高性能，我编写了一个查表法算 sin 的函数。为了适配不同 ROM 大小的 mcu, 这个表还有大有小多个版本。最大的表，里面有 1800 项，因为是保存的 0-90度的 sin 指，因此分辨率达到了 0.05度。

而且，为了进一步提高性能，表里存放的，并不是 float, 而是我自己编写的定点数 float_number。

问题就出在这个float_number 上。

因为这个定点表我是这么写的

```c++
static const float_number sin_table[] = {
 float_number(0.0),
 float_number{0.000872664515},float_number{0.001745328366},float_number{0.002617990887},
 ......
};
```

因为这个表，其内存放的并不是内置类型。而是我自己编写的 float_number 类。这是一个定点数类， 使用 C++ 的运算符重载机制，可以做到无缝替换 float, 实现浮点改定点。

但是，正因为这个类不是内置类型，于是编译器实际上安排的是，将 ```0.0, 0.000872664515``` 等数字，存于 .rodata 段，然后将 sin_table 事实上分配于 .bss 段。
并在初始化代码里将 .bss 段的 sin_table 用存于 .rodata 段的各大 double 数据进行初始化。

也就是说，这个  sin 表，实际上即占用了 .rodata 也占用了 .bss 。而 .bss 段占用的是mcu里更为珍贵的RAM。
之所以最近才思考这个问题，是因为 EG6832 只有区区 8K 的 RAM。相比拥有 384K 的 ESP32 和 32K RAM 的 AT32, 这个 mcu 的内存实在过于珍贵。
以至于我很快遇到内存不足的问题。

# 解决之道

解决的办法，便是“编译期” 构造。让 sin_table 直接存放的是已经从 double 类型构造完毕的对象。这样这个 sin_table 就即不会占用内存，也不用在运行时初始化一遍。

进行编译期构造，我立马想到了2种方式。

其一，便是将已经完成double到fix point转换的数据，存入 byte 数组，而后运行时使用 reinterpret_cast 强制转换。
这个办法，需要我编写一个脚本，脚本在 项目编译 期间执行，将 sin_table 转换为一个字节数组后写入 .c 文件。

其二，便是尝试让编译器自己完成“编译期构造”

第一种做法，实在是过于无趣，虽然这种做法乃是各大单片机佬乐此不疲的通常做法。但那也不过是因为 C 语言过于劣质。他们即便想用编译期构造，那也得编译器支持才行。

第二种做法，粗看一下似乎可行。细细思考，发现非常困难。深入研究后发现，如此简单。

是的，深入研究后，发现异常简单。便是将构造函数添加一个 ```constexpr``` 关键字足矣。

于是，float_number 的构造函数，就从原来的

```c++
    explicit float_number_t(double v): scaled_number(static_cast<number_holder_t>(v * SCALE)){}
```

改成了

```c++
    explicit constexpr float_number_t(double v): scaled_number(static_cast<number_holder_t>(v * SCALE)){}
```

而后重新编译，发现固件的 .data + .bss 段，使用的内存就从 接近 3kb 降低到了 705B. 而 .rodata 段，还因为 float_number 比 double 的体积减少，也减少了占用。

至此，一个关键字引发的超级优化落幕。不仅仅如此，因为之前 EG6832 的内存不足导致只能使用 45 表项，如今也被我改成了同 ESP32 一样，使用奢侈的 1800 表项。sin 分辨率从 2 度提高到了 0.05 度。使得电机运转更为平滑。

# c++ 果然是编写资源受限型代码的神器。
