---
layout: post
title: For every bug, there is a ugly man
---

For every bug found in the softwre, there is a ugly man behind.
For too many days! I've been working on that bug! And the software has already ran in a hotel!
The only way that me can use to debug is using ssh plus vim.
No other way. I cannot use gdb, Because that will let the clients unable to surf online.
My program runs on a Linux router. Hang! Hang! There must be dead locks !
Where is it?! Then for many nights, I can't sleep. Reviewing very code that acquiring locks. There is no mistake.
 ===============================
I have to use gdb. Then re-ran my progrm in gdb.
when it stopped response, I interrupt this stupid program. ..... strike!
The error happens when doing libnet_init() It must not be libnet's bug. .........
Finally, I knew what's wrong. memcpy() param 3 too lengh , in the other file. and other thread.

 For every bug found in the softwre, there is a ugly man behind.
 Now it plays on me.
