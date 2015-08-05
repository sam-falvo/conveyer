import StringIO

from twisted.trial.unittest import SynchronousTestCase

from conveyer.conveyer import Conveyer, CreateLogCmd, AppendLogCmd


class TestConveyer(SynchronousTestCase):
    def setUp(self):
        def file_override(filename, *args, **kwargs):
            """
            Return something that is File-like so we don't hit the filesystem.
            """
            return self.new_file_override()

        self.conveyer_config = {
            "log_file": "testfile.dat",
        }
        self.conveyer = Conveyer(
            config=self.conveyer_config,
            file_override=file_override,
            renamer=self.my_rename,
        )
        self.renamerCalled = False

    def my_rename(self, src, dst):
        """
        Mimic Python's os.rename function, but we don't use anything in the
        real filesystem, so just eat the operation.  We will record that
        we were called though.
        """
        self.renamerCalled = True

    def new_file_override(self):
        """
        This helper is invoked by the tested class when it wants to create a
        new file.  Return a file-like object, so that we avoid hitting the
        filesystem.
        """
        self.events_out = StringIO.StringIO()
        return self.events_out

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
        self.assertEquals(self.events_out.getvalue(), "{message: \"first\"}")

    def test_log_rotation(self):
        """
        Log rotation can occur at any time whatsoever.
        """
        self.conveyer.execute(self.conveyer.log("{message: \"first\"}"))
        self.conveyer.execute(self.conveyer.log("{message: \"second\"}"))
        self.conveyer.execute(self.conveyer.log("{message: \"third\"}"))
        filename = self.conveyer.rotate_logs()
        self.assertEquals(self.conveyer.logfile, None)
        self.assertEquals(filename, "testfile.dat.rotated")

    def test_logfile_recreates_after_rotation(self):
        """
        Log rotation can occur at any time whatsoever.
        """
        self.conveyer.execute(self.conveyer.log("{message: \"first\"}"))
        self.conveyer.execute(self.conveyer.log("{message: \"second\"}"))
        self.conveyer.execute(self.conveyer.log("{message: \"third\"}"))
        self.conveyer.rotate_logs()
        self.conveyer.execute(self.conveyer.log("{message: \"fourth\"}"))
        self.assertEquals(self.events_out.getvalue(), "{message: \"fourth\"}")
        self.assertTrue(self.renamerCalled)
