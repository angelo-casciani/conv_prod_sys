(define (problem reasoners_prob)
    (:domain reasoners)
    (:objects 
        T1 T2
    )
    (:init
        (validation T1)
        (simulation T2)
        (priority T1)
    )
    
    (:goal
        (and
        (validation_called T1)
        (simulation_called T2)
        )
    )
)