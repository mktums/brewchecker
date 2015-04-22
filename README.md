# brew404
## What it is?
**brew404** is a tool for checking [Homebrew](http://brew.sh/) packages' availability, written in Python.

## What it does?
It downloads latest [Homebrew sources](https://github.com/homebrew/homebrew), scans [`Formula`](https://github.com/Homebrew/homebrew/tree/master/Library/Formula) folder for formulas, parse every of them, and tries to download every package, patch, etc.

While running it shows what packages contains error, like this:

![screenshot](https://cloud.githubusercontent.com/assets/204508/7277847/ec3b4238-e91a-11e4-9d0e-ab64b5b21826.png)

## Installation
### Requirements
#### Python packages
**brew404** mostly rely on `stdlib`'s modules and `pip`'s VCS interface. Also, it uses [`pycurl`](http://pycurl.sourceforge.net/).

To install latest versions of them:

``` bash
pip install --upgrade pip pycurl
```

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

### Getting sources
``` bash 
git clone https://github.com/mktums/brew404
```

## Usage
So far it's just 
``` bash
./main.py
```



## TODO:
1. So far **brew404** works really slow (currently it's 6+ hours), since it not utilizes nor `threading` nor `multiprocessing` Python's modules.
2. Some formulas have URL(s) that must be evaluated with Ruby (see [Issue #1](https://github.com/mktums/brew404/issues/1)), but since we can't do it from Python - it must be done some other way. For example: 
``` bash
echo "PP.pp(lib_name.f.stable)" | ./homebrew/bin/brew irb -r pp -f
```
