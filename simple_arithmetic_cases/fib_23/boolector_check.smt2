(define-fun assertion.0 ((|n| (_ BitVec 11)) (|i| (_ BitVec 11)) ) Bool (=> (= #b00010010110 ((_ extract 10 0) |n|)) (bvule (= (bvadd ((_ extract 10 0) |n|) ((_ extract 10 0) |n|)) ((_ extract 10 0) |i|)) #b0)))
(declare-const |n| (_ BitVec 11)) 
(declare-const |i| (_ BitVec 11)) 
(assert (not (assertion.0 |n| |i|)))
(check-sat)