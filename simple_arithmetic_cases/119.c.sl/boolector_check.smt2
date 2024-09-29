(define-fun assertion.0 ((|x| (_ BitVec 8)) (|y| (_ BitVec 8)) (|size| (_ BitVec 8)) ) Bool (=> (bvule (= ((_ extract 7 0) |x|) (bvadd ((_ extract 7 0) |y|) ((_ extract 7 0) |size|))) (= #b11100101 (bvsub ((_ extract 7 0) |size|) ((_ extract 7 0) |y|)))) (bvule (= ((_ extract 7 0) |x|) (bvadd ((_ extract 7 0) |y|) ((_ extract 7 0) |size|))) (= #b00000000 (bvsub ((_ extract 7 0) |size|) ((_ extract 7 0) |y|))))))
(declare-const |x| (_ BitVec 8)) 
(declare-const |y| (_ BitVec 8)) 
(declare-const |size| (_ BitVec 8)) 
(assert (not (assertion.0 |x| |y| |size|)))
(check-sat)