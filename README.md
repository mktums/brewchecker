# brew404
> Any program is only as good as it is useful.
> – _Linus Torvalds_

## What it is?
**brewchecker** is a tool for checking [Homebrew](http://brew.sh/) packages' availability, written in Python.

## What it does?
It downloads latest [Homebrew sources](https://github.com/homebrew/homebrew) to temporary folder, scans [`Formula`](https://github.com/Homebrew/homebrew/tree/master/Library/Formula) folder for formulas, parse every of them, and tries to download every package, patch, etc from 'stable' section.

**Output of this script is JSON document with statuses of all Formulas' resources.**

## Installation
### Requirements
#### System-wide applications
You must have `libcurl` library installed, and follow VCS binaries in `PATH`:

* `git`
* `hg`
* `bzr` (currently not used by Homebrew, but we have to support it)
* `cvs`
* `svn`
* `fossil`

##### OS X:
On OS X you can get all this by using **Homebrew**

``` bash
brew install git hg bzr cvs svn fossil curl
```

### Installation
To install **brewchecker** use following command:

``` bash
pip install https://github.com/mktums/brewchecker/releases/download/v0.2/brewchecker-0.2.tar.gz
```

#### Getting sources
``` bash 
git clone https://github.com/mktums/brewchecker
```

## Usage
In most cases you will want to run it as `brewchecker -qeo report.json`

### All options

``` bash
Usage: brewchecker [OPTIONS]

Options:
  -n, --threads INTEGER  Number of simultaneous downloads performed by
                         brewchecker.
                         Warning: increasing this number may
                         cause errors and slow down your system.  [default: 6]
  -q, --quiet            No log will be printed to STDOUT.  [default: False]
  -e, --only-errors      Report will only contain formulas with errors.
                         [default: False]
  -l, --log FILENAME     Path to log file.
  -o, --output FILENAME  Path to output file where JSON report will be saved.
                         Warning: omitting this option will cause printing
                         report after with its log, unless -q/--quiet is
                         presented.
  --help                 Show this message and exit.
```
