---
layout: post
title:  asio::promise yyds
tags:   [asio, promise, c++20]
---

最近在写以太坊的巧克力浏览器（区块链浏览器）。因为区块链浏览器需要访问历史的块，因此需要节点以 archive 模式同步。

遂运行了一个 geth。 然而半个月过去了，才同步了四百万高度，而且这四百万高度的最后一百万花了80%的时间。
同步速度以肉眼可见的速度下降，ETA 变的越来越长。 从一个月慢慢的增长到6个月。

于是寻找更快的客户端。找到了 erigon。erigon 号称2天完成 archive 节点同步。
结果牛逼是吹大了啊。最后耗费了10天完成了同步。

geth 在同步的时候， rpc 是可用的，geth 同步到哪里， eth_getBlockNumber 返回的高度就是哪里。
因此在同步的时候，我也开始同步巧克力浏览器的数据了。

巧克力浏览器是通过 eth_getblockbynumber 和 eth_gettransactionreceipt 把所有的交易数据都存入自己的数据库实现的。虽然其实可以等用户浏览到那个块再通过 rpc 获取数据，但是这样轻模式就没有检索功能了。所以还是需要解析所有的交易存入自己的数据库。

最终放弃 geth 二改用 erigon 的时候，巧克力浏览器才同步到一百多万的高度，就被迫停止了。

因为 erigon 只有完成同步，才会更新 eth_getBlockNumber 返回的高度。他同步的方式是先下载所有的块，然后执行，让后更新state数据，然后更新 rpc 接口的数据，然后获取最新高度，然后把落下的全下载回来，然后执行，让后更新state数据，然后更新 rpc 接口的数据，然后获取最新高度，然后把落下的全下载回来，然后执行，让后更新state数据，然后更新 rpc 接口的数据，然后获取最新高度...... 直到最后每次批处理的块只有1个，就算同步彻底完成。
如果 eth_getBlockNumber 一直返回 0 高度，我的浏览器就没法同步了，于是只能等。

问题是，他第一次的批量的时候，就试图从 0 一直批量执行到 1401万高度。结果，执行了10天才批量执行完。这一等就是十天, 等到了除夕前一天啊。执行完毕后，就再次落后十万高度了，于是进入第二次批处理。_因为我在机械盘上运行 erigon，因此 erigon 最后会永远落后几百到几千个高度，不过这个是后话，第一次批处理完成后，我的浏览器又可以开起来同步了_

结果，我对巧克力浏览器的同步速度非常的不满了。

因为，按同步速度估算，可没法10天完成巧克力浏览器的同步。大约需要20天，而且 ETA 在增加！最后可能达到了三年之久。为啥我能提前知道eta在增加呢？因为我观察到，同步空快很快，同步内部有交易的块就慢下来了。早期空块多，但是后期基本都是满块。满块的同步速度低到令人发指的超过数秒！

经过研究发现，速度是慢在了 gettransactionreceipt 上。这个接口对未缓存的交易返回速度需要数百毫秒。_第二次调用其实几个毫秒就返回了._
而巧克力浏览器访问的都是数年前的交易，都是属于 old data。因此每次调用它都要等待几百毫秒。
如果一个块里有个一百个交易，同步速度就惊人的 slow down 了。

如果把gettransactionreceipt的调用并发化呢？

大过年的，大家在看春晚，我却在敲代码。在改进巧克力浏览器的同步速度。完成批量同步，需要对原来的代码进行2个改进，第一个改进，是让原来的 jsonrpc 接口支持 pipelining，其次是实现 *等待所有协程完成* 的一个 asio 协程工具。虽然用在线程上此类的工具汗牛充栋，但是用在asio的协程上的工具可是 non-exist的。
有了这2个工具，只要把原来 for each transaction ; do get_transactioreceipt ; done 的代码，改成一次创建所有的协程去 get_transactioreceipt . 然后等待协程返回然后收集结果。 基本上就是 c++ 版的 asyncjs 里的并发 map 操作。

