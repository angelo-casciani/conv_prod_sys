(define (domain reasoners)
    (:requirements :strips :typing :conditional-effects :action-costs) 
    
    (:predicates
        (validation ?x)
        (simulation ?x)
        (validation_called ?x)
        (simulation_called ?x)
        (priority ?x)
    )

    (:action call_validator
        :parameters (?x)
        :precondition (and
        (validation ?x)
        (or
            (priority ?x)
            (forall (?y)
                (not          
                    (and 
                        (priority ?y) 
                        (simulation ?y)
                    )       
                )
            )
        )
        )
        :effect
        (validation_called ?x)
    )

    (:action call_simulator
    :parameters (?x)
    :precondition (and
        (simulation ?x)
        (or
            (priority ?x)
            (forall (?y)
                (not          
                    (and
                        (priority ?y) 
                        (validation ?y)
                        (not (= ?x ?y))
                    )       
                )
            )
        )
    )
    :effect
        (simulation_called ?x)
)
)