"""
Conveyer takes logging events from Logstash, and conveys them to a Rackspace-
compatible cloud monitoring agent.
"""

import attr

from klein import Klein


app = Klein()


@attr.s
class CreateLogCmd(object):
    """
    Create a new log file.

    The caller of this command is responsible for properly disposing of any
    previous log file, should one already exist.  This WILL overwrite the old
    log file contents.
    """

    filename = attr.ib(validator=attr.validators.instance_of(str))


class AppendLogCmd(object):
    """
    Append to the currently open log file.
    """


@attr.s
class Conveyer(object):
    """
    Save logging events into a file under normal conditions.  When
    circumstances requires, change out the file.
    """

    config = attr.ib(validator=attr.validators.instance_of(dict))

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
        return [
            CreateLogCmd(filename=self.config["log_file"]),
            AppendLogCmd()
        ]


# @app.route('/')
# def hello(request):
#     """dummy."""
#     request.response = 200
#     return "\n\nStill running!\n\n"
#
#
# @app.route('/log', methods=['POST'])
# def accept_log(request):
#     """dummy."""
#     request.response = 200
#     the_log = request.content.read()
#     return "I GOT THE FOLLOWING LOG:\n{}".format(the_log)
