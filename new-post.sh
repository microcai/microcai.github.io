#!/bin/bash
# vim: sts=4 sw=4 et

EDITOR=${EDITOR:-vim}

title_orig="$@"
title_orig=${title_orig:-"new post"}
title=${title_orig// /-}

date=$(date "+%Y-%m-%d")

file="./_posts/${date}-${title}.md"
if [ -f $file ]; then
    echo -e "Warring! file exist"
    echo -e "overwrite? [y/n]"

    read -n 1 answer
    if [ "$answer" = y ]; then
        \rm -f $file
    else
        echo "exit"
        exit 1
    fi
fi

cat << EOF > $file
---
layout: post
title:  $title_orig
tags:   [ ]
---
EOF

echo -e "\ncreate $file"

echo -e "\nedit it now?[y/n]"
read -n 1 answer

if [ "$answer" = y ]; then
    $EDITOR $file
else
    exit 0
fi
