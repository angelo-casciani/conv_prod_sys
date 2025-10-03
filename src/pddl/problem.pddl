(define (problem reasoners_prob)
    (:domain reasoners)
    (:objects 
        I - input
        P - process
        O - output
        A1 A2 A3 A4 A5 - activity
    )
    (:init
        (has_pieces I) 
        (requires_maintenance A4) 
        (is_maintained A1) 
        (is_maintained A2) 
        (is_maintained A3) 
        (is_maintained A5) 
        (target_activity A4)
    )
    
    (:goal
        (and (has_time O) (is_maintained A4))
    )
)