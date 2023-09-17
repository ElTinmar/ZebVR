- separate process that run in an infinite loop until told to terminate   
- shared memory mechanism : queue, pipes, sockets, sharedctypes array, shared memory file, ... 
- (packing or serializing) / (unpacking or deserializing) the data 
- several sender for one receiver or several receivers for one sender:  
    - senders must dispatch (load balancing) or copy the data to all receivers
    - receivers must poll/select incoming data from all senders
- write/read directly into/from buffers to avoid copying the data around
    