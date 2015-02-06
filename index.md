---
layout: default
description: A description about my blog homepage
---

<div id="About">

Hello, I am 菜菜博士. I am co-founder of avplayer.org. This blog is mostly about technology, though you will find some random musings about pop, politics and culture. <a href="/about.html">More...</a>

</div>

<div id="posts">
  <h3><a href="/feed">RSS feed</a></h3>
  <h2>日志</h2>
  <ul>
    {% for post in site.posts %}
      <li><span class="date">{{ post.date | date_to_string }}</span> - <a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endfor %}
  </ul>
</div>
<div id="pages">
  <h2>Pages</h2>
  <ul>
    {% for page in site.html_pages %}
      {% if page.title %}
        <li><a href="{{ page.url }}">{{ page.title }}</a></li>
      {% endif %}
    {% endfor %}
  </ul>
</div>
<aside id="exchangelink">
 <div>
 <h2> 其他博客链接 </h2>
 <h4><a href="http://kiki.microcai.org/"> 老婆的博客 </a></h4>
 <h4><a href="http://xrain.simcu.com/"> 静默 – 华丽之作,一切从简 </a></h4>
 </div>
</aside>
<div>
  <iframe width="100%" height="400" class="share_self"  frameborder="0" scrolling="no" src="http://widget.weibo.com/weiboshow/index.php?language=&width=0&height=400&fansRow=2&ptype=1&speed=100&skin=5&isTitle=0&noborder=0&isWeibo=1&isFans=0&uid=1292997095&verifier=b5a9690c&dpc=1"></iframe>
</div>
