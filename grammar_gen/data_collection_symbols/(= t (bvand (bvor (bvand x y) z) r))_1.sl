(synth-fun skel ( (s Bool) (x Bool) (y Bool) (z Bool) (t Bool)  )  Bool    
          ((Start Bool (
		                                  (eq depth1 depth1)
		                                  (uneq depth1)
          ))
          (depth1 Bool (
                                            s
                                            x
                                            y
                                            z
                                            t
                                            (bvand depth2 depth2)
		                                  (bvsub depth2 depth2)
		                                  (bvor depth2 depth2)
		                                  (bvadd depth2 depth2)
          ))
          (depth2 Bool (
                                            s
                                            x
                                            y
                                            z
                                            t
                                            (bvand depth2 depth2)
		                                  (bvsub depth2)
		                                  (bvor depth2 depth2)
		                                  (bvadd depth2 depth2)
		                                  
          ))
          (depth3 Bool (
                                            s
                                            x
                                            y
                                            z
                                            t
		                                  (bvand depth4 depth4)
		                                  (bvsub depth4)
		                                  (bvor depth4 depth4)
		                                  (bvadd depth4 depth4)
          ))
          (depth4 Bool (
                                            s
                                            x
                                            y
                                            z
                                            t
          )))
)
