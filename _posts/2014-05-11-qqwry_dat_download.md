---
layout: post
title: 纯真数据库下载或自动更新实现
tags: [c++]
---

用过珊瑚虫的童鞋都知道, 有个叫 "纯真数据库" 的东西, 可以查询 ip 地址对应的物理地址.

纯真数据库是有个名为 QQWry,DAT 的二进制文件, 可以通过纯真数据库自己提供的查询程序进行更新.

有关该数据库格式和解析的内容, 本帖子暂时不讲, 有机会的话, 偶会另行开个新帖子讲讲.


这里讲的是, 不通过官方的查询程序, 如何获取到这个数据库. 通过对官方程序进行抓包, 得出下载此数据库, 主要需要下载

http://update.cz88.net/ip/copywrite.rar

和

http://update.cz88.net/ip/qqwry.rar

两个文件.


但是很明显,这两个压根不是 rar 文件呀! 别被扩展名迷惑了.


因为要下载两个文件, 所以得出一个很明显的结论, ** 第二个文件需要用到第一个文件里的信息才能正确解开, 获得 qqwry.dat 文件. **

那么,  copywrite.rar 里到底有神马东西呢?

我们来打开它


ghex copywrite.rar

![copywrite.png](/images/copywrite_rar.png)

好吧,老实说, 根本看不明白嘛!

那咋办？

祭出　IDA !!!!!!


----------

华丽的风格线，　其实网上已经有人说了，　这个　copywrite.rar 就是如下一个结构体．

```c++

struct copywritetag{
    uint32_t sign;// "CZIP"
    uint32_t version;//一个和日期有关的值
    uint32_t unknown1;// 0x01
    uint32_t size;// qqwry.rar大小
    uint32_t unknown2;
    uint32_t key;// 解密qqwry.rar前0x200字节所需密钥
    char text[128];//提供商
    char link[128];//网址
};


```

这里，最重要的就是　key 这个整数拉！　接下来要在解码　qqwry.rar 里用到


----------

下载，　qqwry.rar 初步断定这个是一个压缩文件．　为啥？　因为比　qqwry.dat 明显小了不少！

别看他是　rar 扩展名，　肯定不是用的　rar 压缩算法．　为啥？　明显会用　zlib 这样的开源库来压缩嘛！　何况这样的压塑　php 都能做，是吧．　初步估计是　inflate  压塑，　对，　就是　zlib 用的那个．　约莫估计用　php 的　compress() 函数直接压塑来的．

但是，用　zlib 将　qqwry.dat 压塑后，　文件大小居然一样！　哈，不过，文件头看着他怎么就是不一样呢？


注意到上面的注释没? key 用来解码　qqwry.rar 的头　0x200 个字节．　也就是说，　先用　key 把开头的　 0x200 个字节给解码了，　新的数据就可以　zlib 解压了．


啥？　你问我，这　0x200　偏移量怎么来的　？　诶，笨，　自己比较去吧，　却是和　zlib 压塑的，　就只有前面　0x200 不一样罢了．



那么，这　0x200 个字节的数据，　到底如何解码呢？

来，再次祭出　IDA !!!!!!


----------

好了，网上已经有了祭出　IDA 然后得出解码算法了，　咱看下

```
    for (int i = 0; i<0x200; i++)
    {
        key *= 0x805;
        key++;
        key &= 0xFF;
        uint32_t v = reinterpret_cast<const uint8_t*>(qqwry_rar.data())[i] ^ key;

        qqwry_rar[i] = v;
    }


```

good 这样就完成了．

接下来把　qqwry_rar 这个数组里的数据喂给　zlib 的　uncompress 函数就完成解压了！　ｂｉｎｇｏ


