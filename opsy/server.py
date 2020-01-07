from cheroot import wsgi
from cheroot.ssl.pyopenssl import pyOpenSSLAdapter


def create_server(app, host, port, threads=10, ssl_enabled=None,
                  certificate=None, private_key=None, ca_certificate=None):
    server = wsgi.Server((host, port), app, numthreads=threads)
    if ssl_enabled:
        server.ssl_adapter = pyOpenSSLAdapter(
            certificate, private_key, certificate_chain=ca_certificate)
    return server
