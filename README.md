# lorenzbot
Poloniex exchange trading bot

TO DO:
- Finish Telegram-triggered csv profit calculator
- Determine what is causing mismatch between calculated and executed order size
- Make csv profit calc ignore last group of buys without a sell for calculation
- Move balance/trade log verification to isolated function
- Multi-line Telegram message formatting
- Add MongoDB collection to store Telegram users
- Return weighted average from calc_limit_price()
- Test if program functions without defining global variables
- List out all variables used and formalize to clean up program
- Make boolean arguments into human-readable format
- Clean up arguments --> Make parent/child --> Make sure all conditions satisfied
- Add "shutdown" function that can be called anywhere instead of updater.stop() each time

LATER:
- Add argument for minimum loop time (loop_time_min)
- Add Poloniex coach?
- Add Telegram alerts when adjustments are made due to balance/trade amount issues

IF TIME:
- Add argument for product selection

NEEDS TESTING:

DONE:
- Add argument for trade amount
- Add argument for profit threshold
- Add argument for "live trading" with active API key/secret vs view-only
- Fix sell function
- Fix csv logging
- Add regular account balance check
- Fix log file naming
- Add check to make sure arguments passed to program aren't too extreme due to typo
- Add base_price to csv log
- Add function for loop time adjustment
- Test dynamic loop time
- Add check for sell completion and create new collection only after
- Add handling of situation where on sell not enough asks are available in depth=20
- Merge calc_trade_amount() and loop_time_dynamic()
- Add function for trade amount adjustment
- Add counting for buy and sell skips
- Add Telegram alerts
- Add handling for max trade limit
- Add check for minimum buy/sell amount
-- Buy = 0.0001USDT
-- Sell = 0.0001USDT
- Base csv name and renaming on collection cleaning
- Check is csv logging true before activating Telegram profit calculation