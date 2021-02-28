#!/usr/bin/env python3

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

CACHEDIR=f'{tempfile.gettempdir()}/.pypiutil_cache'
TTL=3600
MAX_SUMMARY=10

def err(msg):
    print("\x1b[31;1mError:\x1b[0m " + msg)

def fetch(url):
    cache = get_cache(url)
    os.makedirs(CACHEDIR, exist_ok=True)
    if not os.path.exists(cache) or TTL < time.time() - os.stat(cache).st_mtime:
        with urllib.request.urlopen(url) as u:
            with open(cache, "wb") as f:
                data = u.read()
                f.write(data)
                with open(f'{CACHEDIR}/list','a') as f:
                    f.write('{0}\t{1}\n'.format(re.sub(r'.*/','',cache), url))
    else:
        with open(cache, "rb") as f:
            data = f.read()
    return data

def get_body(html):
    if m := re.search(r'(?s)<body>(.*)<\/body>', html):
        return m.group(1)
    else:
        return ""

def get_cache(id):
    return f'{CACHEDIR}/{get_hash(id)}'

def get_hash(id):
    return hashlib.sha512(id.encode()).hexdigest()

def get_package_description_summary(html):
    if m := re.search(r'.*package-description__summary.*', html):
        return strip_tags(m[0])
    return None

def strip_tags(s):
    return re.sub(r'<[^>]*>', '', s).strip()



def pypiutil_search(args):
    pattern = args.pattern
    html = fetch('https://pypi.org/simple/').decode('utf-8')
    body = get_body(html)
    lines = (strip_tags(s) for s in body.split("\n"))
    lines = (s for s in lines if re.search(pattern, s))
    print("\n".join(lines))

def pypiutil_show(args):
    pypiutil_web(args)

def pypiutil_summary(args):
    pkg = args.pkg
    html = fetch(f'https://pypi.org/project/{pkg}/').decode('utf-8')
    if summary := get_package_description_summary(html):
        print(summary)
    else:
        err("No summary found.")

def pypiutil_web(args):
    pkg = args.pkg
    cmds = ['cygstart', 'explorer.exe', 'xdg-open']
    open = list(cmd for cmd in cmds if shutil.which(cmd))
    if len(open) <= 0:
        err(f'{cmds} not found.')
        exit(1)
    subprocess.call([open[0], f'https://pypi.org/project/{pkg}/'])



parser = argparse.ArgumentParser(description='pypi utility')
parser.set_defaults(func=lambda args : parser.print_help())

subparsers = parser.add_subparsers()

parser_search = subparsers.add_parser('search', help='Search packages.')
parser_search.add_argument('pattern', nargs='?', default=r'.+')
parser_search.set_defaults(func=pypiutil_search)

parser_show = subparsers.add_parser('show', help='Show package details.')
parser_show.add_argument('pkg')
parser_show.set_defaults(func=pypiutil_show)

parser_summary = subparsers.add_parser('summary', help='Show package summary.')
parser_summary.add_argument('pkg')
parser_summary.set_defaults(func=pypiutil_summary)

parser_web = subparsers.add_parser('web', help='Show package details with web.')
parser_web.add_argument('pkg')
parser_web.set_defaults(func=pypiutil_web)

args = parser.parse_args()

args.func(args)
