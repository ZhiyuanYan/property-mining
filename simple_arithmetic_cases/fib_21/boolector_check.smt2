(define-fun assertion.0 ((|n| (_ BitVec 11)) (|k| (_ BitVec 11)) (|i| (_ BitVec 11)) ) Bool (=> (= #b00000101000 ((_ extract 10 0) |n|)) (bvule #b00000101000 (bvsub (bvor ((_ extract 10 0) |n|) ((_ extract 10 0) |k|)) (bvand ((_ extract 10 0) |i|) ((_ extract 10 0) |i|))))))
(declare-const |n| (_ BitVec 11)) 
(declare-const |k| (_ BitVec 11)) 
(declare-const |i| (_ BitVec 11)) 
(assert (not (assertion.0 |n| |k| |i|)))
(check-sat)