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

    def test_nth_log_post(self):
        """
        The second, and subsequent, time we send a log event, it must not
        recreate the log file, but it does need to append the event to the one
        we already have.
        """
        self.conveyer.execute(self.conveyer.log("{message: \"first\"}"))
        commands = self.conveyer.log("{message: \"second\"}")
        self.assertEquals(len(commands), 1)
        self.assertEquals(type(commands[0]), AppendLogCmd)
        self.assertEquals(commands[0].event, "{message: \"second\"}")
