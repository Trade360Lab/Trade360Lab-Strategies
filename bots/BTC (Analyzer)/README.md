<div align="center">

# BTC Daily Forecast Bot

**Simple ML-based crypto market outlook bot**
*Build. Test. Explore.*

</div>

---

## 📌 Overview

BTC Daily Forecast Bot — это минималистичный ML-информатор, который:

* загружает свежие данные BTC/USDT с Binance
* строит фичи (индикаторы, волатильность, тренд)
* прогоняет обученную модель (XGBoost)
* выдаёт вероятности:

  * 📈 UP
  * 📉 DOWN
  * 🤷 UNSURE
* определяет:

  * фазу рынка
  * волатильность
  * моментум
* отправляет тебе отчёт (в консоль или Telegram)

👉 Это **не торговый бот**, а **инструмент анализа рынка**.

---

## ⚙️ Project Structure

```bash
btc_daily_bot/
├── artifacts/
│   ├── model.pkl
│   ├── feature_columns.json
│   ├── model_meta.json
│   └── training_config.json
├── binance_loader.py
├── predictor.py
├── reporter.py
├── run_daily_bot.py
├── requirements.txt
└── Dockerfile
```

---

## 🚀 Installation

### 1. Clone repository

```bash
git clone https://github.com/your-repo/btc_daily_bot.git
cd btc_daily_bot
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run locally

```bash
python run_daily_bot.py
```

Ты получишь отчёт примерно такого вида:

```text
BTC Daily Outlook

Symbol: BTCUSDT
Timeframe: 1H

Probabilities:
UP: 41%
DOWN: 27%
UNSURE: 32%

Decision: UP
Confidence: 14%

Market:
- Phase: bullish
- Volatility: normal
- Momentum: positive
```

---

## 🤖 Telegram Integration

### 1. Создать бота

* Открыть Telegram → @BotFather
* Выполнить: `/start` → `/newbot`
* Получить `BOT_TOKEN`

---

### 2. Узнать chat_id

Написать боту любое сообщение и открыть:

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

Найти `chat.id`

---

### 3. Запуск с Telegram

#### Linux / Mac:

```bash
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id

python run_daily_bot.py
```

#### Windows (PowerShell):

```powershell
$env:TELEGRAM_BOT_TOKEN="your_token"
$env:TELEGRAM_CHAT_ID="your_chat_id"

python run_daily_bot.py
```

---

## 🐳 Run with Docker

### 1. Build image

```bash
docker build -t btc-daily-bot .
```

---

### 2. Run container

```bash
docker run --rm btc-daily-bot
```

---

### 3. Run with Telegram

```bash
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  btc-daily-bot
```

---

## ⏰ Daily запуск (cron)

Запускать каждое утро:

```bash
0 8 * * * /usr/bin/docker run --rm btc-daily-bot
```

---

## 🧠 How it works

```text
Binance API → Features → ML Model → Probabilities → Decision Layer → Report
```

---

## ⚠️ Important Notes

* ❗ Бот не даёт торговых сигналов
* ❗ Не является финансовой рекомендацией
* ❗ Используется только для анализа

---

## 🔮 Future Improvements

* Walk-forward retraining
* Optuna hyperparameter tuning
* Web UI / API
* Integration with trading engine

---

<div align="center">

**Build. Test. Explore**

</div>
