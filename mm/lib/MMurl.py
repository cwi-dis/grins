__version__ = "$Id$"

import string
import os
from urllib import *
# Grr, 2.1 __all__ compatibility:
from urllib import unwrap, pathname2url, url2pathname, splittype, splithost, splitquery, splitattr, toBytes, addinfourl
import socket

_OriginalFancyURLopener = FancyURLopener

_end_loop = '_end_loop'
class FancyURLopener(_OriginalFancyURLopener):
    def __init__(self, *args):
        apply(_OriginalFancyURLopener.__init__, (self,) + args)
        self.tempcache = {}
        self.__unlink = os.unlink # See cleanup()
        self.__OriginalFancyURLopener = _OriginalFancyURLopener

        # prefetch support
        self.__prefetchcache = {}
        self.__prefetchtempfiles = {}

    def __del__(self):
        self.__OriginalFancyURLopener.__del__(self)
        del self.__OriginalFancyURLopener

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        void = fp.read()
        fp.close()
        raise IOError, (errcode, 'http error: ' + errmsg, headers)

    def http_error_302(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        # XXX The server can force infinite recursion here!
        if headers.has_key('location'):
            newurl = headers['location']
        elif headers.has_key('uri'):
            newurl = headers['uri']
        else:
            return
        void = fp.read()
        fp.close()
        fp = self.open(newurl, data, method)
        h = fp.info()
        if not h.has_key('Content-Location') and \
           not h.has_key('Content-Base'):
            h.dict['content-location'] = newurl
            h.headers.append('Content-Location: %s\r\n' % newurl)
        return fp

    def prompt_user_passwd(self, host, realm):
        import windowinterface
        try:
            w = windowinterface.Window('passwd', grab = 1)
        except AttributeError:
            return _OriginalFancyURLopener.prompt_user_passwd(self, host, realm)
        l = w.Label('Enter username and password for %s at %s' % (realm, host))
        t1 = w.TextInput('User:', '', None, (self.usercb, ()),
                         top = l, left = None, right = None)
        t2 = w.TextInput('Passwd:', '', None, (self.passcb, ()),
                         modifyCB = self.modifycb,
                         top = t1, left = None, right = None)
        b = w.ButtonRow([('OK', (self.do_return, ())),
                         ('Cancel', (self.cancelcb, ()))],
                        vertical = 0,
                        top = t2, left = None, right = None, bottom = None)
        self.userw = t1
        self.passwdw = t2
        self.passwd = []
        self.user = ''
        self.password = ''
        w.show()
        try:
            windowinterface.mainloop()
        except _end_loop:
            pass
        w.hide()
        w.close()
        del self.userw, self.passwdw
        return self.user, self.password

    def modifycb(self, text):
        if text:
            if text == '\b':
                if self.passwd:
                    del self.passwd[-1]
                return ''
            self.passwd.append(text)
            return '*' * len(text)

    def usercb(self):
        self.user = self.userw.gettext()
        if self.password:
            self.do_return()
        else:
            self.passwdw.setfocus()

    def passcb(self):
        self.password = string.joinfields(self.passwd, '')
        if self.user:
            self.do_return()
        else:
            self.userw.setfocus()

    def cancelcb(self):
        self.user = self.password = None
        self.do_return()

    def do_return(self):
        raise _end_loop

    def open_local_file(self, url):
        import urlparse
        scheme, netloc, url, params, query, fragment = urlparse.urlparse(url)
        url = urlparse.urlunparse((scheme, netloc, url, '', '', ''))
        return _OriginalFancyURLopener.open_local_file(self, url)

    #
    # Prefetch section
    #
    # override retrieve for prefetch implementation
    def retrieve(self, url, filename=None, reporthook=None, data=None, method=None):
        # retrieve(url) returns (filename, None) for a local object
        # or (tempfilename, headers) for a remote object.
        url = unwrap(url)
        import urlparse
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        if not scheme or scheme == 'file':
            i = string.find(path, '?')
            if i > 0:
                path = path[:i]
            url = urlparse.urlunparse((scheme, netloc, path, '', '', ''))
        if self.__prefetchcache.has_key(url):
            # complete prefetch first
            #print 'completing prefetch'
            self.__fin_retrieve(url)
        if self.__prefetchtempfiles.has_key(url):
            #print 'retrieving prefetched',self.__prefetchtempfiles[url]
            return self.__prefetchtempfiles[url]

        url = unwrap(toBytes(url))
        if self.tempcache and url in self.tempcache:
            return self.tempcache[url]
        type, url1 = splittype(url)
        if filename is None and (not type or type == 'file'):
            try:
                fp = self.open_local_file(url1, data, method)
                hdrs = fp.info()
                del fp
                return url2pathname(splithost(url1)[1]), hdrs
            except IOError, msg:
                pass
        fp = self.open(url, data, method)
        headers = fp.info()
        if filename:
            tfp = open(filename, 'wb')
        else:
            import tempfile
            garbage, path = splittype(url)
            garbage, path = splithost(path or "")
            path, garbage = splitquery(path or "")
            path, garbage = splitattr(path or "")
            suffix = os.path.splitext(path)[1]
            (fd, filename) = tempfile.mkstemp(suffix)
            self.__tempfiles.append(filename)
            tfp = os.fdopen(fd, 'wb')
        result = filename, headers
        if self.tempcache is not None:
            self.tempcache[url] = result
        bs = 1024*8
        size = -1
        read = 0
        blocknum = 0
        if reporthook:
            if "content-length" in headers:
                size = int(headers["Content-Length"])
            reporthook(blocknum, bs, size)
        while 1:
            block = fp.read(bs)
            if block == "":
                break
            read += len(block)
            tfp.write(block)
            blocknum += 1
            if reporthook:
                reporthook(blocknum, bs, size)
        fp.close()
        tfp.close()
        del fp
        del tfp

        # raise exception if actual size does not match content-length header
        if size >= 0 and read < size:
            raise ContentTooShortError("retrieval incomplete: got only %i out "
                                       "of %i bytes" % (read, size), result)

        return result

    # override cleanup for prefetch implementation
    def cleanup(self):
        # This code sometimes runs when the rest of this module
        # has already been deleted, so it can't use any globals
        # or import anything.

        # first close open streams
        for fp, tfp in self.__prefetchcache.values():
            fp.close()
            tfp.close()
        self.__prefetchcache = {}

        # unlink temp files
        for file, header in self.__prefetchtempfiles.values():
            try:
                self.__unlink(file)
            except:
                pass
        self.__prefetchtempfiles = {}

        # call original cleanup
        self.__OriginalFancyURLopener.cleanup(self)

    # open stream to url and read headers but not data yet
    # see retrieve for signature
    def begin_retrieve(self, url, filename=None, reporthook=None):
        url = unwrap(url)
        self.__clean_retrieve(url)
        type, url1 = splittype(url)
        if not filename and (not type or type == 'file'):
            try:
                fp = self.open_local_file(url1)
                hdrs = fp.info()
                del fp
                return url2pathname(splithost(url1)[1]), hdrs
            except IOError, msg:
                pass
        fp = self.open(url)
        headers = fp.info()
        if not filename:
            import tempfile
            garbage, path = splittype(url)
            garbage, path = splithost(path or "")
            path, garbage = splitquery(path or "")
            path, garbage = splitattr(path or "")
            suffix = os.path.splitext(path)[1]
            filename = tempfile.mktemp(suffix)
            self.__prefetchtempfiles[url] = filename, headers
        tfp = open(filename, 'wb')
        self.__prefetchcache[url] = fp, tfp
        return filename, headers

    # retrieve a block of length bs from already open stream to url
    def do_retrieve(self, url, bs):
        if not self.__prefetchcache.has_key(url):
            return None
        fp, tfp = self.__prefetchcache[url]
        block = fp.read(bs)
        if block:
            tfp.write(block)
        return block!=None

    # prefetch completed
    def end_retrieve(self, url):
        if not self.__prefetchcache.has_key(url):
            return
        fp, tfp = self.__prefetchcache[url]
        fp.close()
        tfp.close()
        del self.__prefetchcache[url]

    # retrieve rest of resource
    def __fin_retrieve(self, url):
        if not self.__prefetchcache.has_key(url):
            return None
        fp, tfp = self.__prefetchcache[url]
        del self.__prefetchcache[url]
        bs = 1024*8
        block = fp.read(bs)
        while block:
            tfp.write(block)
            block = fp.read(bs)
        fp.close()
        tfp.close()

    # clean any refs and resources for url
    def __clean_retrieve(self, url):
        if self.__prefetchcache.has_key(url):
            fp, tfp = self.__prefetchcache[url]
            fp.close()
            tfp.close()
            del self.__prefetchcache[url]
        if self.__prefetchtempfiles.has_key(url):
            file, hdr = self.__prefetchtempfiles[url]
            try:
                os.unlink(file)
            except:
                pass
            del self.__prefetchtempfiles[url]

    def _retrieved(self, url):
        if self.tempcache.has_key(url):
            return 1
        return self.__prefetchtempfiles.has_key(url) and \
                not self.__prefetchcache.has_key(url)

    # extension from urllib that provides a PUT method
    def open(self, fullurl, data=None, method=None):
        """Use URLopener().open(file) instead of open(file, 'r')."""
        if method is not None and method == 'GET' and data is not None:
            raise IOError, ('open error', 'cannot use GET with data')
        if method is not None and method == 'POST' and data is None:
            raise IOError, ('open error', 'cannot use POST without data')
        if method is not None and method == 'PUT' and data is None:
            raise IOError, ('open error', 'cannot use PUT without data')
        fullurl = unwrap(toBytes(fullurl))
        if self.tempcache and fullurl in self.tempcache:
            filename, headers = self.tempcache[fullurl]
            fp = open(filename, 'rb')
            return addinfourl(fp, headers, fullurl)
        urltype, url = splittype(fullurl)
        if not urltype:
            urltype = 'file'
        if urltype in self.proxies:
            proxy = self.proxies[urltype]
            urltype, proxyhost = splittype(proxy)
            host, selector = splithost(proxyhost)
            url = (host, fullurl) # Signal special case to open_*()
        else:
            proxy = None
        name = 'open_' + urltype
        self.type = urltype
        name = name.replace('-', '_')
        if not hasattr(self, name):
            if proxy:
                return self.open_unknown_proxy(proxy, fullurl, data, method)
            else:
                return self.open_unknown(fullurl, data, method)
        try:
            if data is None:
                if method is None:
                    return getattr(self, name)(url)
                else:
                    return getattr(self, name)(url, method = method)
            else:
                if method is None:
                    return getattr(self, name)(url, data)
                else:
                    return getattr(self, name)(url, data, method)
        except socket.error, msg:
            raise IOError, ('socket error', msg), sys.exc_info()[2]

    def open_unknown(self, fullurl, data=None, method=None):
        """Overridable interface to open unknown URL type."""
        type, url = splittype(fullurl)
        raise IOError, ('url error', 'unknown url type', type)

    def open_unknown_proxy(self, proxy, fullurl, data=None, method=None):
        """Overridable interface to open unknown URL type."""
        type, url = splittype(fullurl)
        raise IOError, ('url error', 'invalid proxy for %s' % type, proxy)

    def open_http(self, url, data=None, method=None):
        """Use HTTP protocol."""
        import httplib
        user_passwd = None
        proxy_passwd= None
        if isinstance(url, str):
            host, selector = splithost(url)
            if host:
                user_passwd, host = splituser(host)
                host = unquote(host)
            realhost = host
        else:
            host, selector = url
            # check whether the proxy contains authorization information
            proxy_passwd, host = splituser(host)
            # now we proceed with the url we want to obtain
            urltype, rest = splittype(selector)
            url = rest
            user_passwd = None
            if urltype.lower() != 'http':
                realhost = None
            else:
                realhost, rest = splithost(rest)
                if realhost:
                    user_passwd, realhost = splituser(realhost)
                if user_passwd:
                    selector = "%s://%s%s" % (urltype, realhost, rest)
                if proxy_bypass(realhost):
                    host = realhost

            #print "proxy via http:", host, selector
        if not host:
            raise IOError, ('http error', 'no host given')

        if proxy_passwd:
            import base64
            proxy_auth = base64.b64encode(proxy_passwd).strip()
        else:
            proxy_auth = None

        if user_passwd:
            import base64
            auth = base64.b64encode(user_passwd).strip()
        else:
            auth = None
        h = httplib.HTTP(host)
        if data is not None:
            h.putrequest(method or 'POST', selector)
            h.putheader('Content-Type', 'application/x-www-form-urlencoded')
            h.putheader('Content-Length', '%d' % len(data))
        else:
            h.putrequest('GET', selector)
        if proxy_auth:
            h.putheader('Proxy-Authorization', 'Basic %s' % proxy_auth)
        if auth:
            h.putheader('Authorization', 'Basic %s' % auth)
        if realhost:
            h.putheader('Host', realhost)
        for args in self.addheaders:
            h.putheader(*args)
        h.endheaders()
        if data is not None:
            h.send(data)
        errcode, errmsg, headers = h.getreply()
        if errcode == -1:
            # something went wrong with the HTTP status line
            raise IOError, ('http protocol error', 0,
                            'got a bad status line', None)
        fp = h.getfile()
        if errcode == 200:
            return addinfourl(fp, headers, "http:" + url)
        else:
            return self.http_error(url, fp, errcode, errmsg, headers, data, method)

    if hasattr(socket, "ssl"):
        def open_https(self, url, data=None, method=None):
            """Use HTTPS protocol."""
            import httplib
            user_passwd = None
            proxy_passwd = None
            if isinstance(url, str):
                host, selector = splithost(url)
                if host:
                    user_passwd, host = splituser(host)
                    host = unquote(host)
                realhost = host
            else:
                host, selector = url
                # here, we determine, whether the proxy contains authorization information
                proxy_passwd, host = splituser(host)
                urltype, rest = splittype(selector)
                url = rest
                user_passwd = None
                if urltype.lower() != 'https':
                    realhost = None
                else:
                    realhost, rest = splithost(rest)
                    if realhost:
                        user_passwd, realhost = splituser(realhost)
                    if user_passwd:
                        selector = "%s://%s%s" % (urltype, realhost, rest)
                #print "proxy via https:", host, selector
            if not host: raise IOError, ('https error', 'no host given')
            if proxy_passwd:
                import base64
                proxy_auth = base64.b64encode(proxy_passwd).strip()
            else:
                proxy_auth = None
            if user_passwd:
                import base64
                auth = base64.b64encode(user_passwd).strip()
            else:
                auth = None
            h = httplib.HTTPS(host, 0,
                              key_file=self.key_file,
                              cert_file=self.cert_file)
            if data is not None:
                h.putrequest(method or 'POST', selector)
                h.putheader('Content-Type',
                            'application/x-www-form-urlencoded')
                h.putheader('Content-Length', '%d' % len(data))
            else:
                h.putrequest('GET', selector)
            if proxy_auth: h.putheader('Proxy-Authorization', 'Basic %s' % proxy_auth)
            if auth: h.putheader('Authorization', 'Basic %s' % auth)
            if realhost: h.putheader('Host', realhost)
            for args in self.addheaders: h.putheader(*args)
            h.endheaders()
            if data is not None:
                h.send(data)
            errcode, errmsg, headers = h.getreply()
            if errcode == -1:
                # something went wrong with the HTTP status line
                raise IOError, ('http protocol error', 0,
                                'got a bad status line', None)
            fp = h.getfile()
            if errcode == 200:
                return addinfourl(fp, headers, "https:" + url)
            else:
                return self.http_error(url, fp, errcode, errmsg, headers,
                                       data, method)

    def open_file(self, url, data=None, method=None):
        """Use local file or FTP depending on form of URL."""
        if not isinstance(url, str):
            raise IOError, ('file error', 'proxy support for file protocol currently not implemented')
        if url[:2] == '//' and url[2:3] != '/' and url[2:12].lower() != 'localhost/':
            if data is not None:
                raise IOError, ('ftp error', 'only GET allowed')
            return self.open_ftp(url)
        else:
            return self.open_local_file(url, data, method)

    def open_local_file(self, url, data=None, method=None):
        """Use local file."""
        if data is not None and method != 'PUT':
            raise IOError, ('local file error', 'only PUT and GET supported')
        import mimetypes, mimetools, email.Utils
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        host, file = splithost(url)
        if host:
            host, port = splitport(host)
            if port or socket.gethostbyname(host) not in (localhost(), thishost()):
                raise IOError, ('local file error', 'not on local host')
        localname = url2pathname(file)
        if data is not None:
            fp = open(localname, 'wb')
            fp.write(data)
            fp.close()
        try:
            stats = os.stat(localname)
        except OSError, e:
            raise IOError(e.errno, e.strerror, e.filename)
        size = stats.st_size
        modified = email.Utils.formatdate(stats.st_mtime, usegmt=True)
        mtype = mimetypes.guess_type(url)[0]
        headers = mimetools.Message(StringIO(
            'Content-Type: %s\nContent-Length: %d\nLast-modified: %s\n' %
            (mtype or 'text/plain', size, modified)))
        urlfile = file
        if file[:1] == '/':
            urlfile = 'file://' + file
        return addinfourl(open(localname, 'rb'), headers, urlfile)

    def http_error(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        """Handle http errors.
        Derived class can override this, or provide specific handlers
        named http_error_DDD where DDD is the 3-digit error code."""
        # First check if there's a specific handler for this error
        name = 'http_error_%d' % errcode
        if hasattr(self, name):
            func = getattr(self, name)
            result = func(url, fp, errcode, errmsg, headers, data, method)
            if result:
                return result
        return self.http_error_default(url, fp, errcode, errmsg, headers)

    def http_error_301(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        """Error 301 -- also relocated (permanently)."""
        return self.http_error_302(url, fp, errcode, errmsg, headers, data, method)

    def http_error_303(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        """Error 303 -- also relocated (essentially identical to 302)."""
        return self.http_error_302(url, fp, errcode, errmsg, headers, data, method)

    def http_error_307(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        """Error 307 -- relocated, but turn POST into error."""
        if data is None:
            return self.http_error_302(url, fp, errcode, errmsg, headers, data, method)
        else:
            return self.http_error_default(url, fp, errcode, errmsg, headers)

    def http_error_401(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        """Error 401 -- authentication required.
        This function supports Basic authentication only."""
        if not 'www-authenticate' in headers:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        stuff = headers['www-authenticate']
        import re
        match = re.match('[ \t]*([^ \t]+)[ \t]+realm="([^"]*)"', stuff)
        if not match:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        scheme, realm = match.groups()
        if scheme.lower() != 'basic':
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        name = 'retry_' + self.type + '_basic_auth'
        return getattr(self,name)(url, realm, data, method)

    def http_error_407(self, url, fp, errcode, errmsg, headers, data=None, method=None):
        """Error 407 -- proxy authentication required.
        This function supports Basic authentication only."""
        if not 'proxy-authenticate' in headers:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        stuff = headers['proxy-authenticate']
        import re
        match = re.match('[ \t]*([^ \t]+)[ \t]+realm="([^"]*)"', stuff)
        if not match:
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        scheme, realm = match.groups()
        if scheme.lower() != 'basic':
            URLopener.http_error_default(self, url, fp,
                                         errcode, errmsg, headers)
        name = 'retry_proxy_' + self.type + '_basic_auth'
        return getattr(self,name)(url, realm, data, method)

    def retry_proxy_http_basic_auth(self, url, realm, data=None, method=None):
        host, selector = splithost(url)
        newurl = 'http://' + host + selector
        proxy = self.proxies['http']
        urltype, proxyhost = splittype(proxy)
        proxyhost, proxyselector = splithost(proxyhost)
        i = proxyhost.find('@') + 1
        proxyhost = proxyhost[i:]
        user, passwd = self.get_user_passwd(proxyhost, realm, i)
        if not (user or passwd): return None
        proxyhost = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + proxyhost
        self.proxies['http'] = 'http://' + proxyhost + proxyselector
        return self.open(newurl, data, method)

    def retry_proxy_https_basic_auth(self, url, realm, data=None, method=None):
        host, selector = splithost(url)
        newurl = 'https://' + host + selector
        proxy = self.proxies['https']
        urltype, proxyhost = splittype(proxy)
        proxyhost, proxyselector = splithost(proxyhost)
        i = proxyhost.find('@') + 1
        proxyhost = proxyhost[i:]
        user, passwd = self.get_user_passwd(proxyhost, realm, i)
        if not (user or passwd): return None
        proxyhost = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + proxyhost
        self.proxies['https'] = 'https://' + proxyhost + proxyselector
        return self.open(newurl, data, method)

    def retry_http_basic_auth(self, url, realm, data=None, method=None):
        host, selector = splithost(url)
        i = host.find('@') + 1
        host = host[i:]
        user, passwd = self.get_user_passwd(host, realm, i)
        if not (user or passwd): return None
        host = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + host
        newurl = 'http://' + host + selector
        return self.open(newurl, data, method)

    def retry_https_basic_auth(self, url, realm, data=None, method=None):
        host, selector = splithost(url)
        i = host.find('@') + 1
        host = host[i:]
        user, passwd = self.get_user_passwd(host, realm, i)
        if not (user or passwd): return None
        host = quote(user, safe='') + ':' + quote(passwd, safe='') + '@' + host
        newurl = 'https://' + host + selector
        return self.open(newurl, data, method)

_urlopener = None
def urlopen(url, data=None, method=None):
    global _urlopener
    if not _urlopener:
        _urlopener = FancyURLopener()
    return _urlopener.open(url, data=data, method=method)

def urlretrieve(url, filename=None, data=None):
    global _urlopener
    if not _urlopener:
        _urlopener = FancyURLopener()
    return _urlopener.retrieve(url, filename=filename, data=data)

def urlcleanup():
    if _urlopener:
        _urlopener.cleanup()

def geturlopener():
    global _urlopener
    if not _urlopener:
        _urlopener = FancyURLopener()
    return _urlopener

def urlretrieved(url):
    global _urlopener
    if not _urlopener:
        _urlopener = FancyURLopener()
    return _urlopener._retrieved(url)

import urlparse
def basejoin(base, url, allow_fragments = 1):
    newurl = urlparse.urljoin(base, url, allow_fragments)
    type, url = splittype(newurl)
    if type == 'file' and url[:3] != '///':
        newurl = canonURL(newurl)
    return newurl

def guessurl(filename):
    import os
    # convert filename to URL
    utype, url = splittype(filename)
    if utype is not None and utype in ('http', 'file', 'ftp', 'rtsp'):
        # definitely a URL
        return filename
    if os.sep in filename:
        # probably a file name
        return pathname2url(filename)
    # possibly a relative URL
    return filename

_pathname2url = pathname2url
def pathname2url(path):
    import os, sys
    if sys.platform == 'win32' and os.name != 'ce':
        import longpath
        filename = longpath.short2longpath(path)
    url = _pathname2url(path)
    type, rest = splittype(url)
    if not type and rest[:1] == '/':
        if rest[:3] == '///':
            url = 'file:' + url
        else:
            url = 'file://' + url
    return url

def canonURL(url):
    type, rest = splittype(url)
    if not type or type == 'file':
        # if no type it's a file URL
        if rest[:1] != '/':
            # make absolute pathname
            import os
            url = canonURL(basejoin(pathname2url(os.getcwd())+'/',rest))
        elif rest[:3] == '///':
            url = 'file:' + rest
        else:
            url = 'file://' + rest
    return url
