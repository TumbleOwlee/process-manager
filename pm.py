#!/bin/python3

import os
import inquirer
import requests_unixsocket
from blessings import Terminal
from argparse import ArgumentParser

# Used for terminal coloring
term = Terminal()


# Run the given command
def run(sock, args):
    session = requests_unixsocket.Session()
    if args.ARGS is not None and len(args.ARGS) > 0:
        env = dict()
        if args.env is not None:
            for e in args.env:
                split = e.split("=", 1)
                env[split[0]] = split[1]
        json = {
            'working_directory': os.path.abspath(args.cwd),
            'command': args.ARGS,
            'environment': env
        }
        resp = session.post(f"{sock}/run", json=json)
        if resp.status_code != 200:
            print(f"{term.yellow}[!]{term.normal} Run command rejected by daemon.")
    else:
        print(f"{term.yellow}[!]{term.normal} Do nothing. Missing command.")


# Get status of all known processes
def status(sock, args):
    session = requests_unixsocket.Session()
    resp = session.get(f"{sock}/status")
    if resp.status_code != 200:
        print(f"{term.yellow}[!]{term.normal} Run command rejected by daemon.")
    else:
        json = resp.json()
        if len(json) == 0:
            print(f"{term.yellow}[!]{term.normal} No processes found.")
        else:
            print("   State   │  ID  │ Command")
            print("───────────┼──────┼───────────────────────────────────────────────────────────────────────────")
            for x in json:
                alive = "   alive  " if json[x]['alive'] else " not alive"
                print(alive + " │ {:04d}".format(int(x)) + " │ " + " ".join(json[x]['config']['command']))


# Kill a specific pid or choose from list
def kill(sock, args):
    session = requests_unixsocket.Session()
    if args.pid is not None:
        resp = session.get(f"{sock}/kill/{args.pid}")
        if resp.status_code != 200:
            print(f"{term.yellow}[!]{term.normal} Kill command rejected by daemon.")
    else:
        resp = session.get(f"{sock}/status")
        if resp.status_code != 200:
            print(f"{term.yellow}[!]{term.normal} Run command rejected by daemon.")
        else:
            json = resp.json()
            choices = ["{:4d}".format(int(x)) + ": " + " ".join(json[x]['config']['command']) for x in json if json[x]['alive']]
            if len(choices) > 0:
                questions = [
                    inquirer.Checkbox('pid',
                                      message='What process ids to terminate?',
                                      choices=choices)
                ]
                answers = inquirer.prompt(questions)['pid']
                for answer in answers:
                    pid = answer.split(':', 1)[0].strip()
                    resp = session.get(f"{sock}/kill/{pid}")
                    if resp.status_code != 200:
                        print(f"{term.yellow}[!]{term.normal} Kill command rejected by daemon for pid={pid}.")
            else:
                print(f"{term.yellow}[!]{term.normal} No active processes found.")


if __name__ == '__main__':
    parser = ArgumentParser(description="Process management tool.")
    parser.add_argument("--sock", "-s", required=False, default="/tmp/process-mgmt.sock")
    parser.add_argument("--cwd", "-c", required=False, default=os.getcwd())
    subparsers = parser.add_subparsers(title='subcommands', dest="command")
    run_parser = subparsers.add_parser(name='run')
    run_parser.add_argument("--env", "-e", help="Environment pairs of <NAME>=<VALUE>", nargs="*")
    run_parser.add_argument("ARGS", help="Command arguments", nargs="*")
    kill_parser = subparsers.add_parser(name='kill')
    kill_parser.add_argument("--pid", '-p', required=False, help="Process identifier.")
    status_parser = subparsers.add_parser(name='status')
    args = parser.parse_args()

    sock = "http+unix://" + args.sock.replace("/", "%2F")

    if args.command == "run":
        run(sock, args)
    elif args.command == "kill":
        kill(sock, args)
    elif args.command == "status":
        status(sock, args)
