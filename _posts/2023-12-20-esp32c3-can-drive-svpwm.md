---
layout: post
title: ESP32C3 也能输出svpwm
tags: [变频器, ESP32C3, ESP32]
---

# 前言
先看以下乐馨官方的 ESP32S3 和 ESP32C3 的对比

![](/images/esp32s3-vs-esp32c3.png)

很明显，ESP32C3 缺乏 MCPWM 设备。

所谓 MCPWM, 就是专门为产生svpwm设计的电路。他能产生6路互补的PWM信号，并且实现中央对齐。然后还能实现在PWM信号的特定位置产生同步事件。app据此可以在这个同步事件上实现电流采样。

一度我以为 ESP32C3 是无法用于驱动电机的。

直到一次偶然，我看到 SimpleFOC 的论坛里有人提到要支持 ESP32C3。我在想，这C3不是没MCPWM么？ SimpleFOC咋支持？

事实是，SimpleFOC 也确实不支持 C3。但是有人回复他实现过。就用的 LEDC PWM。


要知道，ESP32C3 可比 S3 便宜了一半还多。要真的能驱动电机，那我的 VVVF 变频器大业，又多了一项可选的MCU！

# 实践

虽然别人有提过他用 LEDC PWM 实现了 foc。但是吧，无代码无真相。但是总归人家说可以。那我研究研究吧。于是购入 ESP32S3。

等等，不是说C3吗？咋买了S3呢？因为我确信我的VVVF需要蓝牙！需要WIFI！AT32F415已经不能满足我的需求了。

然后顺便买了个9.9的 ESP32C3开发板。

等开发板到了，我马上研究起了 ESP32C3。虽然C3是顺便买的，但是不妨碍我先研究它。

于是在项目里创建了 lib/libvfd/hal/esp32c3pwm.{hpp,cpp} 文件。

着手研究 ESP32C3 里的 LEDC PWM。

最后踩了无数的坑后，把他实现出来了。

