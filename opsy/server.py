from cheroot import wsgi
from cheroot.ssl.pyopenssl import pyOpenSSLAdapter


def run_opsy(script_info, host=None, port=None, ssl_enabled=None,
             certificate=None, private_key=None, ca_certificate=None):
    app = script_info.load_app()
    host = host or app.config.opsy['server']['host']
    port = port or app.config.opsy['server']['port']
    ssl_enabled = ssl_enabled or app.config.opsy['server']['ssl_enabled']
    certificate = certificate or app.config.opsy['server']['certificate']
    private_key = private_key or app.config.opsy['server']['private_key']
    ca_certificate = ca_certificate or \
        app.config.opsy['server']['ca_certificate']
    server = wsgi.Server((host, port), app)
    proto = 'http'
    if ssl_enabled:
        server.ssl_adapter = pyOpenSSLAdapter(
            certificate, private_key, certificate_chain=ca_certificate)
        proto = 'https'
    app.logger.info(f'Starting server at {proto}://{host}:{port}/...')
    try:
        server.start()
    except KeyboardInterrupt:
        app.logger.info('Stopping opsy...')
    finally:
        server.stop()
