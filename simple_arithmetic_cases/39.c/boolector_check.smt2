(define-fun assertion.0 ((|n| (_ BitVec 10)) (|c| (_ BitVec 10)) ) Bool (=> (bvule ((_ extract 9 0) |c|) (bvsub (bvand ((_ extract 9 0) |n|) ((_ extract 9 0) |n|)) #b1111111111)) (bvule (bvadd (bvand ((_ extract 9 0) |n|) ((_ extract 9 0) |c|)) (bvsub ((_ extract 9 0) |n|) ((_ extract 9 0) |c|))) (bvadd (bvor ((_ extract 9 0) |n|) ((_ extract 9 0) |c|)) #b0111110100))))
(declare-const |n| (_ BitVec 10)) 
(declare-const |c| (_ BitVec 10)) 
(assert (not (assertion.0 |n| |c|)))
(check-sat)