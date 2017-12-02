# lorenzbot
Poloniex exchange trading bot

TO DO:
- "Cash out" profits to BTC (or whatever else)
-- OR add max sell amount that is ~5%? less than total bought to "accumulate" trade currency
- Make exception log include more information (traceback, time, etc.)
- Remove redundant logging output (ex. DEBUG when INFO already present)
- Consider reimplementing buy_threshold to ensure base price usefully reduced
- Standardize Telegram message string creation (consolidate?)
- Change Telegram message to use list/dict of variables and loop to create string or send multiple lines
- Delete all API keys, generate new, and make Github repository public
- Telegram command to retrieve most recent exception (from recent exception log)
- Consider limiting buy amounts under certain circumstances (?)
- /profit Telegram functions, but always returns 'No sell trades executed.'
- Make Telegram messages include more helpful information
-- /status: trade_usdt_remaining, trade_usdt_max, etc.
-- Simplify Telegram messages for clarity
-- Trade alerts: trade_usdt_remaining
- Clean up unnecessary logging output, especially for INFO level

LATER:
- Major error with sell processing (when available str < calc_trade_totals('bought') [following manual withdraw]) ****
- Very rarely, trades < 0.0001USDT total are still attempted, but exception is handled properly
- Add Telegram alerts when adjustments are made due to balance/trade amount issues
- Use Telegram chat rather than individual user alerts?
- Add Telegram chat to output all exceptions, errors, etc.?
- Add Telegram inline buttons to increase functionality and user choice in data retrieved
- Use Telegram built-in restricted access for users (https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator)
- Allow verify_amounts() to increase trade_usdt_max
-- USDT balance minus remaining trade allotment (trigger increase of max?)
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
- Test on other markets (ex. 'BTC_STR')
- Move major functions to library in object-oriented setup
- Add argument for product selection
- Add MongoDB collection to store Telegram users
- Python emoji module with Telegram messages
- Remove loop delay almost entirely, replacing with constant monitoring of real-time websocket order book

NEEDS TESTING:
- Add price difference from target to Telegram messages
- Catch ALL exceptions with logger...some going completely uncaught/unhandled ****
- On Poloniex internal error, buy (and possibly sell) trades are still logged as if they were successful
- Multi-line Telegram message formatting (needs testing and improvement)
- Handle Telegram timeout exception
- Telegram error/exception alerts
- Determine what causes trade_usdt_remaining to be adjusted to negative value on startup
-- Has to do with resetting amount to 98% of total when insufficient balance encountered?
-- Also, mismatch between calculated and executed order size?

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
- Check if csv logging true before activating Telegram profit calculation
- Move balance/trade log verification to isolated function
- Fix Telegram-triggered csv profit calculator
- Integrate telegram_failures counter
- Fix failure to rebuy after sell due to lack of maximum trade value reset
-- Create "reset maxima" function to reset trade maximum values which may have been reduced during buy phase
- Limit Telegram buy messages (by time?)
- Fix sells always being triggered on start (incorrect total str bought amount)
-- Collection retrieved on startup should be most recent but list returned not sorted
- Copy/rename most recent log files on program exit for easy access
- Average trade_amount per buy
- Move config files to new directory and create example files
- Add more data to csv profit calculation return dictionary
- Move "Price Difference from Base" so that it's only called once on INFO level
- Add "Price Difference from Target"

RESOURCES:
- Exception Handling:
https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python