import unittest
import os
import tempfile
import pandas as pd
from utils.data_loader import load_data

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.test_dir.name, 'test.csv')
        df = pd.DataFrame({'amount': [100, 200, 300]})
        df.to_csv(self.csv_path, index=False)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_csv(self):
        df = load_data(self.csv_path)
        self.assertEqual(len(df), 3)
        self.assertIn('amount', df.columns)

if __name__ == '__main__':
    unittest.main()