```

#if defined(ESP_PLATFORM)

#ifdef CONFIG_IDF_TARGET_ESP32C3

#include "esp32c3pwm.hpp"
#include "driver/ledc.h"
#include "esp_err.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/timers.h"
#include "private/commons.hpp"

#include "os/os.hpp"

#define FOC_MCPWM_TIMER_RESOLUTION_HZ 40000000 // 40MHz, 1 tick = 0.025us

#ifndef INVERT_LOW_SIDE
#define INVERT_LOW_SIDE 0
#endif

const static char* TAG = "vfd";

namespace motorlib
{
	struct esp32c3pwmdriver_impl
	{
		/*
		 * Prepare and set configuration of timers
		 * that will be used by LED Controller
		 */
		ledc_timer_config_t timer_config = {
			.speed_mode		 = LEDC_LOW_SPEED_MODE, // timer mode
			.duty_resolution = LEDC_TIMER_13_BIT,	// resolution of PWM duty
			.timer_num		 = LEDC_TIMER_0,		// timer index
			.freq_hz		 = 4000,				// frequency of PWM signal
			.clk_cfg		 = LEDC_AUTO_CLK,		// Auto select the source clock
		};

		int gen_gpios[6]; // 3 GPIO pins for generator config

		// hardware variables
		int pwm_frequency;
		int pwm_period;

		esp32c3pwmdriver_impl(
			int pin_AH, int pin_AL, int pin_BH, int pin_BL, int pin_CH, int pin_CL, int PWM_freq)
			: pwm_frequency(PWM_freq)
		{
			gen_gpios[0] = pin_AH;
			gen_gpios[1] = pin_BH;
			gen_gpios[2] = pin_CH;
			gen_gpios[3] = pin_AL;
			gen_gpios[4] = pin_BL;
			gen_gpios[5] = pin_CL;

			// ledc_timer_config.duty_resolution = ledc_find_suitable_duty_resolution(LEDC_USE_XTAL_CLK, pwm_frequency);

			pwm_period = 1 << timer_config.duty_resolution;
			// pwm_frequency = timer_config.freq_hz;

			esp_err_t ret;
			ledc_timer_rst(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0);

			ret = ledc_timer_config(&timer_config);
			timer_config.timer_num = LEDC_TIMER_1;
			ret = ledc_timer_config(&timer_config);
			os::printf("ledc_channel_config return %d\n", ret);

			ledc_channel_config_t ledc_channel[] = {
				{
					.gpio_num	= pin_AH,
					.speed_mode = LEDC_LOW_SPEED_MODE,
					.channel	= LEDC_CHANNEL_0,
					.timer_sel	= LEDC_TIMER_0,
					.duty		= 1,
					.hpoint		= 0,
					.flags		= { .output_invert = 0 },
				},
				{
					.gpio_num	= pin_BH,
					.speed_mode = LEDC_LOW_SPEED_MODE,
					.channel	= LEDC_CHANNEL_1,
					.timer_sel	= LEDC_TIMER_0,
					.duty		= 1,
					.hpoint		= 0,
					.flags		= { .output_invert = 0 },
				},
				{
					.gpio_num	= pin_CH,
					.speed_mode = LEDC_LOW_SPEED_MODE,
					.channel	= LEDC_CHANNEL_2,
					.timer_sel	= LEDC_TIMER_0,
					.duty		= 1,
					.hpoint		= 0,
					.flags		= { .output_invert = 0 },
				},
				{ .gpio_num		= pin_AL,
					.speed_mode = LEDC_LOW_SPEED_MODE,
					.channel	= LEDC_CHANNEL_3,
					.timer_sel	= LEDC_TIMER_1,
					.duty		= 1,
					.hpoint		= 0,
					.flags		= { .output_invert = !INVERT_LOW_SIDE } },
				{ .gpio_num		= pin_BL,
					.speed_mode = LEDC_LOW_SPEED_MODE,
					.channel	= LEDC_CHANNEL_4,
					.timer_sel	= LEDC_TIMER_1,
					.duty		= 1,
					.hpoint		= 0,
					.flags		= { .output_invert = !INVERT_LOW_SIDE } },
				{ .gpio_num		= pin_CL,
					.speed_mode = LEDC_LOW_SPEED_MODE,
					.channel	= LEDC_CHANNEL_5,
					.timer_sel	= LEDC_TIMER_1,
					.duty		= 1,
					.hpoint		= 0,
					.flags		= { .output_invert = !INVERT_LOW_SIDE } },
			};

			for (int ch = 0; ch < 6; ch++)
			{
				ret = ledc_channel_config(&ledc_channel[ch]);
				os::printf("ledc_channel_config return %d\n", ret);
			}

			stop();
		}

		void set_duty(float_number U_a, float_number U_b, float_number U_c)
		{
			auto u_lpoint = clamp<int>(U_a * pwm_period, 0, pwm_period-1);
			auto v_lpoint = clamp<int>(U_b * pwm_period, 0, pwm_period-1);
			auto w_lpoint = clamp<int>(U_c * pwm_period, 0, pwm_period-1);

			ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, u_duty);
			ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, v_duty);
			ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2, w_duty);
			ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_3, u_duty);
			ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_4, v_duty);
			ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_5, w_duty);

			ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
			ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1);
			ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2);
			ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_3);
			ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_4);
			ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_5);
		}

		void set_frequency(int freq)
		{
			if (freq <= 6000 && freq >= 3000)
			{
				ledc_set_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0, freq);
				ledc_set_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_1, freq);
				pwm_frequency = freq;
                esp_timer_restart(hr_timer, 1000000/freq);
			}
		}

		void stop()
		{
			ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
			ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, 0);
			ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2, 0);
			ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_3, 0);
			ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_4, 0);
			ledc_stop(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_5, 0);
		}

		void start() { }

		int get_frequency() { return pwm_frequency; }

		pwmdriver::timer_fn pwm_cb;

		static void timer_cb(void* user_data)
		{
			auto _this = reinterpret_cast<esp32c3pwmdriver_impl*>(user_data);_this->pwm_cb(_this->pwm_frequency);
		}

		esp_timer_handle_t hr_timer;

		void link_timer(pwmdriver::timer_fn fn)
		{
			pwm_cb = fn;

			esp_timer_create_args_t timer_arg = {
				.callback			   = timer_cb,
				.arg				   = this,
				.dispatch_method	   = ESP_TIMER_TASK,
				.name				   = "pwm_tmr",
				.skip_unhandled_events = true,
			};

			esp_timer_create(&timer_arg, &hr_timer);
			// 200us = 5khz pwm
			esp_timer_start_periodic(hr_timer, 200);
		}

        ~esp32c3pwmdriver_impl()
        {
            esp_timer_stop(hr_timer);
			esp_timer_delete(hr_timer);
        }
	};

	//////////////////////////////////////////////////////////////////////////////
	esp32c3pwmdriver::esp32c3pwmdriver(
		int pin_AH, int pin_AL, int pin_BH, int pin_BL, int pin_CH, int pin_CL)
	{
		impl = new esp32c3pwmdriver_impl(pin_AH, pin_AL, pin_BH, pin_BL, pin_CH, pin_CL, 4000);
	}

	esp32c3pwmdriver::~esp32c3pwmdriver()
	{
        delete impl;
    }

	// Function setting the duty cycle to the pwm pin (ex. analogWrite())
	// - BLDC driver - 6PWM setting
	// - hardware specific
	void esp32c3pwmdriver::set_duty(float_number U_a, float_number U_b, float_number U_c)
	{
		impl->set_duty(U_a, U_b, U_c);
	}

	void esp32c3pwmdriver::start() { impl->start(); }

	void esp32c3pwmdriver::stop() { impl->stop(); }

	int esp32c3pwmdriver::get_frequency() { return impl->get_frequency(); }

	void esp32c3pwmdriver::set_frequency(int f) { impl->set_frequency(f); }

	void esp32c3pwmdriver::link_timer(timer_fn fn) { impl->link_timer(fn); }

}

#endif // CONFIG_IDF_TARGET_ESP32C3
#endif // defined(ESP_PLATFORM)
```

不同于其他平台使用 PWM 自身的定时器中断，esp32c3 上，pwm 周期更新的回调是由一个高精度定时器回调提供的。之所以不用 pwm 的回调，是因为 ledc pwm 并不会产生这样的中断——除非使用了硬件fade功能。
但电机控制岂是fade能瞎fade的？

# 运行

实际上，由于实现的仓促。这个pwm输出总觉得不是很靠谱。不过当我怀着忐忑的心情，准备报废掉一个耗资300 大洋让JLC打样贴片的驱动版的时候。。。奇迹发生了。电机转起来了。

不过，因为支持的pwm频率很有限，导致无法用电机播放《世上只有妈妈好了》。

当然，之前的驱动板播放的音乐可以猛戳[这里](https://www.bilibili.com/video/BV1ce411C79z/)看。

