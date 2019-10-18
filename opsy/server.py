from cheroot import wsgi
from cheroot.ssl.pyopenssl import pyOpenSSLAdapter


def create_server(app, host, port, ssl_enabled=None, certificate=None,
                  private_key=None, ca_certificate=None):
    server = wsgi.Server((host, port), app)
    if ssl_enabled:
        server.ssl_adapter = pyOpenSSLAdapter(
            certificate, private_key, certificate_chain=ca_certificate)
    return server
