# Content

[Intro](https://github.com/sam-falvo/conveyer#introduction)  
[Why](https://github.com/sam-falvo/conveyer#why)  
[How](https://github.com/sam-falvo/conveyer#how)  

[Install](https://github.com/sam-falvo/conveyer/#install)  
[Config agent](https://github.com/sam-falvo/conveyer/#configure-conveyor-plugin)  
[Config graphs](https://github.com/sam-falvo/conveyer/#/configure-ackspace-monitoring-graphs)  
[Config logstash](https://github.com/sam-falvo/conveyer#testing-with-logstash)  

# Introduction

At least as of this commit,
Logstash does not
seem to rotate (high-load) logs
written to a file on-demand.
This precludes using external tools,
like Rackspace Cloud Monitoring Agent plugins,
to monitor metrics emitted by Logstash
in a finite amount of disk space.
Using Conveyer,
we take Logstash-generated events
and write them to a file.
Unlike Logstash's file output configuration,
Conveyer provides the ability to rotate
the log file it writes to on-demand.
Through this guaranteed atomic mechanism,
logs may be consumed by tooling
while providing a fresh log file for Logstash's use.
Meanwhile,
Logstash is completely ignorant of what's happening.

# How it works

Conveyer basically consists of two parts.
The daemon is intended to sit on a Logstash instance,
which has an HTTP output
configured to POST
to the conveyer daemon's `/log` endpoint.
The conveyer writes any received data to a log file.
So far, this sounds just like what you'd expect from a file output configuration.

When an external tool wants access to the logs safely,
it executes a POST request against the conveyer daemon's `/rotate` endpoint.
Conveyer will then close the log file it's currently using,
*rename* it to a new temporary name,
(lazily) creates a new log file for subsequent Logstash requests,
then return the name of the old file to the client.

The log consumer
is responsible for deleting the log file it's given when it's done using it.

**NOTE:** Right now, Conveyer statically determines
the name of the renamed logfile.
This means that
rotation will overwrite
any previous rotation.
Please consider this an implementation detail,
and try not to depend on this behavior.
*Always* use the filename returned from Conveyer
to gain access to the rotated logs.

# Why?

We needed to monitor and alert on some aggregated metrics.
We configured Logstash to do this for us,
but we found that our monitoring agent could not work with this data directly.
We needed to write a custom plug-in to make everything work together.

I first thought of using a daemon to keep everything in memory;
however, I came to the realization that if the process died for any reason,
we'd lose more data than we were comfortable with.
Writing data to a file seemed a natural choice to minimize data loss.

At this point, I tried looking for solutions for log rotation.
I wasn't happy with anything that I saw with a day or two of research.
So, knowing I can write my own solution in at least as much time,
I decided to write my own solution to the problem.


# Install

Typically,
Conveyer would be installed
using an orchestration tool such as Chef.
But alternatively here's a couple other ways 
to get it set up,
with ubuntu or other apt enabled systems

## With make  

This will install, link and run this plugin

`make`

## Manually 

```
apt-get update
apt-get install pip
pip install --upgrade pip
apt-get uninstall pip
pip install --upgrade virtualenv
git clone git@github.com/sam-falvo/conveyer
cd conveyer
virtualenv .ve
. .ve/bin/activate
pip install -e .
```

The first `apt-get` invokation updates the package database, while the second installs Ubuntu's default `pip` version.

I then use `pip` to replace itself with the latest version,
and remove Ubuntu's copy, for it is now irrelevant.
I then install `virtualenv` if it's not already installed.

After cloning this repository,
I create a virtualenv for Conveyer,
and install Conveyer itself therein.

At this point,
Conveyer is now properly installed.
Understanding these steps should give you
the background you need
to properly configure the orchestration tool
of your choice.

## Agent-based install

If your host has the Rackspace Cloud Monitoring Agent installed,
you can install the Conveyer Plugin fairly trivially:

```
export RMA=/usr/lib/rackspace-monitoring-agent/plugins
cp plugins/conveyer-plugin.py $RMA
chown --reference=$RMA $RMA/conveyer-plugin.py
cp plugins/conveyer-plugin.json /etc
chown --reference=$RMA /etc/conveyer-plugin.json
```

# Running Conveyer

You can launch the Conveyer daemon
using the following command:

```
python conveyer/conveyer.py
```

# Configure conveyor

You may optionally configure
how it runs 
with a set of
three environment variables:

|Variable|Default|Purpose|
|:-------|:-----:|:------|
|CONVEYER_PORT|10100|This determines which TCP/IP port Conveyer will listen for POST requests on.|
|CONVEYER_HOST|localhost|This determines the interface(s) Conveyer will listen on.|
|CONVEYER_LOGS|/tmp/logs|This determines the temporary repository of logs that Conveyer will store events in.  This file is what's rotated upon receiving a `/rotate` request.|

For example,
a fully customized invokation of Conveyer
might look like this:

```
CONVEYER_PORT=8080 CONVEYER_HOST=::1 CONVEYER_LOGS=/home/myself/mylogs python conveyer/conveyer.py
```
Below reads a sample configuration,
which may be found by default in `/etc/conveyer-plugin.json`,
understood by the Conveyer Plugin:

```
{
    "state_file_name": "/tmp/plugin-state-file.json",
    "conveyer_url": "http://localhost:10100/rotate",
    "metrics": [
        "failure.server.launch.count",
        "failure.authentication.identity.count",
    ]
}
```


The settings have the following meaning:

|Setting|Meaning|
|:----|:----|
|`state_file_name`|When Conveyer runs, it must record running information in order to translate Logstash-provided counts into gauge measurements that Cloud Monitoring expects.  This running data must be persisted from run to run.  This setting establishes *where* those settings are stored.|
|`conveyer_url`|This URL will be POSTed to in order to ask Conveyer daemon to rotate the logs.|
|`metrics`|An array of metrics as gathered by Logstash.  You'll probably want to tailor these to your specific needs.|

If you wish to store the configuration elsewhere,
you may launch the plugin with the environment variable
`CONVEYER_CONVEYER_AGENT_PLUGIN_CONFIG`
set to a different location, like so:

```
CONVEYER_AGENT_PLUGIN_CONFIG=/var/conveyer/config.json python conveyer-plugin.py
```

# Configure Rackspace Monitoring graphs

Assuming you installed the plugin correctly,
it should run automatically whenever Rackspace Cloud Monitoring polls your server.
However,
you'll need to configure cloud monitoring itself
to poll the agent with a custom check.

1.  Log into your <https://mycloud.rackspace.com> control panel.
2.  Click on the server of your choice to bring up its attributes.
3.  Scroll all the way to the bottom, where you'll find the section **Monitoring Data**.
4.  Click on **View Server's Metrics in Rackspace Intelligence**.
5.  Click on **Monitor**, and then the link for your server.
6.  Click on **Create Check**, under *Monitoring Checks*.
7.  Under *Check Type*, select **Custom Plugin**.
8.  Choose a name for your check; for now, I'll assume `foo-check`.
9.  For *Command*, enter `python conveyer-plugin.py`.
10.  Click **Create Check**.

After a while,
you should start to see graphs appear under *Visualize* >> *Custom Graphs*.

1.  Click on **Visualize**.
2.  Click on **Explore an Entity**.
3.  Click on the name of your server under *Choose One Entity*.
4.  Click on **foo-check** (or whatever name you chose above) under *Choose One Check*.
5.  Click on **Select all** under *Choose Multiple Metrics*.
6.  Click on **Generate Graphs**.

# Testing with Logstash

You can test Conveyer with a local deployment of Logstash.
I use the following Logstash configuration for this purpose:

input {
	generator {
		message => "Launching server failed: UpstreamError('identity error: 401 - Unable to authenticate user with credentials provided.',)"
	}
}

filter {
	if [message] =~ /.*Launching server failed.*/ {
		metrics {
			meter => ["failure.server.launch"]
			add_tag => ["metric"]
			flush_interval => 1
		}
	}

	if [message] =~ /identity error: 401/ {
		metrics {
			meter => ["failure.authentication.identity"]
			add_tag => ["metric"]
			flush_interval => 1
		}
	}
}

output {
	if "metric" in [tags] {
		http {
			http_method => "post"
			url => "http://localhost:10100/log"
		}
	}

	file {
		path => "/tmp/ls.log"
	}
}

Save this configuration file inside Logstash's directory,
say, as `test.config`,
and invoke it as follows:

```
bin/logstash agent -f test.config
```

You should see Logstash
produce a ton of log entries
in `/tmp/ls.log`.
Periodically, though,
it should generate metrics
and forward them to Conveyer.
You should see Conveyer deposit events
in `/tmp/conveyer-logs` approximately once every second.
The flush rate is determined by the `flush_interval` setting
in `test.config`.
Finally, if you execute:

```
curl -X POST http://localhost:10100/rotate
```

You should see the name of the rotated logfile,
and `/tmp/conveyer-logs` should start to fill with all-new content.

