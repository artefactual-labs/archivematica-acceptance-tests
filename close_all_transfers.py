import unittest
from archivematicaselenium import ArchivematicaSelenium


class CloseAllTransfersTests(ArchivematicaSelenium):

    def test_remove_all_transfers(self):
        self.remove_all_transfers()

    def tearDown(self):
        self.driver.close()
        self.driver.quit()


if __name__ == "__main__":
    unittest.main()
