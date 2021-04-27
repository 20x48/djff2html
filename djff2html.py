#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
from random import randint
from typing import Tuple, Union, Optional
from functools import lru_cache

def generate(git_dir: str, file: str, debug: bool=False, **options) -> (Union[str, None], Union[None, Tuple[str]], Optional[Tuple[str]]):
    stdout, stderr = subprocess.Popen(
        ('git', '--git-dir', git_dir, 'log', '-p', '--no-color', '--decorate=short', '--', file),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate()

    out: Tuple[str] = stdout.decode('utf-8').splitlines()  # 卧槽？？才知道这里居然也可以写类型标注……
    err: Tuple[str] = stderr.decode('utf-8').splitlines() or None

    @lru_cache
    def opt(k: str) -> bool:
        return options.get(k, True)

    html = []
    merr = []
    opti = False

    for i, line in enumerate(out, 1):
        # empty lines
        if not line or line.isspace():
            continue

        # commit
        if line.startswith('commit'):
            opti = False
            if opt('show_commit'):
                html.append(f'<p class="com">{escape(line[7:].strip())}</p>')
            continue

        # simple optimization
        if not opti:
            if line.startswith('Author'): # author
                if opt('show_author'):    # 也许他们会检查邮箱域名；通过这种方式误导他们。
                    html.append(f'<p class="aut">{escape(line[7:].strip()).replace("@", f"<i>{randint(0, 0xFFFFF):05X}</i>")}</p>')
                continue
            elif line.startswith('Date'): # date
                if opt('show_date'):
                    html.append(f'<p class="dat">{escape(line[5:].strip())}</p>')
                continue
            elif line.startswith('    '): # commit message
                if opt('show_message'):
                    html.append(f'<p class="msg">{escape(line[4:].rstrip())}</p>')
                continue
            # diff  `diff --git a/README.md b/README.md`
            # new   `new file mode 100644`
            # ---   `--- a/README.md`
            # +++   `+++ b/README.md`
            # index `index 0000000..ec2bc6a`
            elif (line.startswith('diff')
              or  line.startswith('new')
              or  line.startswith('---')
              or  line.startswith('+++')
              or  line.startswith('index')): continue
            elif line[0] == '@': opti = True
            elif debug: # Mismatched
                merr.append((0, i, line))
                continue

        if   line[0] == '@':  html.append(f'<p class="chp">{escape(line[3:-3].strip())}</p>') # changed position 可能会多次出现
        elif line[0] == ' ':  html.append(f'<p class="nch">{escape(line[1:].rstrip())}</p>')  # no any change
        elif line[0] == '+':  html.append(f'<p class="add">{escape(line[1:].rstrip())}</p>')  # add
        elif line[0] == '-':  html.append(f'<p class="rmv">{escape(line[1:].rstrip())}</p>')  # remove
        elif line[0] == '\\': html.append('<p class="non"></p>') # "No newline at end of file"
        elif debug: merr.append((1, i, line)) # Mismatched

    if err:
        out = None
    else:
        out = (
            '<!DOCTYPE html>'
            '<html>'
                '<head>'
                    '<meta charset="utf-8" />'
                    '<meta name="generator" content="djff2html" />'
                    f'<title>Changes of {escape(file)}</title>'
                    '<style>'
                        'body{margin:20px;font-size:15px;white-space:pre;font-family:monospace}'
                        'p{margin:0;height:1.65em}'
                        'p::before{text-shadow:2px 2px 2px #BDBDBD}'
                        '.com,.aut,.dat,.msg{color:#263238;padding:0 .35em 0 5em;position:relative;background-color:#FFF8E1}'
                        '.com::before,.aut::before,.dat::before{position:absolute;left:.35em;font-weight:bolder}'
                        '.com::before{content:"COMMIT:"}'
                        '.aut::before{content:"AUTHOR:"}' '.aut>i{font-size:0}' '.aut>i::before{font-size:15px;content:"@";font-style:normal}'
                        '.dat::before{content:"DATE:"}'
                        '.msg{font-weight:350;background-color:#FFF3E0}'
                        '.chp,.nch,.add,.rmv,.non{position:relative}'
                        '.chp{color:#4A148C;background-color:#F3E5F5;padding:0 .35em}'
                        '.chp::before{content:"@@ "}'
                        '.chp::after{content:" @@"}'
                        '.nch,.add,.rmv,.non{position:relative;padding-left:1.35em}'
                        '.nch::before,.add::before,.rmv::before,.non::before{position:absolute;left:.35em}'
                        '.nch{color:#9E9E9E;background-color:#F5F5F5}'
                        '.add{color:#2E7D32;text-decoration:underline #A5D6A7;background-color:#E8F5E9}'    '.add::before{content:"+"}'
                        '.rmv{color:#c62828;text-decoration:line-through;background-color:#FFEBEE}'         '.rmv::before{content:"-"}'
                        '.non{color:#78909C;background-color:#ECEFF1}'  r'.non::before{content:"\\"}'       '.non::after{content:"No newline at end of file.";font-style:italic}'
                    '</style>'
                '</head>'
                '<body>'
                    f'{"".join(html)}'
                '</body>'
            '</html>'
        )

    if debug:
        return out, err, merr
    else:
        return out, err

def escape(text: str) -> str:
    return ''.join({'"':'&#34;',
                    '&':'&amp;',
                    '<':'&lt;'}.get(c, c) for c in text)