# lorenzbot
Poloniex exchange trading bot

TO DO:
- Add Telegram alerts
- List out all variables used and formalize to clean up program
- Make boolean arguments into human-readable format
- Clean up arguments --> Make parent/child --> Make sure all conditions satisfied

LATER:
- Add argument for minimum loop time (loop_time_min)
- Add Poloniex coach?

IF TIME:
- Add argument for product selection

NEEDS TESTING:
- Add handling for max trade limit

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