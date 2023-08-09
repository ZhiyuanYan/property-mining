(synth-fun skel ()  Bool    
          ((Start Bool (
		                                  (eq depth1 depth1)
		                                  (uneq depth1)
          ))
          (depth1 Bool (
                                            variable
                                            (bvand depth2 depth2)
		                                  (bvsub depth2 depth2)
		                                  (bvor depth2 depth2)
		                                  (bvadd depth2 depth2)
          ))
          (depth2 Bool (
                                            variable
                                            (bvand depth2 depth2)
		                                  (bvsub depth2)
		                                  (bvor depth2 depth2)
		                                  (bvadd depth2 depth2)
		                                  
          ))
          (depth3 Bool (
                                            variable
		                                  (bvand depth4 depth4)
		                                  (bvsub depth4)
		                                  (bvor depth4 depth4)
		                                  (bvadd depth4 depth4)
          ))
          (depth4 Bool (
                                            variable
          )))
)
