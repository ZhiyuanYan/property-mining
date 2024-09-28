(synth-fun skel ( (x[7:0] Bool) (y[7:0] Bool)  )  Bool    
          ((Start Bool (
		                                  (eq depth1 depth1)
		                                  (bvule depth1 depth1)
          ))
          (depth1 Bool (
                                            x[7:0]
                                            y[7:0]
                                            const
                                            (eq depth2 depth2)
                                            (bvule depth2 depth2)
                                            (bvand depth2 depth2)
		                                    (bvsub depth2 depth2)
		                                    (bvor depth2 depth2)
                                            (bvadd depth2 depth2)
          ))
          (depth2 Bool (
                                            x[7:0]
                                            y[7:0]
                                            const
		                                    (eq depth3 depth3)
                                            (bvule depth3 depth3)
                                            (bvand depth3 depth3)
		                                    (bvsub depth3 depth3)
		                                    (bvor depth3 depth3)
                                            (bvadd depth3 depth3)	                                  
          ))
          (depth3 Bool (
                                            x[7:0]
                                            y[7:0]
          )))
)
