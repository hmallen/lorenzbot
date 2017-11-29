coll_names = ['11282017_191207', '11282017_200516', '11272017_184825', '11282017_191258']
print('coll_names: ' + str(coll_names))

print(type(coll_names[0]))

coll_names_alt = coll_names
coll_names_alt.sort()
print('coll_names_alt.sort(): ' + str(coll_names_alt))

for name in coll_names:
    name = int(name)
    #print(name)

print(type(coll_names[0]))

for x in range(0, len(coll_names)):
    coll_names[x] = int(coll_names[x])
    #print(coll_names[x])

print(type(coll_names[0]))

coll_names_sorted = coll_names.sort()
print('coll_names_sorted: ' + str(coll_names_sorted))
print('coll_names.sort(): ' + str(coll_names))
