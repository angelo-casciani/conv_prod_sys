(define (domain reasoners)
    (:requirements :strips :typing :conditional-effects :action-costs) 

    (:types
        input process output station - object
    )
    (:predicates
        ;; Simulation
        (deadlock_free ?x - process) 
        (has_pieces ?x)
        (has_time ?x)
        (produced_from ?x ?y)
        (next_station ?x ?y)
        (target_station ?s - station)
        ;; Verification
        (state ?x)
        (reachable ?x)
        (reachable_from ?x ?y)
        (eventually_reachable ?x)
        (trace ?x)
        (stay ?x)
        (forever ?x)
        ;; Maintenance
        (requires_maintenance ?s - station)
        (is_maintained ?s - station)
        (simulation_done)
    )

    (:action simulate_time_with_station
        :parameters (?x - input ?s - station ?y - process ?z - output)
        :precondition (and (deadlock_free ?y) (has_pieces ?x) (target_station ?s))
        :effect (and (has_time ?z) (produced_from ?x ?z) (simulation_done))
        )

    (:action simulate_pieces_with_station
        :parameters (?x - input ?s - station ?y - process ?z - output)
        :precondition (and (deadlock_free ?y) (has_time ?x)  (target_station ?s))
        :effect (and (has_pieces ?z) (produced_from ?z ?x) (simulation_done))
    )

    (:action simulate_next_station
        :parameters (?x - station  ?z - station ?y - process)
        :precondition (and (deadlock_free ?y) )
        :effect (and (next_station ?x ?z))
    )
    
    (:action validate_deadlock
        :parameters (?x - process)
        :precondition ()
        :effect (and (deadlock_free ?x))
    )

    (:action validate_reachable_state
        :parameters (?x - input)
        :precondition (and (state ?x))
        :effect (and (reachable ?x))
    )

    (:action validate_reachable_state_with_time
        :parameters (?x - input ?y - input)
        :precondition (and (state ?x) (has_time ?y))
        :effect (and (reachable ?x))
    )

    (:action validate_eventual_reachable_state
        :parameters (?x - input)
        :precondition (and (state ?x))
        :effect (and (eventually_reachable ?x))
    )

    (:action validate_trace
        :parameters (?x - output ?y - output)
        :precondition (and (has_time ?x))
        :effect (and (trace ?y))
    )

    (:action validate_stay_in_state
        :parameters (?x - input ?y - input)
        :precondition (and (state ?x) (has_time ?y))
        :effect (and (stay ?x))
    )
    
    (:action validate_forever_state
        :parameters (?x - input)
        :precondition (and (state ?x))
        :effect (and (forever ?x))
    )
    
    (:action validate_reachable_from_state
        :parameters (?x - input ?y - input)
        :precondition (and (state ?x) (state ?y))
        :effect (and (reachable_from ?x ?y))
    )
    
    (:action maintenance
        :parameters (?s - station)
        :precondition (and (requires_maintenance ?s) (simulation_done))
        :effect (and (not (requires_maintenance ?s))
                    (is_maintained ?s))
    )

    ;TO DO
    ;Process mining actions, understand the possible dependencies with other modules
    
)