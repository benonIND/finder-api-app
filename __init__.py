import ssl
self.session.verify = True
self.session.cert = None
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
self.session.ssl_context = ssl_context
