import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from raw.util import FileKey, get_raw_file_path


class TestGetRawFilePath(unittest.TestCase):
    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_get_raw_file_path(self, mock_exists, mock_makedirs):
        mock_exists.return_value = False

        out_dir = Path("/path/to/raw/dir")
        key = FileKey("BINANCE", "BTC-USDT", date(2023, 10, 2))

        file_path = get_raw_file_path(out_dir, key)

        mock_makedirs.assert_called_once_with(Path("/path/to/raw/dir/BTC-USDT/BINANCE"))
        self.assertEqual(
            Path("/path/to/raw/dir/BTC-USDT/BINANCE/BINANCE_BTC-USDT_20231002_raw.csv"),
            file_path,
        )

    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_get_raw_file_path_folder_exists(self, mock_exists, mock_makedirs):
        mock_exists.return_value = True

        out_dir = Path("/path/to/raw/dir")
        key = FileKey("BINANCE", "BTC-USDT", date(2023, 10, 2))

        file_path = get_raw_file_path(out_dir, key)

        mock_makedirs.assert_not_called()
        self.assertEqual(
            Path("/path/to/raw/dir/BTC-USDT/BINANCE/BINANCE_BTC-USDT_20231002_raw.csv"),
            file_path,
        )
