(define (domain reasoners)
    (:requirements :strips :typing :conditional-effects :action-costs) 
    
    (:predicates
        (validation ?x)
        (simulation ?x)
        (next ?x ?y)
        (current ?x)
        (called ?x)
    )

    (:action call_validator
        :parameters (?x)
        :precondition (and
        (validation ?x)
        (current ?x)
        )
        :effect (and 
            (called ?x)
            (not (current ?x))
            (forall (?y) (when (next ?x ?y) (current ?y)))
        )
    )

   (:action call_simulator
        :parameters (?x)
        :precondition (and
        (simulation ?x)
        (current ?x)
        )
        :effect (and 
            (called ?x)
            (not (current ?x))
            (forall (?y) (when (next ?x ?y) (current ?y)))
        )
    )
)