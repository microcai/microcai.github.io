#!/usr/bin/env python3
"""抓取 DeepSeek 分享对话并导出为 Markdown。

用法:
    python3 fetch_deepseek_chat.py <分享链接或分享ID> [输出文件.md]

示例:
    python3 fetch_deepseek_chat.py https://chat.deepseek.com/share/2qjurwbufhichkrc7j
    python3 fetch_deepseek_chat.py 2qjurwbufhichkrc7j 我的对话.md

说明:
    - 仅用标准库, 无需安装依赖。
    - 思考过程输出为折叠块, 联网搜索的网页来源附在对应回答末尾。
    - WebFetch 会被截断, 但此 API 返回完整 JSON, 不受限制。
"""

import json
import re
import sys
import urllib.request
from datetime import date

API_URL = "https://chat.deepseek.com/api/v0/share/content?share_id={sid}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://chat.deepseek.com/share/{sid}",
}


def extract_share_id(arg: str) -> str:
    """从链接或裸 ID 中提取分享 ID。"""
    m = re.search(r"share/([A-Za-z0-9]+)", arg)
    if m:
        return m.group(1)
    arg = arg.strip()
    if re.fullmatch(r"[A-Za-z0-9]+", arg):
        return arg
    sys.exit(f"错误: 无法从 {arg!r} 解析分享 ID")


def fetch(share_id: str) -> dict:
    """调用分享内容 API, 返回 biz_data。"""
    req = urllib.request.Request(
        API_URL.format(sid=share_id),
        headers={k: v.format(sid=share_id) for k, v in HEADERS.items()},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("code") != 0:
        sys.exit(f"错误: API 返回 code={data.get('code')} msg={data.get('msg')}")
    biz = data.get("data", {}).get("biz_data")
    if not biz or not biz.get("messages"):
        sys.exit("错误: 响应中没有对话内容 (分享链接是否已失效?)")
    return biz


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:40].strip() or "deepseek_chat"


def default_filename(biz: dict, share_id: str) -> str:
    """优先用对话标题, 否则用首条提问截断, 最后退回分享 ID。"""
    title = (biz.get("title") or "").strip()
    if not title or title in ("Shared Conversation", "分享的对话", "来自分享的对话"):
        for msg in biz["messages"]:
            if msg.get("role") == "USER":
                for frag in msg.get("fragments", []):
                    if frag.get("type") == "REQUEST":
                        title = frag.get("content", "").strip()
                        break
            if title:
                break
    return sanitize_filename(title or share_id) + ".md"


def render(biz: dict, share_id: str) -> str:
    """把 biz_data 渲染成 Markdown 文本。"""
    messages = biz["messages"]
    lines = [f"# {biz.get('title') or 'DeepSeek 对话'}", ""]
    lines.append(f"> 来源: https://chat.deepseek.com/share/{share_id}  ")
    lines.append(f"> 共 {sum(1 for m in messages if m['role'] == 'USER')} 轮对话, "
                 f"导出时间: {date.today().isoformat()}")
    lines.append("")

    round_no = 0
    for msg in messages:
        role = msg.get("role")
        if role == "USER":
            round_no += 1
            lines += [f"## 第 {round_no} 轮", ""]

        label = "用户" if role == "USER" else "DeepSeek"
        lines += [f"**{label}:**", ""]

        sources = []
        for frag in msg.get("fragments", []):
            ftype = frag.get("type")
            if ftype in ("REQUEST", "RESPONSE"):
                lines += [frag.get("content", ""), ""]
            elif ftype == "THINK":
                think = (frag.get("content") or "").strip()
                if think:
                    lines += ["<details><summary>思考过程</summary>", "",
                              think, "", "</details>", ""]
            elif ftype == "TOOL_OPEN":
                result = frag.get("result") or {}
                if result.get("url"):
                    sources.append(result)

        if sources:
            lines += ["**参考来源:**", ""]
            seen = set()
            for s in sources:
                url = s["url"]
                if url in seen:
                    continue
                seen.add(url)
                title = (s.get("title") or url).strip()
                lines.append(f"- [{title}]({url})")
            lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    share_id = extract_share_id(sys.argv[1])
    outfile = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"正在抓取 {share_id} ...")
    biz = fetch(share_id)

    text = render(biz, share_id)
    path = outfile or default_filename(biz, share_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    rounds = sum(1 for m in biz["messages"] if m["role"] == "USER")
    print(f"完成: {rounds} 轮对话, {len(text)} 字符 -> {path}")


if __name__ == "__main__":
    main()
