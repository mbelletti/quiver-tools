quiver-tools aka qt
===================

An utility to search or export Quiver notebooks to a markdown files.

[Quiver](http://happenapps.com/#quiver) is a great notebook app built for programmers. Code and text can be freely mixed. 

## Features

- Keep links between notes. 
- Export and link resources
- Automatic download javascript requirement:
  - [raphael](https://raw.githubusercontent.com/DmitryBaranovskiy/raphael)
  - [underscore](https://raw.githubusercontent.com/jashkenas/underscore)
  - [sequence_diagram](https://raw.githubusercontent.com/bramp/js-sequence-diagrams)
  - [flowchart](https://raw.githubusercontent.com/adrai/flowchart.js)


## Installation

- [Download the script](https://raw.githubusercontent.com/mbelletti/quiver-tools/master/qt.py)
- Put it on your path
- `chmod u+x qt.py`

## Usage

	usage: qt.py [-h] [-l] [-q QUERY] [-n NOTEBOOKS] [-e EXCLUDE_NOTEBOOKS]
	             [-x EXPORT] [-v] [-L LIBRARY]

	Quiver helper

	optional arguments:
	  -h, --help            show this help message and exit
	  -l, --list            List notebooks
	  -q QUERY, --query QUERY
	                        Search <query> in notes
	  -n NOTEBOOKS, --notebooks NOTEBOOKS
	                        Restrict search in notebooks. Needs uuids space
	                        separated
	  -e EXCLUDE_NOTEBOOKS, --exclude_notebooks EXCLUDE_NOTEBOOKS
	                        Exclude notebooks from search. Needs uuids space
	                        separated
	  -x EXPORT, --export EXPORT
	                        Export to folder
	  -v, --verbose         Verbose
	  -L LIBRARY, --library LIBRARY
	                        Quiver library path

## Feature Requests and Issues

Feel free to [add an issue or feature request](https://github.com/mbelletti/quiver-tools/issues). Pull requests are welcome as well! 
