"""Extract files from an Electron asar archive. Read-only, stdlib only."""
import json
import struct
import sys


def load(asar_path):
    f = open(asar_path, "rb")
    head = f.read(16)
    _, _, _, json_len = struct.unpack("<IIII", head)
    table = json.loads(f.read(json_len).decode("utf-8"))
    return f, table, 16 + json_len


def walk(node, prefix=""):
    for name, entry in node.get("files", {}).items():
        path = f"{prefix}{name}"
        if "files" in entry:
            yield from walk(entry, path + "/")
        else:
            yield path, entry


def main():
    asar, target = sys.argv[1], sys.argv[2]
    f, table, base = load(asar)
    entries = dict(walk(table))
    for p in sorted(entries):
        if target in p:
            print(p, entries[p]["size"])
    exact = [p for p in entries if p.endswith(target)]
    if exact and len(sys.argv) > 3:
        e = entries[exact[0]]
        f.seek(base + int(e["offset"]))
        sys.stdout.write(f.read(e["size"]).decode("utf-8", "replace"))
    f.close()


if __name__ == "__main__":
    main()
