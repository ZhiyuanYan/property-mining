(synth-fun skel ()  Bool    
          ((Start Bool (
		                                  (eq depth1 depth1)
		                                  (uneq depth1 depth1)
          ))
          (depth1 Bool (
                                            variable
                                            const
                                            (eq depth2 depth2)
                                            (uneq depth2 depth2)
                                            (bvand depth2 depth2)
		                                    (bvsub depth2 depth2)
		                                    (bvor depth2 depth2)
          ))
          (depth2 Bool (
                                            variable
                                            const
		                                    (eq depth3 depth3)
                                            (uneq depth3 depth3)
                                            (bvand depth3 depth3)
		                                    (bvsub depth3 depth3)
		                                    (bvor depth3 depth3)
		                                  
          ))
          (depth3 Bool (
                                            variable
                                            const
		                                    (eq depth4 depth4)
                                            (uneq depth4 depth4)
		                                    (bvand depth4 depth4)
		                                    (bvsub depth4 depth4)
		                                    (bvor depth4 depth4)
          ))
          (depth4 Bool (
                                            variable
                                            const
          )))
)
