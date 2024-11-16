---
layout: post
title: 用本机 clang 进行交叉编译
tags: [clang, cross-compile, linux]
---

你在 A 平台上编译一份代码，编译出来的结果，在 A 平台无法运行，只能在 B 平台运行。这个就叫交叉编译。

通常使用交叉编译，是因为 B 平台太弱鸡，性能无法胜任编译工作。

因此大部分交叉编译，都是发生在 x86 上为 arm 编译。

为了进行交叉编译，你需要使用一种专门为交叉编译而开发的工具 —— **交叉编译器**。

在 Gentoo 上，交叉编译器可以使用工具 ”crossdev" 自动构建出来。

比如

```base
crossdev -t aarch64-unknow-linux-gnu
```

最后，你会获得一系列 aarch64-unknow-linux-gnu- 打头的编译工具。其中 aarch64-unknow-linux-gnu-gcc 就是 C语言的交叉编译器。
aarch64-unknow-linux-gnu-g++ 就是 C++ 的交叉编译器。还有 aarch64-unknow-linux-gnu-ld 自然就是交叉连接器。

这些工具的文件名，你可以传给编译脚本，就实现了交叉编译。

如果是 CLANG ， 情况发生了一些变化。

首先，你还是可以通过重新编译 clang ， 设定 clang 的目标平台，配置 clang 的安装前缀，最终获得一系列 aarch64-unknow-linux-gnu-llvm 开头的 llvm 工具链。

比如 aarch64-unknow-linux-gnu-llvm-link, aarch64-unknow-linux-gnu-llvm-as . 以及 aarch64-unknow-linux-gnu-clang 和 aarch64-unknow-linux-gnu-clang++。

但是，我要说但是了。这套做法，其实完全没有必要。

因为 LLVM 的设计结构就决定了，你当前系统里安装的 clang 编译器，体内已经蕴含了全部受llvm支持的平台的机器代码生成能力。
而 gcc 的体内，一次只能含有一个平台的机器码生成能力，其他架构的机器码生成功能会通过条件编译排除。这是 gcc 需要专门构建交叉编译器的原因。


在任何平台上，你都可以使用 clang 生成 任意平台的代码。方法是传递 --target 参数。

比如

```bash
clang++ --target aarch64-unknow-linux-gnu main.cpp
```

不出任何意外的，意外发生了。

clang 能成功编译，但是在 最后 连接 的阶段报错了。会提示找不到 crtbeginS.o 之类的文件。

其实很好理解。 clang 虽然拥有生成任意平台的二进制的能力，但是，编译并不只是产生目标文件。更重要的是，还需要连接到运行时库。

那么，这个运行时库要怎么获取呢？ 答案是： 下载 alarm 的 根目录 包。

比如下载 ArchLinuxARM-aarch64-latest.tar.gz

将 ArchLinuxARM-aarch64-latest.tar.gz 解压到 /usr/gnemul/qemu-aarch64/

```bash
sudo tar -xvf ArchLinuxARM-aarch64-latest.tar.gz -C /usr/gnemul/qemu-aarch64/
```

然后使用这个命令编译

```bash
clang++ --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/ main.cpp
```

恭喜你，这次成功编译了。（截至今日， archlinuxarm 上带的 STL 是个有 bug 的版本，导致它的头文件有错误。见 [bug](https://github.com/llvm/llvm-project/issues/92586), 如果遇到了，请相信我，不是我教的方法的问题，是真的系统带的头文件有 bug。自己按bug汇报修下吧。）


对于支持将 “clang++ --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/” 作为编译器的 autotools 工具来说，这个教程已经结束了。

因为只要配置环境变量

```bash
export CC="clang --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/"
export CXX="clang++ --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/"
```

autotools 系列工具就能正常运行了。

但是，同样的方法在 cmake 上会失效。
因为 cmake 会把 “clang++ --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/” 作为一个整体去调用可执行文件。
当然，系统里并不存在一个名为 “clang++ --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/” 的可执行文件。。。。

对 cmake 来说，还得多做一个工作，就是建立一个 wrapper。

比如写一个 aarch64-unknow-linux-gnu-clang 的脚本，脚本里面这么写

```bash
#!/bin/bash
exec clang --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/ $*
```

还有写一个 aarch64-unknow-linux-gnu-clang++ 的脚本，脚本里面这么写

```bash
#!/bin/bash
exec clang++ --target aarch64-unknow-linux-gnu --sysroot=/usr/gnemul/qemu-aarch64/ $*
```

这样，就可以如传统的交叉编译器做法一样，让 cmake 使用 aarch64-unknow-linux-gnu-clang 和 aarch64-unknow-linux-gnu-clang++ 作为编译器进行交叉。


