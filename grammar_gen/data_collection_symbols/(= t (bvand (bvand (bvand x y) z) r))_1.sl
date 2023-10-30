(synth-fun skel ( (r Bool) (x Bool) (y Bool) (z Bool) (t Bool)  )  Bool    
          ((Start Bool (
		                                  (eq depth1 depth1)
		                                  (uneq depth1 depth1)
          ))
          (depth1 Bool (
                                            r
                                            x
                                            y
                                            z
                                            t
                                            const
                                            (bvand depth2 depth2)
                                            (bvxor depth2 depth2)
		                                  (bvsub depth2 depth2)
		                                  (bvor depth2 depth2)
		                                  (bvadd depth2 depth2)
          ))
          (depth2 Bool (
                                            r
                                            x
                                            y
                                            z
                                            t
                                            (bvand depth3 depth3)
                                            (bvxor depth3 depth3)
		                                  (bvsub depth3 depth3)
		                                  (bvor depth3 depth3)
		                                  (bvadd depth3 depth3)
		                                  
          ))
          (depth3 Bool (
                                            r
                                            x
                                            y
                                            z
                                            t
		                                  (bvand depth4 depth4)
                                            (bvxor depth4 depth4)
		                                  (bvsub depth4 depth4)
		                                  (bvor depth4 depth4)
		                                  (bvadd depth4 depth4)
          ))
          (depth4 Bool (
                                            r
                                            x
                                            y
                                            z
                                            t
          )))
)
