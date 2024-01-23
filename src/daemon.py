#!/bin/python3

import os
import pwd
import shutil
import subprocess
from argparse import ArgumentParser
from flask import Flask, request, jsonify

# Create app
app = Flask(__name__)

# Global data store
data = dict()
next_id = 1

# Get username
username = pwd.getpwuid(os.getuid())[0]


# Extract value from request payload
def get_or(key: str, default=None):
    if key in request.json:
        return request.json[key]
    else:
        return default


# Terminate a given process
@app.route("/kill/<id>", methods=["GET"])
def kill(id):
    id = int(id)
    if id in data:
        p = data[id]["process"]
        if p.poll() is None:
            p.terminate()
            print(f"[i] terminate process {id}.\n")
            try:
                p.wait(5)
            except subprocess.TimeoutExpired:
                p.kill()
                print(f"[i] Kill process {id}.\n")
        return jsonify(), 200, {"ContentType": "application/json"}
    else:
        return jsonify(), 400, {"ContentType": "application/json"}


# Get list of all known processes
@app.route("/status", methods=["GET"])
def status():
    to_remove = []
    status_codes = dict()
    for id in data:
        alive = data[id]["process"].poll() is None
        status_codes[id] = {"alive": alive, "config": data[id]["config"]}
        if not alive:
            to_remove.append(id)
    for id in to_remove:
        data[id]["process"].wait()
        del data[id]
    return jsonify(status_codes), 200, {"ContentType": "application/json"}


# Start process for the given command
@app.route("/run", methods=["POST"])
def run():
    global next_id
    # Extract config
    cfg = {
        "working_directory": os.path.abspath(get_or("working_directory", None)),
        "command": get_or("command", []),
        "environment": get_or("environment", dict()),
    }

    # Create directory
    if os.path.exists(f"/tmp/process-mgmt-{username}/{next_id}"):
        shutil.rmtree(f"/tmp/process-mgmt-{username}/{next_id}")
    os.mkdir(f"/tmp/process-mgmt-{username}/{next_id}")

    # Create output files
    stdout = open(f"/tmp/process-mgmt-{username}/{next_id}/stdout", "w")
    stderr = open(f"/tmp/process-mgmt-{username}/{next_id}/stderr", "w")

    # Setup environment
    env = os.environ.copy()
    env = {**env, **cfg["environment"]}

    # Start process
    print(
        f"[i] Start process {next_id} in {cfg['working_directory']} with: {cfg['command']}"
    )
    process = subprocess.Popen(
        cfg["command"],
        env=env,
        cwd=cfg["working_directory"],
        stdout=stdout,
        stderr=stderr,
        stdin=subprocess.PIPE,
    )
    print(f"[i] Process {next_id} started.")

    # Store data
    data[next_id] = {
        "process": process,
        "config": cfg,
    }

    # Increment for next
    next_id += 1

    # Return status code
    return jsonify(success=True), 200, {"ContentType": "application/json"}


# Main entry point
if __name__ == "__main__":
    parser = ArgumentParser(description="Process management engine.")
    req_group = parser.add_argument_group("required")
    req_group.add_argument(
        "--file",
        type=str,
        help=f"Unix socket file. [default: /tmp/process-mgmt-{username}.sock]",
        default=f"/tmp/process-mgmt-{username}.sock",
    )
    args = parser.parse_args()

    if os.path.exists(f"/tmp/process-mgmt-{username}"):
        shutil.rmtree(f"/tmp/process-mgmt-{username}")
    os.mkdir(f"/tmp/process-mgmt-{username}")

    path = os.path.abspath(args.file)
    print(f"[i] Unix socket: unix://{path}")
    app.run(host=f"unix://{path}")
