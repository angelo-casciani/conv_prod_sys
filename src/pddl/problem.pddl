(define (problem reasoners_prob)
    (:domain reasoners)
    (:objects 
        I - input
        P - process
        O - output
        S1 S2 S3 S4 S5 - station
    )
    (:init
        (has_pieces I)
        (is_maintained S1)
        (is_maintained S3)
        (is_maintained S4)
        (is_maintained S5)
        (is_maintained S2)
        (target_station S2)
    )
    
    (:goal
        (has_time O)
    )
)