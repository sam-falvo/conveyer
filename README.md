# Introduction

At least as of this commit, Logstash does not seem to rotate (high-load) logs written to a file on-demand.
This precludes using external tools, like Rackspace Cloud Monitoring Agent plugins, to monitor metrics emitted by Logstash in a finite amount of disk space.
Using Conveyer, we take Logstash-generated events and write them to a file.
Unlike Logstash's file output configuration, Conveyer provides the ability to rotate the log file it writes to on-demand.
Through this guaranteed atomic mechanism, logs may be consumed by tooling while providing a fresh log file for Logstash's use.
Meanwhile, Logstash is completely ignorant of what's happening.

# How it works

This program implements a daemon.
The daemon is intended to sit on a Logstash instance,
which has an HTTP output configured to POST to the conveyer daemon.
The conveyer writes any received data to a log file.
So far, this sounds just like what you'd expect from a file output configuration.

When an external tool wants access to the logs,
it executes a GET request against the conveyer daemon.
Conveyer will then close the log file it's currently using,
rename it to a new temporary name,
open a new log file for subsequent Logstash requests,
then return the name of the old file to the client.

The log consumer is responsible for deleting the log file it's given when it's done using it.

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

# Configuration

# API

tbd.

