(define-fun assertion.0 ((|j| (_ BitVec 11)) (|i| (_ BitVec 11)) (|k| (_ BitVec 11)) ) Bool (=> (= (= ((_ extract 10 0) |j|) ((_ extract 10 0) |k|)) #b0) (bvule ((_ extract 10 0) |j|) ((_ extract 10 0) |i|))))
(declare-const |j| (_ BitVec 11)) 
(declare-const |i| (_ BitVec 11)) 
(declare-const |k| (_ BitVec 11)) 
(assert (not (assertion.0 |j| |i| |k|)))
(check-sat)