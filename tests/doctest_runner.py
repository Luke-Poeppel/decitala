"""
There are a number of doctests in the source, but they cannot be run in the 
standard way as the files have relative imports. As such, we may run them here. 
"""

if __name__ == "__main__":
    import doctest
    from decitala import (
        fragment,
        utils,
        trees,
        pofp,
    )
    doctest.testmod(fragment)
    doctest.testmod(utils)
    doctest.testmod(trees)
    doctest.testmod(pofp)