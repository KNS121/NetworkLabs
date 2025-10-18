import hashlib
import time

data = "Hello worldaa"
package_data_size = 2


def CalculateHashSum(data):
    return hashlib.sha256(data.encode()).hexdigest()


def msg_to_packeges(data):

    packages = []

    for i in range(0,len(data), package_data_size):

        package_nubmer = (i//package_data_size)%2

        package = {
            "seq_num": package_nubmer,
            "hash_sum": CalculateHashSum(data[i:i+package_data_size]),
            "data": data[i:i+package_data_size]
        }

        packages.append(package)


    return packages


#print(msg_to_packeges(data))

#class Sender:

#    def __init__(self):
#        
#        self.check_ack = False
#        self.check_time = True


#    def send_package(package):
        
#        while 



def Sender(data):
    packages = msg_to_packeges(data)

    #package_index = 0

    for i in range(len(packages)):

        package = packages[i]
        check_package = False

        start_time = time.time()

        print(f"start_time {start_time}")

        timedelta = 2

        while (timedelta > 0.5):
            print(package)
            Reciever(package)            
            check_package = Reciever(package)
            timedelta = time.time() - start_time



def Reciever(package):
    check_hash_sum = False

    if CalculateHashSum(package["data"]) == package["hash_sum"] :
        check_hash_sum = True

    time.sleep(0.2)

    print(check_hash_sum)

    return check_hash_sum


Sender(data)





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