原来的 jsonrpc client，采取的做法是  async_write 后 async_read (当然是带 yield 的协程版），这样每次只能等待 rpc 返回后才能发起下一个 rpc 调用。
如果不改进 这个客户端类的代码，就只能被迫使用连接池才能并发调用 get_transactioreceipt 了。因此改进了这个 rpc 对象的代码， 可以在多个协程里并发的调用 jsonrpc.async_req(params, yield); 

并发 get_transactioreceipt 的版本上线后，同步速度一下子就改进了！块里交易量的多寡，对同步速度的影响就小下来了。当然是不能指望它毫无影响的 _:)_。

这样就过了一个愉快的除夕和新年。

那么，代码就从
```
for all tx
    get_transactioreceipt ...
save_block
```

变成了
```
for for all tx
    asio::spawn(  get_transactioreceipt ... ) # 开一堆协程
wait all corotines
save_block
```

同步了几天，高度到了四百万了，按这个速度，10天即可完成同步。考虑到后期满块增加，也不会超过20天吧。看来三月份就可以满血上线了。

然而，到了立春前天一看日志，情况变不对劲了。速度又慢下来了。

原来是数据库操作慢下来了！原先空快多，交易量少。同步了三百万高度，交易量都不足千万。
但是到四百多万高度，交易量已经膨胀到超过一个亿了。

我的小 nas 哪里受得了这么大的表啊。数据库爆表了。马上花了数个小时的时间，做了分表。保存一个block内容的时间才从数百毫秒重新下降到20毫秒上下。
但是显然和初期的5毫秒上下保存有差距。

显然，如果把数据库的保存操作异步化，就可以提升速度。

这个虽然很简单，只要把保存这个操作放到单独的协程里进行即可。

但是，问题出在我的同步逻辑上。因为 jsonrpc 会丢失链接（手动重启 erigon 或者 erigon crash )，数据库也会挂（手贱和其他问题）
如果异步了，就不容易处理在挂掉的点上重新执行一遍这个逻辑。

这个时候，我很怀念 nodejs 的 promise/await ， 如果有 promise 就好了，我的代码可以改成这样。

```
[fetch_ok, data] = await rpc_get_block_data(sync_height)

for (; sync_height < await rpc.get_blockheight();)
{
    next_block_data_promise =  rpc_get_block_data(sync_height + 1); // 马上获取下一个块, 后台获取，不等待结果
    if (fetch_ok)
    {
        save_ok = await save_to_db(data);
        if (save_ok)
        {
            sync_height++;
            [fetch_ok, data] = await next_block_data_promise; // 等待异步完成结果
       }
    }
    else
        [fetch_ok, data] = await rpc_get_block_data(sync_height); // 重获取一次
}

```

这样，如果 db 保存失败，sync_height 就不会增加，并且重新获取。
这样避免同步的过程中出现漏同步，出现空洞高度。这种写法还避免了完全异步fetch和save模式下的同步协作问题。大大简化了代码。

研究了一整天，最后发现了 asio 早已提供了 promise/await！

下面进入 boost::asio::experimental::use_promise 的世界！

上面这个代码，用 asio 的方式，写法就是这样

```
[fetch_ok, data] = rpc_get_block_data(sync_height， yield); // yield 说明上下文是在 asio::spawn 开启的协程里

for (; sync_height < await rpc.get_blockheight();)
{
    // 马上获取下一个块, 后台获取，不等待结果, 注意这里的 use_promise 替代了 yield
    next_block_data_promise =  rpc_get_block_data(sync_height + 1, asio::experimental::use_promise); 
    if (fetch_ok)
    {
        save_ok = save_to_db(data, yield);
        if (save_ok)
        {
            sync_height++;
            [fetch_ok, data] = next_block_data_promise.async_wait(yield); // 等待异步完成结果 这里的 wait 用了 yield
       }
    }
    else
        [fetch_ok, data] = rpc_get_block_data(sync_height, yield); // 重获取一次, 不用 promise 了
}

```

当然，自己的 rpc_get_block_data 也要经过修改，实现支持 yield/use_promise 双操作。 括弧 asio 自己的IO对象其实都支持 回调/yield/use_promise 三操作的。


promise/await 永远的神！

PS: 我运行在家nas上的巧克力浏览器，虽然还在同步，但是可以使用了 [geth.home.microcai.org:3586](http://geth.home.microcai.org:3586/)

当然，因为是家里的 nas，so 只能用 ipv6 访问。不开放 ipv4 访问，免得麻烦。

稳定性不保证哈！随时调试。
