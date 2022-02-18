import sys
import subprocess
import os

if len(sys.argv) == 3:
    file = sys.argv[1]
    output = sys.argv[2]
else:
    print("No file or output provided")

(dir, name) = os.path.split(file)

with open(file) as f:
    tikz = f.read()

tikzlibraries = ["automata", "positioning",
                 "arrows", "circuits.logic.US", "patterns"]

tex = f"{file}.tex"
pdf = f"{name}.pdf"
svg = f"{output}/{name}.svg"

with open(tex, "w") as f:
    f.write("\\documentclass{standalone}\n")
    f.write("\\usepackage{tikzit}\n")
    f.write("\\input{blog.tikzstyles}\n")
    f.write("\\usetikzlibrary{" + ",".join(tikzlibraries) + "}\n\n")
    f.write("\\begin{document}\n")
    f.write(tikz)
    f.write("\\end{document}\n")

subprocess.run(["latexmk", "-pdf", tex])
subprocess.run(["pdf2svg", pdf, svg])
subprocess.run(["rm", tex])
subprocess.run(["rm", pdf])
subprocess.run(["rm", f"{name}.log", f"{name}.aux",
               f"{name}.fls", f"{name}.fdb_latexmk"])
