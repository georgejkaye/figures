import sys
import subprocess
import os
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


if len(sys.argv) > 2:
    dir = sys.argv[1]
    output = sys.argv[2]
else:
    print("No file or output provided")

tikzlibraries = ["automata", "positioning",
                 "arrows", "circuits.logic.US", "patterns"]


def compile():
    for file in os.listdir(dir):
        filename = os.fsdecode(file)
        path = os.path.join(dir, filename)
        if filename.endswith(".tikz"):
            with open(os.path.join(dir, filename), "r") as f:
                tikz = f.read()

            tex = f"{path}.tex"
            pdf = f"{file}.pdf"
            svg = f"{output}{file}.svg"

            with open(tex, "w") as f:
                f.write("\\documentclass{standalone}\n")
                f.write("\\usepackage{tikzit}\n")
                f.write("\\input{tikz/blog.tikzstyles}\n")
                f.write(
                    "\\usetikzlibrary{" + ",".join(tikzlibraries) + "}\n\n")
                f.write("\\begin{document}\n")
                f.write(tikz)
                f.write("\\end{document}\n")

            subprocess.run(["latexmk", "-pdf", "-quiet", tex])
            subprocess.run(["pdf2svg", pdf, svg])
            subprocess.run(["rm", tex])
            subprocess.run(["rm", pdf])
            subprocess.run(["rm", f"{file}.log", f"{file}.aux",
                            f"{file}.fls", f"{file}.fdb_latexmk"])


if len(sys.argv) == 4:
    if sys.argv[3] == "--watch":
        print(f"Watching for changes in {dir}")
        watch = True
    else:
        compile()
        exit(0)

if not os.path.isdir(output):
    os.makedirs(output)


patterns = ["blog.tikzstyles"]
ignore_patterns = None
ignore_directories = None
case_sensitive = True


class Handler(FileSystemEventHandler):
    def on_create(self, event):
        if event.src_path[-5:] == ".tikz" or event.src_path[-11:] == ".tikzstyles":
            compile()

    def on_modified(self, event):
        if event.src_path[-5:] == ".tikz" or event.src_path[-11:] == ".tikzstyles":
            compile()


observer = Observer()
observer.schedule(Handler(), dir)
observer.start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    observer.stop()
    observer.join()