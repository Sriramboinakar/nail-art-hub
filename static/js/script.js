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

  function checkReady() {
    var svc = bookService.value;
    var name = bookName.value.trim();
    var phone = bookPhone.value.trim();
    bookBtn.disabled = !(svc && selectedSlot && name && phone);
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
  document.getElementById('payForm').style.display = 'block';
  document.getElementById('paySuccess').style.display = 'none';
  document.getElementById('payModal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('payModal').style.display = 'none';
}

function processPayment() {
  var btn = document.getElementById('processBtn');
  btn.disabled = true;
  btn.textContent = 'Processing...';
  setTimeout(async function() {
    try {
      var svc = document.getElementById('bookService');
      var br = document.getElementById('bookBranch');
      await fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: document.getElementById('bookName').value.trim(),
          phone: document.getElementById('bookPhone').value.trim(),
          service_id: parseInt(svc.value),
          service_name: svc.options[svc.selectedIndex].text,
          branch_id: br.value,
          branch_name: br.options[br.selectedIndex].text,
          date: document.getElementById('bookDate').value,
          time: (typeof selectedSlot !== 'undefined' ? selectedSlot : document.querySelector('.slot-btn.selected')?.textContent?.trim()) || '',
          total: 99,
          advance: 99,
          payment_status: 'paid'
        })
      });
      document.getElementById('payForm').style.display = 'none';
      document.getElementById('paySuccess').style.display = 'block';
      document.getElementById('confirmText').innerHTML = svc.options[svc.selectedIndex].text + '<br>' + document.getElementById('bookDate').value + ' at ' + (document.querySelector('.slot-btn.selected')?.textContent?.trim() || '');
    } catch (e) {
      alert('Error: ' + e.message);
    }
    btn.disabled = false;
    btn.textContent = 'Pay &#8377;99';
  }, 1500);
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
