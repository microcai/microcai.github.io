---
layout: post
title:  git 定义商城
tags:   [git, mall, markdown, OOR]
---

# 引

    商人商人实在太伤人
    你说所有人都这么看你
    怨不得每一天唉声又叹气
    感慨着赚钱真的不容易

    其实商人就是买东西
    把东边的买卖到西边去
    辨贵贱 调余缺 度远近
    世上不能没有我和你

    急人之所急 需人之所需
    这才是真正做生意
    买的找不到（着）卖的 卖的找不到（着）买的
    一潭死水怎会有生机
    急人之所急 需人之所需
    这才是真正帮了自己
    一网不捞鱼 二网不捞鱼
    三网就捞个大尾巴尾巴尾巴鱼



做买卖, 就得有铺子. 从前的铺子, 在街头.
现在的铺子, 还可以在网上.

只要是个铺子, 就得有人打理.

不管是格子铺, 还是架子铺. 东西都要分门别类的摆放好. 逛的人舒心了, 才会多来逛.

通常网铺会提供一个在线的编辑器, 用于输入描述性的文字. 还可以设定字体,字号,颜色.

还能插入图片.

# 痛

图文并茂, 才能赏心悦目.

编辑器可是个大工程, 何况还是在线的.

于是, 编辑商品的编辑器, 就只能因繁就简了. 只能聊胜于无了.

每天面对这么简陋的编辑器, 小二也觉得越来越犯2. 于是, 放截图替代了用简陋编辑器含辛茹苦的码字.

看着好像是个精心排版的东西, 实际上是在其他软件上排版好, 然后截图过来的图片.

编辑功能彻底成了摆设.

即使是这样, 小二还嫌他传图功能都鸡肋呢!

在店小二还在学习 加粗,变大,插图片 富文本三部曲的时候, 程序员也想给自己的 README 加一点点的样式.

程序员可不喜欢纯靠鼠标精确点击实现的 加粗,变大,插图片 三部曲.

于是 markdown 应运而生.

如果仅仅只是把鸡肋的富文本编辑器换成 markdown, 那只完成了改变的第一步.

第二步, 是把商品元属性的设置, 从鼠标的点击中释放出来.

程序员不喜欢写文档, 但是喜欢写注释.
因为注释是跟随代码的.

分离的文档, 如离家的孩子, 流浪在外边. 就像脱离了控制的野指针一样.


# 解 # 

于是, 我发明了使用 GIT 管理店铺商品的商城.


每一件待售的商品, 都是一个 markdown 文档.
商品的 类目, 价格, 等等信息, 和 图文并茂的详情描述, 一起写到一个文档里.

把所有的商品, 按目录组织好, 并且通过 git 进行版本控制.

一个店铺, 一个 git 仓库.

把 本地编辑好的 文档, push 到远程, 上架就完成了.

下架, 也只需要删除文件, 并 push.

因为 git 控制了版本, 以后想重新上架, 也只需要 revert 那个删除的提交.

因为文档都在本地, 可以使用自己最趁手的编辑器编辑. 许多编辑器还有非常高级的批量操作功能, 对管理大量商品简直如虎添翼.

至于图片, 和仓库保存到一起就行.

商品的描述, 统统放在 goods 目录下. 图片放在 images/ 目录下.

假设你编辑的商品是 goods/cat1/iphone4.md

图片在 images/cat1/iphone.jpg

编辑的时候, 使用 ```![img](../../images/cat1/iphone.jpg)``` 指令引入图片
由于使用的是相对 iphone4.md 文件的相对路径, 因此 markdown 编辑器在本地是可以正确预览的.

>这部分相对路径的引用, 会在服务端分发给买家的浏览器的时候, 替换成图片的绝对地址.
因此, 本地编辑预览和在线浏览都不会有问题.

# 优

除了这个改进, 还有就是整个商城的前端是 SPA. _Single Page Application_

markdown 也是在前端渲染的. 同以往 SPA 使用 RESTfull API 不同, 我的商城使用了
长链接.

长链接, 就取消了 cookie 的需求. 不用对每个请求都进行鉴权. 只要连接建立的时候鉴权一次.

长链接, 比 pipeling 更进一步, 实现了 OOR _out of order rpc_. 

> HTTP pipeling, 只是复用链接的时候激进了点, 不等请求返回就发送后续请求.
> 但是, 应答内容本身还是按请求的次序返回的.
> 而 OOR, 应答返回是乱序的. 执行完毕就返回, 无需按请求提交的次序返回
> 故 OOR 需要每个请求都带一个唯一的 id. 服务端返回应答的时候会携带上请求对应的 id

因此, 用三个关键字概况我的商城的改进, 就 3 点

 - OOR 
 - markdown 
 - git

店小二只需使用 visual studio code 就可以完成店铺管理.
