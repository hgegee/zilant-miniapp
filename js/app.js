/* ZILANT RENTAL — Telegram Mini App */

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.setHeaderColor("#141414");
  tg.setBackgroundColor("#141414");
  try {
    tg.disableVerticalSwipes?.();
  } catch (_) {}
}

// ─── State ───
let state = {
  brand: "Все",
  body: "Все",
  carId: CARS[3]?.id || CARS[0].id,
  from: "",
  to: "",
  name: "",
  phone: "",
  driver: false,
  section: "fleet",
};

function todayPlus(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

state.from = todayPlus(1);
state.to = todayPlus(3);

// ─── Helpers ───
function getCar(id) {
  return CARS.find((c) => c.id === id) || CARS[0];
}

function filteredCars() {
  return CARS.filter((c) => {
    if (state.brand !== "Все" && c.brand !== state.brand) return false;
    if (state.body !== "Все" && c.body !== state.body) return false;
    return true;
  });
}

function brandCount(b) {
  return b === "Все" ? CARS.length : CARS.filter((c) => c.brand === b).length;
}

function calcTotal() {
  const car = getCar(state.carId);
  const days = calcDays(state.from, state.to);
  const disc = calcDiscount(days);
  const base = car.price * days;
  const discAmt = Math.round(base * disc);
  const driverCost = state.driver ? 5000 * days : 0;
  return { days, base, disc, discAmt, driverCost, total: base - discAmt + driverCost };
}

// ─── Navigation ───
function showSection(id) {
  state.section = id;
  document.querySelectorAll(".section").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((el) => el.classList.remove("active"));
  const sec = document.getElementById("sec-" + id);
  const tab = document.querySelector(`.tab[data-section="${id}"]`);
  if (sec) sec.classList.add("active");
  if (tab) tab.classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
  updateMainButton();
}

// ─── Render Fleet ───
function renderFilters() {
  const brandsEl = document.getElementById("brand-filters");
  const bodiesEl = document.getElementById("body-filters");
  brandsEl.innerHTML = ["Все", ...BRANDS]
    .map(
      (b) =>
        `<button class="chip ${state.brand === b ? "active" : ""}" data-brand="${b}">${b}<span class="count">${brandCount(b)}</span></button>`
    )
    .join("");
  bodiesEl.innerHTML = ["Все", ...BODIES]
    .map(
      (b) =>
        `<button class="chip ${state.body === b ? "active" : ""}" data-body="${b}">${b}</button>`
    )
    .join("");

  brandsEl.querySelectorAll("[data-brand]").forEach((btn) => {
    btn.onclick = () => {
      state.brand = btn.dataset.brand;
      renderFilters();
      renderCars();
    };
  });
  bodiesEl.querySelectorAll("[data-body]").forEach((btn) => {
    btn.onclick = () => {
      state.body = btn.dataset.body;
      renderFilters();
      renderCars();
    };
  });
}

function renderCars() {
  const list = filteredCars();
  const el = document.getElementById("cars-list");
  if (!list.length) {
    el.innerHTML = `<div class="empty">Нет машин по фильтрам.<br><button class="btn-sm" style="margin-top:12px" id="reset-filters">Сбросить</button></div>`;
    document.getElementById("reset-filters")?.addEventListener("click", () => {
      state.brand = "Все";
      state.body = "Все";
      renderFilters();
      renderCars();
    });
    return;
  }
  el.innerHTML = list
    .map((c) => {
      const tag = c.tag ? `<span class="car-tag">${c.tag}</span>` : "";
      return `
      <article class="car-card" data-id="${c.id}">
        <div class="car-card-top">
          <div>
            <div class="car-brand">${c.brand}</div>
            <div class="car-model">${c.model}</div>
          </div>
          ${tag}
        </div>
        <div class="car-specs">${c.body} · ${c.specs}</div>
        <div class="car-bottom">
          <div class="car-price">${formatPrice(c.price)} ₽ <span>/ сут</span></div>
          <button class="btn-sm" data-book="${c.id}">Выбрать</button>
        </div>
      </article>`;
    })
    .join("");

  el.querySelectorAll("[data-book]").forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      state.carId = btn.dataset.book;
      showSection("booking");
      renderBookingForm();
    };
  });
  el.querySelectorAll(".car-card").forEach((card) => {
    card.onclick = () => {
      state.carId = card.dataset.id;
      showSection("booking");
      renderBookingForm();
    };
  });
}

