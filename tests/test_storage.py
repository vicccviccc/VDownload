import json
import tempfile
import unittest
from pathlib import Path
from storage import LocalStore, MAX_HISTORY
from clipboard_watch import ClipboardWatcher

URL = 'https://www.youtube.com/watch?v=abcdefghijk'


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = LocalStore(self.root)

    def test_defaults_and_corrupt_json(self):
        self.assertEqual(self.store.preferences()['mode'], 'MP4')
        (self.root / 'preferences.json').write_text('{', encoding='utf-8')
        self.assertEqual(self.store.preferences()['quality'], '1080p')

    def test_preferences_roundtrip(self):
        options = {'mode': 'MP3', 'quality': '320 kbps', 'fps': '60 FPS',
                   'folder': str(self.root)}
        self.assertTrue(self.store.save_preferences(options))
        self.assertEqual(self.store.preferences(), options)

    def test_invalid_preferences(self):
        self.store.save_preferences({'mode': 'MP3', 'quality': '1080p',
                                     'fps': 'bad', 'folder': 'missing-folder'})
        options = self.store.preferences()
        self.assertEqual(options['quality'], '192 kbps')
        self.assertEqual(options['fps'], 'Automático')
        self.assertTrue(Path(options['folder']).is_dir())

    def test_history_roundtrip_and_clear(self):
        self.assertTrue(self.store.record('Vídeo teste', 'youtu.be/abcdefghijk',
                                          'MP4', '1080p', self.root))
        item = self.store.history()[0]
        self.assertEqual(item['title'], 'Vídeo teste')
        self.assertEqual(item['url'], URL)
        self.assertTrue(self.store.clear_history())
        self.assertEqual(self.store.history(), [])

    def test_history_invalid_entries_and_limit(self):
        self.store.record('Teste', URL, 'MP4', '1080p', self.root)
        valid = self.store.history()[0]
        raw = [None, {}, {**valid, 'url': 'https://example.org'}, *([valid] * 120)]
        (self.root / 'history.json').write_text(json.dumps(raw), encoding='utf-8')
        self.assertEqual(len(self.store.history()), MAX_HISTORY)

    def test_storage_unavailable(self):
        invalid = self.root / 'file'
        invalid.write_text('not a directory', encoding='utf-8')
        store = LocalStore(invalid)
        self.assertFalse(store.save_preferences({}))
        self.assertEqual(store.history(), [])


class ClipboardTests(unittest.TestCase):
    def test_ignores_existing_and_duplicate_links(self):
        watch = ClipboardWatcher()
        watch.reset(URL)
        self.assertIsNone(watch.observe('youtu.be/abcdefghijk?si=abc'))
        self.assertEqual(watch.observe('youtu.be/12345678901'),
                         'https://www.youtube.com/watch?v=12345678901')

    def test_ignores_invalid_and_busy(self):
        watch = ClipboardWatcher()
        self.assertIsNone(watch.observe('texto privado'))
        self.assertIsNone(watch.observe(URL, busy=True))
        self.assertIsNone(watch.observe(URL))
        self.assertIsNone(watch.observe(None))
        self.assertEqual(watch.observe(URL), URL)
