# brew404
> Any program is only as good as it is useful.
> – _Linus Torvalds_

## What it is?
**brew404** is a tool for checking [Homebrew](http://brew.sh/) packages' availability, written in Python.

## What it does?
It downloads latest [Homebrew sources](https://github.com/homebrew/homebrew), scans [`Formula`](https://github.com/Homebrew/homebrew/tree/master/Library/Formula) folder for formulas, parse every of them, and tries to download every package, patch, etc from 'stable' section.

While running it shows statuses of package's resources:

![screenshot](https://cloud.githubusercontent.com/assets/204508/7444267/095d0b88-f183-11e4-8e2c-d6eae9f7d186.png)

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
1. So far **brew404** works really slow (currently it tooks 2.5+ hours to finish), since it not utilizes nor `threading` nor `multiprocessing` Python's modules.
