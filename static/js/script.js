document.addEventListener('DOMContentLoaded', function() {

  var hamburger = document.getElementById('hamburger');
  var navLinks = document.getElementById('navLinks');

  if (hamburger) {
    hamburger.addEventListener('click', function() {
      navLinks.classList.toggle('open');
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (navLinks) navLinks.classList.remove('open');
      }
    });
  });

});

function openLightbox(src) {
  document.getElementById('lightboxImg').src = src;
  document.getElementById('lightbox').classList.add('open');
}

function closeLightbox() {
  document.getElementById('lightbox').classList.remove('open');
}

/* ===== Google Reviews ===== */
(function() {
  var carousel = document.getElementById('googleReviewsCarousel');
  if (!carousel) return;
  fetch('/api/reviews')
    .then(function(r) { return r.json(); })
    .then(function(reviews) {
      carousel.innerHTML = '';
      reviews.forEach(function(r) {
        var card = document.createElement('div');
        card.className = 'gr-card';
        var starsHtml = '';
        for (var i = 1; i <= 5; i++) {
          starsHtml += '<span class="' + (i <= r.rating ? 'filled' : '') + '">&#9733;</span>';
        }
        var initial = r.author ? r.author.charAt(0).toUpperCase() : '?';
        card.innerHTML =
          '<div class="gr-card-author">' +
            '<div class="gr-card-avatar">' + initial + '</div>' +
            '<div>' +
              '<div class="gr-card-name">' + escHtml(r.author) + '</div>' +
              '<div class="gr-card-date">' + escHtml(r.date || '') + '</div>' +
            '</div>' +
          '</div>' +
          '<div class="gr-card-stars">' + starsHtml + '</div>' +
          '<div class="gr-card-text">"' + escHtml(r.text) + '"</div>';
        carousel.appendChild(card);
      });
    })
    .catch(function() {});
  function escHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str || ''));
    return div.innerHTML;
  }
})();