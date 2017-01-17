---
layout: post
title: 聊聊  type  erasure
tags: [c++]
---

# 什么是类型橡皮擦? 

type eraer是什么？ 为什么这么有用？ 到底它是如何帮助你构建灵活强大的软件的？ 

我们知道 C＋＋ 是一个强类型的语言。 不同类型之间有天壤之别 ，不能任意转化——函数有签名，只有符合类型检查才能调用。
类型稍微有点不匹配，那带来的是一堆堆编译错误。 
然后很多时候，我们会想，C＋＋的类型能不要那么强就好了！比如说设计一个回调函数 ，这回调函数非得是那个类型的才能使用，多不方便。 
为了方便用户，为了能适应变化，我们将不得不使用 void*  参数，然后不停地进行强制类型转换。

如果 ......

如果能把类型变弱点就好了!

type erasure 技术应运而生。
其实我们常用的 std::function / boost::function 就是一种  type erasure。
std::function 在一定程度上，抹去了函数的类型。不论来的类型是函数对象，还是函数指针，它统统接受，统统能赋值给它。要知道，函数对象可是有无穷多种类型。

# 弱类型？ 和模板啥区别？

模板靠编译期自动生成一个类型兼容的函数来做到弱类型，而  type erasure则能实现在运行期弱类型。

```c++
template<class Callback>
void somefunc( int  somearg, Callback  callback); 
```

这个是弱类型了吧，但是是靠编译期实现的。如果有100 个类型的回调，就会生成 100 份代码，去适应 100 个类型的回调函数。
但是如果是这样的代码

```c++
void somefunc( int somearg, std::function<void> callback); 
```

这个也是弱类型吧，但是，不论有多少回调类型，一份代码足矣。
也就是说， type erasure 能弥补模板运行期弱类型能力不足的问题。

而有时候，你不得不使用 type erasure。
比如说，你需要保持一个容器，里面全是回调函数。
那么模板就无能为力了。因为创建一个容器的时候，已经要把所有的元素的类型都固定为一个了。 
这个时候你必须借助 type erasure 

```c++
std::vector<std::function<void()>> function_container;
```

有的人会说，用  void*  不也能实现么？

# type erasure 和 void* 区别在哪？ 

和 void* 抹杀一切类型不同， type erasure 只谋杀一部分类型。 
比如说 std::function , 虽然抹杀了各种函数指针和函数对象之间的差异。
但是，他们还是有其共同点： 还是函数，还能调用。
而使用 void* 的话，就什么类型都抹杀了 
所以这是和 void * 的根本差异 


# 那么，type erasure 如何实现？ 

type erasure 的实现通常包含3 个部分: 接口适配器部分、类型基、模板派生类。 
接口适配器，就是暴露给用户的接口 
这个接口表现的很弱类型。 
内部实现上呢，是通过包含一个基类指针，指向分配出来的 模板派生类实现的 
这样

```c++
class interface
{
  Base ＊ ptr; 

  public:
  some_common_func()
  {
    ptr->some_common_func();
  }

  template<class T>
  interface(T t)
  {
    ptr = new adapter<T>(t);
  }
};


class Base {
public:
virtual ~Base();
virtual some_common_func() = 0 ;
} ; 

template < class T >
class adapter : public Base
{
  T t;
public: 
some_common_func()
{
  t.some_common_func();
}

adapter(T _t): t(_t){}

};
```

通过  new Adapter<被适配的类型>  
赋值给 Base* 来保存这个 被适配的类型。 
通过 C＋＋ 的虚函数机制， 最终调用到被适配的类型里的操作。
