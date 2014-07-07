from helper import unittest, PillowTestCase, tearDownModule, lena, netpbm_available

from PIL import Image
from PIL import GifImagePlugin

codecs = dir(Image.core)

# sample gif stream
file = "Tests/images/lena.gif"
with open(file, "rb") as f:
    data = f.read()


class TestFileGif(PillowTestCase):

    def setUp(self):
        if "gif_encoder" not in codecs or "gif_decoder" not in codecs:
            self.skipTest("gif support not available")  # can this happen?

    def test_sanity(self):
        im = Image.open(file)
        im.load()
        self.assertEqual(im.mode, "P")
        self.assertEqual(im.size, (128, 128))
        self.assertEqual(im.format, "GIF")

    def test_optimize(self):
        from io import BytesIO

        def test(optimize):
            im = Image.new("L", (1, 1), 0)
            file = BytesIO()
            im.save(file, "GIF", optimize=optimize)
            return len(file.getvalue())
        self.assertEqual(test(0), 800)
        self.assertEqual(test(1), 38)

    def test_roundtrip(self):
        out = self.tempfile('temp.gif')
        im = lena()
        im.save(out)
        reread = Image.open(out)

        self.assert_image_similar(reread.convert('RGB'), im, 50)

    def test_roundtrip2(self):
        # see https://github.com/python-pillow/Pillow/issues/403
        out = self.tempfile('temp.gif')
        im = Image.open('Tests/images/lena.gif')
        im2 = im.copy()
        im2.save(out)
        reread = Image.open(out)

        self.assert_image_similar(reread.convert('RGB'), lena(), 50)

    def test_palette_handling(self):
        # see https://github.com/python-pillow/Pillow/issues/513

        im = Image.open('Tests/images/lena.gif')
        im = im.convert('RGB')

        im = im.resize((100, 100), Image.ANTIALIAS)
        im2 = im.convert('P', palette=Image.ADAPTIVE, colors=256)

        f = self.tempfile('temp.gif')
        im2.save(f, optimize=True)

        reloaded = Image.open(f)

        self.assert_image_similar(im, reloaded.convert('RGB'), 10)

    def test_palette_434(self):
        # see https://github.com/python-pillow/Pillow/issues/434

        def roundtrip(im, *args, **kwargs):
            out = self.tempfile('temp.gif')
            im.save(out, *args, **kwargs)
            reloaded = Image.open(out)

            return [im, reloaded]

        orig = "Tests/images/test.colors.gif"
        im = Image.open(orig)

        self.assert_image_equal(*roundtrip(im))
        self.assert_image_equal(*roundtrip(im, optimize=True))

        im = im.convert("RGB")
        # check automatic P conversion
        reloaded = roundtrip(im)[1].convert('RGB')
        self.assert_image_equal(im, reloaded)

    @unittest.skipUnless(netpbm_available(), "netpbm not available")
    def test_save_netpbm_bmp_mode(self):
        img = Image.open(file).convert("RGB")

        tempfile = self.tempfile("temp.gif")
        GifImagePlugin._save_netpbm(img, 0, tempfile)
        self.assert_image_similar(img, Image.open(tempfile).convert("RGB"), 0)

    @unittest.skipUnless(netpbm_available(), "netpbm not available")
    def test_save_netpbm_l_mode(self):
        img = Image.open(file).convert("L")

        tempfile = self.tempfile("temp.gif")
        GifImagePlugin._save_netpbm(img, 0, tempfile)
        self.assert_image_similar(img, Image.open(tempfile).convert("L"), 0)

    def test_seek(self):
        img = Image.open("Tests/images/dispose_none.gif")
        framecount = 0
        try:
            while True:
                framecount += 1
                img.seek(img.tell() +1)
        except EOFError:
            self.assertEqual(framecount, 5)

    def test_dispose_none(self):
        img = Image.open("Tests/images/dispose_none.gif")
        try:
            while True:
                img.seek(img.tell() +1)
                self.assertEqual(img.disposal_method, 1)
        except EOFError:
            pass

    def test_dispose_background(self):
        img = Image.open("Tests/images/dispose_bgnd.gif")
        try:
            while True:
                img.seek(img.tell() +1)
                self.assertEqual(img.disposal_method, 2)
        except EOFError:
            pass

    def test_dispose_previous(self):
        img = Image.open("Tests/images/dispose_prev.gif")
        try:
            while True:
                img.seek(img.tell() +1)
                self.assertEqual(img.disposal_method, 3)
        except EOFError:
            pass

    def test_iss634(self):
        img = Image.open("Tests/images/iss634.gif")
        # seek to the second frame
        img.seek(img.tell() +1)
        # all transparent pixels should be replaced with the color from the first frame
        self.assertEqual(img.histogram()[img.info['transparency']], 0)


if __name__ == '__main__':
    unittest.main()

# End of file