// ─── Booking ───
function renderBookingForm() {
  const car = getCar(state.carId);
  const sel = document.getElementById("book-car");
  sel.innerHTML = CARS.map(
    (c) =>
      `<option value="${c.id}" ${c.id === state.carId ? "selected" : ""}>${carName(c)} — от ${formatPrice(c.price)} ₽</option>`
  ).join("");

  document.getElementById("book-from").value = state.from;
  document.getElementById("book-to").value = state.to;
  document.getElementById("book-to").min = state.from;
  document.getElementById("book-name").value = state.name;
  document.getElementById("book-phone").value = state.phone;
  updateDriverUI();
  updateSummary();
}

function updateDriverUI() {
  const box = document.getElementById("driver-check");
  box.classList.toggle("on", state.driver);
}

function updateSummary() {
  const { days, base, disc, discAmt, driverCost, total } = calcTotal();
  const car = getCar(state.carId);
  let html = `
    <div class="summary-row"><span>${carName(car)}</span><span>${formatPrice(car.price)} ₽/сут</span></div>
    <div class="summary-row"><span>Срок</span><span>${days} сут.</span></div>
    <div class="summary-row"><span>База</span><span>${formatPrice(base)} ₽</span></div>`;
  if (disc > 0) {
    html += `<div class="summary-row"><span>Скидка ${Math.round(disc * 100)}%</span><span>−${formatPrice(discAmt)} ₽</span></div>`;
  }
  if (driverCost > 0) {
    html += `<div class="summary-row"><span>Водитель</span><span>+${formatPrice(driverCost)} ₽</span></div>`;
  }
  html += `<div class="summary-row total"><span>Итого</span><span class="val">${formatPrice(total)} ₽</span></div>`;
  document.getElementById("book-summary").innerHTML = html;
  updateMainButton();
}

function validateBooking() {
  const errors = {};
  if (!state.carId) errors.car = "Выберите авто";
  if (!state.from) errors.from = "Укажите дату";
  const days = calcDays(state.from, state.to);
  if (days < 1) errors.to = "Возврат позже получения";
  if ((state.name || "").trim().length < 2) errors.name = "Укажите имя";
  const digits = (state.phone || "").replace(/\D/g, "");
  if (digits.length < 10) errors.phone = "Укажите телефон";
  return errors;
}

function showErrors(errors) {
  ["car", "from", "to", "name", "phone"].forEach((k) => {
    const el = document.getElementById("err-" + k);
    if (el) el.textContent = errors[k] || "";
  });
}

function formatPhone(raw) {
  let d = raw.replace(/\D/g, "");
  if (d.startsWith("8")) d = "7" + d.slice(1);
  if (!d.startsWith("7")) d = "7" + d;
  d = d.slice(0, 11);
  const p = d.slice(1);
  let out = "+7";
  if (p.length) out += " (" + p.slice(0, 3);
  if (p.length >= 3) out += ")";
  if (p.length > 3) out += " " + p.slice(3, 6);
  if (p.length > 6) out += "-" + p.slice(6, 8);
  if (p.length > 8) out += "-" + p.slice(8, 10);
  return out;
}

function submitBooking() {
  const errors = validateBooking();
  showErrors(errors);
  if (Object.keys(errors).length) {
    if (tg) tg.HapticFeedback?.notificationOccurred("error");
    return;
  }
  const car = getCar(state.carId);
  const { days, total } = calcTotal();
  const payload = {
    type: "booking",
    carId: state.carId,
    carName: carName(car),
    from: state.from,
    to: state.to,
    days,
    name: state.name.trim(),
    phone: state.phone,
    driver: state.driver,
    total,
  };

  if (tg && tg.sendData) {
    tg.sendData(JSON.stringify(payload));
    if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
  } else {
    // Outside Telegram — show success screen
    document.getElementById("success-text").textContent =
      `${payload.name}, заявка на ${payload.carName} (${days} сут.) принята. Мы перезвоним в течение 15 минут.`;
    document.getElementById("success").classList.add("show");
  }
}

// ─── MainButton ───
function updateMainButton() {
  if (!tg || !tg.MainButton) return;
  if (state.section === "booking") {
    const { total, days } = calcTotal();
    tg.MainButton.setText(days > 0 ? `Отправить · ${formatPrice(total)} ₽` : "Отправить заявку");
    tg.MainButton.show();
    tg.MainButton.enable();
    tg.MainButton.onClick(submitBooking);
  } else if (state.section === "fleet") {
    tg.MainButton.setText("Забронировать");
    tg.MainButton.show();
    tg.MainButton.onClick(() => {
      showSection("booking");
      renderBookingForm();
    });
  } else {
    tg.MainButton.hide();
  }
}

