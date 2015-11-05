#!/usr/bin/env python
import argparse
import sys
import os
import requests
from lxml.html import soupparser
from lxml import etree

import re


def loadThing(path, root_dir):
    content = ''
    media_type = ''
    if path.startswith('http:') or path.startswith('https:'):
        r = requests.get(path)
        media_type = r.headers.get('Content-Type', '')
        content = r.content

    elif path:
        src_path = os.path.join(root_dir, path)
        content = open(src_path, 'rb').read()
    return {
        'content': content,
        'media_type': media_type
    }


def toDataURL(content, media_type=''):
    encoded = content.encode('base64').replace('\n','')
    return 'data:{media_type};base64,{encoded}'.format(**locals())     


def transformHTML(i, o, root_dir='.', prefix=None, exclude=None):
    """
    @param root_dir: Path to look for resources from.
    @param prefix: If provided, don't inline stuff.  Instead, prepend
        the prefix to relative paths.
    """
    exclude = exclude or []
    root = soupparser.parse(i)
    html = root.getroot()

    # links (css)
    if 'link' not in exclude:
        for link in html.xpath('//link'):
            href = link.attrib.get('href', '')
            if prefix:
                # prefix
                link.attrib['href'] = prefix + href
            else:
                # inline
                loaded = loadThing(href, root_dir)
                style_tag = etree.Element('style')
                style_tag.text = loaded['content']
                link.getparent().replace(link, style_tag)

    # css
    if 'css' not in exclude:
        r_import = re.compile(r'(@import\s+url\((.*?)\)\s*;)')
        r_url = re.compile(r'(url\((.*?)\))', re.S | re.M)
        for style in html.xpath('//style'):
            # imports
            while True:
                imports = r_import.findall(style.text)
                if not imports:
                    break
                for rule, url in imports:
                    # inline
                    loaded = loadThing(url, root_dir)
                    style.text = style.text.replace(rule, loaded['content'])

            # other urls
            urls = r_url.findall(style.text)
            for match, url in urls:
                if prefix:
                    # prefix
                    pass
                else:
                    # inline
                    loaded = loadThing(url, root_dir)
                    style.text = style.text.replace(match,
                        'url('+toDataURL(**loaded)+')')

    # images
    if 'img' not in exclude:
        for image in html.xpath('//img'):
            src = image.attrib.get('src', '')
            if src.startswith('data:'):
                # already a data url
                continue
            if prefix:
                # prefix
                if src.startswith('//') or src.startswith('http:') or src.startswith('https:'):
                    pass
                else:
                    image.attrib['src'] = prefix + src
            else:
                # inline
                loaded = loadThing(src, root_dir)
                image.attrib['src'] = toDataURL(**loaded)
    o.write(etree.tostring(html))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', '-p', default='.',
        help='Path from which relative files will be resolved.')
    ap.add_argument('--prefix', '-P', default=None,
        help='String to preppend to all relative paths.')
    ap.add_argument('--exclude', '-x',
        action='append',
        choices=['img', 'link', 'css'],
        help='Exclude certain things from being processed.')

    args = ap.parse_args()
    transformHTML(sys.stdin, sys.stdout,
        root_dir=args.path,
        prefix=args.prefix,
        exclude=args.exclude)

