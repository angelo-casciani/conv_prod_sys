(define (problem reasoners_prob)
    (:domain reasoners)
    (:objects 
        I - input
        P - process
        O - output
        station11 station21 station31 station41 station51 - activity
    )
    (:init
        (has_pieces I) 
        (requires_maintenance station41) 
        (is_maintained station11) 
        (is_maintained station21) 
        (is_maintained station31) 
        (is_maintained station51) 
        (target_activity station41)
    )
    
    (:goal
        (and (has_time O) (is_maintained station41))
    )
)