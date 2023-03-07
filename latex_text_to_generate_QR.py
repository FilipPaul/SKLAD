latex_text = R"""%%PREAMBLE %%%%%%%%%%%%%%%%%%%%%%%%%%%%
\documentclass[10pt, a4paper]{article}% size of txt = 10pt

\usepackage[top= 1.5cm,
			bottom = 1.5cm,
			left = 1cm,
			right = 1cm,
			footskip = 0cm,
			headsep = 0cm,
			headheight = 0cm
			]{geometry}
\pagestyle{empty}


%\usepackage{showframe}
%\renewcommand\ShowFrameLinethickness{0.15pt}
%\renewcommand*\ShowFrameColor{\color{red}}
\usepackage{graphicx}

\begin{document}
\noindent
"""

latex_end_text = R"\end{document}"