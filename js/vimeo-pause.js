/* Pause Vimeo embeds when they scroll out of view.
   One-at-a-time playback is handled by autopause=1 in the embed URLs. */
(function () {
  function init() {
    if (!window.Vimeo || !('IntersectionObserver' in window)) return;
    var iframes = document.querySelectorAll('iframe[src*="player.vimeo.com"]');
    if (!iframes.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.intersectionRatio < 0.2) {
          var p = e.target._ofxPlayer || (e.target._ofxPlayer = new Vimeo.Player(e.target));
          p.pause().catch(function () {});
        }
      });
    }, { threshold: [0, 0.2] });
    iframes.forEach(function (f) { io.observe(f); });
  }
  if (document.readyState === 'complete') init();
  else window.addEventListener('load', init);
})();
