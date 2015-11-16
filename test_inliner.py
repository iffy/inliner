from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from StringIO import StringIO

import requests

from lxml.html import soupparser
from lxml import etree

from inliner import transformHTML


class EverythingTest(TestCase):

    def assertEquivalentHTML(self, a, b, *args, **kwargs):
        a = etree.tostring(soupparser.fromstring(a))
        b = etree.tostring(soupparser.fromstring(b))
        self.assertEqual(a, b, *args, **kwargs)

    def transform(self, text, root_dir='.', prefix=None):
        fh_o = StringIO()
        transformHTML(StringIO(text), fh_o, root_dir=root_dir, prefix=prefix)
        return fh_o.getvalue()

    def test_images(self):
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        tmp.child('foo.jpg').setContent('something')

        src = '<img src="foo.jpg">'
        self.assertEquivalentHTML(self.transform(src, tmp.path),
            '<img src="data:;base64,{0}">'.format('something'.encode('base64').strip()))

    def test_image_long(self):
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        image_data = 'a' * 1000
        tmp.child('foo.jpg').setContent(image_data)

        src = '<img src="foo.jpg">'
        out = self.transform(src, tmp.path)
        self.assertNotIn('\n', out,
            "Should not contain newlines")

    def test_image_alreadyData(self):
        src = '<img src="data:;base64,abcdef">'
        self.assertEquivalentHTML(self.transform(src),
            '<img src="data:;base64,abcdef">')

    def test_image_fetch_png(self):
        content = requests.get('https://httpbin.org/image/png').content
        expected = content.encode('base64').replace('\n', '')
        src = '<img src="https://httpbin.org/image/png">'
        self.assertEquivalentHTML(self.transform(src),
            '<img src="data:image/png;base64,{0}">'.format(expected))

    def test_image_fetch_jpeg(self):
        content = requests.get('https://httpbin.org/image/jpeg').content
        expected = content.encode('base64').replace('\n', '')
        src = '<img src="https://httpbin.org/image/jpeg">'
        self.assertEquivalentHTML(self.transform(src),
            '<img src="data:image/jpeg;base64,{0}">'.format(expected))

    def test_css(self):
        """
        """
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        tmp.child('foo.css').setContent('abcdef')

        src = '<link href="foo.css" rel="stylesheet" />'
        expected = '<style>abcdef</style>'
        self.assertEquivalentHTML(self.transform(src, tmp.path),
            expected)

    def test_css_import(self):
        """
        """
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        tmp.child('foo.css').setContent('@import url(bar.css); foo;')
        tmp.child('bar.css').setContent('bar;');
        
        src = '<link href="foo.css" rel="stylesheet" />'
        expected = '<style>bar; foo;</style>'
        self.assertEquivalentHTML(self.transform(src, tmp.path),
            expected)

    def test_css_import_font(self):
        """

        """
        tmp = FilePath(self.mktemp())
        tmp.makedirs()
        tmp.child('foo.css').setContent("@font-face { src: local('Foo'), url(goo.woff2) format('woff2'); }")
        tmp.child('goo.woff2').setContent('The contents')

        src = '<link href="foo.css" rel="stylesheet" />'
        expected = "<style>@font-face {{ src: local('Foo'), url(data:;base64,{0}) format('woff2'); }}</style>".format(
            'The contents'.encode('base64').replace('\n', ''))
        self.assertEquivalentHTML(self.transform(src, tmp.path),
            expected)

    def test_prefixOnly(self):
        """
        You can specify a prefix to all relative resources.
        """
        src = ('<link href="foo.css" rel="stylesheet" />'
               '<img src="../something.jpg">'
               '<img src="http://foo.com/image.jpg">')
        expected = ('<link href="root/foo.css" rel="stylesheet" />'
                    '<img src="root/../something.jpg">'
                    '<img src="http://foo.com/image.jpg">')
        self.assertEquivalentHTML(self.transform(src, prefix='root/'),
            expected)

    def test_prefixOnly_styleBlockEscaping(self):
        """
        When prefixing stuff, it shouldn't ruin encoded characters.
        """
        src = ('<style>foo > bar { color: #fff; }</style>')
        transformed = self.transform(src, prefix='foo/')
        self.assertIn('foo > bar', transformed)

