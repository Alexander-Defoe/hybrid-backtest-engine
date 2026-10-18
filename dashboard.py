"""A small web dashboard for the backtest engine.

Run it with:   python dashboard.py
Then open:     http://127.0.0.1:5000

Settings can be changed in the browser and the simulation re-runs immediately. Every
result is shown twice: over the period the settings were chosen on, and over a later
period the settings never saw. Only the second one is evidence of anything.
"""

import json
import logging

from flask import Flask, jsonify, render_template, request

from src.experiment import MarketData, build_signals, evaluate_period, DEFAULT_TRAIN_FRACTION

app = Flask(__name__)
# Picks up edits to the page without needing a restart
app.config['TEMPLATES_AUTO_RELOAD'] = True

logging.basicConfig(level=logging.WARNING)

with open('config.json', 'r') as file:
    BASE_CONFIG = json.load(file)

# Loaded once at startup and reused for every request, since the prices never change
MARKET = None


def get_market():
    global MARKET
    if MARKET is None:
        MARKET = MarketData(BASE_CONFIG)
    return MARKET


def config_from_request(args):
    """Overlays any settings passed from the browser onto the ones in config.json."""
    strategy = BASE_CONFIG['strategy'].copy()
    risk = BASE_CONFIG['risk_management'].copy()

    for key, cast in [('macd_fast', int), ('macd_slow', int), ('rsi_window', int),
                      ('rsi_overbought', float), ('sma_macro_window', int)]:
        if key in args:
            strategy[key] = cast(args[key])

    for key in ['stop_loss_percentage', 'target_percentage', 'commission_rate',
                'slippage_rate', 'target_risk']:
        if key in args:
            risk[key] = float(args[key])

    return strategy, risk


@app.route('/')
def index():
    market = get_market()
    return render_template(
        'dashboard.html',
        defaults={**BASE_CONFIG['strategy'], **BASE_CONFIG['risk_management']},
        symbols=market.symbols,
        initial_cash=market.initial_cash,
        first_date=market.dates[0],
        last_date=market.dates[-1],
        total_days=market.rows,
        train_fraction=DEFAULT_TRAIN_FRACTION,
        # The first result is baked into the page so it draws immediately, with no round trip
        initial=backtest(request.args),
    )


def backtest(args):
    market = get_market()
    strategy_config, risk_config = config_from_request(args)

    train_fraction = float(args.get('train_fraction', DEFAULT_TRAIN_FRACTION))
    split = market.split_at(train_fraction)

    signal_data = build_signals(market, strategy_config)

    trained = evaluate_period(market, signal_data, risk_config, 0, split)
    unseen = evaluate_period(market, signal_data, risk_config, split, market.rows)
    full = evaluate_period(market, signal_data, risk_config, 0, market.rows)

    return {
        'trained': trained,
        'unseen': unseen,
        'full': full,
        'split_index': split,
        'settings': {**strategy_config, **risk_config},
        'symbols': market.symbols,
        'initial_cash': market.initial_cash,
    }


@app.route('/api/backtest')
def api_backtest():
    return jsonify(backtest(request.args))


if __name__ == '__main__':
    print("Loading market data...")
    get_market()
    print("Dashboard running at http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
