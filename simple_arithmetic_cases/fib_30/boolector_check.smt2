(define-fun assertion.0 ((|n| (_ BitVec 11)) (|c| (_ BitVec 11)) ) Bool (=> (= #b00010010110 (bvor (bvand ((_ extract 10 0) |c|) ((_ extract 10 0) |n|)) (bvand ((_ extract 10 0) |n|) ((_ extract 10 0) |n|)))) (bvule (bvadd ((_ extract 10 0) |n|) ((_ extract 10 0) |c|)) #b11111111001)))
(declare-const |n| (_ BitVec 11)) 
(declare-const |c| (_ BitVec 11)) 
(assert (not (assertion.0 |n| |c|)))
(check-sat)