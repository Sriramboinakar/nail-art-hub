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

  var dateInput = document.getElementById('bookDate');
  if (dateInput) {
    var today = new Date();
    dateInput.valueAsDate = today;
    dateInput.setAttribute('min', today.toISOString().split('T')[0]);
  }

  var bookService = document.getElementById('bookService');
  var bookName = document.getElementById('bookName');
  var bookPhone = document.getElementById('bookPhone');
  var bookBranch = document.getElementById('bookBranch');
  var bookDate = document.getElementById('bookDate');
  var slotGrid = document.getElementById('slotGrid');
  var bookBtn = document.getElementById('bookBtn');

  var selectedSlot = null;
  var step2 = document.getElementById('step2');
  var step3 = document.getElementById('step3');

  function updateSteps() {
    var svc = bookService.value;
    var name = bookName.value.trim();
    var phone = bookPhone.value.trim();
    if (step2) step2.classList.toggle('locked', !svc);
    if (step3) step3.classList.toggle('locked', !(svc && name && phone));
  }

  function checkReady() {
    var svc = bookService.value;
    var name = bookName.value.trim();
    var phone = bookPhone.value.trim();
    bookBtn.disabled = !(svc && selectedSlot && name && phone);
    updateSteps();
  }

  function loadSlots() {
    var branch = bookBranch.value;
    var date = bookDate.value;
    if (!date) return;
    fetch('/api/slots?branch=' + branch + '&date=' + date)
      .then(function(r) { return r.json(); })
      .then(function(slots) {
        slotGrid.innerHTML = '';
        slots.forEach(function(s) {
          var d = document.createElement('div');
          d.className = 'slot-btn' + (s.booked ? ' booked' : '');
          d.textContent = s.time;
          if (!s.booked) {
            d.onclick = function() { selectSlot(this); };
          }
          slotGrid.appendChild(d);
        });
      });
  }

  function selectSlot(el) {
    document.querySelectorAll('.slot-btn').forEach(function(s) { s.classList.remove('selected'); });
    el.classList.add('selected');
    selectedSlot = el.textContent.trim();
    checkReady();
  }

  if (bookService) bookService.addEventListener('change', checkReady);
  if (bookName) bookName.addEventListener('input', checkReady);
  if (bookPhone) bookPhone.addEventListener('input', checkReady);
  if (bookDate) bookDate.addEventListener('change', loadSlots);
  if (bookBranch) bookBranch.addEventListener('change', loadSlots);

  loadSlots();

  window.selectSlot = selectSlot;

});

function openLightbox(src) {
  document.getElementById('lightboxImg').src = src;
  document.getElementById('lightbox').classList.add('open');
}

function closeLightbox() {
  document.getElementById('lightbox').classList.remove('open');
}

function openPayment() {
  document.getElementById('razorpayBtnWrap').style.display = 'block';
  document.getElementById('payProcessing').style.display = 'none';
  document.getElementById('paySuccess').style.display = 'none';
  document.getElementById('payModal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('payModal').style.display = 'none';
}

function getBookingData() {
  var svc = document.getElementById('bookService');
  var br = document.getElementById('bookBranch');
  return {
    name: document.getElementById('bookName').value.trim(),
    phone: document.getElementById('bookPhone').value.trim(),
    service_id: parseInt(svc.value),
    service_name: svc.options[svc.selectedIndex].text,
    branch_id: br.value,
    branch_name: br.options[br.selectedIndex].text,
    date: document.getElementById('bookDate').value,
    time: (typeof selectedSlot !== 'undefined' ? selectedSlot : document.querySelector('.slot-btn.selected')?.textContent?.trim()) || ''
  };
}

function confirmBooking() {
  var d = getBookingData();
  var svc = document.getElementById('bookService');
  return fetch('/api/book', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: d.name, phone: d.phone, service_id: d.service_id, service_name: d.service_name, branch_id: d.branch_id, branch_name: d.branch_name, date: d.date, time: d.time, total: 99, advance: 99, payment_status: 'paid' })
  });
}

