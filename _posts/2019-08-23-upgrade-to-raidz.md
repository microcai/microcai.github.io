---
layout: post
title: 升级到4盘 raidz
tags: [zfs, raidz]
---



上次折腾NAS, 使用了2个8T的盘建的 raid1. 速度不太满意. raid0 当然怕挂一个盘数据就没了, 索性就再买2个8T的, 组建4盘位raid5. 



这阵列升级啊, 一般的做法是, 先建 raid5 新阵列, 然后把数据拷贝过去, 然后... 等等, 2个盘建什么 raid5. 那先把 raid1 取消镜像吧. 那也只有3个盘啊! 三个盘是能 raid5  问题是拷贝完了多一个盘, 而且我的目的是4盘 raid5.



咋办?



简单, 首先确实是需要取消镜像,  然后把剩下的3个盘, 和一个 假设备 一起建一个 4 盘的 raid5, 然后在数据拷贝进去之前, 把假设备从阵列里下线. 然后把数据从旧盘上拷贝到新阵列.

最后完成拷贝后, 把旧盘替换到阵列里取代下线的假设备, 然后等待 raid5 重建完成. 即可大功告成.

假冒设备的制作方法是 

```bash
#dd bs=1 count=1 if=/dev/zero of=/fakedisk.img seek=8T
```

接着取消 sda sdb 的镜像

```bash
#zpool detach pool1 sda
```

然后创建新池并立即下线假盘

```bash
#zpool create pool2 raidz sda /fakedisk.img sdc sdd 
#zpool offline pool2 /fakedisk.img
#rm /fakedisk.img
```

接下来就是 zfs send 和 zfs recv 迁移数据

```bash
#zfs send pool1 | zfs recv pool2
```

漫长的拷贝完成后

```bash
#zpool destroy pool1
#zpool replace pool2 /fakedisk.img sdb
```

然后又是漫长的 raid5 重建的过程.

当然, pool2 盘已经可用了;) 重建的时候只是性能些许下降.

/fakedisk.img 文件因为是稀疏文件, 虽然文件大小达到了 8T, 但是实际上并不占用磁盘空间.

创建完 池后, 大小也是非常小的, 但是如果这个时候开始拷贝数据, 那么这个 fakedisk.img 文件占用的磁盘空间会

慢慢变大, 就把 NAS 的 根分区(在U盘上)撑爆了. 所以要在考试拷贝数据前, 将它强制下线并删除.

这个时候 pool2 就是3盘有效的降级状态. 放心, 这个过程中盘挂了 数据还是有2份, 一份在老盘里, 一份在阵列里.

最危险的时候, 其实是在最后重建raid5 的时候, 这时候挂了一个盘, 数据就没了 (笑)

