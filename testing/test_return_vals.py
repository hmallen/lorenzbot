def test_func():
    amt = 1000.123
    tot = 999.123

    return {'amount': amt, 'total': tot}


vals = test_func()
print(vals['amount'])
print(vals['total'])
