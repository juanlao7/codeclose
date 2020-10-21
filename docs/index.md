---
no_title: true
---

<style type="text/css">
    #bigTitle {
        font-size: 1.5em;
        margin: 1em 0;
		text-align: center;
	}
	
	#bigTitle::before {
		display: none !important;
	}

    @media screen and (min-width: 42em) {
        #content p,
        #content h2 {
            text-align: center;
        }

        #content h2 {
            margin-top: 80px !important;
        }
    }
</style>

<p id="bigTitle">A visual tool for implementing machine learning pipelines.</p>

## Getting started

Read [the basics](documentation/basics) to learn how to use Protopipe.

However, if you prefer to learn by doing, follow [this quick introductory tutorial](tutorials/introductory/SLAVE).

<a class="button" href="download"><i class="icon-download"></i> Download</a>

## No programming involved

Prepare your data and train multiple models just by connecting a few cards.

![3 connected cards](assets/img/basics/design_1.png)

## Find the best model

Automatically find the optimal value for any parameter of your pipeline.

![Parameter tuning](assets/img/index/find_1.png)

## All results organized

Keep track of all your experiments.

![Table of results](assets/img/index/all-results_1.png)

## Integrated cross-sectional analysis

Study the effect of each parameter on the final result.

![Cross-sectional analysis](assets/img/reports_screen/cross-sectional_1.png)

## Write faster

Export experimental data to <img class="hardcoded" alt="LaTeX" src="assets/img/index/LaTeX_logo.svg" style="width: 65px; vertical-align: middle;" /> with a single click.

<div style="display: flex; justify-content: space-evenly; align-items: flex-start">
	<img class="hardcoded" alt="LaTeX table" src="assets/img/index/LaTeX_table.svg" style="float: left; width: 45%; vertical-align: top; margin-top: 12px;" />
	<img class="hardcoded" alt="LaTeX chart" src="assets/img/index/LaTeX_chart.svg" style="float: right; width: 45%; vertical-align: top;" />
</div>

<!--
LaTeX table:

% Please add the following required packages to your document preamble:
% \usepackage{booktabs}
\begin{table}[]
\center
\begin{tabular}{@{}rrr@{}}
\toprule
Dropout factor & Learning rate & Model loss \\ \midrule
0.5            & 0.001         & 0.4125     \\
0.6            & 0.001         & 0.4253     \\
0.4            & 0.01          & 0.5523     \\
0.3            & 0.01          & 0.6725     \\
0.7            & 0.1           & 0.6324     \\
0.5            & 0.1           & 0.6987     \\ \bottomrule
\end{tabular}
\caption{Best results for each learning rate.}
\label{tab:my-table}
\end{table}

LaTeX chart:

\documentclass{article}
\usepackage{pgfplots}
\usepgfplotslibrary{fillbetween}
\begin{document}
	\thispagestyle{empty}
	\begin{tikzpicture}
	\begin{axis}[
	xlabel=Dropout factor,
	ylabel=Model loss]
	\addplot [name path=upper, draw=none]
	coordinates {
		(0.1, 0.9185)
		(0.2, 0.8865)
		(0.3, 0.7812)
		(0.4, 0.7523)
		(0.5, 0.5889)
		(0.6, 0.6538)
		(0.7, 0.7558)
		(0.8, 0.8999)
		(0.9, 0.9535)
	};
	\addplot [name path=lower, draw=none]
	coordinates {
		(0.1, 0.6785)
		(0.2, 0.5665)
		(0.3, 0.5812)
		(0.4, 0.4123)
		(0.5, 0.3289)
		(0.6, 0.4538)
		(0.7, 0.6558)
		(0.8, 0.6999)
		(0.9, 0.7135)
	};
	\addplot [fill=blue!10] fill between[of=upper and lower];
	\addplot [color=blue, mark=*]
	coordinates {
		(0.1, 0.7985)
		(0.2, 0.7265)
		(0.3, 0.6812)
		(0.4, 0.5823)
		(0.5, 0.4589)
		(0.6, 0.5538)
		(0.7, 0.7058)
		(0.8, 0.7999)
		(0.9, 0.8335)
	};
	\end{axis}
	\end{tikzpicture}
\end{document}
-->

<!--
## No installation required

Protopipe is a web platform accessible from any web browser, operating system and device.

<p style="text-align: center">
    <img class="hardcoded" src="assets/img/index/operating_systems.svg" alt="Windows, Linux, macOS, iOS, Android" style="margin: 1rem 0" />
</p>
-->
