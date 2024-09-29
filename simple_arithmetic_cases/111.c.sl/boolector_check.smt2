(define-fun assertion.0 ((|sn| (_ BitVec 10)) ) Bool (bvule (bvand ((_ extract 9 0) |sn|) (bvor ((_ extract 9 0) |sn|) ((_ extract 9 0) |sn|))) #b0100101100))
(declare-const |sn| (_ BitVec 10)) 
(assert (not (assertion.0 |sn|)))
(check-sat)