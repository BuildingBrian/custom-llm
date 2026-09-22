"""Drive the unchanged chat.py through a pseudo-terminal so a screenshot shows the prompts being typed.

Nothing about the model or chat.py changes: this only types a fixed list of prompts into the real
interface, one character at a time, and copies the terminal output to the screen.
Usage: python tools/chat_demo.py <model.pt> <transcript.json>
"""
import os, pty, select, sys, time

PROMPTS = ["the customer", "the opposite of tall is", "a trout is a",
           "the cup is not red . it is green . the cup is",
           "my laptop crashed yesterday", "hello how are you today"]

def pump(fd, seconds):
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if fd in r:
            try:
                data = os.read(fd, 4096)
            except OSError:
                return False
            if not data:
                return False
            os.write(1, data)
    return True

def main():
    model, transcript = sys.argv[1], sys.argv[2]
    pid, fd = pty.fork()
    if pid == 0:
        os.execv(sys.executable, [sys.executable, "chat.py", "--model", model, "--transcript", transcript])
    pump(fd, 4.0)
    for p in PROMPTS:
        for ch in p:
            os.write(fd, ch.encode()); time.sleep(0.04)
        os.write(fd, b"\n"); pump(fd, 1.5)
    os.write(fd, b"/quit\n"); pump(fd, 2.0)
    os.waitpid(pid, 0)

if __name__ == "__main__":
    main()
