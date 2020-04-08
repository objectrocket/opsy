from cheroot import wsgi
from cheroot.ssl.pyopenssl import pyOpenSSLAdapter


def create_server(app):
    server_config = app.config.opsy['server']
    server = wsgi.Server((server_config['host'], server_config['port']), app,
                         numthreads=server_config['threads'])
    if server_config['ssl_enabled']:
        server.ssl_adapter = pyOpenSSLAdapter(
            server_config['certificate'], server_config['private_key'],
            certificate_chain=server_config['ca_certificate'])
    return server
