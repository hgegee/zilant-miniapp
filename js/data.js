const CARS = [
  { id: "audi-a7", brand: "Audi", model: "A7", body: "Седан", price: 14000, specs: "Лифтбек · полный привод" },
  { id: "bmw-320d", brand: "BMW", model: "320d G20", body: "Седан", price: 9000, specs: "Дизель · задний привод" },
  { id: "bmw-530i", brand: "BMW", model: "530i G30", body: "Седан", price: 12000, specs: "Бензин · 252 л.с." },
  { id: "bmw-530d", brand: "BMW", model: "530d G30", body: "Седан", price: 13000, specs: "Дизель · xDrive" },
  { id: "bmw-530d-s2", brand: "BMW", model: "530d Stage 2", body: "Седан", price: 15000, tag: "Stage 2", specs: "Дизель · xDrive" },
  { id: "bmw-550d", brand: "BMW", model: "550d G30 Stage 1", body: "Седан", price: 18000, tag: "Stage 1", specs: "Дизель · xDrive" },
  { id: "bmw-740d", brand: "BMW", model: "740d G11", body: "Седан", price: 20000, specs: "Бизнес-класс · xDrive" },
  { id: "bmw-x3", brand: "BMW", model: "X3", body: "Внедорожник", price: 11000, specs: "Кроссовер · xDrive" },
  { id: "bmw-x5", brand: "BMW", model: "X5", body: "Внедорожник", price: 17000, specs: "Внедорожник · xDrive" },
  { id: "bentley-bentayga", brand: "Bentley", model: "Bentayga W12", body: "Внедорожник", price: 60000, tag: "W12", specs: "Внедорожник · 608 л.с." },
  { id: "bentley-continental", brand: "Bentley", model: "Continental", body: "Купе", price: 55000, specs: "Гран-туризмо · полный привод" },
  { id: "mb-cla250", brand: "Mercedes-Benz", model: "A250 4Matic Stage 1", body: "Седан", price: 11000, tag: "Stage 1", specs: "Бензин · 4Matic" },
  { id: "mb-gla45", brand: "Mercedes-Benz", model: "GLA45 AMG Edition 1", body: "Внедорожник", price: 16000, tag: "AMG", specs: "Кроссовер · 4Matic" },
  { id: "mb-e200c", brand: "Mercedes-Benz", model: "E200 Coupe", body: "Купе", price: 12000, specs: "Купе · задний привод" },
  { id: "mb-s350d", brand: "Mercedes-Benz", model: "S350d W222 AMG Facelift", body: "Седан", price: 22000, specs: "Представительский · 4Matic" },
  { id: "mb-g350d", brand: "Mercedes-Benz", model: "G350d 2021", body: "Внедорожник", price: 35000, tag: "2021", specs: "Внедорожник · полный привод" },
  { id: "mini-cabrio", brand: "Mini", model: "Cooper S Cabrio", body: "Кабриолет", price: 9000, specs: "Кабриолет · бензин" },
  { id: "mazda-6", brand: "Mazda", model: "6 2022", body: "Седан", price: 6500, specs: "Седан · бензин" },
  { id: "genesis-g80", brand: "Genesis", model: "G80", body: "Седан", price: 11000, specs: "Бизнес-седан · бензин" },
  { id: "lexus-es200", brand: "Lexus", model: "ES200", body: "Седан", price: 8000, specs: "Седан · бензин" },
  { id: "lexus-es250", brand: "Lexus", model: "ES250 2016/2021", body: "Седан", price: 9000, specs: "Седан · бензин" },
  { id: "toyota-v55", brand: "Toyota", model: "Camry V55", body: "Седан", price: 5000, specs: "Седан · бензин" },
  { id: "toyota-v70", brand: "Toyota", model: "Camry V70", body: "Седан", price: 6000, specs: "Седан · бензин" },
];

