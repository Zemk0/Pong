# Vector Pong – Dokumentácia

## 1. Vector2D – Vektorová matematika

Trieda pre 2D vektory používaná pri pohybe lopty a pálek.

### Atribúty
- `x`, `y` – súradnice alebo komponenty vektora.

### Metódy
- `__add__`, `__sub__`, `__mul__`, `__truediv__` – základné operácie s vektormi.
- `dot(other)` – skalárny súčin, používaný pri výpočte odrazov:
V_new = V - 2 * (V · N) * N

markdown
Kopírovať kód
- `magnitude()` – veľkosť vektora:
|V| = sqrt(x^2 + y^2)

markdown
Kopírovať kód
- `normalize()` – jednotkový vektor `(x/|V|, y/|V|)`
- `set_magnitude(new_mag)` – zmena veľkosti vektora pri zachovaní smeru
- `reflect(normal)` – odraz vektora od povrchu (normála N)

**Použitie:** Lopta a pálky využívajú `Vector2D` pre pohyb, kolízie a odrazy.

---

## 2. Paddle – Pálka

### Atribúty
- `position` – horný ľavý roh pálky (Vector2D)
- `width`, `height` – rozmery
- `speed` – základná rýchlosť pohybu (px/s)

### Metódy
- `move(direction, dt, speed_multiplier)` – pohyb hore/dole podľa klávesov
- `direction` = -1 (hore), 1 (dole)
- `dt` = delta time
- `speed_multiplier` = úprava rýchlosti (napr. slider)
- `get_rect()` – vráti `pygame.Rect` na kreslenie a kolíziu

**Matematika:** Rýchlosť sa násobí `dt`, aby pohyb nebol závislý na FPS.

---

## 3. Ball – Lopta

### Atribúty
- `position`, `velocity` – Vector2D
- `radius` – veľkosť lopty
- `base_speed` – základná rýchlosť
- `acceleration_enabled` – prepínač zrýchlenia
- `acceleration_factor` – faktor zrýchlenia pri odraze

### Metódy
- `reset(x, y)` – reset lopty do stredu, náhodný uhol (-45° až 45°)
v_x = cos(theta) * base_speed
v_y = sin(theta) * base_speed

markdown
Kopírovať kód
- `update(dt, speed_multiplier)` – pohyb lopty
position += velocity * dt * speed_multiplier

markdown
Kopírovať kód
- `reflect_from_paddle(paddle)` – odraz lopty podľa miesta zásahu pálky
- Offset od stredu pálky normalizovaný do [-1, 1]
- Bounce angle: `bounce_angle = normalized_offset * MAX_BOUNCE_ANGLE`
- Nová rýchlosť:
  ```
  v_x = cos(bounce_angle) * speed * direction
  v_y = sin(bounce_angle) * speed
  ```
- `check_paddle_collision(paddle)` – kolízia lopty a pálky
- Najbližší bod pálky k stredu lopty
- Ak `distance <= radius`, nastane odraz
- `check_wall_collision()` – odraz od hornej/dolnej steny
- `check_score()` – kontrola, či lopta prešla ľavú alebo pravú hranicu

**Matematika:** Odrazy sú založené na analytickej geometrii a trigonometrických výpočtoch.

---

## 4. Button – Tlačidlo

Jednoduchý UI prvok s hover efektom.

### Metódy
- `check_hover(mouse_pos)` – kontrola, či myš je nad tlačidlom
- `is_clicked(mouse_pos, mouse_pressed)` – kontrola kliknutia
- `draw(screen)` – vykreslenie tlačidla s obrysom a textom

---

## 5. Slider – Nastavenie hodnôt

Používa sa pre rýchlosti lopty/pálky, celkovú rýchlosť hry.

- Lineárna interpolácia:
handle_x = x0 + (value - min) / (max - min) * width

markdown
Kopírovať kód
- Hodnotu je možné meniť ťahaním myšou.

---

## 6. Toggle – Prepínač True/False

- Boolean prepínač (napr. zrýchlenie lopty)
- Kliknutím sa mení stav a vizuálne sa posúva gombík
- Farby:
- Zelená = zapnuté
- Tmavošedá = vypnuté

---

## 7. Game – Hlavná trieda hry

Riadi celý priebeh hry.

### Atribúty
- `screen`, `clock`, `running`
- `state` – menu, playing, paused, postgame
- Pálky, lopta, skóre
- UI prvky: tlačidlá, slidery, toggle

### Metódy
- `reset_round()` – reset lopty a pálok
- `reset_game()` – reset skóre a kola
- `handle_input(dt)` – spracovanie klávesov W/S, UP/DOWN
- `update(dt)` – aktualizácia lopty, kolízií, skórovania
- `draw()` – vykreslenie hry, pálek, lopty, skóre, pauzy
- `run()` – hlavný loop:
1. Spracovanie vstupu
2. Aktualizácia logiky
3. Vykreslenie (DRAW)
4. Flip obrazovky

**Matematika / fyzika:**  
- Pohyb lopty a pálok je založený na vektoroch a delta time  
- Odrazy od pálky sú trigonometrické podľa miesta zásahu  
- Rýchlosti sa môžu meniť cez slidery a toggle (multiplier / zrýchlenie)

---

## 8. Logika hry

- Hráči ovládajú pálky:
- Ľavá: W / S
- Pravá: UP / DOWN
- Lopta sa odráža od pálek a stien.
- Po prekročení hranice sa skóre pripočíta a lopta sa resetuje.
- Pauza: ESC alebo SPACE
- Slider a toggle umožňujú meniť:
- Celkovú rýchlosť hry
- Rýchlosť pálok
- Rýchlosť lopty
- Zapnutie zrýchlenia lopty pri odrazoch

---

💡 **Hlavná myšlienka:**  
Kód kombinuje **analytickú geometriu, vektorovú fyziku a trigonometriu** pre realistické odrazy lopty. UI prvky umožňujú interaktívnu úpravu parametrov počas hry. Hra je **nezávislá na FPS** a umožňuje hladký pohyb.
