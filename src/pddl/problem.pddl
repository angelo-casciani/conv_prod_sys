(define (problem reasoners_prob)
    (:domain reasoners)
    (:objects 
        P - process
        I1 - input 
        T1 - output
    )
    (:init
        (has_pieces I1)
        (state T1)
    )
    
    (:goal
        (trace T1)
    )
)