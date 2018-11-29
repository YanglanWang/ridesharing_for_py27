dis=dict()
dis[1]='2083.21004126'
dis[2]='2083.21004127'
dis[3]='2083.21004128'
dis[4]='2083.21004129'
f=open('test_dictionary','w')
# f.write(str(dis))
for key in dis.keys():
    f.write(str(key)+', ' + dis[key] + '\n')

f.close()
