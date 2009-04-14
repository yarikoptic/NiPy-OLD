import os
import gzip
import bz2
from urlparse import urlparse
from urllib2 import urlopen
from tempfile import mkstemp

from nipy.utils.path import path

zipexts = (".gz",".bz2")
file_openers = {".gz":gzip.open, ".bz2":bz2.BZ2File, None:file}

def iszip(filename):
    """ Is this filename a zip file.

    :Returns: ``bool``
    """
    _, ext = path(filename).splitext()
    return ext in zipexts

def unzip(filename):
    """ Unzip the given file into another file.  Return the new file's name.

    :Returns: ``string``
    """
    if not iszip(filename):
        raise ValueError("file %s is not zipped"%filename)
    unzip_name, zipext = splitzipext(filename)
    opener = file_openers[zipext]
    outfile = file(unzip_name,'w')
    outfile.write(opener(filename).read())
    outfile.close()
    return unzip_name

def iswritemode(mode):
    """ Test if the given mode will open a file for writing.

    :Parameters:
        `mode` : string
            The mode to be checked

    :Returns: ``bool``
    """
    return mode.find("w")>-1 or mode.find("+")>-1



def splitzipext(filename):
    """
    return (base, zip_extension) from filename.
    If filename does not have a zip extention then
    base = filename and zip_extension = None
    """
    if iszip(filename):
        return path(filename).splitext()
    else:
        return filename, None




def isurl(pathstr):
    """
    Check whether a given string can be parsed as a URL.

    :Parameters:
        `pathstr` : string
            The string to be checked.
    
    :Returns: ``bool``
    """
    scheme, netloc, _, _, _, _ = urlparse(pathstr)
    return bool(scheme and netloc)




def ensuredirs(directory):
    """
    Ensure that the given directory path actually exists.
    If it doesn't, create it.

    :Returns: ``None``
    """
    if not isinstance(directory, path):
        directory = path(directory)
    if not directory.exists():
        directory.makedirs()




class Cache (object):
    """
    A file cache. The path of the cache can be specified
    or else use ~/.nipy/cache by default.
    """
    
    def __init__(self, cachepath=None):
        if cachepath is not None: 
            self.path = path(cachepath)
        elif os.name == 'posix':
            self.path = path(os.environ["HOME"]).joinpath(".nipy","cache")
        elif os.name == 'nt':
            self.path = path(os.environ["HOMEPATH"]).joinpath(".nipy","cache")
        if not self.path.exists():
            ensuredirs(self.path)

    def tempfile(self,suffix='', prefix=''):
        """ Return an temporary file name in the cache"""
        _, fname = mkstemp(suffix, prefix, self.path)
        return fname

    def filepath(self, uri):
        """
        Return the complete path + filename within the cache.
        """
        (_, netloc, upath, _, _, _) = urlparse(uri)
        return self.path.joinpath(netloc, upath[1:])

    def filename(self, uri): 
        """
        Return the complete path + filename within the cache.

        :Returns: ``string``
        """
        return str(self.filepath(uri))
    
    def cache(self, uri):
        """
        Copy a file into the cache.

        :Returns: ``None``
        """
        if self.iscached(uri):
            return
        upath = self.filepath(uri)
        ensuredirs(upath.dirname())
        try:
            openedurl = urlopen(uri)
        except:
            raise IOError("url not found: "+str(uri))
        file(upath, 'w').write(openedurl.read())
        
    def clear(self):
        """ Delete all files in the cache.

        :Returns: ``None``
        """
        for f in self.path.files():
            f.rm()
        
    def iscached(self, uri):
        """ Check if a file exists in the cache.

        :Returns: ``bool``
        """
        return self.filepath(uri).exists()
        
    def retrieve(self, uri):
        """
        Retrieve a file from the cache.
        If not already there, create the file and
        add it to the cache.

        :Returns: ``file``
        """
        self.cache(uri)
        return file(self.filename(uri))


class DataSource (object):

    def __init__(self, cachepath=os.curdir):
        self._cache = Cache(cachepath)

    def tempfile(self,suffix='', prefix=''):
        ''' Return an temporary file name in the cache'''
        return self._cache.tempfile(suffix, prefix)

    def _possible_names(self, filename):
        names = [filename]
        if not iszip(filename):
            for zipext in zipexts:
                names.append(filename+zipext)
        return tuple(names)

    def cache(self, pathstr):
        if isurl(pathstr):
            self._cache.cache(pathstr)

    def filename(self, pathstr):
        found = None
        for name in self._possible_names(pathstr):
            try:                
                if isurl(name):
                    self.cache(name)
                    found = self._cache.filename(name)
                else:
                    raise Exception
            except:
                if path(name).exists():
                    found = name
            if found:
                break
        if found is None:
            raise IOError("%s not found"%pathstr)
        return found

    def exists(self, pathstr):
        try:
            _ = self.filename(pathstr)
            return True
        except IOError:
            return False

    def open(self, pathstr, mode='r'):
        if isurl(pathstr) and iswritemode(mode):
            raise ValueError("URLs are not writeable")
        found = self.filename(pathstr)
        _, ext = splitzipext(found)
        if ext == 'bz2':
            mode.replace("+", "")
        return file_openers[ext](found, mode=mode)

    def _fullpath(self, pathstr):
        return pathstr


class Repository (DataSource):
    """DataSource with an implied root."""
    def __init__(self, baseurl, cachepath=None):
        DataSource.__init__(self, cachepath=cachepath)
        self._baseurl = baseurl

    def _fullpath(self, pathstr):
        return path(self._baseurl).joinpath(pathstr)

    def filename(self, pathstr):
        return DataSource.filename(self, str(self._fullpath(pathstr)))

    def exists(self, pathstr):
        return DataSource.exists(self, self._fullpath(pathstr))

    def open(self, pathstr, mode='r'):
        return DataSource.open(self, self._fullpath(pathstr), mode)
