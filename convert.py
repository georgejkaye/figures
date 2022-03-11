import sys
import subprocess
import os
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


if len(sys.argv) > 2:
    root = sys.argv[1]
    output = sys.argv[2]
else:
    print("No file or output provided")

if len(sys.argv) == 4:
    if sys.argv[3] == "--watch":
        watch = True
    else:
        watch = False
else:
    watch = False

tikzlibraries = ["automata", "positioning",
                 "arrows", "circuits.logic.US", "patterns"]


def compile(dir, updated=None):
    for current_root, subdirs, files in os.walk(dir):
        print(f"[tikz] Compiling tikz in {current_root}")
        output_dir = os.path.join(output, current_root)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        for file in files:
            filename = os.fsdecode(file)
            if updated is None or updated in os.path.join(current_root, filename):
                path = os.path.join(dir, filename)
                if filename.endswith(".tikz"):
                    with open(os.path.join(current_root, filename), "r") as f:
                        tikz = f.read()

                    tex = f"{path}.tex"
                    pdf = f"{file}.pdf"
                    svg = f"{file}.svg"
                    svg_path = os.path.join(output_dir, svg)
                    with open(tex, "w") as f:
                        f.write("\\documentclass{standalone}\n")
                        f.write("\\usepackage{tikz/tikzit}\n")
                        f.write("\\input{tikz/blog.tikzstyles}\n")
                        f.write(
                            "\\usetikzlibrary{" + ",".join(tikzlibraries) + "}\n\n")
                        f.write("\\begin{document}\n")
                        f.write(tikz)
                        f.write("\\end{document}\n")

                    print(f"[tikz] Compiling tikzfile {tex}")
                    subprocess.run(["latexmk", "-pdf", "-quiet", tex],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"[tikz] Converting output {pdf} to {svg_path}")
                    subprocess.run(["pdf2svg", pdf, svg_path])
                    subprocess.run(["rm", tex])
                    subprocess.run(["rm", pdf])
                    subprocess.run(["rm", "-f", "*.log", f"*.aux",
                                    "*.fls", f"*.fdb_latexmk"])


def update(event):
    path = event.src_path
    if len(path) > 5 and path[-5:] == ".tikz":
        compile(root, path)
    if len(path) > 11 and path[-11:] == ".tikzstyles":
        compile(root)


class Handler(FileSystemEventHandler):

    def on_create(self, event):
        update(event)

    def on_modified(self, event):
        update(event)


print(f"[tikz] Compiling tikz from {root} and putting them in {output}")
compile(root)

if watch:
    print(f"[tikz] Watching for changes in {root}")
else:
    exit(0)

observer = Observer()
observer.schedule(Handler(), root, recursive=True)
observer.start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    observer.stop()
    observer.join()
