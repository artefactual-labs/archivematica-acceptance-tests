import unittest
from archivematicaselenium import ArchivematicaSelenium


class CloseAllIngestsTests(ArchivematicaSelenium):

    def test_remove_all_ingests(self):
        self.remove_all_ingests()

    def tearDown(self):
        self.driver.close()
        self.driver.quit()


if __name__ == "__main__":
    unittest.main()
