---
layout: post
title: 使用自己硬件的时候写的两个补丁
tags: [kernel]
---

# 键盘问题

去年买了一个机械键盘。不过一直有一个困扰我的问题，就是键盘插入 USB 口后，会等待 10s 左右的时间，然后才识别。查看 dmesg 输出会看到有什么 Timeout 的。
后来发现是硬件 bug。而这种硬件 bug 是可以被内核 work-arround 的。 具体的来说就是，一个 USB-HID 插入的时候，内核会询问设备的一些特性，比如说是否支持多点触控之类的。
但是我这块键盘并不会不报告，导致内核等了大概 10s 没收到报告，于是就当你不支持咯。才继续下去。当然，除了这个该死的硬件闭口不谈外，没啥别的 bug。 所以 10秒后，键盘还是能正常使用。

那么解决办法就很简单了，把这个键盘的设备 ID 添加到一个 缺陷列表， 列表文件在 drivers/hid/usbhid/hid-quirks.c 。
当然，遵循内核的设计风格，不能直接把设备 ID 这种 16 进制的数字填进去，所以在 drivers/hid/hid-ids.h 这里添加了宏定义。
补丁如下


```
  From 7af026610fe6a41426f53f3a4ea41e3aa1ee780f Mon Sep 17 00:00:00 2001
  From: microcai <microcaicai@gmail.com>
  Date: Sun, 13 Jul 2014 15:41:14 +0800
  Subject: [PATCH] HID: usbhid: add quirks for 0x04d9:0xa096 keyborad device

  I am using a USB keyborad that give me
  "usb_submit_urb(ctrl) failed: -1" error when I plugin it.
  and I need to wait for 10s for this device to be ready.

  by adding this quirks, the usb keyborad is usable right after plugin

  Signed-off-by: Wangzhao Cai <microcaicai@gmail.com>
  ---
  drivers/hid/hid-ids.h           | 1 +
  drivers/hid/usbhid/hid-quirks.c | 1 +
  2 files changed, 2 insertions(+)

  diff --git a/drivers/hid/hid-ids.h b/drivers/hid/hid-ids.h
  index 48b66bb..9683f6c 100644
  --- a/drivers/hid/hid-ids.h
  +++ b/drivers/hid/hid-ids.h
  @@ -479,6 +479,7 @@
  #define USB_DEVICE_ID_HOLTEK_ALT_MOUSE_A070    0xa070
  #define USB_DEVICE_ID_HOLTEK_ALT_MOUSE_A072    0xa072
  #define USB_DEVICE_ID_HOLTEK_ALT_MOUSE_A081    0xa081
  +#define USB_DEVICE_ID_HOLTEK_ALT_KEYBOARD_A096 0xa096
  
  #define USB_VENDOR_ID_IMATION          0x0718
  #define USB_DEVICE_ID_DISC_STAKKA      0xd000
  diff --git a/drivers/hid/usbhid/hid-quirks.c b/drivers/hid/usbhid/hid-quirks.c
  index 31e6727..e2e8b7c 100644
  --- a/drivers/hid/usbhid/hid-quirks.c
  +++ b/drivers/hid/usbhid/hid-quirks.c
  @@ -124,6 +124,7 @@ static const struct hid_blacklist {
	  { USB_VENDOR_ID_SYNAPTICS, USB_DEVICE_ID_SYNAPTICS_HD, HID_QUIRK_NO_INIT_REPORTS },
	  { USB_VENDOR_ID_SYNAPTICS, USB_DEVICE_ID_SYNAPTICS_QUAD_HD, HID_QUIRK_NO_INIT_REPORTS },
	  { USB_VENDOR_ID_SYNAPTICS, USB_DEVICE_ID_SYNAPTICS_TP_V103, HID_QUIRK_NO_INIT_REPORTS },
  +       { USB_VENDOR_ID_HOLTEK_ALT, USB_DEVICE_ID_HOLTEK_ALT_KEYBOARD_A096, HID_QUIRK_NO_INIT_INPUT_REPORTS | HID_QUIRK_HIDINPUT_FORCE },
  
	  { 0, 0 }
  };
  -- 
  2.0.4

```

# 看门狗设备问题

