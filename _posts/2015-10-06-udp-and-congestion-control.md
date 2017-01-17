---
layout: post
title: UDP and congestion control
tags: [network, TCP, UDP]
---

TCP is good, good for nearly everything. It's a general purpose abstraction for networking applications. But TCP is bad for one thing: it's general. If you have some special need, setsockopt(2) can help you. But really, it dosen't help much.

What if you have customized need for congestion control?

The need for different congestion control algorithm is the main reason that we implement
our protocol ontop of UDP.

I was a little bit shocked that during the 4.2 merge window of Linux, TCP too got a new congestion control algorithm that's a little bit similar to the one I used in my protocol - that is, based on the change rate of RTT, rather than based on a packet lost.

The new one in TCP is called Delay-gradient congestion control.

This new Delay-gradient congestion control and the one employed by my protocol are different in many ways, but they do share a commmon concept : detect the bandwith by the monitoring the changes of RTT. The traditional ways of doing such detecting is by packet lost - you cut your sending speed when you detect a packet lost.

Since TCP has this new fancy congestion control algorithm, why we still use UDP?

Well, we are still different in many ways. Our protocol are more tolerance on packet lost than TCP, which makes it more suitable on transnational network.

We tolerant on packet lost will still employe "Delay-gradient" to prevent a packet lost. Can TCP provide this? No.

So, use UDP if you need fine control over congestion control algorithm, otherwise TCP.
