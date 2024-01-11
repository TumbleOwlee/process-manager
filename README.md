![Header](images/header.png)

# Introduction

This repository provides a simple daemon and CLI tool to execute and manage background processes.

# Quickstart

The daemon and CLI tool utilize some non-standard libraries. Thus, you have to install the necessary requirements.
```bash
python3 -m pip install -r requirements.txt
```
You may have to find and install the required libraries manually if your python environment is managed by the package manager of the OS.

Afterwards you have to run the daemon since it starts, kills and reports the status of processes by providing a simple HTTP API. 
```bash
./daemon.py
```
By default the daemon will create the socket file `/tmp/process-mgmt-<user>.sock`. You can change it by setting the `--file` option.

While the daemon is active you can command it to start and kill processes or to retrieve the status.
```bash
# Start process in background
./pm.py run -- sleep 15
# The argument '--' is only necessary if your command takes arguments with '-' prefix
# That's the case because else argparse will try to use it and fail.

# Get status of active processes
./pm.py status

# Kill any active process
./pm.py kill <PID1> <PID2> ...
# You can also just run `pm.py kill` and a list is presented that allows you to select the processes to kill.
```

# Example

Please note that the horizontal line of the table outputs is only messed up in the recording because of the the conversion to `svg` for embedding.

<p align="center">
  <img width="600" src="images/example.svg">
</p>
