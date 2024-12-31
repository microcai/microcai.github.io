---
layout: post
title: 在Linux上交叉编译windows版 Qt 和 qt应用
tags: [llvm, mingw32, clang, qt]
---

# 准备工具链

一个半月前，我研究了一下 [使用本机 clang 进行交叉编译](https://microcai.org/2024/11/16/cross-compile-by-clang.html)。那时候，是在本机 x86 上交叉编译 arm 和 mips 架构的软件。目标系统还是 linux 的。

交叉编译，需要使用交叉工具链。而使用本机clang进行交叉编译，只是将交叉工具链里的“编译器”换成了本机本就安装的 clang, 而 “头文件和库文件” 则是使用 archlinux 和 mips debian 的 rootfs 提供。
缺啥库，qemu-user + chroot 进去后直接安装即可。

关于如何进行异构chroot, 我在 [chroot to arm on an x86 Gentoo
](https://microcai.org/2011/04/26/chrootarm.html) 和 [异构容器](https://microcai.org/2022/04/26/hybrid-container.html) 里分别讲述过。

但是，一个合格的开发者，怎么可能只写 Linux 程序呢？

非常自然的，交叉编译到 windows 上也是一个正经需求。

要交叉到 windows 上，通常的做法是使用 MinGW。MinGW 不仅仅是一套移植到 Windows 上的 gcc 工具链，还是一套在 Linux 下产生exe文件的交叉编译器。

但是正如标签里的 clang 所言，本篇介绍的，可不是 MinGW ， 而是继续使用本机的 clang 进行交叉编译 exe。

编译器本机早就有了，头文件和库呢？

答案是，还得从 mingw 里拿。

通常来说， mingw 里是一套 “自由” 的 sdk. 意味着它使用 动态链接的 MSVCRT.DLL 作为 C 库, 然后辅之以  libmingw32-1.dll 作为 posix 兼容层，然后 libgcc-1.dll 作为 编译器运行时。
然后是 libwinpthread-1.dll 提供 pthread ，然后使用 libstdc++-1.dll 提供 c++ 标准库。

链接出来的 exe 带上一堆 dll 可不是我喜欢的做法。我希望使用静态链接，最多动态链接到标准系统DLL。显然 mingw32 并不能满足我的要求。使用它的库，就非得带上一堆 DLL。

既然之前用 clang 进行交叉，那么我也希望继续使用 clang 交叉编译 exe。本来计划从 VS2022 里抠头文件，毕竟 VS2022 的头文件肯定是兼容 clang 的。

结果大喜过望的是，[LLVM-MINGW32](https://github.com/mstorsjo/llvm-mingw/releases) 恰好满足了我的需求。 LLVM-MINGW32 是将 mingw32 里的 gcc 换成了 clang 。同时被替换掉的还有运行时。应该说，只是使用了 mingw32 开发的 windows SDK。剩下的是 llvm 项目的。c++ 标准库使用的是 libc++。编译器运行时是llvm开发的 libcompiler-rt，而 C 库，则使用的微软新做的 UCRT。UCRT 从 win10 开始就是系统标准库了。win10 以前的系统还提供了 “安装程序”。

因此，在不进行任何设置的情况下， llvm-mingw32 编译出来的程序，会依赖  ucrtbase.dll, libc++.dll, libunwind.dll  libwinpthread-1.dll。

其中 ucrtbase.dll 是 标准系统库。因此，需要将剩下的库进行“静态"即可。

我的做法仍是，修改 clang 编译器的配置文件 x86_64-w64-windows-gnu.cfg 为如下内容。

```
-target x86_64-w64-mingw32
-rtlib=compiler-rt
-stdlib=libc++
-fuse-ld=lld
-flto=thin
-Wl,--start-group -Wl,-Bstatic -lc++ -lunwind -lwinpthread -Wl,-Bdynamic -Wl,--end-group -lucrtbase
```

这样就不必在每个项目里都改 cmakelists.txt 添加静态链接参数了。

有了，llvm-mingw ，接下来就是准备一个 llvm-mingw 编译的 静态 QT 库了。

# 准备 qt 静态库

从 git 拉 qt 源码：

```bash
git clone https://code.qt.io/qt/qt5.git qt-source -b v6.8.1
cd qt-source
./init-repository.pl
```

这是非常漫长的一个过程。如果可能的话，挂上 VPN。

交叉编译 QT 啊，需要一种叫 Qt6HostInfoConfig.cmake 的文件。这个文件告诉了 qt ，到哪里去找“本机 qt 工具”。

因为 qt 编译的过程中，需要使用 moc, uic 之类的工具对源码进行处理。而这些工具需要在本机运行。因此不能编译，而必须使用本机已有的。不然在 linux 上如何运行 moc.exe 呢？

本机 qt 工具，可以直接使用系统自带的 qt. d但是系统自带的 qt 是没有 Qt6HostInfoConfig.cmake 的。
因此需要自己编写一个。内容如下：

```cmake
set(Qt6CoreTools_DIR /usr/lib64/cmake/Qt6CoreTools)
set(Qt6DBusTools_DIR /usr/lib64/cmake/Qt6DBusTools)
set(Qt6GuiTools_DIR /usr/lib64/cmake/Qt6GuiTools)
set(Qt6LinguistTools_DIR /usr/lib64/cmake/Qt6LinguistTools)
set(Qt6QmlTools_DIR /usr/lib64/cmake/Qt6QmlTools)
set(Qt6Quick3DTools_DIR /usr/lib64/cmake/Qt6Quick3DTools)
set(Qt6QuickTools_DIR /usr/lib64/cmake/Qt6QuickTools)
set(Qt6ScxmlTools_DIR /usr/lib64/cmake/Qt6ScxmlTools)
set(Qt6ShaderTools_DIR /usr/lib64/cmake/Qt6ShaderTools)
set(Qt6ShaderToolsTools_DIR /usr/lib64/cmake/Qt6ShaderToolsTools)
set(Qt6Tools_DIR /usr/lib64/cmake/Qt6Tools)
set(Qt6ToolsTools_DIR /usr/lib64/cmake/Qt6ToolsTools)
set(Qt6UiTools_DIR /usr/lib64/cmake/Qt6UiTools)
set(Qt6WaylandScannerTools_DIR /usr/lib64/cmake/Qt6WaylandScannerTools)
set(Qt6WebEngineCoreTools_DIR /usr/lib64/cmake/Qt6WebEngineCoreTools)
set(Qt6WidgetsTools_DIR /usr/lib64/cmake/Qt6WidgetsTools)
```

把这个文件丢到 mingw 的文件夹里备用。比如 `~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/`

然后开始编译 qt 。命令如下：

```bash

git clone https://code.qt.io/qt/qt5.git qt-source -b v6.8.1
cd qt-source
./init-repository.pl
cd ..

export PATH="~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin:$PATH"

mkdir qt-build
cd qt-build

../qt-source/configure -optimize-size -debug-and-release -static -static-runtime -xplatform win32-clang-g++ -platform win32-clang-g++ \
-qt-host-path ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/ \
-prefix "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/qt-release" -confirm-license \
-no-feature-accessibility \
-no-feature-valgrind \
-no-feature-appstore-compliant \
-no-feature-assistant \
-no-feature-example-hwr \
-no-feature-windeployqt \
-no-feature-macdeployqt \
-no-feature-androiddeployqt \
-no-feature-designer \
-no-feature-qdbus \
-no-feature-qtdiag \
-no-feature-qtplugininfo \
-no-feature-qtattributionsscanner \
-skip qtopcua,qtgrpc,qt3d,qtcanvas3d,qtdatavis3d,qtgamepad,qtcharts,qtconnectivity,qtmqtt,qtcoap,qtqa,qtdbus,qtremoteobjects,qtpim,qtspeech,qtfeedback,qtactiveqt,qtserialbus,qtserialport,tests \
-- -DFEATURE_cxx20=ON -DCMAKE_TOOLCHAIN_FILE=~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/cross_llvm_mingw.cmake


cmake --build .
cmake --install .

```

需要注意的是 `-qt-host-path` 参数。还有 `-DCMAKE_TOOLCHAIN_FILE`

~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/cross_llvm_mingw.cmake 的内容如下

```
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_VERSION 10.0)

set(CMAKE_SYSTEM_PROCESSOR x86_64)
set(WIN32 TRUE)
set(WIN64 TRUE)
set(MINGW TRUE)
set(MSVC FALSE)

set(CMAKE_SIZEOF_VOID_P 8)

# specify the cross compiler
set(ENV{PATH} "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin:$ENV{PATH}")
set(CMAKE_C_COMPILER "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin/x86_64-w64-mingw32-clang")
set(CMAKE_CXX_COMPILER "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin/x86_64-w64-mingw32-clang++")

# where is the target environment
set(CMAKE_FIND_ROOT_PATH "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/")
set(CMAKE_SYSROOT "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/")

# search for programs in the build host directories
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# for libraries and headers in the target directories
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE BOTH)
```

期间会 100% 遇到编译错误。主要是 Qt 开发人员不怎么使用 CI 进行测试。因此本机调试通过就急着提交源码。根本不管源码能不能在别的环境下编译通过。

所有如果遇到编译错误，请自行修正源码中的错误。^_^。

目前 在 v6.8.1 分支中，遇到的编译错误来自 qtquick3d 带的三方库 embree。
有些是因为 使用了 Windows.h 这样的头文件名字导致失败。这个可以不修改源码，自己跑到 mingw 的头文件夹里，把windows.h 做各软连接 Windows.h 搞定。还有什么 Winsock2.h 和 winsock2.h 之类的区别。
凡是遇到这种大小写问题导致的头文件没找到，优先改 mingw 的头文件做软连接。这样不需要修改源码。
这样，就只有 embree 的代码是需要真的修改的了。embree 的错误其实上游是修正了的，可以参考上游的修正 [fix issue #486](https://github.com/RenderKit/embree/commit/cda4cf191)

当然，如果是只编译 qtbase 是不需要操心这些的。

编译完成后，就把 qt安装到了 mingw 的文件夹里。当然安装到别的文件夹里也可以。我倾向于安装到 mingw 的文件夹里。主要是因为 cmake工具链使用了 --sysroot=mingw安装目录 参数。
对没在 sysroot 里的库可能会被 “无视“。

# 使用 qt 静态库

接下来，就是对使用 qt 的项目进行交叉了。同样的，需要写一份 toolchain 文件。

```
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_VERSION 10.0)

set(CMAKE_SYSTEM_PROCESSOR x86_64)
set(WIN32 TRUE)
set(WIN64 TRUE)
set(MINGW TRUE)
set(MSVC FALSE)

set(CMAKE_SIZEOF_VOID_P 8)

# specify the cross compiler
set(CMAKE_C_COMPILER "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin/x86_64-w64-mingw32-clang")
set(CMAKE_CXX_COMPILER "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin/x86_64-w64-mingw32-clang++")

# where is the target environment
set(CMAKE_FIND_ROOT_PATH "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/")
set(CMAKE_SYSROOT "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/")
set(ENV{PATH} "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/bin:$ENV{PATH}")

# search for programs in the build host directories
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# for libraries and headers in the target directories
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE BOTH)

set(CMAKE_CXX_FLAGS_RELEASE "-flto=thin")

set(CMAKE_PREFIX_PATH "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6")
set(QT_HOST_PATH "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/")
set(Qt6HostInfo_DIR "~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/")
set(QT_FORCE_FIND_TOOLS  ON)

set(Qt6BundledZLIB_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledZLIB)
set(Qt6BundledPcre2_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledPcre2)
set(Qt6BundledLibpng_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledLibpng)
set(Qt6BundledHarfbuzz_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledHarfbuzz)
set(Qt6BundledFreetype_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledFreetype)
set(Qt6BundledLibjpeg_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledLibjpeg)
set(Qt6BundledOpenXR_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6BundledOpenXR)
set(Qt6Qml_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6Qml)
set(Qt6_DIR ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/qt-release/lib/cmake/Qt6)

```

保存为 ~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/cross_llvm_mingw.cmake

然后，就可以使用

```bash
cmake --toolchain=~/llvm-mingw-20241217-ucrt-ubuntu-20.04-x86_64/x86_64-w64-mingw32/share/cross_llvm_mingw.cmake  path_to_source
```

进行交叉编译了。

使用方式可以看下我这个终端录屏 [asciinema录制回放](https://asciinema.org/a/pOzr0D9u9WMxTdy7yDeEFIgxW)

