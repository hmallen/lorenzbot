x = 1
y = 2
z = 3

test_list = []

test_list.append(x)
test_list.append(y)
test_list.append(z)

print(test_list)

item_index = test_list.index(1)
print(item_index)
item_index = test_list.index(2)
print(item_index)
item_index = test_list.index(3)
print(item_index)
#item_index = test_list.index(4)
#print(item_index)

item_count = test_list.count(1)
print(item_count)
item_count = test_list.count(4)
print(item_count)

if item_count > 0:
    print('YES')
else:
    print('NO')