function razorpayPay() {
  fetch('/api/razorpay-config').then(function(r) { return r.json(); }).then(function(config) {
    if (!config.key) {
      alert('Razorpay is not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in Vercel environment variables.');
      return;
    }
    document.getElementById('razorpayBtnWrap').style.display = 'none';
    document.getElementById('payProcessing').style.display = 'block';
    fetch('/api/create-order', { method: 'POST' }).then(function(r) { return r.json(); }).then(function(order) {
      var d = getBookingData();
      var rzp = new Razorpay({
        key: config.key,
        amount: order.amount,
        currency: order.currency,
        order_id: order.id,
        name: 'Nail Art Hub',
        description: d.service_name + ' | ' + d.date + ' ' + d.time,
        image: '/static/images/logo.jpeg',
        prefill: { name: d.name, contact: d.phone },
        theme: { color: '#8B3A3F' },
        handler: function(response) {
          fetch('/api/verify-payment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ razorpay_order_id: response.razorpay_order_id, razorpay_payment_id: response.razorpay_payment_id, razorpay_signature: response.razorpay_signature })
          }).then(function(v) { return v.json(); }).then(function(verify) {
            if (verify.verified) {
              confirmBooking().then(function() {
                document.getElementById('payProcessing').style.display = 'none';
                document.getElementById('paySuccess').style.display = 'block';
                document.getElementById('confirmText').innerHTML = d.service_name + '<br>' + d.date + ' at ' + d.time;
              });
            } else {
              alert('Payment verification failed. Please contact support.');
              document.getElementById('razorpayBtnWrap').style.display = 'block';
              document.getElementById('payProcessing').style.display = 'none';
            }
          });
        },
        modal: { ondismiss: function() {
          document.getElementById('razorpayBtnWrap').style.display = 'block';
          document.getElementById('payProcessing').style.display = 'none';
        }}
      });
      rzp.open();
    }).catch(function(e) {
      alert('Error creating payment: ' + e.message);
      document.getElementById('razorpayBtnWrap').style.display = 'block';
      document.getElementById('payProcessing').style.display = 'none';
    });
  });
}

function upiPay() {
  var d = getBookingData();
  if (!d.name || !d.phone || !d.time) return;
  var upiId = document.getElementById('upiIdDisplay') ? document.getElementById('upiIdDisplay').textContent.trim() : 'nailarthub20@upi';
  var note = 'Nail%20Art%20Hub%20-%20' + encodeURIComponent(d.service_name) + '%20' + encodeURIComponent(d.date) + '%20' + encodeURIComponent(d.time);
  var upiLink = 'upi://pay?pa=' + encodeURIComponent(upiId) + '&am=99&cu=INR&tn=' + note;
  document.getElementById('razorpayBtnWrap').style.display = 'none';
  document.getElementById('payProcessing').style.display = 'block';
  document.getElementById('payProcessing').innerHTML = '<div style="font-size:14px;color:#888;margin-bottom:12px">Opening UPI app...</div><div style="font-size:13px;color:#666;margin-bottom:16px">After paying, click confirm below</div><button onclick="confirmBooking().then(function(){document.getElementById(\'payProcessing\').style.display=\'none\';document.getElementById(\'paySuccess\').style.display=\'block\';var d=getBookingData();document.getElementById(\'confirmText\').innerHTML=d.service_name+\'<br>\'+d.date+\' at \'+d.time})" class="btn-primary" style="width:100%;padding:13px;font-size:15px;border:none;border-radius:50px;cursor:pointer;color:#fff;background:#25D366;font-weight:600">&#10003; I\'ve Paid — Confirm Booking</button>';
  window.open(upiLink, '_blank');
}

function resetBooking() {
  closeModal();
  document.getElementById('bookService').value = '';
  document.getElementById('bookBtn').disabled = true;
  document.getElementById('bookName').value = '';
  document.getElementById('bookPhone').value = '';
  document.querySelectorAll('.slot-btn').forEach(function(s) { s.classList.remove('selected'); });
  if (typeof selectedSlot !== 'undefined') selectedSlot = null;
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