在 奶茶东 6/18 活动的时候，杀了一块 Z97 主板和 i7 一块回来。当然，顺便低价处理掉了原来的 P8P67 主板和 E3-1230 CPU。

在使用 P8P67 的时候，我一直有开启 systemd 的 看门狗支持。设备 /dev/watchdog 和看门狗。驱动为 iTCO_wdt。
这个看门狗乃芯片组内置设备。所有的 intel 芯片组（别太老的）都有。
但是换了主板后，看门狗设备不见了。我不相信 intel 阉割了这个功能。肯定是驱动问题。

看门狗是挂在 LPC 总线上的。CONFIG\_LPC\_ICH=y 已经确定开启了。但是设备就是没有。

lspci 看到了一个设备 

00:1f.0 ISA bridge: Intel Corporation 9 Series Chipset Family Z97 LPC Controller

使用 -vvv 增强输出详细度后，看到 Kernel driver in use: 这里居然是空的。

等等，为啥是 ISA bridge 啊！ 于是折腾把 ISA 总线编译进去。 结果还是没有。放了一段时间没去搭理。

今天又看了一下，发现详尽模式输出是这样的

00:1f.0 ISA bridge [0601]: Intel Corporation 9 Series Chipset Family Z97 LPC Controller [8086:8cc4]

[8086:8cc4] ?? 这个 ID 内核有么？

于是搜索了 drivers/mfd/lpc\_ich.c 这个文件，发现 id 那么多，唯独没有这个 ID !!! 于是抱着试试看的态度，向这个文件添加了这个 id , 哈哈，重启后，看门狗设备就乖乖出现了。

下面放出这个补丁，以便让使用这款 华硕 Z97-A 主板的人收益


```
  From 2abf7529a1b213ad2cab036cfb99dacba22d3107 Mon Sep 17 00:00:00 2001
  From: Wanzhao Cai <microcaicai@gmail.com>
  Date: Sat, 9 Aug 2014 01:46:29 +0800
  Subject: [PATCH] mfd: lpc_ich: add support for Intel Z97 chipset

  This patch adds the LPC Controller Device IDs found on ASUS Z97-A mother broad.

  lspci output for this mother broad:

  00:1f.0 ISA bridge [0601]: Intel Corporation 9 Series Chipset Family Z97 LPC Controller [8086:8cc4]
	  Subsystem: ASUSTeK Computer Inc. Device [1043:8534]
	  Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	  Status: Cap+ 66MHz- UDF- FastB2B- ParErr-
	  DEVSEL=medium >TAbort- <TAbort- <MAbort- >SERR-
	  <PERR- INTx-
	  Latency: 0
	  Capabilities: [e0] Vendor
	  Specific Information: Len=0c <?>
	  Kernel driver in use: lpc_ich
	  Kernel modules: lpc_ich

  Signed-off-by: Wanzhao Cai <microcaicai@gmail.com>
  ---
  drivers/mfd/lpc_ich.c | 1 +
  1 file changed, 1 insertion(+)

  diff --git a/drivers/mfd/lpc_ich.c b/drivers/mfd/lpc_ich.c
  index 7d8482f..e4b37c0 100644
  --- a/drivers/mfd/lpc_ich.c
  +++ b/drivers/mfd/lpc_ich.c
  @@ -738,6 +738,7 @@ static const struct pci_device_id lpc_ich_ids[] = {
	  { PCI_VDEVICE(INTEL, 0x1f3b), LPC_AVN},
	  { PCI_VDEVICE(INTEL, 0x0f1c), LPC_BAYTRAIL},
	  { PCI_VDEVICE(INTEL, 0x2390), LPC_COLETO},
  +       { PCI_VDEVICE(INTEL, 0x8cc4), LPC_WPT_LP},
	  { PCI_VDEVICE(INTEL, 0x9cc1), LPC_WPT_LP},
	  { PCI_VDEVICE(INTEL, 0x9cc2), LPC_WPT_LP},
	  { PCI_VDEVICE(INTEL, 0x9cc3), LPC_WPT_LP},
  -- 
  2.0.4

```


许多时候为内核添加设备支持就是一个 id 添加进去的事情，呵呵。如果发现自己的设备不被支持了，就试试看这招吧！





