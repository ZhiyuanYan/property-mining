(define-fun assertion.0 ((|y| (_ BitVec 11)) (|x| (_ BitVec 11)) ) Bool (=> (bvule (bvor ((_ extract 10 0) |y|) (bvand ((_ extract 10 0) |x|) ((_ extract 10 0) |y|))) #b00011001000) (bvule (bvsub ((_ extract 10 0) |y|) ((_ extract 10 0) |x|)) #b00001100100)))
(declare-const |y| (_ BitVec 11)) 
(declare-const |x| (_ BitVec 11)) 
(assert (not (assertion.0 |y| |x|)))
(check-sat)