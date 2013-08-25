---
layout: post
title: 让 C 回调支持 boost::bind
---

C++ 的 bind 非常方便! 但是如果你不得不处理一些 C 接口, 情况就会变得很糟糕, 你不得不处理一堆的 void* , 不能使用 bind ! 有神码办法可以解决这个问题呢!? 答案就是 接下来介绍的模板技术 c_func_wraper !

用法很简单, 看下面的例子


```C++
static void * my_thread_func(int a, int b,  int c)
{
	std::cout <<  a <<  b <<  c <<  std::endl;
	return NULL;
}
int main(int, char*[])
{
	c_func_wraper<void *(*) (void *),  void*()> func;
	func = boost::bind(&my_thread_func, 1, 2, 3);
	pthread_t new_thread;
	pthread_create(&new_thread, NULL, func.c_func_ptr(), func.c_void_ptr());
	pthread_join(new_thread, NULL);
        return 0;
}
```

pthread 是一个典型的 C 接口,  需要传递给线程的参数通过 void* 传递进来.  	c_func_wraper 则将 bind 和 C 接口的回调给整合起来了!


	c_func_wraper 接受2个模板参数, 一个是 C 接口需要的 **函数指针**类型, 另一个是 类似 boost::function 所接受的函数原型声明. 注意, C 类型的声明和 boost::function 风格的声明的区别. 另外就是当前 C  类型必须是 void* 在最后一个参数. 以后可以添加出更多位置支持 :)  如第一个参数是 void* user_data 的 C 回调.

接着为其 使用 bind 赋值. 赋值完毕, 就可以通过 c_func_ptr 和 c_void_ptr 两个对象获取到兼容的 C 版本了, 然后传递给 pthread_create. 就大公告成了. :) 


下面是 实现 

```c++

template<typename CFuncType, typename ClosureSignature>
class c_func_wraper :boost::noncopyable
{
public:
	c_func_wraper()
	{
		m_wrapped_func = new boost::function<ClosureSignature>;
	}
	~c_func_wraper()
	{
		delete m_wrapped_func;
		m_wrapped_func = NULL;
	}
	template<typename T>
 	c_func_wraper(const T &bindedfuntor)
 	{
  		m_wrapped_func = new boost::function<ClosureSignature>;
 		*m_wrapped_func = bindedfuntor;
 	}
	template<typename T>
	c_func_wraper<CFuncType, ClosureSignature>& operator = (const T &bindedfuntor)
	{
		*m_wrapped_func = bindedfuntor;
		return *this;
	}
	void * c_void_ptr()
	{
		return new boost::function<ClosureSignature>(*m_wrapped_func);
	}
	CFuncType c_func_ptr()
	{
		return (CFuncType)wrapperd_callback;
	}
private:
	template<typename R>
	static R wrapperd_callback(void* user_data)
	{
		boost::scoped_ptr<boost::function<ClosureSignature>  > wrapped_func(
					reinterpret_cast<boost::function<ClosureSignature> *>(user_data));
		return (R)(*wrapped_func)();
	}
	template< typename R, typename ARG1>
	static R wrapperd_callback(ARG1 arg1, void* user_data)
	{
		boost::scoped_ptr<boost::function<ClosureSignature>  > wrapped_func(
					reinterpret_cast<boost::function<ClosureSignature> *>(user_data));
		return (*wrapped_func)(arg1);
	}
private:
	boost::function<ClosureSignature> * m_wrapped_func;
};
```

