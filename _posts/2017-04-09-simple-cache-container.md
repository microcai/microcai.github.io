---
layout: post
title: 使用异常实现cache
tags:   [c++, exception]
---

异常用来做错误处理的时候，程序到处都是 try  cache ，代码十分的丑陋，我是不怎么喜欢的，我喜欢 asio 那种用 error\_code  汇报错误 —— 不传 ec 的时候就抛异常，传就不抛，改为写入错误到 ec。

但是，异常用来做流程控制，又特别的好用。流程控制，无非顺序、选择、分支和循环。在 c++里，又比 C 多了一个异常。在嵌套很深的地方，跳出逻辑，除了异常，就没有其他更好的办法了。

在编写软件的时候，时常需要对一些数据做 cache。在使用的时候，要先检查 cache，存在则使用 cache ，不存在则按照老办法办，然后存入 cache。

每次使用前都进行判断， 污染了快速路径的代码，对有简洁洁癖的程序员来说，内心是十分的纠结的。

这个时候， 你就需要 异常。将 cache hit 作为正常的流程进行编写， 假定全部的数据都是在 cache 里的。这万一发生了 cache miss ， 则抛出异常，并在异常处理重新载入数据。然后重启处理。

说到重启处理， 在 Windows 的 SEH 里，存在 ```EXECEPT_CONTINUE_EXECUTION``` 这个异常处理的结果， windows 看到异常处理函数返回这个，就会回到发生异常的地方重新执行。然而这毕竟是一个 Windows 系统特有的 SEH ， 而且依赖底层CPU提供的机制。 编写C++是断然不能使用这套机制的。

思考的最终结果，就是下面这样的结构

```

for (int =0; i < retry_times ; i++)
{ 
    try  
    {
            auto  v = cache_map_sometype.get_cache(key);
            // process with v ....
            ........
    }  
    catch(cache_miss&)
    {   
           // load v from other resources, database, filesystem, network, etc.
           ......
            cache_map_sometype.add_cache(key, v);
            contine; // NOTE about this.
    }
    break;  
}

```

在正常处理流程里， 执行到最后会有个 break 退出 for 循环。所以 for 循环在 cache hit 的状态下只执行一次。在 cache miss 的时候， catch block 里最后有一行 continue 。 于是就重启处理过程了。

下面给出 cache_map 的代码。

<pre style='color:#eff0f1;background-color:#232629;'>

<span style='color:#27ae60;'>#pragma once</span>

<span style='color:#27ae60;'>#include </span><span style='color:#27ae60;'>&lt;tuple&gt;</span>
<span style='color:#27ae60;'>#include </span><span style='color:#27ae60;'>&lt;map&gt;</span>

<span style='color:#27ae60;'>#include </span><span style='color:#27ae60;'>&lt;boost/thread.hpp&gt;</span>
<span style='color:#27ae60;'>#include </span><span style='color:#27ae60;'>&lt;boost/thread/shared_mutex.hpp&gt;</span>
<span style='color:#27ae60;'>#include </span><span style='color:#27ae60;'>&lt;boost/date_time/posix_time/ptime.hpp&gt;</span>

<b>struct</b> cache_miss {};

