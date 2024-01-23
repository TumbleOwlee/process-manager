#!/usr/bin/python3

import os
import pwd
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
            "working_directory": os.path.abspath(args.cwd),
            "command": args.ARGS,
            "environment": env,
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
            lengths = []
            for x in json:
                length = len(json[x]["config"]["command"]) - 1
                for y in json[x]["config"]["command"]:
                    length += len(y)
                lengths.append(length)
            max_line = max(lengths)
            sep = ["─"] * min(term.width - 28, max_line - 7)
            print(
                f"   {term.blue}State{term.normal}   {term.yellow}│{term.normal}  {term.blue}ID{term.normal}  {term.yellow}│{term.normal} {term.blue}Command{term.normal}"
            )
            print(term.yellow + "───────────┼──────┼─────────" + "".join(sep) + term.normal)
            for x in json:
                alive = (
                    f"   {term.green}alive{term.normal}  " if json[x]["alive"] else f" {term.red}not alive{term.normal}"
                )
                print(
                    alive
                    + f" {term.yellow}│{term.normal} "
                    + "{:04d}".format(int(x))
                    + f" {term.yellow}│{term.normal} "
                    + " ".join(json[x]["config"]["command"])
                )


# Kill a specific pid or choose from list
def kill(sock, args):
    session = requests_unixsocket.Session()
    if args.PID is not None and len(args.PID) > 0:
        for pid in args.PID:
            resp = session.get(f"{sock}/kill/{pid}")
            if resp.status_code != 200:
                print(f"{term.yellow}[!]{term.normal} Kill command for PID={pid} rejected by daemon.")
    else:
        resp = session.get(f"{sock}/status")
        if resp.status_code != 200:
            print(f"{term.yellow}[!]{term.normal} Run command rejected by daemon.")
        else:
            json = resp.json()
            choices = [
                "{:4d}".format(int(x)) + ": " + " ".join(json[x]["config"]["command"]) for x in json if json[x]["alive"]
            ]
            if len(choices) > 0:
                questions = [inquirer.Checkbox("pid", message="What process ids to terminate?", choices=choices)]
                answers = inquirer.prompt(questions)["pid"]
                for answer in answers:
                    pid = answer.split(":", 1)[0].strip()
                    resp = session.get(f"{sock}/kill/{pid}")
                    if resp.status_code != 200:
                        print(f"{term.yellow}[!]{term.normal} Kill command rejected by daemon for pid={pid}.")
            else:
                print(f"{term.yellow}[!]{term.normal} No active processes found.")


if __name__ == "__main__":
    username = pwd.getpwuid(os.getuid())[0]
    parser = ArgumentParser(description="Process management tool.")
    parser.add_argument(
        "--sock",
        "-s",
        help=f"Socket file to use. [default: /tmp/process-mgmt-{username}.sock]",
        required=False,
        default=f"/tmp/process-mgmt-{username}.sock",
    )
    parser.add_argument("--cwd", "-c", required=False, default=os.getcwd())
    subparsers = parser.add_subparsers(title="subcommands", dest="command")
    run_parser = subparsers.add_parser(name="run")
    run_parser.add_argument("--env", "-e", help="Environment pairs of <NAME>=<VALUE>", nargs="*")
    run_parser.add_argument("ARGS", help="Command arguments", nargs="*")
    kill_parser = subparsers.add_parser(name="kill")
    kill_parser.add_argument("PID", help="Process identifier.", nargs="*")
    status_parser = subparsers.add_parser(name="status")
    args = parser.parse_args()

    sock = "http+unix://" + args.sock.replace("/", "%2F")

    if args.command == "run":
        run(sock, args)
    elif args.command == "kill":
        kill(sock, args)
    elif args.command == "status":
        status(sock, args)
