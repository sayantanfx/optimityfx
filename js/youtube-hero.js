/* Hero showreel — YouTube IFrame API player.
   - No YouTube branding / title / share overlays (modestbranding + transparent cover)
   - No related-video suggestions after end (rel=0, and the video loops so it never ends)
   - Loops continuously, muted autoplay
   - Auto-pauses when scrolled out of frame, resumes when back in view
   - Click anywhere on the video toggles play / pause */
(function () {
  var VIDEO_ID = 'epNgXLAN47M';
  var player, ready = false, userPaused = false;

  // Load the IFrame API once, then build the player. Guard against the race
  // where the API is already loaded (callback would otherwise never fire).
  window.onYouTubeIframeAPIReady = createPlayer;
  if (window.YT && window.YT.Player) {
    createPlayer();
  } else if (!document.querySelector('script[src*="iframe_api"]')) {
    var tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);
  }

  function createPlayer() {
    if (player) return;
    player = new YT.Player('yt-hero', {
      videoId: VIDEO_ID,
      playerVars: {
        autoplay: 1,
        mute: 1,
        loop: 1,
        playlist: VIDEO_ID,   // required for loop=1 on a single video
        controls: 0,
        modestbranding: 1,
        rel: 0,               // no suggestions from other channels at end
        showinfo: 0,
        iv_load_policy: 3,    // hide annotations
        fs: 0,
        disablekb: 1,
        playsinline: 1
      },
      events: {
        onReady: function () {
          ready = true;
          player.mute();
          player.playVideo();
          observe();
        },
        onStateChange: function (e) {
          // Reveal the video only while it is actually playing. In every other
          // state (unstarted, paused by the scroll observer, buffering) the
          // opaque cover masks YouTube's title / "More videos" overlay.
          var stage = document.querySelector('.hero-video .stage');
          if (e.data === YT.PlayerState.PLAYING) stage.classList.add('is-playing');
          else if (e.data === YT.PlayerState.PAUSED || e.data === YT.PlayerState.UNSTARTED) {
            stage.classList.remove('is-playing');
          }
          // Belt-and-suspenders: if the video ever ends, restart instead of
          // showing YouTube's end-screen suggestions.
          if (e.data === YT.PlayerState.ENDED) {
            player.seekTo(0);
            player.playVideo();
          }
        }
      }
    });
  }

  // Click-to-toggle on the transparent cover.
  var cover = document.querySelector('.yt-cover');
  if (cover) {
    // Click toggles mute/unmute — never pause, so YouTube's pause overlay
    // (title + "More videos" grid) can never appear while on screen.
    cover.addEventListener('click', function () {
      if (!ready) return;
      if (player.isMuted()) player.unMute();
      else player.mute();
    });
  }

  // Pause when the player scrolls out of view, resume when back (unless the
  // user paused it manually).
  function observe() {
    var el = document.querySelector('.hero-video .frame');
    if (!el || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!ready) return;
        if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
          if (!userPaused) player.playVideo();
        } else {
          player.pauseVideo();
        }
      });
    }, { threshold: [0, 0.5] });
    io.observe(el);
  }
})();