<b>template</b>&lt;<b>typename</b> KeyType, <b>typename</b> ValueType, <span style='color:#2980b9;'>int</span> cache_aging_time = <span style='color:#f67400;'>30</span>&gt;
<b>class</b> cache_map
	: <b>protected</b> <span style='color:#59ff04;'>std::map</span>&lt;KeyType, <span style='color:#59ff04;'>std::tuple</span>&lt;ValueType, <span style='color:#56e092;'>boost::posix_time::ptime</span>&gt;&gt;
{
	<b>typedef</b> <span style='color:#59ff04;'>std::map</span>&lt;KeyType, <span style='color:#59ff04;'>std::tuple</span>&lt;ValueType, <span style='color:#56e092;'>boost::posix_time::ptime</span>&gt;&gt; base_type;

<b>public</b>:
	ValueType get_cache(<span style='color:#2980b9;'>const</span> KeyType&amp; key) <b>throw</b>(cache_miss)
	{
		<span style='color:#56e092;'>boost::shared_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; l(m_mutex);

		<b>typename</b> base_type::iterator it = base_type::find(key);

		<b>if</b> (it == base_type::end())
		{
			<b>throw</b> cache_miss();
		}

		<span style='color:#59ff04;'>std::tuple</span>&lt;ValueType, <span style='color:#56e092;'>boost::posix_time::ptime</span>&gt; &amp; value_pack = it-&gt;second;

		<b>auto</b> should_be_after = <span style='color:#56e092;'>boost::posix_time::second_clock::universal_time</span>() - <span style='color:#56e092;'>boost::posix_time::seconds</span>(cache_aging_time);

		<b>if</b> (<span style='color:#59ff04;'>std::get</span>&lt;<span style='color:#f67400;'>1</span>&gt;(value_pack) &gt; should_be_after)
			<b>return</b> <span style='color:#59ff04;'>std::get</span>&lt;<span style='color:#f67400;'>0</span>&gt;(value_pack);
		<b>throw</b> cache_miss();
	}

	<span style='color:#2980b9;'>void</span> remove_cache(<span style='color:#2980b9;'>const</span> KeyType&amp; k)
	{
		<span style='color:#56e092;'>boost::unique_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; l(m_mutex);

		base_type::erase(k);
	}

	ValueType get_cache(<span style='color:#2980b9;'>const</span> KeyType&amp; key) <span style='color:#2980b9;'>const</span> <b>throw</b>(cache_miss)
	{
		<span style='color:#56e092;'>boost::shared_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; l(m_mutex);

		<b>typename</b> base_type::const_iterator it = base_type::find(key);

		<b>if</b> (it == base_type::end())
		{
			<b>throw</b> cache_miss();
		}

		<span style='color:#2980b9;'>const</span> <span style='color:#59ff04;'>std::tuple</span>&lt;ValueType, <span style='color:#56e092;'>boost::posix_time::ptime</span>&gt; &amp; value_pack = it-&gt;second;

		<b>auto</b> should_be_after = <span style='color:#56e092;'>boost::posix_time::second_clock::universal_time</span>() - <span style='color:#56e092;'>boost::posix_time::seconds</span>(cache_aging_time);

		<b>if</b> (<span style='color:#59ff04;'>std::get</span>&lt;<span style='color:#f67400;'>1</span>&gt;(value_pack) &gt; should_be_after)
			<b>return</b> <span style='color:#59ff04;'>std::get</span>&lt;<span style='color:#f67400;'>0</span>&gt;(value_pack);
		<b>throw</b> cache_miss();
	}

	<span style='color:#2980b9;'>void</span> add_to_cache(<span style='color:#2980b9;'>const</span> KeyType&amp; k , <span style='color:#2980b9;'>const</span> ValueType&amp; v)
	{
		<span style='color:#56e092;'>boost::unique_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; l(m_mutex);

		base_type::erase(k);

		base_type::insert(<span style='color:#59ff04;'>std::make_pair</span>(k, <span style='color:#59ff04;'>std::make_tuple</span>(v, <span style='color:#56e092;'>boost::posix_time::second_clock::universal_time</span>())));
	}

	<span style='color:#2980b9;'>void</span> tick()
	{
		<span style='color:#56e092;'>boost::upgrade_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; readlock(m_mutex);
		<span style='color:#59ff04;'>std::shared_ptr</span>&lt;<span style='color:#56e092;'>boost::upgrade_to_unique_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt;&gt; writelock;
		<b>auto</b> should_be_after = <span style='color:#56e092;'>boost::posix_time::second_clock::universal_time</span>() - <span style='color:#56e092;'>boost::posix_time::seconds</span>(<span style='color:#f67400;'>30</span>);

		<b>for</b> (<b>auto</b> it = base_type::begin(); it != base_type::end(); )
		{
			<span style='color:#2980b9;'>const</span> <span style='color:#59ff04;'>std::tuple</span>&lt;ValueType, <span style='color:#56e092;'>boost::posix_time::ptime</span>&gt; &amp; value_pack = it-&gt;second;

			<b>if</b> (<span style='color:#59ff04;'>std::get</span>&lt;<span style='color:#f67400;'>1</span>&gt;(value_pack) &lt; should_be_after)
			{
				<b>if</b> (!writelock)
					writelock.reset(<b>new</b> <span style='color:#56e092;'>boost::upgrade_to_unique_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt;(readlock));
				base_type::erase(it++);
			}
			<b>else</b>
				it++;
		}
	}

<b>private</b>:
	<span style='color:#2980b9;'>mutable</span> <span style='color:#56e092;'>boost::shared_mutex</span> m_mutex;
};

<b>template</b>&lt;<b>typename</b> KeyType, <b>typename</b> ValueType&gt;
<b>class</b> cache_map &lt;KeyType, ValueType, <span style='color:#f67400;'>0</span>&gt;
	: <b>protected</b> <span style='color:#59ff04;'>std::map</span>&lt;KeyType, ValueType&gt;
{
	<b>typedef</b> <span style='color:#59ff04;'>std::map</span>&lt;KeyType, ValueType&gt; base_type;
<b>public</b>:

	ValueType&amp; get_cache(<span style='color:#2980b9;'>const</span> KeyType&amp; key) <b>throw</b>(cache_miss)
	{
		<span style='color:#56e092;'>boost::shared_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; l(m_mutex);

		<b>auto</b> it = base_type::find(key);

		<b>if</b> (it == base_type::end())
		{
			<b>throw</b> cache_miss();
		}

		<b>return</b> it-&gt;second;
	}

	<span style='color:#2980b9;'>void</span> add_to_cache(<span style='color:#2980b9;'>const</span> KeyType&amp; k , <span style='color:#2980b9;'>const</span> ValueType&amp; v)
	{
		<span style='color:#56e092;'>boost::unique_lock</span>&lt;<span style='color:#56e092;'>boost::shared_mutex</span>&gt; l(m_mutex);

		base_type::erase(k);

		base_type::insert(<span style='color:#59ff04;'>std::make_pair</span>(k, v));
	}

	<span style='color:#2980b9;'>void</span> tick()
	{
	}

<b>private</b>:
	<span style='color:#2980b9;'>mutable</span> <span style='color:#56e092;'>boost::shared_mutex</span> m_mutex;
};
</pre>
