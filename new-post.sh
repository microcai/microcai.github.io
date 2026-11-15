#!/bin/bash
# vim: sts=4 sw=4 et
# 新建文章：./new-post.sh "标题" [英文slug]
# slug 决定 URL，不传则用标题（中文标题会产生中文 URL，建议显式传英文 slug）

EDITOR=${EDITOR:-vim}

title_orig=${1:-"new post"}
slug=${2:-$(echo "$title_orig" | tr ' ' '-')}
date=$(date "+%Y-%m-%d")

file="./content/posts/${date}-${slug}.md"
if [ -f "$file" ]; then
    echo -e "Warring! file exist"
    echo -e "overwrite? [y/n]"

    read -n 1 answer
    if [ "$answer" = y ]; then
        rm -f "$file"
    else
        echo "exit"
        exit 1
    fi
fi

cat << EOF > "$file"
---
title: $title_orig
tags: []
date: $date
slug: $slug
---
EOF

echo -e "\ncreate $file"

echo -e "\nedit it now?[y/n]"
read -n 1 answer

if [ "$answer" = y ]; then
    $EDITOR "$file"
else
    exit 0
fi
