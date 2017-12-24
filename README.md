# lorenzbot
Poloniex exchange trading bot (Currently only for STRUSDT market)

To use:
1) In the config folder, you'll find example ini config files for Poloniex and Telegram. Create configs using your API information for each.
2) Command line options need clean-up, but you can find all the options with 'python lorenzbot.py -h'
3) If Telegram setup and activated, connect to bot using '/connect'
4) Telegram will alert on events and exceptions. Other commands include '/status' and '/profit'
5) If you use '--withdraw' option, it will send to MY Stellar Lumens wallet unless you change the address at the top of 'lorenzbot.py'

TO DO:
- "Logger object has no attribute: critical"
- Buy skip counter no longer increments
- Look into 2 buys being made back-to-back on first run
- After sell, Telegram sell message is sent twice
- No Telegram withdraw message is sent
- Verify proper order of dynamic amount calculation to prevent hanging/missed trades
- Add projected STR profit if in accumulate mode
- Removed view-only API keys and must restore if required
- Verify calculation of profit (seems wrong)
- Tradable USDT balance is slightly below expected (noticed in accumulate mode)
- Determine minimum withdraw amount and make sure check is implemented before attempt
- Make sure no conflict between accumulate and withdraw mode (and that they work together)
- Merge config file into unified config
- Make exception log include more information (traceback, time, etc.)
-- /status: trade_usdt_remaining, trade_usdt_max, etc.
-- Trade alerts: trade_usdt_remaining
- Telegram command to retrieve most recent exception (from recent exception log)
- Test if program functions without defining global variables
- Change Telegram message to use list/dict of variables and loop to create string or send multiple lines
- Clean up unnecessary logging output, especially for INFO level
-- Move INFO level to bottom of main loop and improve order

LATER:
- For dynamic loop, reduce if either below buy target or approaching sell target
- Gather info on minimum trade total automatically somehow?
- Major error with sell processing (when available str < calc_trade_totals('bought') [following manual withdraw]) ****
- Add Telegram alerts when adjustments are made due to balance/trade amount issues
- Use Telegram chat rather than individual user alerts?
- Add Telegram inline buttons to increase functionality and user choice in data retrieved
- Use Telegram built-in restricted access for users (https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator)
-- USDT balance minus remaining trade allotment (trigger increase of max?)
- Implement more efficient handling for failure to create new MongoDB collection
- Return weighted average from calc_limit_price()
- List out all variables used and formalize to clean up program
- Make boolean arguments into human-readable format
- Clean up arguments --> Make parent/child --> Make sure all conditions satisfied
- Add "shutdown" function that can be called anywhere instead of updater.stop() each time
- Make csv profit calc ignore last group of buys without a sell for calculation

IF TIME:
- "Cash out" profits to BTC (or whatever else)
- Test on other markets (ex. 'BTC_STR')
- Move major functions to library in object-oriented setup
- Add argument for product selection
- Add MongoDB collection to store Telegram users
- Python emoji module with Telegram messages
- Remove loop delay almost entirely, replacing with constant monitoring of real-time websocket order book
- Add Telegram chat to output all exceptions, errors, etc.?
- Consider reimplementing buy_threshold to ensure base price usefully reduced
- Add argument for minimum loop time (loop_time_min)?
- Add Poloniex coach?

NEEDS TESTING:
- Add some form of "heartbeat" for verification of program run status
- Fix csv profit calculation to work with "accumulate" mode
- Add max sell amount that is ~5%? less than total bought to "accumulate" trade currency
- Catch ALL exceptions with logger...some going completely uncaught/unhandled ****
- On Poloniex internal error, buy (and possibly sell) trades are still logged as if they were successful
- Multi-line Telegram message formatting (needs improvement)
- Handle Telegram timeout exception
- Telegram error/exception alerts
- Very rarely, trades < 0.0001USDT total are still attempted, but exception is handled properly

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
- Add price difference from target to Telegram messages
- Determine what causes trade_usdt_remaining to be adjusted to negative value on startup
-- Has to do with resetting amount to 98% of total when insufficient balance encountered?
-- Also, mismatch between calculated and executed order size?
- /profit Telegram functions, but always returns 'No sell trades executed.'
- No profit message sent
- Add date/time and anything else useful to exception log
- Withdraw profit to STR address
- Program went INSANE when API IP restrictions enabled from site
-- Fixed by adding AWS elastic ip to whitelist on site
- Add file to store users connected to Telegram and reconnect on restart
- Make loop time ~30 sec if approaching sell point
- Fix trade execution to work with increased trade minimum of $0.50
- Set initial trade amount to trade total of ~$0.50 based on current conditions
- Fix trade amount calculation to work with increased trade minimum of $0.50
- Reference stored Telegram users for heartbeat timeout alert messages
- Delete all API keys, generate new, and make Github repository public

RESOURCES:
- Exception Handling:
https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python
