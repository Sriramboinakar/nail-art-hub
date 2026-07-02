import sys; sys.path.insert(0, '.')
from app import app

with app.test_client() as c:
    r = c.get('/')
    html = r.data.decode()
    
    checks = [
        ("Logo", "logo.jpeg" in html),
        ("Hero image", "hero.jpeg" in html),
        ("Heading", "Luxury Nail Art" in html),
        ("Services", "Gel Manicure" in html and "Bridal Nails" in html),
        ("Gallery", "gallery1.jpeg" in html),
        ("Before & After", "Before &" in html),
        ("Dammaiguda branch", "Dammaiguda" in html),
        ("Moula Ali branch", "Moula Ali" in html),
        ("Booking form", "Pay Advance" in html),
        ("Dammaiguda map link", "BO8n1BS5hnwJsdkFb" in html),
        ("Moula Ali map link", "YaLRVzZx8LbY6POBY" in html),
        ("Payment modal", "payModal" in html),
        ("No broken Jinja", "{{" not in html),
    ]
    
    for name, ok in checks:
        print(f'[{"OK" if ok else "FAIL"}] {name}')
    
    r2 = c.get('/api/services')
    print(f'\nServices API: {len(r2.json)} services')
    
    r3 = c.get('/api/branches')
    for b in r3.json:
        print(f'  {b["name"]}: maps={"yes" if b.get("maps") else "no"}')
    
    r4 = c.get('/api/slots?branch=1&date=2026-07-02')
    print(f'Slots API: {len(r4.json)} slots')
    
    for img in ['logo.jpeg', 'hero.jpeg'] + [f'gallery{i}.jpeg' for i in range(1,9)]:
        r = c.get(f'/static/images/{img}')
        print(f'[{"OK" if r.status_code==200 else "FAIL"}] {img}')
    
    ok_count = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f'\n{ok_count}/{total} checks passed')
