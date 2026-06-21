from __future__ import annotations

import cmd

from osb.cli.session import World

_GUIDE = "\n".join(
    [
        "OSB commands. You type short 'handles' (like emma, walker), not full names.",
        "A '<bubble>' is an id such as b0 that is printed when you create a bubble.",
        "",
        "people:",
        "  register_subject <name>             add a help-seeker (a subject)",
        "                                      example:  register_subject john",
        "  register_advisor <name> <attrs>     add an advisor; attrs are comma-separated",
        "                                      example:  register_advisor doc cancer_specialist,medical_doctor",
        "  advisors                            list advisors and their attributes",
        "  users                               list everyone and all bubbles",
        "  available <name> on|off             mark an advisor available / unavailable",
        "",
        "bubbles:",
        "  bubble <subject> <policy>           subject opens a bubble; policy is clause;clause",
        "                                      and is met when EVERY clause has a matching advisor",
        "                                      example:  bubble emma cancer_specialist;legal_advisor",
        "  join <bubble> <advisor>             an advisor joins      example:  join b0 walker",
        "  remove <bubble> <advisor>           subject drops an advisor",
        "  replace <bubble> <advisor> [policy] subject swaps an advisor for another match",
        "  close <bubble>                      subject closes the bubble",
        "",
        "messages:",
        "  send <bubble> <from> <message>      post an encrypted message",
        "                                      example:  send b0 emma Hello, I need advice",
        "  inbox <bubble> <reader>             read the messages a member can decrypt",
        "",
        "accountability:",
        "  trace <bubble> <member>             Registrar + Tracer together reveal a real identity",
        "",
        "  help                                show this guide",
        "  quit                                leave",
    ]
)


def _start_here() -> str:
    return "\n".join(
        [
            "Getting started (type one line at a time):",
            "  1) emma opens a bubble needing a cancer specialist AND a legal advisor:",
            "       bubble emma cancer_specialist;legal_advisor",
            "     this prints a bubble id such as b0 - use that id in the next steps.",
            "  2) the invited advisors join:",
            "       join b0 walker",
            "       join b0 bennett",
            "  3) emma sends a message and an advisor reads it:",
            "       send b0 emma Hello, I was just diagnosed",
            "       inbox b0 walker",
            "  4) reveal an advisor's real identity, then close the bubble:",
            "       trace b0 walker",
            "       close b0",
            "",
            "Type 'help' for every command, 'users' to see who exists, 'quit' to leave.",
        ]
    )


class OSBShell(cmd.Cmd):
    intro = ""
    prompt = "osb> "

    def __init__(self) -> None:
        super().__init__()
        self.world = World()

    def _run(self, fn, *args) -> None:
        try:
            print(fn(*args))
        except Exception as exc:
            print(f"error: {exc}")

    def do_register_subject(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 1:
            print("usage: register_subject <name>          example: register_subject john")
            return
        self._run(self.world.register_subject, parts[0])

    def do_register_advisor(self, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            print("usage: register_advisor <name> <attr,attr>   example: register_advisor doc cancer_specialist")
            return
        attrs = [a.strip() for a in parts[1].split(",") if a.strip()]
        self._run(self.world.register_advisor, parts[0], attrs)

    def do_advisors(self, arg: str) -> None:
        self._run(self.world.list_advisors)

    def do_users(self, arg: str) -> None:
        self._run(self.world.overview)

    do_status = do_users

    def do_available(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2 or parts[1] not in ("on", "off"):
            print("usage: available <name> on|off          example: available walker off")
            return
        self._run(self.world.set_available, parts[0], parts[1] == "on")

    def do_bubble(self, arg: str) -> None:
        parts = arg.split(maxsplit=1)
        if len(parts) != 2:
            print("usage: bubble <subject> <policy>        example: bubble emma cancer_specialist;legal_advisor")
            return
        self._run(self.world.create_bubble, parts[0], parts[1])

    def do_join(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2:
            print("usage: join <bubble> <advisor>          example: join b0 walker")
            return
        self._run(self.world.join, parts[0], parts[1])

    def do_send(self, arg: str) -> None:
        parts = arg.split(maxsplit=2)
        if len(parts) < 3:
            print("usage: send <bubble> <from> <message>   example: send b0 emma hello team")
            return
        self._run(self.world.send, parts[0], parts[1], parts[2])

    def do_inbox(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2:
            print("usage: inbox <bubble> <reader>          example: inbox b0 walker")
            return
        self._run(self.world.inbox, parts[0], parts[1])

    def do_remove(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2:
            print("usage: remove <bubble> <advisor>        example: remove b0 walker")
            return
        self._run(self.world.remove, parts[0], parts[1])

    def do_replace(self, arg: str) -> None:
        parts = arg.split(maxsplit=2)
        if len(parts) < 2:
            print("usage: replace <bubble> <advisor> [policy]   example: replace b0 bennett")
            return
        policy = parts[2] if len(parts) == 3 else None
        self._run(self.world.replace, parts[0], parts[1], policy)

    def do_close(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 1:
            print("usage: close <bubble>                   example: close b0")
            return
        self._run(self.world.close, parts[0])

    def do_trace(self, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2:
            print("usage: trace <bubble> <member>          example: trace b0 walker")
            return
        self._run(self.world.trace, parts[0], parts[1])

    def do_help(self, arg: str) -> None:
        print(_GUIDE)

    def do_quit(self, arg: str) -> bool:
        return True

    do_exit = do_quit

    def do_EOF(self, arg: str) -> bool:
        print()
        return True

    def default(self, line: str) -> None:
        print(f"unknown command: {line.split()[0]}   (type 'help' to see the commands)")

    def emptyline(self) -> None:
        pass


def run_shell() -> int:
    shell = OSBShell()
    print("Setting up sample users, please wait...")
    print(shell.world.seed())
    print()
    print(shell.world.list_advisors())
    print()
    print("'emma' is the patient (subject); the others are advisors. Use these short handles.")
    print()
    print(_start_here())
    shell.cmdloop()
    return 0
