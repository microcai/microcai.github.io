---
layout: post
title: 不要 new 一个 char 数组当缓冲区
tags: [c++, cpp, new, malloc]
---

性能调优是一个有魔力的工作。最近研究到了 ```std::pmr::```, 就想着看能否有些老代码能改进改进，提高下性能。

但是，测试的时候，发现还是有一些路径的效率不理想。

经过好久的排查，最终定位代码到这么一行

```c++
auto buffer_size = 5*1024*1024;
auto buffer = std::make_unique<char[]>(buffer_size);
```

好家伙，原来 ```make_unique<char[]>``` 这么慢的吗？

原来 make_unique 不单单是 分配了 buffer_size 个字节的内存，同时还 构造了如此数量的 char 对象。
问题是我这只是个 buffer, 不需要初始化啊！

继续查看生成的汇编代码，发现 make_unique 还是很聪明的，并没有在一个 for 循环里调用5百万次 char 的构造函数。
看来第一种 for 循环五百万次赋值 0 的担忧是没了。
结果看到了汇编代码里的 ```call memset@plt```

所以说，哪怕编译器自动的把初始化代码优化为了一个  memset 调用，它还是调用了 memset ， memset 对一个 5MB 的内存，还是要花点时间的。

于是我随手把代码改成了

```c++
auto buffer_size = 5*1024*1024;
std::unique_ptr<void, decltype(&std::free)> buffer(std::malloc(buffer_size), &std::free);
```

测试发现性能飙升了十几倍。

# 总结

在不需要初始化的 buffer 分配领域，使用 malloc 是比 new 更好的选择。


