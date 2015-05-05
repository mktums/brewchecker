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
pip install https://github.com/mktums/brewchecker/releases/download/v0.1/brewchecker-0.1.tar.gz
```

#### Getting sources
``` bash 
git clone https://github.com/mktums/brewchecker
```

## Usage
So far it's just 
``` bash
brewchecker
```
