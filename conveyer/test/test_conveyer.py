from twisted.trial.unittest import SynchronousTestCase

from conveyer.conveyer import Conveyer, CreateLogCmd, AppendLogCmd


class TestConveyer(SynchronousTestCase):
    def setUp(self):
        self.conveyer_config = {
            "log_file": "testfile.dat",
        }
        self.conveyer = Conveyer(config=self.conveyer_config)

    def test_first_log_post(self):
        """
        The first time we send a log message/event to the conveyer, it
        needs to create an empty log file, then append to it.
        """
        commands = self.conveyer.log("{message: \"test\"}")
        self.assertEquals(len(commands), 2)
        creator, appender = commands
        self.assertEquals(type(creator), CreateLogCmd)
        self.assertEquals(type(appender), AppendLogCmd)
        self.assertEquals(creator.filename, "testfile.dat")
        self.assertEquals(appender.event, "{message: \"test\"}")
