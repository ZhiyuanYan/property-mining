(define-fun assertion.0 ((|c| (_ BitVec 11)) ) Bool (bvule ((_ extract 10 0) |c|) (bvadd #b00000000100 ((_ extract 10 0) |c|))))
(declare-const |c| (_ BitVec 11)) 
(assert (not (assertion.0 |c|)))
(check-sat)