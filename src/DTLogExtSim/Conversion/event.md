corner2:
    - START - start
    - RETURN - TO REMOVE
    - TRANSFER - complete
    
station11:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete
    
station21:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station21_pass:
    - PASS - start
    - TRANSFER - complete  

station22:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station22_pass:
    - PASS - start
    - TRANSFER - complete  

splitter1: TO REMOVE
    - FORWARD
    - TRANSFER
    - RETURN
    
station31:
    - BLOCK - TO REMOVE
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station31_pass:
    - PASS - start
    - TRANSFER - complete  
    
station41:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station41_pass:
    - PASS - start
    - TRANSFER - complete  
    
station51:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station51_pass:
    - PASS - start
    - TRANSFER - complete  
    
station52:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station52_pass:
    - PASS - start
    - TRANSFER - complete  
    
splitter3: TO REMOVE
    - FORWARD
    - TRANSFER
    - RETURN
    
station61:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station61_pass:
    - PASS - start
    - TRANSFER - complete  
    
station71:
    - UNLOAD - TO REMOVE
    - LOAD - assign 
    - PASS - TO REMOVE (created another activity)
    - PROCESS - start 
    - FAIL - TO REMOVE
    - TRANSFER - complete

station71_pass:
    - PASS - start
    - TRANSFER - complete  
    
corner1:
    - TRANSFER
    - RETURN
    
splitter5: TO REMOVE
    - CHECKOUT - TO REMOVE
    - FINISH - COMPLETE
    - SCRAP - COMPLETE
    - FORWARD - TO REMOVE
    - RETURN - TO REMOVE
    - TRANSFER - TO REMOVE
    
splitter2: TO REMOVE
    - FORWARD
    - TRANSFER
    - RETURN
    
splitter4: TO REMOVE
    - FORWARD
    - TRANSFER
    - RETURN
