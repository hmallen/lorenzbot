a = float(1)
b = float(0)

e_last = None

try:
    c = a / b
except Exception as e:
    e_last = e

if e_last:
    #print('Exception: ' + e_last)
    print('Exception: ' + str(e_last))
else:
    print('No exception.')

e_last = None

try:
    c = b / a
except Exception as e:
    e_last = e

if e_last:
    #print('Exception: ' + e_last)
    print('Exception: ' + str(e_last))
else:
    print('No exception.')
