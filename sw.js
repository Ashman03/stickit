/* Stickit offline support.
   The app page is fetched fresh when online (so updates show up straight away)
   and served from the cache when offline. Icons and fonts are cached as they load.
   Bump VERSION when the icon or manifest changes. */
var VERSION = "stickit-v1";
var SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-180.png", "./icons/icon-192.png", "./icons/icon-512.png"];

self.addEventListener("install", function(e){
  e.waitUntil(caches.open(VERSION).then(function(c){ return c.addAll(SHELL); }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener("activate", function(e){
  // Other apps share this github.io address, so only clear Stickit's own old caches.
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k.indexOf("stickit-") === 0 && k !== VERSION; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

self.addEventListener("fetch", function(e){
  var req = e.request;
  if(req.method !== "GET") return;
  var url = new URL(req.url);

  // The app page: network first, cached copy when offline.
  if(req.mode === "navigate"){
    e.respondWith(fetch(req).then(function(res){
      var copy = res.clone();
      caches.open(VERSION).then(function(c){ c.put("./index.html", copy); });
      return res;
    }).catch(function(){
      return caches.match("./index.html", {ignoreSearch: true});
    }));
    return;
  }

  // Google Fonts and Stickit's own files: cached copy first, refreshed in the background.
  var ours = url.origin === self.location.origin && url.pathname.indexOf(new URL("./", self.location).pathname) === 0;
  var fonts = url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";
  if(!ours && !fonts) return;
  e.respondWith(caches.open(VERSION).then(function(c){
    return c.match(req).then(function(hit){
      var net = fetch(req).then(function(res){
        if(res && (res.ok || res.type === "opaque")) c.put(req, res.clone());
        return res;
      }).catch(function(){ return hit; });
      return hit || net;
    });
  }));
});
