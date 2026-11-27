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

    def test_invalid_ports_and_controls(self):
        for link in ('https://youtube.com:invalid/watch?v=' + ID,
                     'https://youtube.com:8080/watch?v=' + ID,
                     'https://you\ntube.com/watch?v=' + ID,
                     'https://@youtube.com/watch?v=' + ID):
            with self.subTest(link=link):
                with self.assertRaises(ValueError):
                    youtube_url(link)

    def test_mp4_options(self):
        with tempfile.TemporaryDirectory() as folder:
            opts = make_options(folder, 'MP4', '2160p (4K)', None, None)
            self.assertIn('[height<=2160]', opts['format'])
            self.assertTrue(opts['noplaylist'])
            self.assertFalse(opts['overwrites'])
            self.assertEqual(opts['merge_output_format'], 'mp4')
            self.assertNotIn('height', make_options(folder, 'MP4', 'Melhor disponível', None, None)['format'])

    def test_mp3_options(self):
        with tempfile.TemporaryDirectory() as folder:
            opts = make_options(folder, 'MP3', '192 kbps', None, None)
            self.assertEqual(opts['postprocessors'][0]['preferredcodec'], 'mp3')
            self.assertEqual(opts['postprocessors'][0]['preferredquality'], '192')
            with self.assertRaises(ValueError):
                make_options(folder, 'MP3', '1080p', None, None)

    def test_fps(self):
        with tempfile.TemporaryDirectory() as folder:
            for fps, expected in [('30 FPS', '[fps>=29][fps<=30.5]'), ('60 FPS', '[fps>=59][fps<=60.5]')]:
                opts = make_options(folder, 'MP4', '1080p', None, None, fps=fps)
                self.assertEqual(opts['format'].count(expected), 2)
                self.assertEqual(opts['format'].count('[height<=1080]'), 2)
            self.assertNotIn('[fps', make_options(folder, 'MP4', '1080p', None, None)['format'])
            self.assertNotIn('[fps', make_options(folder, 'MP3', '192 kbps', None, None, fps='60 FPS')['format'])
            with self.assertRaises(ValueError):
                make_options(folder, 'MP4', '1080p', None, None, fps='90 FPS')

    def test_friendly_error(self):
        self.assertEqual(friendly_error('\x1b[31mErro\x1b[0m'), 'Erro')
        self.assertIn('HTTP 403', friendly_error('HTTP Error 403: Forbidden'))
        self.assertIn('FPS', friendly_error('Requested format is not available'))

    def test_embed_and_music_links(self):
        for link in ('https://www.youtube.com/embed/' + ID,
                     'https://music.youtube.com/watch?v=' + ID):
            self.assertEqual(youtube_url(link), CANONICAL)

    def test_invalid_destination(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                make_options(Path(folder) / 'inexistente', 'MP4', '1080p', None, None)

    def test_invalid_format_and_quality(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                make_options(folder, 'AVI', '1080p', None, None)
            with self.assertRaises(ValueError):
                make_options(folder, 'MP4', '9999p', None, None)

    def test_progress_limits(self):
        self.assertEqual(progress_data({'downloaded_bytes': 250, 'total_bytes': 200})[0], 1.0)
        self.assertEqual(progress_data({'downloaded_bytes': -1, 'total_bytes': 200})[0], 0.0)
        self.assertEqual(progress_data({'downloaded_bytes': 50, 'total_bytes_estimate': 100})[0], 0.5)

    def test_invalid_progress_data(self):
        result = progress_data({'downloaded_bytes': 'oops', 'total_bytes': -10,
                                'speed': float('inf'), 'eta': float('nan')})
        self.assertIsNone(result[0])
        self.assertEqual(result[1], '0.0 B / —')
        self.assertEqual(result[2:], ('—', '—'))

    def test_progress(self):
        self.assertEqual(progress_data({'downloaded_bytes': 100, 'total_bytes': 200, 'eta': 65})[0], 0.5)
        self.assertEqual(progress_data({'eta': 65})[-1], '01:05')
        self.assertIsNone(progress_data({})[0])


if __name__ == '__main__':
    unittest.main()