// ─── Other sections ───
function renderTariffs() {
  document.getElementById("plans-list").innerHTML = PLANS.map(
    (p) => `
    <div class="plan-card ${p.highlight ? "highlight" : ""}">
      <div class="plan-term">${p.term}</div>
      <div class="plan-discount">${p.discount}</div>
      <div class="plan-note">${p.note}</div>
    </div>`
  ).join("");
}

function renderConditions(tab = "driver") {
  document.querySelectorAll(".cond-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.cond === tab);
  });
  const items = CONDITIONS[tab] || [];
  document.getElementById("cond-list").innerHTML = items
    .map(
      (i) => `
    <div class="cond-item">
      <h4>${i.t}</h4>
      <p>${i.d}</p>
    </div>`
    )
    .join("");
}

function renderAdvantages() {
  document.getElementById("stats").innerHTML = `
    <div class="stat-card"><div class="stat-val">23</div><div class="stat-label">автомобиля</div></div>
    <div class="stat-card"><div class="stat-val">9</div><div class="stat-label">марок</div></div>
    <div class="stat-card"><div class="stat-val">15 мин</div><div class="stat-label">оформление</div></div>
    <div class="stat-card"><div class="stat-val">24/7</div><div class="stat-label">подача</div></div>`;
  document.getElementById("adv-list").innerHTML = ADVANTAGES.map(
    (a) => `
    <div class="adv-item">
      <h4>${a.t}</h4>
      <p>${a.d}</p>
    </div>`
  ).join("");
}

function renderFaq() {
  document.getElementById("faq-list").innerHTML = FAQ.map(
    (f, i) => `
    <div class="faq-item" data-i="${i}">
      <button class="faq-q">${f.q}</button>
      <div class="faq-a">${f.a}</div>
    </div>`
  ).join("");
  document.querySelectorAll(".faq-item").forEach((item) => {
    item.querySelector(".faq-q").onclick = () => {
      item.classList.toggle("open");
    };
  });
}

function renderContacts() {
  document.getElementById("contacts-list").innerHTML = `
    <div class="contact-card">
      <div class="contact-label">Телефон</div>
      <div class="contact-val"><a href="tel:+78430000000">${PHONE}</a></div>
    </div>
    <div class="contact-card">
      <div class="contact-label">Режим работы</div>
      <div class="contact-val">Ежедневно, 24/7</div>
    </div>
    <div class="contact-card">
      <div class="contact-label">Город</div>
      <div class="contact-val">Казань, Татарстан</div>
    </div>
    <div class="contact-card">
      <div class="contact-label">Мессенджеры</div>
      <div class="contact-val">Telegram · WhatsApp</div>
    </div>`;
}

// ─── Init ───
document.addEventListener("DOMContentLoaded", () => {
  // Tabs
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.onclick = () => {
      const id = tab.dataset.section;
      showSection(id);
      if (id === "fleet") {
        renderFilters();
        renderCars();
      }
      if (id === "booking") renderBookingForm();
      if (id === "tariffs") renderTariffs();
      if (id === "conditions") renderConditions("driver");
      if (id === "advantages") renderAdvantages();
      if (id === "faq") renderFaq();
      if (id === "contacts") renderContacts();
    };
  });

  // Condition tabs
  document.querySelectorAll(".cond-tab").forEach((t) => {
    t.onclick = () => renderConditions(t.dataset.cond);
  });

  // Booking inputs
  document.getElementById("book-car").onchange = (e) => {
    state.carId = e.target.value;
    updateSummary();
  };
  document.getElementById("book-from").onchange = (e) => {
    state.from = e.target.value;
    document.getElementById("book-to").min = state.from;
    updateSummary();
  };
  document.getElementById("book-to").onchange = (e) => {
    state.to = e.target.value;
    updateSummary();
  };
  document.getElementById("book-name").oninput = (e) => {
    state.name = e.target.value;
  };
  document.getElementById("book-phone").oninput = (e) => {
    const formatted = formatPhone(e.target.value);
    state.phone = formatted;
    e.target.value = formatted;
  };
  document.getElementById("driver-row").onclick = () => {
    state.driver = !state.driver;
    updateDriverUI();
    updateSummary();
  };

  // Fallback bottom button
  document.getElementById("fallback-submit")?.addEventListener("click", () => {
    if (state.section === "booking") submitBooking();
    else {
      showSection("booking");
      renderBookingForm();
    }
  });

  document.getElementById("success-close")?.addEventListener("click", () => {
    document.getElementById("success").classList.remove("show");
    showSection("fleet");
  });

  // Initial
  renderFilters();
  renderCars();
  renderBookingForm();
  renderTariffs();
  renderConditions();
  renderAdvantages();
  renderFaq();
  renderContacts();
  showSection("fleet");
  updateMainButton();
});
