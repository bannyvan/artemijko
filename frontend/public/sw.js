importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js');

if (workbox) {
  workbox.core.setCacheNameDetails({prefix: 'timetracker'});

  workbox.precaching.precacheAndRoute(self.__WB_MANIFEST || []);

  // Cache static
  workbox.routing.registerRoute(
    ({request}) => request.destination === 'style' || request.destination === 'script' || request.destination === 'worker',
    new workbox.strategies.StaleWhileRevalidate({
      cacheName: 'static-assets'
    })
  );

  const bgSyncPlugin = new workbox.backgroundSync.BackgroundSyncPlugin('shift-queue', {
    maxRetentionTime: 24 * 60,
  });

  const shouldQueue = ({url, request}) => {
    return url.pathname.match(/^\/api\/(shifts\/(start|pause|resume|finish)|breaks\/(start|finish))/);
  };

  workbox.routing.registerRoute(
    ({url, request}) => shouldQueue({url, request}) && request.method === 'POST',
    new workbox.strategies.NetworkOnly({ plugins: [bgSyncPlugin] }),
    'POST'
  );
}