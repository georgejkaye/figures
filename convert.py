import sys
import subprocess
import os
import re
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

tikz_libraries = ["automata", "positioning",
                  "arrows", "circuits.logic.US", "patterns"]

tikz_regex = re.compile(r"{% tikz \"([a-z\-\.\/]*)\" %}")


def get_used_tikz(src_dir):
    tikz_files = []
    for current_root, subdirs, files in os.walk(src_dir):
        for file in files:
            filename = os.fsdecode(file)
            if filename.endswith(".md"):
                with open(os.path.join(current_root, filename), "r") as f:
                    text = f.read()
                for match in tikz_regex.finditer(text):
                    src = match.group(1) + ".tikz"
                    tikz_files.append(src)

    tikz_files = list(set(tikz_files))
    return tikz_files


def compile_file(tikz_file, tikz_dir, output_dir, style_file):

    try:
        with open(os.path.join(tikz_dir, tikz_file), "r") as f:
            tikz = f.read()
    except:
        print(f"[tikz] Could not open file {tikz_file}")
        return

    file_name = os.path.basename(tikz_file)
    file_dir = os.path.dirname(tikz_file)
    tex = f"{file_name}.tex"
    pdf = f"{file_name}.pdf"
    svg = f"{file_name}.svg"
    full_output_dir = os.path.join(output_dir, file_dir)
    output_svg_path = os.path.join(full_output_dir, svg)
    with open(tex, "w") as f:
        f.write("\\documentclass{standalone}\n")
        f.write("\\usepackage{" + tikz_dir + "/tikzit}\n")
        f.write("\\input{" + style_file + "}\n")
        f.write(
            "\\usetikzlibrary{" + ",".join(tikz_libraries) + "}\n\n")
        f.write("\\begin{document}\n")
        f.write(tikz)
        f.write("\\end{document}\n")

    print(f"[tikz] Compiling tikzfile {tex}")
    subprocess.run(["latexmk", "-pdf", "-quiet", tex],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(
        f"[tikz] Converting output {pdf} to {output_svg_path}")

    if not os.path.isdir(full_output_dir):
        os.makedirs(full_output_dir)

    subprocess.run(["pdf2svg", pdf, output_svg_path])
    subprocess.run(["rm", tex])
    subprocess.run(["rm", pdf])
    subprocess.run(["rm", "-f", f"{file_name}.log", f"{file_name}.aux",
                    f"{file_name}.fls", f"{file_name}.fdb_latexmk"])


def compile_all_files(tikz_dir, tikz_files, output_dir, style_file):
    for file in tikz_files:
        compile_file(file, tikz_dir, output_dir, style_file)


class TikzHandler(FileSystemEventHandler):

    def __init__(self, tikz_dir, tikz_files, output_dir, style_file):
        self.tikz_dir = tikz_dir
        self.tikz_files = tikz_files
        self.output_dir = output_dir
        self.style_file = style_file

    def update_tikz(self, event):
        path = event.src_path[(len(self.tikz_dir) + 1):]
        if len(path) > 5 and path[-5:] == ".tikz":
            compile_file(path, self.tikz_dir, self.output_dir, self.style_file)
        elif len(path) > 11 and path[-11:] == ".tikzstyles":
            compile_all_files(self.tikz_dir, self.tikz_files,
                              self.output_dir, self.style_file)
        else:
            return

    def on_create(self, event):
        self.update_tikz(event)

    def on_modified(self, event):
        self.update_tikz(event)


class SourceHandler(FileSystemEventHandler):

    def __init__(self, build_dir, tikz_dir, tikz_files, output_dir, style_file, tikz_handler):
        self.build_dir = build_dir
        self.tikz_dir = tikz_dir
        self.tikz_files = tikz_files
        self.output_dir = output_dir
        self.style_file = style_file
        self.tikz_handler = tikz_handler

    def update_build(self, event):
        new_tikz_files = get_used_tikz(self.build_dir)
        diff_files = list(set(new_tikz_files).difference(self.tikz_files))
        for file in diff_files:
            compile_file(file, self.tikz_dir, self.output_dir, self.style_file)
        self.tikz_files = new_tikz_files
        self.tikz_handler.tikz_files = new_tikz_files

    def on_create(self, event):
        self.update_build(event)

    def on_modified(self, event):
        print(f"{event.src_path} has been modified")
        self.update_build(event)


def main():

    mandatory_args = 4

    if len(sys.argv) > mandatory_args:
        tikz_dir = sys.argv[1]
        src_dir = sys.argv[2]
        output_dir = sys.argv[3]
        style_file = sys.argv[4]
    else:
        print("No file or output provided")
        exit(1)

    tikz_dir = os.path.abspath(tikz_dir)
    src_dir = os.path.abspath(src_dir)
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
    tikz_files = get_used_tikz(src_dir)
    compile_all_files(tikz_dir, tikz_files, output_dir, style_file)

    if not watch:
        exit(0)

    tikz_observer = Observer()
    tikz_handler = TikzHandler(tikz_dir, tikz_files, output_dir, style_file)
    tikz_observer.schedule(tikz_handler, tikz_dir, recursive=True)
    tikz_observer.start()
    source_observer = Observer()
    source_handler = SourceHandler(
        src_dir, tikz_dir, tikz_files, output_dir, style_file, tikz_handler)
    source_observer.schedule(source_handler,
                             src_dir, recursive=True)
    source_observer.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        source_observer.stop()
        source_observer.join()
        tikz_observer.stop()
        tikz_observer.join()


if __name__ == "__main__":
    main()
