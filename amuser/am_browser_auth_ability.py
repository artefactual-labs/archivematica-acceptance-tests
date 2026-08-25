"""Archivematica Authentication Ability"""

from . import playwright_ability


class ArchivematicaBrowserAuthenticationAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Archivematica Authentication Ability: the ability of an Archivematica user to
    use a browser to login/out to/from Archivematica and/or the Storage Service.
    """

    def login(self):
        """Login to Archivematica."""
        self.page.goto(self.get_login_url())
        self.page.locator("#id_username").fill(self.am_username)
        self.page.locator("#id_password").fill(self.am_password)
        self.page.locator("button").first.click()

    def login_ss(self):
        """Login to Archivematica Storage Service."""
        self.page.goto(self.get_ss_login_url())
        self.page.locator("#id_username").fill(self.ss_username)
        self.page.locator("#id_password").fill(self.ss_password)
        self.page.locator("input[type=submit]").click()
