# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import logging.config
import os
from urllib.parse import urlparse

from flask import Flask
from flask_assets import Environment
from flask_talisman import Talisman
from webassets.loaders import YAMLLoader

from landoui import auth, errorhandlers
from landoui.logging import log_config_change, MozLogFormatter
from landoui.sentry import initialize_sentry

logger = logging.getLogger(__name__)

# This global is required to allow OIDC initialization on the entire app,
# yet still allow @oidc decorate uses for pages
oidc = None


def get_app_version(path):
    try:
        with open(path) as f:
            version = json.load(f)
            logger.info(f"version file ({path}) loaded.")
    except (IOError, ValueError, TypeError):
        logger.warning(f"version file ({path}) could not be loaded, assuming dev.")
        version = {
            "source": "https://github.com/mozilla-conduit/lando-ui",
            "version": "0.0.0",
            "commit": "",
            "build": "dev",
        }
    return version


def set_config_param(app, key, value, logger=logger, obfuscate=False):
    app.config[key] = value
    log_config_change(key, value if not obfuscate else "*" * 10)


def create_app(
    version_path,
    secret_key,
    session_cookie_name,
    session_cookie_domain,
    session_cookie_secure,
    use_https,
    enable_asset_pipeline,
    lando_api_url,
    debug=False,
):
    """
    Create an app instance.
    """
    csp = {
        "default-src": "'self'",
        "font-src": "'self' https://code.cdn.mozilla.net",
        "style-src": "'self' https://code.cdn.mozilla.net",
        "img-src": "'self' *.cloudfront.net *.gravatar.com " "*.googleusercontent.com",
        "object-src": "'none'",
        "frame-ancestors": "'none'",
        "manifest-src": "'none'",
        "worker-src": "'none'",
        "media-src": "'none'",
        "frame-src": "'none'",
        "base-uri": "'none'",
        "report-uri": "/__cspreport__",
    }  # yapf: disable

    initialize_logging()

    app = Flask(__name__)
    app.debug = debug

    # Set configuration
    version_info = get_app_version(version_path)
    logger.info("application version", extra=version_info)
    initialize_sentry(app, version_info["version"])

    set_config_param(app, "LANDO_API_URL", lando_api_url)
    set_config_param(
        app, "BUGZILLA_URL", _lookup_service_url(lando_api_url, "bugzilla")
    )
    set_config_param(
        app, "PHABRICATOR_URL", _lookup_service_url(lando_api_url, "phabricator")
    )
    set_config_param(app, "SECRET_KEY", secret_key, obfuscate=True)
    set_config_param(app, "SESSION_COOKIE_NAME", session_cookie_name)
    set_config_param(app, "SESSION_COOKIE_DOMAIN", session_cookie_domain)
    set_config_param(app, "SESSION_COOKIE_SECURE", session_cookie_secure)
    set_config_param(app, "SERVER_NAME", session_cookie_domain)
    set_config_param(app, "USE_HTTPS", use_https)

    app.config["PREFERRED_URL_SCHEME"] = "https" if use_https else "http"
    app.config["VERSION"] = version_info

    # Flags that need to be deprecated in the future.
    set_config_param(app, "ENABLE_SEC_APPROVAL", bool(os.getenv("ENABLE_SEC_APPROVAL")))

    set_config_param(
        app,
        "ENABLE_EMBEDDED_TRANSPLANT_UI",
        bool(os.getenv("ENABLE_EMBEDDED_TRANSPLANT_UI")),
    )

    Talisman(app, content_security_policy=csp, force_https=use_https)

    # Authentication
    global oidc
    authentication = auth.OpenIDConnect(auth.OIDCConfig())
    oidc = authentication.auth(app)

    # Register routes via Flask Blueprints
    from landoui.pages import pages
    from landoui.revisions import revisions
    from landoui.dockerflow import dockerflow

    app.register_blueprint(pages)
    app.register_blueprint(revisions)
    app.register_blueprint(dockerflow)

    # Register template helpers
    from landoui.template_helpers import template_helpers

    app.register_blueprint(template_helpers)

    # Register error pages
    errorhandlers.register_error_handlers(app)

    # Setup Flask Assets
    assets = Environment(app)
    if enable_asset_pipeline:
        loader = YAMLLoader(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "assets_src/assets.yml"
            )
        )
        assets.register(loader.load_bundles())

    from werkzeug.middleware.profiler import ProfilerMiddleware

    app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

    logger.info("Application started successfully.")
    return app


def initialize_logging():
    """Initialize application-wide logging."""
    level = os.environ.get("LOG_LEVEL", "INFO")
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "mozlog": {
                    "()": MozLogFormatter,
                    "mozlog_logger": "lando-ui",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "mozlog",
                },
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "loggers": {
                "landoui": {
                    "level": level,
                    "handlers": ["console"],
                },
                "request.summary": {
                    "level": level,
                    "handlers": ["console"],
                },
                "werkzeug": {
                    "level": "ERROR",
                    "handlers": ["console"],
                },
            },
            "root": {
                "handlers": ["null"],
            },
            "disable_existing_loggers": True,
        }
    )
    logger.info("logging configured", extra={"LOG_LEVEL": level})


def _lookup_service_url(lando_api_url, service_name):
    # TODO: Restructure things to pull this information from lando-api
    # itself / lookup like other environment variables. Sticking this here
    # is a temporary hack to unblock GCP migration.
    value = {
        "bugzilla": os.getenv("BUGZILLA_URL"),
        "phabricator": os.getenv("PHABRICATOR_URL"),
    }[service_name]
    if value:
        return value

    # Returns the corresponding service instance url based on the lando-api
    # url given. Errors out if given an invalid lando_api_url or service name.
    lando_api_hostname = urlparse(lando_api_url).netloc.split(":")[0].lower()
    return {
        "lando-api": {
            "bugzilla": "http://bmo.test",
            "phabricator": "http://phabricator.test",
        },
        "lando-api.test": {
            "bugzilla": "http://bmo.test",
            "phabricator": "http://phabricator.test",
        },
        "api.lando.devsvcdev.mozaws.net": {
            "bugzilla": "https://bugzilla-dev.allizom.org",
            "phabricator": "https://phabricator-dev.allizom.org",
        },
        "api.lando.services.mozilla.com": {
            "bugzilla": "https://bugzilla.mozilla.org",
            "phabricator": "https://phabricator.services.mozilla.com",
        },
    }[lando_api_hostname][service_name]
