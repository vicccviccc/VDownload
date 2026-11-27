import unittest
import tempfile
from downloader import youtube_url, make_options, progress_data, friendly_error

ID = 'abcdefghijk'
CANONICAL = 'https://www.youtube.com/watch?v=' + ID


class DownloadTests(unittest.TestCase):
    def test_links(self):
        for link in (CANONICAL, 'youtu.be/' + ID + '?si=123',
                     'https://www.youtube.com/shorts/' + ID,
                     CANONICAL + '&list=abc', 'https://m.youtube.com/live/' + ID):
            with self.subTest(link=link):
                self.assertEqual(youtube_url(link), CANONICAL)

    def test_reject_invalid_links(self):
        for link in ('', 'https://example.com/watch?v=' + ID,
                     'https://youtube.com.evil.com/watch?v=' + ID,
                     'https://youtube.com/playlist?list=abc',
                     'https://x@youtube.com/watch?v=' + ID,
                     'https://youtu.be/abc', 'ftp://youtube.com/watch?v=' + ID):
            with self.subTest(link=link):
                with self.assertRaises(ValueError):
                    youtube_url(link)
