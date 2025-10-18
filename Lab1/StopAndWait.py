import hashlib

data = "Hello world11"
package_data_size = 2

def msg_to_packeges(data):

    packages = []

    for i in range(0,len(data), package_data_size):
        #print(data[i:i+package_data_size])
        package = {
            "seq_num": 0,
            "hash_sum": hashlib.sha256(b"{data[i:i+package_data_size]}").hexdigest(),
            "data": data[i:i+package_data_size]
        }

        packages.append(package)

    return packages


print(msg_to_packeges(data))





#packet1 = {
##    "seq_number": 1,
#    "hash_sum": hashlib.sha256(b"{data1}").hexdigest(),
#    "data": data1
#}

#packet2 = {
#    "seq_number": 1,
#    "hash_sum": hashlib.sha256(b"{data2}").hexdigest(),
#    "data": data1
#}



#print([packet1, packet2])