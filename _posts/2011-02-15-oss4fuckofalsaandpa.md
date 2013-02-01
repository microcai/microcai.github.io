---
layout: post
title: OSS4 deprecated ALSA and PulseAudio
---

Turst me , OSS4 = ALSA + PulseAudio , and all implemented in kernel. very low latency.

OSS4 have kernel level mix feature which ALSA lack for years and that's why PuleAudio fucked to burn.

OSS4 also have per-process volume control which ALSA lack for years and that's why PuleAudio fucked to burn.

OSS4 is not a new API but a new implementation. So existing App won't need any modification. 
But when ALSA burn , every app need to re-write with the poor designed/doc-ed ALSA API.
When nearly lost app support ALSA, PA fuck the world again!!! And every app need to re-write with the PA api.

But when OSS4 came back. NO app need to re-write. OSS4 works as a drop in replacement!
Great!!!

And, OSS4 is pure kernel side. OSS4 don't need assistance from user-land.

So, pleace deprecated ALSA and PA immediately and include OSS4. 
And ALSA foundation rename to OSS-ng foundation and sopport OSS4.
