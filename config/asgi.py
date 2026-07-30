import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

# Django must load before routing/consumers/auth — those modules call get_user_model()
# and auth models; importing them first triggers AppRegistryNotReady.
django_asgi_app = get_asgi_application()

from core.realtime.routing import websocket_urlpatterns  # noqa: E402

# AllowedHostsOriginValidator requires a matching Origin header. Browsers send it;
# many WS tools (Postman, scripts, wscat) omit Origin → handshake rejected before
# the consumer runs. When DEBUG is True, skip origin checks so local testing works.
_ws_urls = URLRouter(websocket_urlpatterns)
_websocket = _ws_urls if settings.DEBUG else AllowedHostsOriginValidator(_ws_urls)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": _websocket,
})
