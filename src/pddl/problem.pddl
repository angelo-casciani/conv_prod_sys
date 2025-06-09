(define (problem reasoners_prob)
    (:domain reasoners)
    (:objects 
        T1 T2 T3
    )
    (:init
        (validation T1)
        (simulation T2)
        (validation T3)
        (current T2)
        (next T2 T3)
        (next T3 T1)
    )
    
    (:goal
        (and
        (called T1)
        (called T2)
        (called T3)
        )
    )
)