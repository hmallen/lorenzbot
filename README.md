# lorenzbot
Poloniex exchange trading bot

TO DO:
- Consider limiting buy amounts under certain circumstances
- /profit Telegram functions, but always returns 'No sell trades executed.'
- Make Telegram messages include more helpful information
-- /status: trade_usdt_remaining, trade_usdt_max, etc.
-- Trade alerts: trade_usdt_remaining
- Add Telegram alerts when adjustments are made due to balance/trade amount issues
- Add Telegram alerts when program exception occurs
- Clean up unnecessary logging output, especially for INFO level

LATER:
- "Cash out" profits to BTC (or whatever else)
- Allow verify_amounts() to increase trade_usdt_max
- Change diff to be relative to low ask actual ("Price Difference from Base")
- Implement more efficient handling for failure to create new MongoDB collection
- Return weighted average from calc_limit_price()
- Allow trade_usdt_max to be adjusted without stopping program
- Test if program functions without defining global variables
- List out all variables used and formalize to clean up program
- Make boolean arguments into human-readable format
- Clean up arguments --> Make parent/child --> Make sure all conditions satisfied
- Add "shutdown" function that can be called anywhere instead of updater.stop() each time
- Add argument for minimum loop time (loop_time_min)
- Add Poloniex coach?
- Make csv profit calc ignore last group of buys without a sell for calculation

IF TIME:
- Add argument for product selection
- Add MongoDB collection to store Telegram users

NEEDS TESTING:
- Determine what is causing mismatch between calculated and executed order size
- Handling of exception from Telegram send message timeout
- On Poloniex internal error, buy (and possibly sell) trades are still logged as if they were successful
- Multi-line Telegram message formatting (needs testing and improvement)

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
- Move balance/trade log verification to isolated function
- Fix Telegram-triggered csv profit calculator
- Integrate telegram_failures counter
- Fix failure to rebuy after sell due to lack of maximum trade value reset
-- Create "reset maxima" function to reset trade maximum values which may have been reduced during buy phase
- Telegram error/exception alerts
- Limit Telegram buy messages (by time?)
- Fix sells always being triggered on start (incorrect total str bought amount)
-- Collection retrieved on startup should be most recent but list returned not sorted
- Copy/rename most recent log files on program exit for easy access