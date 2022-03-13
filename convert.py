import sys
import subprocess
import os
import re
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

tikzlibraries = ["automata", "positioning",
                 "arrows", "circuits.logic.US", "patterns"]

tikz_regex = re.compile(r"src=\"/tikz/([a-z\-\.\/]*).tikz.svg\"")


def get_used_tikz(build_dir, tikz_dir):
    tikz_files = []
    for current_root, subdirs, files in os.walk(build_dir):
        for file in files:
            filename = os.fsdecode(file)
            if filename.endswith(".html"):
                with open(os.path.join(current_root, filename), "r") as f:
                    text = f.read()
                for match in tikz_regex.finditer(text):
                    src = match.group(1) + ".tikz"
                    tikz_files.append(os.path.join(tikz_dir, src))

    tikz_files = list(set(tikz_files))
    return tikz_files


def compile(tikz_dir, tikz_files, output_dir, style_file, updated=None):
    tikz_dir_length = len(tikz_dir)
    for current_root, subdirs, files in os.walk(tikz_dir):
        relative_dir = current_root[tikz_dir_length:]
        if len(relative_dir) > 0:
            relative_dir = relative_dir[1:]
        for file in files:
            filename = os.fsdecode(file)

            full_file = os.path.join(current_root, filename)
            if full_file in tikz_files:
                full_output_dir = os.path.join(output_dir, relative_dir)
                if not os.path.isdir(full_output_dir):
                    os.makedirs(full_output_dir)
                if updated is None or full_file in updated:
                    with open(os.path.join(current_root, filename), "r") as f:
                        tikz = f.read()

                    tex = f"{filename}.tex"
                    pdf = f"{filename}.pdf"
                    svg = f"{filename}.svg"
                    output_svg_path = os.path.join(
                        output_dir, relative_dir, svg)
                    with open(tex, "w") as f:
                        f.write("\\documentclass{standalone}\n")
                        f.write("\\usepackage{" + tikz_dir + "/tikzit}\n")
                        f.write("\\input{" + tikz_dir +
                                "/" + style_file + "}\n")
                        f.write(
                            "\\usetikzlibrary{" + ",".join(tikzlibraries) + "}\n\n")
                        f.write("\\begin{document}\n")
                        f.write(tikz)
                        f.write("\\end{document}\n")

                    print(f"[tikz] Compiling tikzfile {tex}")
                    subprocess.run(["latexmk", "-pdf", "-quiet", tex],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(
                        f"[tikz] Converting output {pdf} to {output_svg_path}")
                    subprocess.run(["pdf2svg", pdf, output_svg_path])
                    subprocess.run(["rm", tex])
                    subprocess.run(["rm", pdf])
                    subprocess.run(["rm", "-f", f"{filename}.log", f"{filename}.aux",
                                    f"{filename}.fls", f"{filename}.fdb_latexmk"])


class TikzHandler(FileSystemEventHandler):

    def __init__(self, tikz_dir, tikz_files, output_dir, style_file):
        self.tikz_dir = tikz_dir
        self.tikz_files = tikz_files
        self.output_dir = output_dir
        self.style_file = style_file

    def update_tikz(self, event):
        path = event.src_path
        if len(path) > 5 and path[-5:] == ".tikz":
            diff_files = [path]
        if len(path) > 11 and path[-11:] == ".tikzstyles":
            diff_files = None
        else:
            return

        compile(self.tikz_dir, self.tikz_files, self.output_dir,
                self.style_file, updated=diff_files)

    def on_create(self, event):
        self.update_tikz(event)

    def on_modified(self, event):
        self.update_tikz(event)


class BuildHandler(FileSystemEventHandler):

    def __init__(self, build_dir, tikz_dir, tikz_files, output_dir, style_file):
        self.build_dir = build_dir
        self.tikz_dir = tikz_dir
        self.tikz_files = tikz_files
        self.output_dir = output_dir
        self.style_file = style_file

    def update_build(self, event):
        new_tikz_files = get_used_tikz(self.build_dir, self.tikz_dir)
        diff_files = list(set(new_tikz_files).difference(self.tikz_files))
        if not len(diff_files) == 0:
            compile(self.tikz_dir, self.tikz_files, self.output_dir,
                    self.style_file, updated=diff_files)
            self.tikz_files = new_tikz_files

    def on_create(self, event):
        self.update_build(event)

    def on_modified(self, event):
        print(f"{event.src_path} has been modified")
        self.update_build(event)


def main():

    mandatory_args = 4

    if len(sys.argv) > mandatory_args:
        tikz_dir = sys.argv[1]
        build_dir = sys.argv[2]
        output_dir = sys.argv[3]
        style_file = sys.argv[4]
    else:
        print("No file or output provided")
        exit(1)

    tikz_dir = os.path.abspath(tikz_dir)
    build_dir = os.path.abspath(build_dir)
    output_dir = os.path.abspath(output_dir)

    if len(sys.argv) == mandatory_args + 2:
        if sys.argv[-1] == "--watch":
            watch = True
        else:
            watch = False
    else:
        watch = False

    print(
        f"[tikz] Compiling tikz from {tikz_dir} and putting them in {output_dir}")
    tikz_files = get_used_tikz(build_dir, tikz_dir)
    compile(tikz_dir, tikz_files, output_dir, style_file)

    if not watch:
        exit(0)

    tikz_observer = Observer()
    tikz_observer.schedule(TikzHandler(
        tikz_dir, tikz_files, output_dir, style_file), tikz_dir, recursive=True)
    tikz_observer.start()
    build_observer = Observer()
    build_observer.schedule(BuildHandler(build_dir, tikz_dir, tikz_files, output_dir, style_file),
                            build_dir, recursive=True)
    build_observer.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        build_observer.stop()
        build_observer.join()
        tikz_observer.stop()
        tikz_observer.join()


if __name__ == "__main__":
    main()