const BRANDS = ["Audi", "BMW", "Bentley", "Mercedes-Benz", "Genesis", "Lexus", "Mini", "Mazda", "Toyota"];
const BODIES = ["Седан", "Внедорожник", "Купе", "Кабриолет"];
const PHONE = "+7 (843) 000-00-00";

const PLANS = [
  { term: "1–2 суток", discount: "Базовая цена", note: "Минимальный срок аренды — 1 сутки", highlight: false },
  { term: "3–6 суток", discount: "−10%", note: "Скидка от базовой цены на весь срок", highlight: false },
  { term: "7–13 суток", discount: "−15%", note: "Бесплатная подача по Казани", highlight: true },
  { term: "От 14 суток", discount: "−25%", note: "Индивидуальные условия и замена авто", highlight: false },
];

const CONDITIONS = {
  driver: [
    { t: "Возраст от 23 лет", d: "Для Bentley и Mercedes G-класса — от 27 лет" },
    { t: "Стаж от 3 лет", d: "Водительское удостоверение категории B" },
    { t: "Два документа", d: "Паспорт РФ и водительское удостоверение" },
  ],
  money: [
    { t: "Залог от 20 000 ₽", d: "Возвращается в день сдачи автомобиля" },
    { t: "Оплата удобным способом", d: "Карта, перевод, наличные, безнал для юрлиц" },
    { t: "Пробег 300 км в сутки", d: "Сверх лимита — от 15 ₽ за километр" },
  ],
  service: [
    { t: "Подача по Казани", d: "Аэропорт, вокзал, отель или адрес клиента" },
    { t: "ОСАГО включено", d: "КАСКО — по запросу для любого автомобиля" },
    { t: "Полный бак", d: "Выдаём и принимаем с полным баком" },
  ],
};

const FAQ = [
  { q: "Какие документы нужны для аренды?", a: "Паспорт гражданина РФ и водительское удостоверение категории B. Для иностранных граждан — паспорт и международное удостоверение." },
  { q: "Можно ли взять машину без залога?", a: "Для постоянных клиентов и при аренде от 14 суток возможны условия без залога или со сниженным залогом. Уточните у менеджера." },
  { q: "Есть ли доставка автомобиля?", a: "Да. Подаём машину в любую точку Казани, в аэропорт и на вокзал. При аренде от 7 суток подача по городу бесплатная." },
  { q: "Можно ли выехать за пределы Казани?", a: "Да, поездки по Татарстану и соседним регионам разрешены. О выезде за пределы республики сообщите заранее." },
  { q: "Что если я верну машину позже?", a: "До 2 часов задержки — без доплаты при предупреждении. Далее — почасовая оплата или продление аренды." },
  { q: "Можно ли арендовать автомобиль с водителем?", a: "Да, на любой автомобиль из автопарка. Стоимость водителя — от 5 000 ₽ за сутки." },
];

const ADVANTAGES = [
  { t: "Выдача за 15 минут", d: "Договор, осмотр и ключи — без очередей." },
  { t: "Свежие автомобили", d: "Машины 2016–2022 годов, обслуживание у дилеров." },
  { t: "Подача 24/7", d: "Аэропорт, вокзал или отель." },
  { t: "Чистота", d: "Мойка и химчистка перед каждой выдачей." },
  { t: "Без скрытых платежей", d: "Цена в договоре = цена на сайте." },
  { t: "Поддержка в пути", d: "Личный менеджер на связи весь срок." },
];

function carName(c) {
  return `${c.brand} ${c.model}`;
}

function formatPrice(n) {
  return n.toLocaleString("ru-RU");
}

function calcDays(from, to) {
  const a = new Date(from);
  const b = new Date(to);
  if (isNaN(a) || isNaN(b) || b <= a) return 0;
  return Math.round((b - a) / 86400000);
}

function calcDiscount(days) {
  if (days >= 14) return 0.25;
  if (days >= 7) return 0.15;
  if (days >= 3) return 0.1;
  return 0;
}
