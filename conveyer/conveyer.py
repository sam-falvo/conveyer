"""
Conveyer takes logging events from Logstash, and conveys them to a Rackspace-
compatible cloud monitoring agent.
"""

import attr
import os

from attr.validators import instance_of

from klein import Klein


@attr.s
class CreateLogCmd(object):
    """
    Create a new log file.

    The caller of this command is responsible for properly disposing of any
    previous log file, should one already exist.  This WILL overwrite the old
    log file contents.
    """

    filename = attr.ib(validator=instance_of(str))

    def execute(self, conveyer):
        """Opens a new log file."""
        _file = conveyer.file_override or file
        conveyer.logfile = _file(self.filename, "wa")


@attr.s
class AppendLogCmd(object):
    """
    Append to the currently open log file.
    """

    event = attr.ib(validator=instance_of(str))

    def execute(self, conveyer):
        """Appends an event to a log file."""
        conveyer.logfile.write(self.event)
        conveyer.logfile.flush()


@attr.s
class _Conveyer(object):
    """
    Save logging events into a file under normal conditions.  When
    circumstances requires, change out the file.
    """

    config = attr.ib(validator=instance_of(dict))
    file_override = attr.ib(validator=lambda _1, _2, v: callable(v))
    renamer = attr.ib(validator=lambda _1, _2, v: callable(v))

    def reset(self):
        """
        Reset the conveyer instance to a fresh state.  Preserve filesystem
        abstractions though.
        """
        self.logfile = None

    def execute(self, commands):
        """
        Executes on a plan returned by the log method.  This separation is
        intended to facilitate easier unit testing in the presence of side-
        effecting code.
        """
        for command in commands:
            command.execute(self)

    def log(self, event):
        """
        Log an event.  If the logfile doesn't yet exist, create one.

        :param str event: The event to log.  This should be Logstash's JSON
            format.  Note that Conveyer does nothing to validate this, however.

        :return: A list of commands to execute.  To accomplish the goal of this
            method, they must be executed in the order they appear in the
            list.  This should be sufficient:

                cmds = conveyer.log(an_event)
                conveyer.execute(cmds)

            We return a list of commands to execute instead of just doing them
            to better facilitate unit testing.
        """
        plan = [AppendLogCmd(event=event)]
        if not self.logfile:
            plan.insert(0, CreateLogCmd(filename=self.config["log_file"]))
        return plan

    def rotate_logs(self):
        """
        Rotate the logs.

        :return: The name of the freshly rotated log file.  You're free to do
           what you with with it.  Delete it if you wish to avoid leaking disk
           space.
        """
        self.logfile.close()
        self.logfile = None
        fn = self.config["log_file"]
        renamed_fn = "{0}.rotated".format(fn)
        self.renamer(fn, renamed_fn)
        return renamed_fn


def Conveyer(config, file_override=None, renamer=None):
    """
    Create and initialize a conveyer instance.
    """
    c = _Conveyer(config=config, file_override=file_override, renamer=renamer)
    c.reset()
    return c


conveyer = Conveyer(
    config={"log_file": "/tmp/logs"},
    file_override=file,
    renamer=os.rename,
)

app = Klein()


@app.route('/')
def hello(request):
    """Report if we're still alive and functioning."""
    request.response = 200
    return "Still running!\n"


@app.route('/log', methods=['POST'])
def accept_log(request):
    """Accept a log message for logging."""
    the_log = request.content.read()
    conveyer.execute(conveyer.log(the_log))
    request.response = 200
    return "ok"


@app.route('/rotate', methods=['POST'])
def rotate_log(request):
    """Rotate the log, and report the filename back to the client."""
    fn = conveyer.rotate_logs()
    request.response = 200
    return fn


if __name__ == '__main__':
    app.run("localhost", 10100)
