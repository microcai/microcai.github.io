镜像  EFI boot 分区。



最近给电脑配了2个 nvme SSD 做 ZFS mirror . 每个盘都分了 2个分区， 一个 EFI system 分区， 一个 ZFS 分区。两个 ZFS 分区放到一个 zfs pool 里做镜像。但是 两个 EFI 分区。。。。怎么 mirror 呢？



首先尝试了 raid1, 发现 raid1 在盘上建的话， 会破坏 ZFS。如果用分区建 raid1, 则分区类型被修改为 linux raid， 而不是 EFI system partition 了， 主板就不识别了。

然后尝试的是挂到 boot1  boot2 两个分区， 后台写个脚本 rsync 拷贝同步。但是发现这个解决方案不够优雅。



如果能建立一个没有 metadata 的 mirror 设备就好了。

几经周折，发现了 dmsetup 命令， 可以建立不依托 metadata 数据的 mirror 分区。如果没有 metadata，就可以保留原汁原味的分区表，只是在系统层做数据 mirror， 无需主板的任何支持。



那么就只要用 dmsetup 设置 nvme0n1p1 和 nvme1n1p1 两个分区为 mirror。 然后把  mirror 设备挂到 /boot。

执行两次  `efibootmgr -c -d /dev/nvme0n1 -L "Linux Boot Manager" -l \\EFI\\BOOTX64.EFI` `efibootmgr -c -d /dev/nvme1n1 -L "Linux Boot Manager" -l \\EFI\\BOOTX64.EFI`

为主板设定两个EFI分区的两个一模一样的引导项。



为了开机自动挂，又写了 boot.mount 

```ini
[Unit]
Before=local-fs.target
After=mirror-boot.service
Requires=mirror-boot.service

[Mount]
Where=/boot
What=/dev/mapper/boot-efi-mirror
Type=vfat
```

和 mirror-boot.service

```ini
[Unit]
Description=Create EFI mirror

[Service]
RemainAfterExit=true
Type=oneshot
ExecStart=/sbin/dmsetup create boot-efi-mirror --table '0 1048576 mirror core 1 1024 2 /dev/nvme0n1p1 0 /dev/nvme1n1p1 0'

[Install]
WantedBy=basic.target
```



这样挂 /boot 的时候会自动启动 mirror-boot.service ，也就是自动调用 dmsetup 把两个 EFI 分区给建好 mirror。